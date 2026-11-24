"""Graphics Studio: a team web app around the theme skill packs.

Run:  copy .env.example to .env, set ANTHROPIC_API_KEY, then uvicorn app:app --host 0.0.0.0 --port 8000

A theme = a folder in themes/ (the skill kit: SKILL.md, references/spec_format.md, templates/, assets/, scripts/build.py).
Add a channel by dropping in another kit folder; nothing else changes.
"""
import importlib.util, inspect, json, os, pathlib, re, tempfile, threading, time, uuid, asyncio
from urllib.parse import quote
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, Response, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

ROOT = pathlib.Path(__file__).parent
load_dotenv(ROOT / ".env")
import copy

import asset_gen, audio_transcribe, toolkit, la_link, z1_plates, bulletin, claude_client, critique, episode_audio, exporter, mf_studio, spec_enrich, storyboard_csv, storyboard_pdf, theme_canvas
from frame_edit_util import (
    apply_flat_paste_replace,
    apply_layer_reference_replace,
    finalize_reference_edit,
    merge_els_edit,
    merge_item_edit,
    mf_path_item_index,
    normalize_cards_items,
    remove_scene_illustrations,
    strip_upload_assets,
)
from claude_client import _storyboard_line_for_frame
from db_store import SQLITE_PATH, backend, connect, insert_project
THEMES = ROOT / "themes"
_HINDI_CAST_LOCK = threading.Lock()
_EXPORT_JOB_DIR = pathlib.Path(tempfile.gettempdir()) / "graphics_studio_exports"
_EXPORT_JOB_DIR.mkdir(parents=True, exist_ok=True)
_EXPORT_JOBS: dict[str, dict] = {}
_EXPORT_JOB_LOCK = threading.Lock()
_EXPORT_RENDER_SLOTS = threading.Semaphore(
    max(1, int(os.environ.get("EXPORT_MAX_CONCURRENT", "1")))
)


def _export_load_snapshot() -> tuple[int, int]:
    with _EXPORT_JOB_LOCK:
        queued = sum(1 for j in _EXPORT_JOBS.values() if j.get("status") == "queued")
        running = sum(1 for j in _EXPORT_JOBS.values() if j.get("status") == "running")
    return queued, running
def preview_base() -> str:
    """Loopback URL for Playwright inside this container (Render sets PORT, not 8000)."""
    port = os.environ.get("PORT", "8000")
    return f"http://127.0.0.1:{port}"


def preview_url(pid: int, fid: str) -> str:
    return f"{preview_base()}/preview/{pid}/{quote(str(fid), safe='')}"
app = FastAPI(title="Graphics Studio")
# LA Studio runs on each computer (127.0.0.1:8770, staging 8771) and reads the hierarchy / links from here.
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
# Any local LA Studio port 8700-8799 (live 8770, staging 8771, test copies via LA_PORT).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(127\.0\.0\.1|localhost):87\d\d$",
    allow_origins=[o.strip() for o in os.environ.get("STUDIO_CORS_ORIGINS", "").split(",") if o.strip()],
    allow_methods=["GET", "POST"], allow_headers=["*"],
)
try:   # generated pictures live on the Railway volume (asset_gen.use_persistent_storage): served through a link
    _linked = asset_gen.use_persistent_storage()
    if _linked:
        print(f"asset_gen: generated pictures kept on the volume ({asset_gen.persist_dir()}) for {_linked} kit(s)")
except Exception as _e:
    print(f"asset_gen: volume link skipped ({_e})")
app.mount("/themes", StaticFiles(directory=THEMES, follow_symlink=True), name="themes")


@app.on_event("startup")
async def _restore_generated_assets():
    # a roomier pool for asyncio.to_thread (database calls, picture restores): the default is cpu+4 threads
    import concurrent.futures
    asyncio.get_running_loop().set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=48))
    # Railway wipes the disk on deploy; generated assets live in the DB and are written back here, in the
    # background: the server answers at once, and a picture someone opens first is fetched on demand.
    async def restore():
        n = await asyncio.to_thread(asset_gen.restore_all)
        if n:
            print(f"asset_gen: restored {n} generated asset(s)")
    app.state.restore_task = asyncio.create_task(restore())


def _z1_frame_gen(spec: dict, frame: dict) -> dict:
    """The spec.gen entries (picture prompts) a Zero1 Hindi frame uses, without file paths."""
    gen = (spec or {}).get("gen") or {}
    keys = set(z1_plates.GEN_RE.findall(json.dumps(frame, ensure_ascii=False)))
    return {k: {kk: vv for kk, vv in gen[k].items() if kk != "file"} for k in sorted(keys) if isinstance(gen.get(k), dict)}


async def _z1_after_edit(pid: int, spec: dict, new: dict, regenerate: bool) -> tuple[dict, dict]:
    """After Claude edits a Zero1 Hindi frame: its picture prompts (frame.gen) go into spec.gen, where the kit
    reads them, and the pictures are made: new or re-prompted ones always, every one of the frame's on
    Regenerate (fresh images). Before, they stayed in the frame and showed as dashed placeholders."""
    new = dict(new)
    fg = new.pop("gen", None) or {}
    new.pop("_gen", None)
    gen = dict(spec.get("gen") or {})
    changed = []
    for k, e in fg.items():
        if not isinstance(e, dict) or not e.get("prompt"):
            continue
        old = gen.get(k) if isinstance(gen.get(k), dict) else {}
        if old.get("prompt") != e.get("prompt") or not old:
            gen[k] = {**{kk: vv for kk, vv in e.items() if kk != "file"}}
            changed.append(k)
    spec = {**spec, "gen": gen}
    used = sorted(set(z1_plates.GEN_RE.findall(json.dumps(new, ensure_ascii=False))))
    todo = [k for k in used if isinstance(gen.get(k), dict) and gen[k].get("prompt")
            and (regenerate or k in changed or k in z1_plates.pending({**spec, "frames": [new]}))]
    if todo and z1_plates.available():
        filled, _report = await asyncio.to_thread(z1_plates.fill, {**spec, "frames": [new]}, print, regenerate, todo, _pdf_ref(pid))
        spec = {**spec, "gen": filled.get("gen") or gen}
    return new, spec


async def _db_call(fn, *a, **kw):
    """A database call from an async handler, run on a worker thread: the server keeps answering everyone else
    while it waits (a slow query used to freeze every page, seen in browsers as ERR_HTTP2_PING_FAILED)."""
    return await asyncio.to_thread(fn, *a, **kw)


_GEN_PATH = re.compile(r"^/themes/([A-Za-z0-9_-]+)/assets/gen/([^/]+)$")


# ---------- what each Claude call cost (Cost window) ----------
import contextvars
_CUR_PROJECT: contextvars.ContextVar = contextvars.ContextVar("gs_project", default=None)
_PID_PATH = re.compile(r"^/api/projects/(\d+)/")
_USAGE_SCHEMA = """CREATE TABLE IF NOT EXISTS usage_log (
    ts DOUBLE PRECISION, label TEXT, model TEXT, project_id INTEGER, input_tokens INTEGER, cache_read INTEGER,
    cache_write INTEGER, cache_write_1h INTEGER, output_tokens INTEGER, cost DOUBLE PRECISION)"""
_SETTINGS_SCHEMA = "CREATE TABLE IF NOT EXISTS studio_settings (skey TEXT PRIMARY KEY, svalue TEXT)"
SETTING_DEFAULTS = {"fix_light": "on"}   # cheaper layout fixes unless switched back in Settings
SETTINGS_ALLOWED = {"sb_split": ("off", "on"), "pdf_light": ("off", "on"), "fix_light": ("off", "on")}
_SETTINGS_CACHE: dict = {"at": 0.0, "v": {}}


def _usage_ensure(c) -> None:
    from db_store import once

    def make(conn):
        conn.execute(_USAGE_SCHEMA)
        conn.execute(_SETTINGS_SCHEMA)
        conn.commit()
    once("usage_log", c, make)


def _record_usage(label: str, model: str, u: dict) -> None:
    with connect() as c:
        _usage_ensure(c)
        c.execute("insert into usage_log(ts,label,model,project_id,input_tokens,cache_read,cache_write,cache_write_1h,"
                  "output_tokens,cost) values(?,?,?,?,?,?,?,?,?,?)",
                  (time.time(), label[:40], model[:60], _CUR_PROJECT.get(), int(u.get("input") or 0), int(u.get("cache_read") or 0),
                   int(u.get("cache_write") or 0), int(u.get("cache_write_1h") or 0), int(u.get("output") or 0),
                   round(claude_client.cost_usd(model, u), 6)))
        c.commit()


def _settings() -> dict:
    if time.time() - _SETTINGS_CACHE["at"] < 20:
        return _SETTINGS_CACHE["v"]
    try:
        with connect() as c:
            _usage_ensure(c)
            v = {r["skey"]: r["svalue"] for r in c.execute("select skey,svalue from studio_settings").fetchall()}
    except Exception:
        v = _SETTINGS_CACHE["v"]
    _SETTINGS_CACHE.update(at=time.time(), v=v)
    return v


claude_client.USAGE_SINK = _record_usage
claude_client.SETTING = lambda k: _settings().get(k)


@app.get("/api/usage")
def usage(days: int = 30):
    """Cost by job (storyboard, PDF batch, frame edit, pictures …) and by day, from the record of every Claude call."""
    days = max(1, min(int(days or 30), 120))
    since = time.time() - days * 86400
    with connect() as c:
        _usage_ensure(c)
        rows = [dict(r) for r in c.execute("select ts,label,model,project_id,input_tokens,cache_read,cache_write,"
                                           "output_tokens,cost from usage_log where ts>=? order by ts", (since,)).fetchall()]
    jobs: dict = {}
    by_day: dict = {}
    projects: dict = {}
    for r in rows:
        k = (r["label"], r["model"])
        j = jobs.setdefault(k, {"label": r["label"], "model": r["model"], "calls": 0, "input": 0, "cache_read": 0,
                                "cache_write": 0, "output": 0, "cost": 0.0})
        j["calls"] += 1
        for a, b in (("input", "input_tokens"), ("cache_read", "cache_read"), ("cache_write", "cache_write"), ("output", "output_tokens")):
            j[a] += int(r[b] or 0)
        j["cost"] += float(r["cost"] or 0)
        day = time.strftime("%Y-%m-%d", time.gmtime(r["ts"]))
        d = by_day.setdefault(day, {"day": day, "cost": 0.0, "calls": 0, "jobs": {}})
        d["cost"] += float(r["cost"] or 0); d["calls"] += 1
        d["jobs"][r["label"]] = d["jobs"].get(r["label"], 0.0) + float(r["cost"] or 0)
        if r["project_id"]:
            projects[r["project_id"]] = projects.get(r["project_id"], 0.0) + float(r["cost"] or 0)
    names = {}
    if projects:
        with connect() as c:
            ids = list(projects)[:200]
            q = ",".join("?" * len(ids))
            names = {r["id"]: r["name"] for r in c.execute(f"select id,name from projects where id in ({q})", ids).fetchall()}
    top = sorted(({"id": k, "name": names.get(k, f"#{k}"), "cost": round(v, 4)} for k, v in projects.items()),
                 key=lambda x: -x["cost"])[:10]
    return {"days": days, "since": since, "total": round(sum(j["cost"] for j in jobs.values()), 4), "calls": len(rows),
            "jobs": sorted(({**j, "cost": round(j["cost"], 4)} for j in jobs.values()), key=lambda x: -x["cost"]),
            "by_day": [{**d, "cost": round(d["cost"], 4)} for d in sorted(by_day.values(), key=lambda x: x["day"])],
            "projects": top, "settings": {k: (_settings().get(k) or ("on" if claude_client.setting_on(k, {"sb_split": "STUDIO_SB_SPLIT", "fix_light": "STUDIO_FIX_LIGHT"}.get(k, ""), SETTING_DEFAULTS.get(k, "off")) else "off")) for k in SETTINGS_ALLOWED}}


@app.put("/api/settings")
async def put_setting(req: Request):
    b = await req.json()
    k, v = str(b.get("key") or ""), str(b.get("value") or "")
    if k not in SETTINGS_ALLOWED or v not in SETTINGS_ALLOWED[k]:
        raise HTTPException(400, "unknown setting")

    def put():
        with connect() as c:
            _usage_ensure(c)
            c.execute("delete from studio_settings where skey=?", (k,))
            c.execute("insert into studio_settings(skey,svalue) values(?,?)", (k, v))
            c.commit()
    await _db_call(put)
    _SETTINGS_CACHE["at"] = 0.0
    return {"ok": True, "key": k, "value": v}


@app.middleware("http")
async def cache_headers(request, call_next):
    pm = _PID_PATH.match(request.url.path)
    if pm:
        _CUR_PROJECT.set(int(pm.group(1)))   # the cost record knows which video a call was for
    m = _GEN_PATH.match(request.url.path)
    if m and not (THEMES / m.group(1) / "assets" / "gen" / m.group(2)).is_file():
        await asyncio.to_thread(asset_gen.restore_one, m.group(1), m.group(2))   # not restored yet after a deploy
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/api/") or path == "/" or path.startswith("/preview/"):
        response.headers["Cache-Control"] = "no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    elif path.endswith("/render.js") or path.endswith("/components.js"):
        response.headers["Cache-Control"] = "no-store, must-revalidate"
    return response


def _storyboard_pdf_on_disk(pid: int) -> bool:
    return storyboard_pdf.pdf_path(pid).is_file()


def _apply_storyboard_pdf_meta(d: dict) -> dict:
    pid = d["id"]
    has = _storyboard_pdf_on_disk(pid)
    d["has_storyboard_pdf"] = has
    look = d.get("look")
    if not isinstance(look, dict):
        look = {}
    if has and look.get("sb_import") != "script":
        look = {**look, "sb_import": "pdf"}
    d["look"] = look
    d["storyboard_pdf_name"] = (look.get("storyboard_pdf_name") or "").strip()
    return d


def _apply_episode_audio_meta(d: dict) -> dict:
    pid = d["id"]
    d["has_episode_audio"] = episode_audio.has_audio(pid)
    d["has_episode_transcript"] = episode_audio.has_transcript(pid)
    tr = episode_audio.read_transcript(pid) if d["has_episode_transcript"] else None
    segs = (tr or {}).get("segments") or []
    d["episode_transcript_segments"] = len(segs)
    try:
        d["episode_audio_seconds"] = round(float((tr or {}).get("duration") or max(float(s.get("end") or 0) for s in segs)), 1) if segs else None
    except (TypeError, ValueError):
        d["episode_audio_seconds"] = None
    meta = episode_audio.read_meta(pid) or {}
    d["episode_audio_name"] = meta.get("original_name") or ""
    return d


def _episode_transcript_for_project(pid: int) -> dict | None:
    if not episode_audio.has_transcript(pid):
        return None
    return episode_audio.read_transcript(pid)


def load(pid):
    with connect() as c:
        r = c.execute("select * from projects where id=?", (pid,)).fetchone()
    if not r:
        raise HTTPException(404, "project not found")
    d = dict(r)
    d["look"] = json.loads(d["look"] or "{}")
    d["spec"] = json.loads(d["spec"] or "null")
    if is_mf_theme_name(d.get("theme") or "") and d.get("spec"):
        d["spec"] = mf_studio.compact_mf_spec_for_studio(d["spec"])
    return _apply_episode_audio_meta(_apply_storyboard_pdf_meta(d))


def effective_look(p: dict) -> dict:
    """Merge project look with spec.look (topic props: the spec's, else the project default)."""
    pl = {k: v for k, v in (p.get("look") or {}).items() if v not in ([], "", None)}   # empty project fields don't hide the spec's
    spec = p.get("spec") or {}
    sl = spec.get("look") if spec else {}
    if isinstance(sl, str):
        out = {**pl, "look_line": sl}
    elif isinstance(sl, dict):
        out = {**sl, **pl}
    else:
        out = {**pl}
    # Look is archived, so the project's props are only the default (coins): Claude's choice in the spec wins
    spec_props = (sl.get("props") or ([sl["prop"]] if sl.get("prop") else None)) if isinstance(sl, dict) else None
    if spec_props:
        out["props"] = spec_props
    elif pl.get("props"):
        out["props"] = pl["props"]
        out.pop("prop", None)
    if pl.get("look_line"):
        out["look_line"] = pl["look_line"]
    if is_zo_theme_name(p.get("theme") or "") and out.get("plate") in (None, "", "default"):
        out["plate"] = mf_studio.ZO_DEFAULT_PLATE
    return out


def is_mf_theme_name(theme: str) -> bool:
    return (THEMES / theme / "templates" / "render.js").is_file()


def is_zo_theme_name(theme: str) -> bool:
    import theme_alias
    return theme_alias.base(theme) == "zo-product-graphics"


HINDI_THEME_NAMES = frozenset({"varsity-hindi-graphics", "varsity-hindi-fa-graphics"})


def is_hindi_theme_name(theme: str) -> bool:
    return theme in HINDI_THEME_NAMES


def is_hindi_fa_theme_name(theme: str) -> bool:
    return theme == "varsity-hindi-fa-graphics"


MF_OVERLAY_TYPES = frozenset({"ribbon", "definition", "anchor"})


def frame_wants_overlay(theme: str, frame: dict) -> bool:
    """True = full frame (skip html_overlay); False = anchor-style (emit overlay export)."""
    if theme == "zero1-reel-graphics":
        return frame.get("type") in {"ost", "anchor"}
    if z1_plates.is_theme(theme):  # faceless IP: every frame is full screen
        return True
    if is_zo_theme_name(theme):
        return (frame.get("mode") or "fss") == "fss"
    if is_mf_theme_name(theme):
        return frame.get("type") in MF_OVERLAY_TYPES
    return frame.get("mode") == "fss"


def save(pid, author, note, version=True, **fields):
    """version=False: a live preview save (no Undo step)."""
    with connect() as c:
        cur = c.execute("select spec, storyboard from projects where id=?", (pid,)).fetchone()
        if not cur:
            raise HTTPException(404, "project not found")
        if "look" in fields and isinstance(fields["look"], dict):
            lk = dict(fields["look"])
            if _storyboard_pdf_on_disk(pid) and lk.get("sb_import") != "script":
                lk.setdefault("sb_import", "pdf")
            fields["look"] = lk
        if version and ("spec" in fields or "storyboard" in fields):
            c.execute(
                "insert into versions(project_id,spec,storyboard,author,note,ts) values(?,?,?,?,?,?)",
                (pid, cur.get("spec"), cur.get("storyboard"), author, note, time.time()),
            )
        for k in ("look", "spec"):
            if k in fields:
                fields[k] = json.dumps(fields[k], ensure_ascii=False)
        fields.update(updated_by=author, updated_at=time.time())
        c.execute(
            f"update projects set {', '.join(f'{k}=?' for k in fields)} where id=?",
            (*fields.values(), pid),
        )
        c.commit()


def who(req: Request):
    return req.headers.get("x-user-email") or req.headers.get("x-forwarded-user") or "anonymous"


def _raise_claude_gateway(exc: BaseException) -> None:
    import anthropic
    if isinstance(exc, anthropic.APIError):
        body = exc.body if isinstance(getattr(exc, "body", None), dict) else {}
        err = body.get("error", {}) if body else {}
        msg = err.get("message") or getattr(exc, "message", None) or str(exc)
        raise HTTPException(502, detail=f"Claude API: {msg}") from exc
    if isinstance(exc, RuntimeError):
        raise HTTPException(502, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(502, detail=str(exc)) from exc
    raise exc

# ------------------------------------------------------------------ theme engine
_mods = {}
def builder(theme):
    if theme not in _mods:
        p = THEMES / theme / "scripts" / "build.py"
        spec = importlib.util.spec_from_file_location(f"build_{theme}", p); m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m); _mods[theme] = m
    return _mods[theme]

def _coerce_studio_item(it: dict, theme: str) -> dict:
    """Map stray kit item types (e.g. Zo heading) so preview does not KeyError."""
    if not isinstance(it, dict):
        return it
    out = dict(it)
    t = out.get("t")
    if theme in ("varsity-english", "varsity-hindi-graphics"):
        if t == "heading":
            out["t"] = "htab"
            out["text"] = out.get("text") or out.get("heading") or ""
            out.pop("heading", None)
        elif theme == "varsity-english" and t == "formula":
            terms = out.get("terms") or []
            bits = []
            for term in terms:
                if isinstance(term, dict):
                    bits.append(str(term.get("label") or term.get("value") or ""))
            out["t"] = "definition"
            out["text"] = out.get("definition") or " = ".join(b for b in bits if b) or out.get("text") or "Formula"
            out.setdefault("style", "capsule")
        elif theme == "varsity-english" and t == "table":
            out["t"] = "glass_table"
        elif theme == "varsity-hindi-graphics" and t in ("glass_table", "calc_table", "points", "person"):
            if t == "points":
                out["t"] = "bullets"
                out["items"] = out.get("items") or []
            elif t == "person":
                out["t"] = "asset"
                out["src"] = out.get("src") or "props/character_pointing.png"
            else:
                out["t"] = "table"
                out.setdefault("head", out.pop("head", None) or ["", ""])
                out.setdefault("rows", out.get("rows") or [])
    for key in ("items", "extras"):
        if isinstance(out.get(key), list):
            out[key] = [_coerce_studio_item(x, theme) if isinstance(x, dict) else x for x in out[key]]
    return out


def _coerce_frame_for_studio(frame: dict, theme: str) -> dict:
    f = copy.deepcopy(frame)
    if theme in ("varsity-english", "varsity-hindi-graphics"):
        if isinstance(f.get("items"), list):
            f["items"] = [_coerce_studio_item(x, theme) for x in f["items"]]
        if isinstance(f.get("extras"), list):
            f["extras"] = [_coerce_studio_item(x, theme) for x in f["extras"]]
    return f


def frame_for_render(p: dict, frame: dict, *, enrich: bool = False, layers: bool = False) -> dict:
    """Return frame JSON for preview/export. Enrich only at storyboard generation — not on render."""
    theme = p.get("theme") or ""
    f = _coerce_frame_for_studio(frame, theme)
    if z1_plates.is_theme(theme):  # Zero1 Hindi: hand the frame its gen: plates; the kit needs no enrichment
        return z1_plates.attach(p.get("spec") or {}, f, layers)
    if enrich:
        spec_enrich.enrich_spec({"frames": [f], "look": effective_look(p)}, p.get("storyboard") or "", theme=theme)
    return f


def _hindi_merged_cast(spec: dict | None, frame: dict | None) -> dict:
    """Merge spec.cast with inline hints on character items (who + char) when top-level cast is missing or keys mismatch."""
    out: dict = {}
    if isinstance(spec, dict):
        sc = spec.get("cast")
        if isinstance(sc, dict):
            out.update(sc)

    def _has_who_key(w: str) -> bool:
        wl = w.lower()
        return any(isinstance(k, str) and k.lower() == wl for k in out)

    def _ingest_char(who, ch, nm):
        if not isinstance(who, str) or not who.strip():
            return
        if _has_who_key(who):
            return
        if ch is None:
            return
        if isinstance(ch, str) and ch.startswith("c") and ch[1:].isdigit():
            ch_n = ch
        else:
            try:
                ch_n = int(ch)
            except (TypeError, ValueError):
                ch_n = ch
        ent: dict = {"char": ch_n}
        if isinstance(nm, str) and nm.strip():
            ent["name"] = nm.strip()
        out[who.strip()] = ent

    if isinstance(frame, dict):
        for it in frame.get("items") or []:
            if not isinstance(it, dict) or it.get("t") != "character":
                continue
            _ingest_char(it.get("who"), it.get("char"), it.get("name"))
        for e in frame.get("els") or []:
            if not isinstance(e, dict) or e.get("type") != "char":
                continue
            who = e.get("who")
            ch = who if isinstance(who, str) and len(who) == 2 and who[0] == "c" and who[1].isdigit() else None
            _ingest_char(who, ch, e.get("label") or e.get("name"))
    return out


def _invoke_frame_html(render, frame, look, edit, all_frames, *, overlay: bool = False):
    sig = inspect.signature(render)
    params = sig.parameters
    kwargs: dict = {}
    if "edit" in params:
        kwargs["edit"] = edit
    if "overlay" in params:
        kwargs["overlay"] = overlay
    if "all_frames" in params and all_frames is not None:
        kwargs["all_frames"] = all_frames
    if "look" in params:
        if kwargs:
            return render(frame, look, **kwargs)
        return render(frame, look)
    if kwargs:
        return render(frame, **kwargs)
    return render(frame)


def frame_page(
    theme,
    frame,
    look,
    base_href: str | None = None,
    edit: bool = False,
    all_frames=None,
    spec: dict | None = None,
    overlay: bool = False,
):
    mod = builder(theme)
    render = mod.frame_html
    prev_studio_web = os.environ.get("STUDIO_WEB")
    if is_hindi_theme_name(theme):
        os.environ["STUDIO_WEB"] = "1"
    try:
        cattr = getattr(mod, "CAST", None)
        # Hindi build uses module-global CAST; concurrent /preview iframes would clear each other without a lock.
        if is_hindi_theme_name(theme) and isinstance(cattr, dict):
            with _HINDI_CAST_LOCK:
                prev_cast = dict(cattr)
                try:
                    cattr.clear()
                    cattr.update(_hindi_merged_cast(spec if isinstance(spec, dict) else None, frame))
                    html = _invoke_frame_html(
                        render, frame, look, edit, all_frames, overlay=overlay
                    )
                finally:
                    cattr.clear()
                    cattr.update(prev_cast)
        else:
            html = _invoke_frame_html(render, frame, look, edit, all_frames, overlay=overlay)
    finally:
        if prev_studio_web is None:
            os.environ.pop("STUDIO_WEB", None)
        else:
            os.environ["STUDIO_WEB"] = prev_studio_web
    href = base_href if base_href is not None else f"/themes/{theme}/scenes/"
    cw, ch = theme_canvas.canvas_for_theme(theme)
    canvas_meta = f'<meta name="studio-canvas" content="{cw},{ch}">'
    if 'name="studio-canvas"' not in html:
        html = html.replace("<head>", f"<head>{canvas_meta}", 1)
    html = html.replace("<head>", f'<head><base href="{href}">', 1)
    if edit:
        if 'class="studio-edit-mode"' in html:
            html = html.replace(
                'class="studio-edit-mode"',
                'class="studio-edit-mode in-studio-iframe"',
                1,
            )
        elif "<body>" in html:
            html = html.replace("<body>", '<body class="in-studio-iframe">', 1)
        edit_css = (ROOT / "static" / "studio_edit.css").read_text()
        registry_js = (ROOT / "static" / "layer_registry.js").read_text()
        interact_js = (ROOT / "static" / "interact.min.js").read_text()
        edit_js = (ROOT / "static" / "studio_edit.js").read_text()
        html = html.replace("</head>", f"<style>{edit_css}</style></head>", 1)
        html = html.replace(
            "</body>",
            f"<script>{registry_js}</script><script>{interact_js}</script>"
            f"<script>{edit_js}</script></body>",
            1,
        )
    return html

# ------------------------------------------------------------------ API
@app.get("/", response_class=HTMLResponse)
def index():
    html = (ROOT / "static" / "index.html").read_text()
    v = int(max((ROOT / "static" / f).stat().st_mtime for f in ("nx-gs.css", "nx-gs.js")))
    return html.replace("__NXV__", str(v))


@app.get("/static/{name}")
def static_file(name: str):
    """The redesign's own files (Make Graphics in LA Studio's design)."""
    if name not in ("nx-gs.css", "nx-gs.js"):
        raise HTTPException(404, "not found")
    return FileResponse(ROOT / "static" / name, media_type="text/css" if name.endswith(".css") else "text/javascript",
                        headers={"Cache-Control": "public, max-age=31536000"})

@app.get("/api/claude-key")
def claude_key_status():
    return claude_client.key_status()


@app.post("/api/claude-key")
async def claude_key_save(req: Request):
    b = await req.json()
    key = (b.get("key") or "").strip()
    if not key:
        raise HTTPException(400, "key is required")
    claude_client.set_api_key(key)
    return claude_client.key_status()


@app.delete("/api/claude-key")
def claude_key_clear():
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        raise HTTPException(400, "Key is set via ANTHROPIC_API_KEY env; unset that to use a saved key.")
    claude_client.clear_saved_api_key()
    return claude_client.key_status()


@app.get("/api/themes")
def themes(): return sorted(p.name for p in THEMES.iterdir() if (p / "SKILL.md").exists())


@app.get("/api/theme-meta")
def theme_meta():
    return theme_canvas.theme_meta_map()


@app.get("/api/status")
def status():
    import socket
    with connect() as c:
        n = c.execute("select count(*) as n from projects").fetchone()["n"]
    eq, er = _export_load_snapshot()
    out = {
        "project_count": n,
        "backend": backend(),
        "host": socket.gethostname(),
        "export_queued": eq,
        "export_running": er,
        "studio_ui": os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or os.environ.get("GIT_COMMIT")
        or str(int((ROOT / "static" / "index.html").stat().st_mtime)),
    }
    if backend() == "sqlite":
        out["db_path"] = str(SQLITE_PATH)
        out["db_mtime"] = SQLITE_PATH.stat().st_mtime if SQLITE_PATH.exists() else None
    else:
        out["db_path"] = "postgres (DATABASE_URL)"
    return out


@app.get("/api/projects")
def projects():
    with connect() as c:
        return c.execute("select id,name,theme,updated_by,updated_at from projects order by updated_at desc").fetchall()

_DEFAULT_LOOK = {"anchor": "right", "fss": "blue", "props": ["coins"]}


@app.get("/api/projects/summary")
def projects_summary():
    """Everything the video lists show (cards and table) in one call: frames made, the first frame (for the card's
    picture), the kit, the LA Studio project it is the Graphics step of, whether it was sent to Layers, and whether it
    is being made right now. Sorting and filtering happen in the page."""
    with connect() as c:
        rows = c.execute("select id,name,theme,updated_by,updated_at,spec,look from projects order by updated_at desc").fetchall()
    try:
        la = {int(l["project_id"]): l for l in la_link.links()}
    except Exception:
        la = {}
    now = time.time()
    out = []
    for r in rows:
        r = dict(r)
        try:
            spec = json.loads(r.pop("spec") or "null") or {}
        except ValueError:
            spec = {}
        try:
            look = json.loads(r.pop("look") or "{}") or {}
        except ValueError:
            look = {}
        if look.get("toolkit"):   # a kit's toolkit (templates), opened from its own button, not a video
            continue
        frames = [f for f in (spec.get("frames") or []) if isinstance(f, dict)]
        pr = PROGRESS.get(r["id"]) or {}
        running = pr.get("state") == "running" and now - (pr.get("ts") or pr.get("started") or 0) < 900
        l = la.get(r["id"]) or {}
        sent = look.get("sent_layers") or 0
        out.append({**r, "frames": len(frames), "first_fid": str(frames[0].get("id")) if frames else None,
                    "making": bool(running), "pdf": look.get("sb_import") == "pdf",
                    "pdf_done": bool(spec.get("pdf_done")), "la_project": l.get("la_project"),
                    "la_name": l.get("la_name") or "", "in_layers": bool(sent and len(frames)),
                    "sent_layers": sent, "channel": la_link.channel_of(r.get("theme") or "")})
    return out


@app.post("/api/projects/{pid}/sent-layers")
def mark_sent_layers(pid: int):
    """Make Layers sent this video's frames to LA Studio: the lists show it as "In Layers". No Undo step."""
    with connect() as c:
        row = c.execute("select look from projects where id=?", (pid,)).fetchone()
        if not row:
            raise HTTPException(404, "project not found")
        try:
            look = json.loads(row["look"] or "{}") or {}
        except ValueError:
            look = {}
        look["sent_layers"] = time.time()
        c.execute("update projects set look=? where id=?", (json.dumps(look, ensure_ascii=False), pid))
        c.commit()
    return {"ok": True, "sent_layers": look["sent_layers"]}


_THUMB_DIR = pathlib.Path(tempfile.gettempdir()) / "graphics_studio_thumbs"
_THUMB_SEM = threading.Semaphore(2)


@app.get("/api/projects/{pid}/frames/{fid}/thumb.png")
async def frame_thumb(pid: int, fid: str, w: int = 480):
    """A small picture of one frame for the cards, filmstrip and lists. Cached on disk by the frame's content, so a
    changed frame gets a new picture and an unchanged one is never rendered twice."""
    import hashlib
    p = (await _db_call(load, pid))
    fr = next((f for f in ((p.get("spec") or {}).get("frames") or []) if str(f.get("id")) == fid), None)
    if fr is None:
        raise HTTPException(404, "frame not found")
    w = max(120, min(int(w or 480), 960))
    key = hashlib.sha1(json.dumps([p["theme"], fr, effective_look(p), (p.get("spec") or {}).get("gen"), w],
                                  sort_keys=True, default=str).encode()).hexdigest()[:20]
    path = _THUMB_DIR / f"{pid}_{key}.jpg"
    hdr = {"Cache-Control": "public, max-age=86400"}
    if path.exists():
        return Response(path.read_bytes(), media_type="image/jpeg", headers=hdr)
    pages = _export_pages(p, {fid})
    if not pages:
        raise HTTPException(404, "frame has nothing to draw yet")
    cw, ch = theme_canvas.canvas_for_theme(p["theme"])

    def render() -> bytes:
        from PIL import Image
        import io
        with _THUMB_SEM:
            try:
                files = exporter._SharedBrowser.render(pages, True, (cw, ch), timeout=90)
                png = files.get(f"png/{pages[0][0]}.png")
            except Exception:
                png = None
            if not png:
                png = exporter.export_png(pages, (cw, ch))
        im = Image.open(io.BytesIO(png)).convert("RGB")
        im.thumbnail((w, w * 2))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82)
        return buf.getvalue()

    try:
        data = await asyncio.to_thread(render)
    except Exception as e:
        raise HTTPException(502, detail=f"thumbnail failed: {e}") from e
    _THUMB_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return Response(data, media_type="image/jpeg", headers=hdr)

@app.post("/api/projects")
async def create(req: Request):
    b = await req.json()
    look = {**_DEFAULT_LOOK, **(b.get("look") or {})}
    try:
        pid = (await _db_call(insert_project, 
            b["name"], b.get("theme", "varsity-english"), b.get("script", ""),
            json.dumps(look), who(req), time.time(),
        ))
    except Exception as e:
        raise HTTPException(500, detail=f"Database: {e}") from e
    return (await _db_call(load, pid))

@app.get("/api/projects/{pid}")
def get(pid: int): return load(pid)


def _delete_project(pid: int) -> dict:
    with connect() as c:
        if not c.execute("select id from projects where id=?", (pid,)).fetchone():
            raise HTTPException(404, "project not found")
        c.execute("delete from versions where project_id=?", (pid,))
        c.execute("delete from projects where id=?", (pid,))
        c.commit()
    try:
        for l in la_link.links():
            if l["project_id"] == pid:
                la_link.unlink(l["la_project"])
    except Exception as e:
        print(f"la link cleanup skipped: {e}")
    return {"ok": True}


# ---------------------------------------------------------------- LA Studio (step 1 "Graphics")
@app.get("/api/health/assets")
def health_assets():
    return asset_gen.storage_status()


@app.get("/api/hierarchy")
def la_hierarchy():
    """Channels → kits, for LA Studio's channel list and its new-project kit choice."""
    return la_link.hierarchy(themes())


@app.get("/api/la/links")
def la_links():
    return {"links": la_link.links()}


@app.post("/api/la/link")
async def la_link_route(req: Request):
    """Link an LA Studio project to a Graphics Studio project: an existing one (project_id) or a new one
    (name + theme). Returns the Graphics Studio project."""
    b = await req.json()
    la = str(b.get("la_project") or "")
    if not la_link.LA_ID.match(la):
        raise HTTPException(400, "Missing LA Studio project id")
    pid = b.get("project_id")
    if pid:
        (await _db_call(load, int(pid)))
    else:
        theme = b.get("theme") or ""
        if theme not in themes():
            raise HTTPException(400, "Pick a kit")
        name = (b.get("name") or "").strip()[:120] or "Untitled"
        look = {**_DEFAULT_LOOK, **({"look_line": ""} if theme != "varsity-english" else {})}
        pid = (await _db_call(insert_project, name, theme, "", json.dumps(look), who(req), time.time()))
    (await _db_call(la_link.link, la, int(pid), b.get("la_name") or ""))
    return (await _db_call(load, int(pid)))


@app.post("/api/la/unlink")
async def la_unlink_route(req: Request):
    b = await req.json()
    (await _db_call(la_link.unlink, str(b.get("la_project") or "")))
    return {"ok": True}


@app.get("/api/la/project/{la_project}")
def la_project_lookup(la_project: str):
    pid = la_link.project_for(la_project)
    return {"project_id": pid}


_INLINE_SLOTS = threading.BoundedSemaphore(int(os.environ.get("STUDIO_INLINE_MAX", "2")))


@app.get("/api/projects/{pid}/frames/{fid}/export.html", response_class=HTMLResponse)
def export_frame_html(pid: int, fid: str):
    """One frame as a self-contained HTML (fonts and pictures inlined): what LA Studio's Import Graphics turns
    into an exact layered PSD. At most STUDIO_INLINE_MAX (2) are built at once: each inlines megabytes of
    pictures, and a burst of them used to starve every other request."""
    p = load(pid)
    pages = _export_pages(p, {fid}, layers=True)
    if not pages:
        raise HTTPException(404, "frame not found or not a graphic")
    with _INLINE_SLOTS:
        return HTMLResponse(exporter.frame_page_for_layers(pages[0][1], THEMES / p["theme"],
                                                           theme_canvas.canvas_for_theme(p["theme"])))


# ---------------------------------------------------------------- toolkit (ZO Product): ready-made frames
def _toolkit_project(theme: str) -> dict:
    """The kit's toolkit project (created the first time)."""
    with connect() as c:
        rows = c.execute("select id, look from projects where theme=? order by id", (theme,)).fetchall()
    for r in rows:
        try:
            if (json.loads(r["look"] or "{}") or {}).get("toolkit"):
                return load(r["id"])
        except ValueError:
            pass
    pid = insert_project(toolkit.NAME.get(theme, "Toolkit"), theme, "", json.dumps({**_DEFAULT_LOOK, "toolkit": True}),
                         "toolkit", time.time())
    save(pid, "toolkit", "toolkit created", spec={"frames": []})
    return load(pid)


def _need_toolkit(theme: str):
    if not toolkit.enabled(theme):
        raise HTTPException(400, "this kit has no toolkit yet")


@app.get("/api/toolkit")
async def toolkit_get(theme: str):
    _need_toolkit(theme)
    tk = await _db_call(_toolkit_project, theme)
    frames = [f for f in (tk.get("spec") or {}).get("frames") or [] if isinstance(f, dict)]
    return {"pid": tk["id"], "updated_at": tk.get("updated_at"), "templates": [toolkit.template_view(f) for f in frames]}


@app.post("/api/toolkit/save")
async def toolkit_save(req: Request):
    """Save a video's frame as a template."""
    b = await req.json()
    src = await _db_call(load, int(b["pid"]))
    _need_toolkit(src["theme"])
    fr = next((f for f in (src.get("spec") or {}).get("frames") or [] if str(f.get("id")) == str(b["fid"])), None)
    if not fr:
        raise HTTPException(404, "frame not found")
    tk = await _db_call(_toolkit_project, src["theme"])
    spec = dict(tk.get("spec") or {"frames": []})
    frames = list(spec.get("frames") or [])
    t = toolkit.from_frame(src, fr, b.get("name") or "", frames)
    spec["frames"] = frames + [t]
    await _db_call(save, tk["id"], who(req), f"template saved: {t['name']}", spec=spec)
    return {"pid": tk["id"], "template": toolkit.template_view(t)}


@app.post("/api/toolkit/blank")
async def toolkit_blank(req: Request):
    """A new template on one of the kit's presenter photos."""
    b = await req.json()
    theme = b.get("theme") or "zo-product-graphics"
    _need_toolkit(theme)
    tk = await _db_call(_toolkit_project, theme)
    spec = dict(tk.get("spec") or {"frames": []})
    frames = list(spec.get("frames") or [])
    t = toolkit.blank(b.get("plate") or "m2_right", frames)
    spec["frames"] = frames + [t]
    await _db_call(save, tk["id"], who(req), "new template", spec=spec)
    return {"pid": tk["id"], "template": toolkit.template_view(t)}


@app.post("/api/toolkit/psd")
async def toolkit_psd(req: Request, theme: str = Form(...), file: UploadFile = File(...)):
    """A template from a layered PSD (photo layer + live text + shapes + pictures)."""
    _need_toolkit(theme)
    raw = await file.read()
    tk = await _db_call(_toolkit_project, theme)
    spec = dict(tk.get("spec") or {"frames": []})
    frames = list(spec.get("frames") or [])
    try:
        t = await asyncio.to_thread(toolkit.psd_to_template, raw, theme, frames,
                                    lambda desc, data, ext: asset_gen.store(theme, desc, data, ext, "toolkit"))
    except Exception as e:
        raise HTTPException(400, f"That PSD could not be read ({type(e).__name__}: {str(e)[:160]})")
    t["name"] = re.sub(r"\.psd$", "", file.filename or "", flags=re.I)[:80] or f"Template {len(frames) + 1}"
    spec["frames"] = frames + [t]
    await _db_call(save, tk["id"], who(req), f"template from PSD: {t['name']}", spec=spec)
    return {"pid": tk["id"], "template": toolkit.template_view(t)}


@app.get("/api/projects/{pid}/pdf-lines")
async def pdf_lines(pid: int):
    """The storyboard PDF's text, line by line: what a toolkit frame can be picked for when there is no script."""
    try:
        raw = storyboard_pdf.read_pdf(pid)
    except (FileNotFoundError, ValueError):
        return {"lines": []}
    return {"lines": await asyncio.to_thread(toolkit.pdf_lines, raw)}


@app.post("/api/projects/{pid}/toolkit-frame")
async def toolkit_frame(pid: int, req: Request):
    """Put a copy of a template into this video for the chosen script lines."""
    b = await req.json()
    p = await _db_call(load, pid)
    _need_toolkit(p["theme"])
    tk = await _db_call(_toolkit_project, p["theme"])
    tpl = next((f for f in (tk.get("spec") or {}).get("frames") or [] if str(f.get("id")) == str(b.get("tk_fid"))), None)
    if not tpl:
        raise HTTPException(404, "template not found")
    lines = b.get("lines") or []
    if not (isinstance(lines, list) and len(lines) == 2):
        raise HTTPException(400, "choose the script lines first")
    spec, fid = toolkit.place(p, tpl, tk.get("look") or {}, lines, b.get("text") or "", b.get("src") or "script")
    await _db_call(save, pid, who(req), f"toolkit frame: {tpl.get('name') or tpl.get('id')}", spec=spec)
    return {**(await _db_call(load, pid)), "new_fid": fid}


@app.post("/api/projects/{pid}/z1-split")
async def z1_split_route(pid: int, req: Request):
    """Zero1 Hindi, before Make Layers: give the characters in the frames' scene plates their own picture (and a clean
    background behind them), so each becomes its own PSD layer. Kept on the plate for next time."""
    b = await req.json()
    p = await _db_call(load, pid)
    if not z1_plates.is_theme(p.get("theme") or ""):
        return {"split": [], "kept": {}, "failed": {}, "already": 0}

    async def job():
        import z1_split
        ids = {str(x) for x in (b.get("ids") or [f.get("id") for f in (p.get("spec") or {}).get("frames") or []])}
        new_spec, rep = await asyncio.to_thread(z1_split.split_frames, p.get("spec") or {}, ids)
        if rep["split"] or rep["kept"]:
            def save():   # straight onto the stored spec (no Undo step): only the split records are added
                with connect() as c:
                    row = c.execute("select spec from projects where id=?", (pid,)).fetchone()
                    cur = json.loads((row or {}).get("spec") or "null") if row else None
                    if not isinstance(cur, dict):
                        return
                    gen = dict(cur.get("gen") or {})
                    for k, v in (new_spec.get("gen") or {}).items():
                        if isinstance(gen.get(k), dict) and isinstance(v, dict) and v.get("split") and v["split"].get("of") == gen[k].get("file"):
                            gen[k] = {**gen[k], "split": v["split"]}
                    cur["gen"] = gen
                    c.execute("update projects set spec=? where id=?", (json.dumps(cur, ensure_ascii=False), pid))
                    c.commit()
            await _db_call(save)
        return rep
    return _stream_json(job())


@app.delete("/api/projects/{pid}")
def delete_project(pid: int):
    return _delete_project(pid)


@app.post("/api/projects/{pid}/delete")
def delete_project_post(pid: int):
    return _delete_project(pid)


@app.post("/api/projects/{pid}/storyboard")
async def make_storyboard(pid: int, req: Request):
    """Generate runs 3–6 min (thinking + render review). Railway closes a request after 5 min with no
    bytes sent, so stream a space every 15 s and send the JSON at the end (leading spaces are valid JSON).
    Errors after streaming starts come back as {"__stream_error": "..."}; the UI's api() raises on it."""
    b = await req.json()
    (await _db_call(load, pid))  # 404 before streaming starts
    return _stream_json(_make_storyboard(pid, b, who(req)))


def _stream_json(coro) -> StreamingResponse:
    """Run a long job, sending a space every 15 s so Railway's 5-min idle cut-off never fires,
    then the JSON result (leading spaces are valid JSON). Errors become {"__stream_error": ...}."""
    task = asyncio.create_task(coro)

    async def body():
        while True:
            done, _ = await asyncio.wait({task}, timeout=15)
            if done:
                break
            yield b" "
        try:
            yield json.dumps(task.result(), default=str).encode()
        except HTTPException as e:
            yield json.dumps({"__stream_error": str(e.detail), "status": e.status_code}).encode()
        except Exception as e:
            yield json.dumps({"__stream_error": f"{type(e).__name__}: {e}", "status": 500}).encode()

    return StreamingResponse(body(), media_type="application/json")


def _with_assets(theme: str, finalize, report: dict, pdf: dict | None = None, on_plate=None):
    """finalize → then replace TODO asset placeholders (runs again after each critique fix)."""
    def fin(sp):
        if finalize:
            sp = finalize(sp)
        if z1_plates.is_theme(theme):
            sp, r = z1_plates.fill(sp, log=print, pdf=pdf, on_plate=on_plate)
        else:
            sp, r = asset_gen.fill_spec(theme, sp, log=print)
        report.setdefault("filled", {}).update(r["filled"])
        report.setdefault("failed", {}).update(r["failed"])
        for d in r["filled"]:
            report["failed"].pop(d, None)
        return sp
    return fin


def _pdf_ref(pid: int) -> dict | None:
    """The project's storyboard PDF for plate references (cache name changes when the PDF is replaced)."""
    path = storyboard_pdf.pdf_path(pid)
    if not path.is_file():
        return None
    return {"path": str(path), "key": f"{pid}_{int(path.stat().st_mtime)}"}


# ---------------------------------------------------------------- live preview (Zero1 Hindi)
# Same storyboard call, same plates, same review as before; the only difference is that frames and plates are
# saved as they appear, so the page can show them instead of waiting for the end. The page polls /progress.
PROGRESS: dict[int, dict] = {}


def _live(pid: int, run: str) -> bool:
    return (PROGRESS.get(pid) or {}).get("run") == run


def _progress(pid: int, run: str, **kw) -> bool:
    if not _live(pid, run):
        return False
    PROGRESS[pid] = {**PROGRESS[pid], **kw, "ts": time.time()}
    return True


def _bump(pid: int, run: str):
    if _live(pid, run):
        PROGRESS[pid]["rev"] = int(PROGRESS[pid].get("rev") or 0) + 1


STOP: dict[int, float] = {}   # pid -> when someone pressed Stop: a run that started before is not saved


def _stopped(pid: int, since: float) -> bool:
    return STOP.get(pid, 0) > since


@app.post("/api/projects/{pid}/stop")
def stop_generating(pid: int):
    """Stop: whatever is being written for this video is thrown away when it comes back (the call already running
    with Claude finishes, but nothing more is spent on it: no pictures, no layout check, nothing saved)."""
    STOP[pid] = time.time()
    if (PROGRESS.get(pid) or {}).get("state") == "running":
        PROGRESS[pid] = {**PROGRESS[pid], "run": "stopped", "state": "error", "msg": "Stopped", "ts": time.time()}
    return {"stopped": True}


@app.get("/api/projects/{pid}/progress")
def project_progress(pid: int):
    cur = dict(PROGRESS.get(pid) or {"state": "idle", "rev": 0})
    cur.pop("run", None)
    now = time.time()
    cur["others"] = sum(1 for k, v in PROGRESS.items()
                        if k != pid and v.get("state") == "running" and now - (v.get("ts") or v.get("started") or 0) < 900)
    if cur.get("started") and cur.get("state") == "running":
        cur["elapsed"] = round(time.time() - cur["started"])
    return cur


def _merge_gen(pid: int, key: str, path: str) -> dict:
    spec = dict(load(pid).get("spec") or {})
    g = dict(spec.get("gen") or {})
    g[key] = {**(g.get(key) or {}), "file": path}
    spec["gen"] = g
    return spec


async def _z1_job(pid: int, user: str, run: str, b: dict, look: dict, script: str, before: dict):
    theme = "zero1-hindi-graphics"
    t0 = time.time()
    shown = [0]

    def on_partial(snap: dict):            # worker thread: frames Claude has finished writing so far
        if not _live(pid, run):
            return
        sp = snap.get("spec") if isinstance(snap.get("spec"), dict) else {}
        frames = [f for f in (sp.get("frames") or [])[:-1] if isinstance(f, dict) and f.get("id") and f.get("type")]
        if not frames:
            n = len(re.findall(r"(?m)^\s*#\d+", snap.get("storyboard") or ""))
            _progress(pid, run, stage="writing", msg=f"Writing the storyboard… {n} beats so far" if n else "Writing the storyboard…")
            return
        if len(frames) == shown[0]:
            return
        shown[0] = len(frames)
        part = {k: v for k, v in sp.items() if k != "frames"}
        part["frames"] = frames
        save(pid, user, "", version=False, storyboard=snap.get("storyboard") or "", spec=part)
        _bump(pid, run)
        _progress(pid, run, stage="frames", msg=f"{len(frames)} frames written so far…")

    def call():
        with claude_client.partial_hook(on_partial):
            return claude_client.storyboard(THEMES / theme, script, look, b.get("notes", ""),
                                            episode_transcript=_episode_transcript_for_project(pid))
    try:
        try:
            out = await asyncio.to_thread(call)
        except Exception as e:
            try:
                _raise_claude_gateway(e)
            except HTTPException as he:
                e = RuntimeError(he.detail)
            if _live(pid, run):              # put the previous frames back
                (await _db_call(save, pid, user, "storyboard failed", version=False, spec=before.get("spec"), storyboard=before.get("storyboard") or ""))
                _bump(pid, run)
            _progress(pid, run, state="error", msg=f"Storyboard failed: {e}")
            return
        if not _live(pid, run):
            return
        sb = out.get("storyboard") or ""
        spec = out.get("spec") or {}
        print(f"[z1 {pid}] storyboard {len(spec.get('frames') or [])} frames {time.time() - t0:.0f}s")
        (await _db_call(save, pid, user, "", version=False, storyboard=sb, spec=spec))
        _bump(pid, run)
        n_plates = len(z1_plates.pending(spec))
        _progress(pid, run, stage="plates", msg=f"All {len(spec.get('frames') or [])} frames written. Making {n_plates} plate(s)…"
                  if n_plates else "All frames written. Checking the renders…")
        made = [0]

        def on_plate(key, path):
            if not _live(pid, run):
                return
            save(pid, user, "", version=False, spec=_merge_gen(pid, key, path))
            made[0] += 1
            _bump(pid, run)
            _progress(pid, run, msg=f"Plates {made[0]}/{n_plates} ready…")

        asset_report: dict = {}
        finalize = _with_assets(theme, None, asset_report, on_plate=on_plate)
        spec = await asyncio.to_thread(finalize, spec)
        if not _live(pid, run):
            return
        _progress(pid, run, stage="review", msg="Checking the rendered frames…")
        critique_report: dict = {}
        try:
            spec, critique_report = await asyncio.to_thread(
                _critique_spec, {**(await _db_call(load, pid)), "look": look}, spec, sb, script, _with_assets(theme, None, asset_report)
            )
        except Exception as e:
            critique_report = {"error": str(e)}
        if not _live(pid, run):
            return
        (await _db_call(save, pid, user, "generated storyboard" + _notes_suffix(critique_report, asset_report), script=script,
             look=look, storyboard=sb, spec=spec))
        _bump(pid, run)
        warn = claude_client.spec_quality_issues(spec, sb, theme=theme)
        warn += [f"layout: {w}" for w in critique_report.get("remaining") or []]
        warn += [f"plate not generated: {d} ({e})" for d, e in (asset_report.get("failed") or {}).items()]
        fixed = critique_report.get("changed") or {}
        bits = [f"{len(spec.get('frames') or [])} frames"]
        if asset_report.get("filled"):
            bits.append(f"{len(asset_report['filled'])} plates made")
        if fixed:
            bits.append(f"review fixed {len(fixed)}")
        _progress(pid, run, state="done", stage="done", msg="Done: " + ", ".join(bits), notes=warn,
                  seconds=round(time.time() - t0))
        print(f"[z1 {pid}] done {time.time() - t0:.0f}s")
    except Exception as e:
        _progress(pid, run, state="error", msg=f"Stopped: {type(e).__name__}: {e}")
        print(f"[z1 {pid}] job error: {e}")


async def _make_storyboard(pid: int, b: dict, user: str):
    t_start = time.time()
    p = (await _db_call(load, pid))
    look = b.get("look", p["look"]); script = b.get("script", p["script"])
    rest = b.get("rest") if isinstance(b.get("rest"), dict) and toolkit.enabled(p["theme"]) else None
    kept: list = []
    if rest:   # keep the toolkit frames; Claude sees their lines marked and writes frames only for the others
        lines = [str(x) for x in rest.get("lines") or []]
        kept = [f for f in (p.get("spec") or {}).get("frames") or []
                if isinstance(f, dict) and f.get("tk_from") and isinstance(f.get("lines"), list) and len(f["lines"]) == 2]
        covered = {i for f in kept for i in range(int(f["lines"][0]), int(f["lines"][1]) + 1)}
        skip = {int(i) for i in rest.get("skip") or [] if str(i).lstrip("-").isdigit()} - covered
        if not [i for i, ln in enumerate(lines) if ln.strip() and i not in covered and i not in skip]:
            raise HTTPException(400, "every line already has a toolkit frame")
        b = {**b, "notes": ((b.get("notes") or "") + "\n" + toolkit.REST_NOTE).strip()}
        claude_script = toolkit.marked_script(lines, covered, skip)
    else:
        claude_script = script
    if z1_plates.is_theme(p["theme"]) and os.environ.get("STUDIO_LIVE_PREVIEW", "1") != "0":
        before = {"spec": p.get("spec"), "storyboard": p.get("storyboard") or ""}
        (await _db_call(save, pid, user, "storyboard started", script=script, look=look,
             **({"spec": p["spec"]} if p.get("spec") else {})))       # keeps the old frames one Undo away
        run = uuid.uuid4().hex
        PROGRESS[pid] = {"run": run, "state": "running", "stage": "writing", "msg": "Writing the storyboard…",
                         "rev": 0, "started": time.time()}
        asyncio.create_task(_z1_job(pid, user, run, b, look, script, before))
        return {**(await _db_call(load, pid)), "background": True}
    try:
        transcript = _episode_transcript_for_project(pid)
        out = await asyncio.to_thread(
            claude_client.storyboard,
            THEMES / p["theme"],
            claude_script,
            look,
            b.get("notes", ""),
            episode_transcript=transcript,
        )
    except Exception as e:
        _raise_claude_gateway(e)
    if _stopped(pid, t_start):
        return {**(await _db_call(load, pid)), "stopped": True}
    theme = p["theme"]
    sb = out.get("storyboard") or ""
    plook = look
    if is_mf_theme_name(theme) and not is_zo_theme_name(theme):
        finalize = mf_studio.compact_mf_spec_for_studio
        spec = finalize(out["spec"])
        plook = {**look}
        if isinstance(spec.get("look"), str):
            plook["look_line"] = spec["look"]
    elif is_zo_theme_name(theme):
        def finalize(sp):
            sp = mf_studio.compact_zo_spec_for_studio(sp)
            if isinstance(look, dict) and look.get("plate") and isinstance(sp.get("look"), dict):
                sp["look"].setdefault("plate", look["plate"])
            return sp
        spec = finalize(out["spec"])
        if rest:
            new = [f for f in spec.get("frames") or [] if isinstance(f, dict) and not str(f.get("id", "")).startswith("tk")]
            spec["frames"] = toolkit.merge_rest(kept, new, [str(x) for x in rest.get("lines") or []], rest.get("src") or "script", skip)
            only_new = {str(f.get("id")) for f in new}
        toolkit.carry(p.get("spec"), spec)
    elif is_hindi_theme_name(theme) or z1_plates.is_theme(theme):
        finalize = None
        spec = out.get("spec") or {}
    else:
        plook = effective_look({**p, "look": look, "spec": out["spec"]})

        def finalize(sp):
            sp["look"] = plook
            return spec_enrich.enrich_spec(sp, sb, theme=theme)
        spec = finalize(out["spec"])
    # Real images for "TODO:<asset>" placeholders (library → Gemini → Claude SVG), so the review sees them.
    asset_report: dict = {}
    finalize = _with_assets(theme, finalize, asset_report)
    spec = await asyncio.to_thread(finalize, spec)
    if _stopped(pid, t_start):
        return {**(await _db_call(load, pid)), "stopped": True}
    # Render → look → fix (the skill's build/WARN/contact-sheet step) before anyone sees the frames.
    critique_report: dict = {}
    try:
        spec, critique_report = await asyncio.to_thread(
            _critique_spec, {**p, "look": plook}, spec, sb, script, finalize,
            (only_new if rest else None)
        )
    except Exception as e:  # never lose a generated spec to a critique failure
        critique_report = {"error": str(e)}
    note = "generated storyboard" + _notes_suffix(critique_report, asset_report)
    (await _db_call(save, pid, user, note, script=script, look=plook, storyboard=sb, spec=spec))
    warn = claude_client.spec_quality_issues(spec, sb, theme=theme)
    warn += [f"layout: {w}" for w in critique_report.get("remaining") or []]
    warn += [f"asset not generated: {d} ({e})" for d, e in (asset_report.get("failed") or {}).items()]
    return {**(await _db_call(load, pid)), "usage": out.get("usage"), "spec_warnings": warn,
            "critique": critique_report, "assets": asset_report}


def _notes_suffix(critique_report: dict, asset_report: dict) -> str:
    bits = []
    if critique_report.get("changed"):
        bits.append(f"auto-fixed {len(critique_report['changed'])} frame(s) after render review")
    if asset_report.get("filled"):
        bits.append(f"generated {len(asset_report['filled'])} asset(s)")
    return f" ({'; '.join(bits)})" if bits else ""


def _critique_spec(p_like: dict, spec: dict, storyboard: str, script: str, finalize, only_ids=None) -> tuple[dict, dict]:
    """Render every frame offline with the kit renderer, then let Claude fix what it sees (critique.py)."""
    theme = p_like["theme"]
    m = builder(theme)
    base = (THEMES / theme / "scenes").as_uri() + "/"

    def render_html(f: dict, sp: dict) -> str:
        pp = {**p_like, "spec": sp}
        return frame_page(
            theme, frame_for_render(pp, f), effective_look(pp),
            base_href=base, all_frames=sp.get("frames") or [], spec=sp,
        )

    def renderable(f: dict) -> bool:
        if is_zo_theme_name(theme):
            return mf_studio.is_zo_renderable(f)
        if is_mf_theme_name(theme):
            return mf_studio.is_mf_renderable(f)
        return True

    check_js = getattr(m, "CHECK_JS", None) or getattr(m, "QA_JS", None) or "() => []"
    check_arg = None
    if theme == "varsity-hindi-graphics":  # QA_JS(mode) in that kit
        check_arg = lambda f: (f.get("mode") or "fss") + ("-split" if f.get("split") else "")
    return critique.run(
        theme_dir=THEMES / theme,
        spec=spec,
        storyboard=storyboard,
        render_html=render_html,
        renderable=renderable,
        check_js=check_js,
        check_arg=check_arg,
        canvas=theme_canvas.canvas_for_theme(theme),
        finalize=finalize,
        script=script,
        only_ids=only_ids,
        log=print,
    )


def _merge_pdf_batch_spec(
    p: dict,
    batch: dict,
    look: dict,
) -> tuple[dict, str]:
    existing = p.get("spec") or {}
    old_frames = list(existing.get("frames") or [])
    seen = {f["id"] for f in old_frames if isinstance(f, dict) and f.get("id")}
    for fr in batch.get("frames") or []:
        if not isinstance(fr, dict):
            continue
        fid = fr.get("id")
        if not fid or fid in seen:
            continue
        seen.add(fid)
        old_frames.append(fr)
    spec = {**existing, "frames": old_frames}
    meta = batch.get("spec_meta") or {}
    if isinstance(meta, dict):
        for key in ("title", "look"):
            if meta.get(key) and not spec.get(key):
                spec[key] = meta[key]
        if isinstance(meta.get("gen"), dict):  # Zero1 Hindi: plate prompts arrive with each batch
            spec["gen"] = {**(spec.get("gen") or {}), **meta["gen"]}
    old_sb = (p.get("storyboard") or "").strip()
    new_sb = (batch.get("storyboard") or "").strip()
    storyboard = new_sb if (new_sb and not old_sb) else (p.get("storyboard") or new_sb or "")
    if is_mf_theme_name(p["theme"]) and isinstance(look, dict) and look.get("look_line") and not spec.get("look"):
        spec["look"] = look["look_line"]
    return spec, storyboard


def _finalize_spec_after_batch(spec: dict, storyboard: str, theme: str, look: dict, p: dict) -> dict:
    if is_mf_theme_name(theme):
        return mf_studio.compact_mf_spec_for_studio(spec)
    if is_zo_theme_name(theme):
        spec = mf_studio.compact_zo_spec_for_studio(spec)
        if isinstance(look, dict) and look.get("plate") and isinstance(spec.get("look"), dict):
            spec["look"].setdefault("plate", look["plate"])
        return spec
    if is_hindi_theme_name(theme) or z1_plates.is_theme(theme):
        return spec
    merged = effective_look({**p, "look": look, "spec": spec})
    spec["look"] = merged
    return spec_enrich.enrich_spec(spec, storyboard, theme=theme)


@app.get("/api/projects/{pid}/episode-transcript")
def get_episode_transcript(pid: int):
    load(pid)
    tr = episode_audio.read_transcript(pid)
    if not tr:
        raise HTTPException(404, "No episode transcript for this project")
    return tr


@app.get("/api/projects/{pid}/episode-audio")
def episode_audio_status(pid: int):
    load(pid)
    tr = episode_audio.read_transcript(pid)
    return {
        "has_audio": episode_audio.has_audio(pid),
        "has_transcript": episode_audio.has_transcript(pid),
        "segment_count": len((tr or {}).get("segments") or []),
        "original_name": (episode_audio.read_meta(pid) or {}).get("original_name") or "",
    }


@app.post("/api/projects/{pid}/episode-audio")
async def upload_episode_audio(pid: int, req: Request, file: UploadFile = File(...)):
    (await _db_call(load, pid))
    raw = await file.read()
    fn = (file.filename or "episode.mp3").lower()
    try:
        path = await asyncio.to_thread(episode_audio.save_audio, pid, raw, fn)
        episode_audio.delete_transcript(pid)
        transcript = await asyncio.to_thread(audio_transcribe.transcribe_file, path)
        await asyncio.to_thread(episode_audio.save_transcript, pid, transcript)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except OSError as e:
        raise HTTPException(507, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(502, str(e)) from e
    (await _db_call(save, pid, who(req), "upload episode audio"))
    return {**(await _db_call(load, pid)), "ok": True}


@app.get("/api/projects/{pid}/episode-audio/file")
def episode_audio_file(pid: int):
    a = episode_audio.audio_path(pid)
    if not a:
        raise HTTPException(404, "no voice-over")
    return FileResponse(a)


@app.delete("/api/projects/{pid}/episode-audio")
async def delete_episode_audio(pid: int):
    (await _db_call(load, pid))
    episode_audio.delete_audio(pid)
    return (await _db_call(load, pid))


@app.get("/api/projects/{pid}/storyboard-pdf")
def has_storyboard_pdf(pid: int):
    p = load(pid)
    look = p.get("look") or {}
    return {
        "has_pdf": storyboard_pdf.pdf_path(pid).is_file(),
        "filename": (look.get("storyboard_pdf_name") or p.get("storyboard_pdf_name") or "").strip(),
        "sb_import": look.get("sb_import") or "",
    }


@app.post("/api/projects/{pid}/storyboard-pdf")
async def upload_storyboard_pdf(pid: int, req: Request, file: UploadFile = File(...)):
    (await _db_call(load, pid))
    ct = (file.content_type or "").split(";")[0].strip().lower()
    fn = (file.filename or "").lower()
    if ct not in ("application/pdf", "application/octet-stream", "binary/octet-stream", "") and not fn.endswith(
        ".pdf"
    ):
        raise HTTPException(400, "Upload a PDF file")
    raw = await file.read()
    try:
        storyboard_pdf.save_pdf(pid, raw)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except OSError as e:
        raise HTTPException(507, str(e)) from e
    p = (await _db_call(load, pid))
    orig = (file.filename or "storyboard.pdf").strip() or "storyboard.pdf"
    pages = None
    try:
        import fitz  # pymupdf
        with fitz.open(stream=raw, filetype="pdf") as doc:
            pages = doc.page_count
    except Exception:
        pass
    look = {**(p.get("look") or {}), "sb_import": "pdf", "storyboard_pdf_name": orig,
            "storyboard_pdf_pages": pages, "storyboard_pdf_bytes": len(raw)}
    extra = {}
    if isinstance(p.get("spec"), dict) and p["spec"].get("pdf_done"):   # a new PDF may have more frames
        extra["spec"] = {**p["spec"], "pdf_done": False}
    (await _db_call(save, pid, who(req), "upload storyboard PDF", look=look, version=False, **extra))
    out = (await _db_call(load, pid))
    return {**out, "ok": True, "has_pdf": _storyboard_pdf_on_disk(pid)}


@app.post("/api/projects/{pid}/storyboard-pdf/batch")
async def storyboard_pdf_batch_route(pid: int, req: Request):
    b = await req.json()
    (await _db_call(load, pid))
    return _stream_json(_storyboard_pdf_batch(pid, b, who(req)))


async def _storyboard_pdf_batch(pid: int, b: dict, user: str):
    p = (await _db_call(load, pid))
    try:
        pdf_bytes = storyboard_pdf.read_pdf(pid)
    except FileNotFoundError:
        raise HTTPException(400, "Upload a storyboard PDF first")
    except ValueError as e:
        raise HTTPException(400, str(e))
    look = effective_look(p)
    if isinstance(look, dict):
        look = {**look, "sb_import": "pdf"}
    finish_all = bool(b.get("finish_all"))
    batch_size = min(10, max(1, int(b.get("batch_size", 10))))
    script = b.get("script", p.get("script") or "")
    transcript = _episode_transcript_for_project(pid)
    # progress for the page (polls /progress): reading → frames written so far → pictures → checking → done
    run = uuid.uuid4().hex[:12]
    t0 = time.time()
    had = len((p.get("spec") or {}).get("frames") or [])
    PROGRESS[pid] = {"run": run, "state": "running", "kind": "pdf", "stage": "reading", "started": t0, "rev": 0,
                     "msg": "Reading the storyboard PDF…", "ready": had, "written": 0, "batch_size": batch_size}
    seen = [0]

    def on_partial(snap: dict):            # worker thread: frames Claude has finished writing in this batch
        fr = [f for f in (snap.get("frames") or [])[:-1] if isinstance(f, dict) and f.get("id")]
        if len(fr) == seen[0]:
            return
        seen[0] = len(fr)
        last = fr[-1]
        name = str(last.get("name") or last.get("title") or last.get("id"))[:48]
        _progress(pid, run, stage="writing", written=len(fr),
                  msg=f"Writing frame {len(fr) + 1}{'' if finish_all else f' of up to {batch_size}'}… (just wrote {last.get('id')}: {name})")

    def call():
        with claude_client.partial_hook(on_partial):
            return claude_client.storyboard_pdf_batch(
            THEMES / p["theme"],
            pdf_bytes,
            script,
            look if isinstance(look, dict) else {},
            b.get("notes", ""),
            batch_size=batch_size,
            finish_all=finish_all,
            existing_spec=p.get("spec") or {},
            existing_storyboard=p.get("storyboard") or "",
            episode_transcript=transcript,
        )
    try:
        try:
            out = await asyncio.to_thread(call)
        except Exception as e:
            _progress(pid, run, state="error", msg=f"Stopped: {e}")
            _raise_claude_gateway(e)
        print(f"pdf batch {pid}: Claude {time.time() - t0:.0f}s, +{out.get('frames_added')} frames", flush=True)
        if _stopped(pid, t0):
            return {**(await _db_call(load, pid)), "stopped": True, "frames_added": 0}
        return await _storyboard_pdf_batch_rest(pid, p, b, user, out, look, script, run, t0)
    finally:
        if _live(pid, run) and (PROGRESS.get(pid) or {}).get("state") == "running":
            _progress(pid, run, state="done", stage="done", msg="Done")


def _mark_pdf_done(pid: int, progress: str) -> None:
    """The PDF has no more graphics: remembered on the spec (no Undo step) so the frames page says "All N frames made"."""
    try:
        with connect() as c:
            row = c.execute("select spec from projects where id=?", (pid,)).fetchone()
            spec = json.loads((row or {}).get("spec") or "null") if row else None
            if isinstance(spec, dict) and not spec.get("pdf_done"):
                spec["pdf_done"] = True
                spec["pdf_progress"] = progress
                c.execute("update projects set spec=? where id=?", (json.dumps(spec, ensure_ascii=False), pid))
                c.commit()
    except Exception as e:
        print(f"pdf done mark skipped: {e}")


async def _storyboard_pdf_batch_rest(pid, p, b, user, out, look, script, run, t0):
    if not out.get("frames_added"):
        raw = out.get("raw_frame_count", 0)
        existing_n = len((p.get("spec") or {}).get("frames") or [])
        if not raw and existing_n:
            _mark_pdf_done(pid, out.get("pdf_progress") or "done")
            return {
                **(await _db_call(load, pid)),
                "pdf_progress": out.get("pdf_progress") or "No more graphic frames in the PDF.",
                "frames_added": 0,
                "spec_warnings": [],
            }
        if raw:
            detail = (
                "Claude returned frames but none could be merged (missing ids or duplicates). "
                "Add Notes describing which PDF rows are graphics vs footage, then try again."
            )
        else:
            detail = (
                "Claude returned no graphic frames from the PDF. You do not need a separate storyboard file — "
                "the PDF is enough. Optional: paste the voiceover script for exact numbers. "
                "In Notes, say how to read the PDF (e.g. ‘timestamp rows marked GFX / FSS are graphics; skip B-roll’)."
            )
        raise HTTPException(422, detail)
    spec, storyboard = _merge_pdf_batch_spec(p, out, look if isinstance(look, dict) else {})
    toolkit.carry(p.get("spec"), spec)
    tkf = [f for f in spec.get("frames") or [] if isinstance(f, dict) and f.get("tk_from") and f.get("lines_src") == "pdf"
           and isinstance(f.get("lines"), list) and len(f["lines"]) == 2]
    if tkf and toolkit.enabled(p["theme"]):
        try:
            others = [f for f in spec["frames"] if isinstance(f, dict) and f not in tkf]
            spec["frames"] = toolkit.merge_rest(tkf, others, toolkit.pdf_lines(storyboard_pdf.read_pdf(pid)), "pdf")
        except Exception as e:
            print(f"toolkit order after pdf batch skipped: {e}")
    prog = str(out.get("pdf_progress") or "")
    spec["pdf_progress"] = prog
    spec["pdf_done"] = prog.strip().lower() in ("done", "complete", "finished")
    _progress(pid, run, stage="pictures", written=out.get("frames_added") or 0,
              msg=f"{out.get('frames_added')} frames written. Placing pictures…")
    lk = look if isinstance(look, dict) else {}
    asset_report: dict = {}
    finalize = _with_assets(
        p["theme"], lambda sp: _finalize_spec_after_batch(sp, storyboard, p["theme"], lk, p), asset_report,
        pdf=_pdf_ref(pid) if z1_plates.is_theme(p["theme"]) else None,
    )
    spec = await asyncio.to_thread(finalize, spec)
    plook = look if isinstance(look, dict) else p.get("look")
    if is_mf_theme_name(p["theme"]) and isinstance(spec.get("look"), str) and isinstance(plook, dict):
        plook = {**plook, "look_line": spec["look"]}
    # review only the frames this batch added
    before = {str(f.get("id")) for f in (p.get("spec") or {}).get("frames") or [] if isinstance(f, dict)}
    new_ids = {str(f.get("id")) for f in spec.get("frames") or [] if isinstance(f, dict)} - before
    critique_report: dict = {}
    if new_ids:
        t1 = time.time()
        _progress(pid, run, stage="checking", msg=f"Checking the {len(new_ids)} new frames for overlaps and cut-off text…")
        try:
            spec, critique_report = await asyncio.to_thread(
                _critique_spec, {**p, "look": plook}, spec, storyboard, script, finalize, new_ids
            )
        except Exception as e:
            critique_report = {"error": str(e)}
        print(f"pdf batch {pid}: check {time.time() - t1:.0f}s, total {time.time() - t0:.0f}s", flush=True)
    (await _db_call(save, 
        pid,
        user,
        f"PDF storyboard batch (+{out['frames_added']} frames)" + _notes_suffix(critique_report, asset_report),
        script=script,
        look=plook,
        storyboard=storyboard,
        spec=spec,
    ))
    warn = claude_client.spec_quality_issues(spec, storyboard, theme=p["theme"], storyboard_led=True)
    warn += [f"layout: {w}" for w in critique_report.get("remaining") or []]
    warn += [f"asset not generated: {d} ({e})" for d, e in (asset_report.get("failed") or {}).items()]
    return {
        **(await _db_call(load, pid)),
        "pdf_progress": out.get("pdf_progress"),
        "frames_added": out.get("frames_added"),
        "frames_dropped": out.get("frames_dropped") or 0,
        "spec_warnings": warn,
        "critique": critique_report,
        "assets": asset_report,
    }


@app.post("/api/projects/{pid}/assets/fill")
async def fill_assets_route(pid: int, req: Request):
    """Generate images for every remaining "TODO:" asset in an existing project ({"redo": true} also
    remakes the images generated earlier)."""
    (await _db_call(load, pid))
    user = who(req)
    try:
        redo = bool((await req.json()).get("redo"))
    except Exception:
        redo = False

    async def job():
        p = (await _db_call(load, pid))
        if z1_plates.is_theme(p["theme"]):
            spec, report = await asyncio.to_thread(z1_plates.fill, p.get("spec") or {}, print, redo, None, _pdf_ref(pid))
            left = len(z1_plates.pending(spec))
        else:
            spec, report = await asyncio.to_thread(asset_gen.fill_spec, p["theme"], p.get("spec") or {}, print, redo)
            left = len(asset_gen.todo_descriptions(spec))
        if report["filled"]:
            verb = "regenerated" if redo else "generated"
            (await _db_call(save, pid, user, f"{verb} {len(report['filled'])} asset(s)", spec=spec))
        return {**(await _db_call(load, pid)), "assets": report, "todo_left": left}
    return _stream_json(job())


@app.put("/api/projects/{pid}")
async def update(pid: int, req: Request):
    b = await req.json(); fields = {k: b[k] for k in ("name", "storyboard", "spec", "look", "theme", "script") if k in b}
    if isinstance(fields.get("spec"), dict) and isinstance(fields["spec"].get("gen"), dict):
        saved_gen = (((await _db_call(load, pid)).get("spec") or {}).get("gen") or {})
        for k, v in fields["spec"]["gen"].items():
            s = saved_gen.get(k) or {}
            if isinstance(v, dict) and not v.get("file") and s.get("file") and s.get("prompt") == v.get("prompt"):
                v["file"] = s["file"]
    if "look" in fields:
        p = (await _db_call(load, pid)); spec = fields.get("spec") or p["spec"]
        if spec:
            merged = effective_look({**p, "look": fields["look"], "spec": spec})
            spec["look"] = merged
            fields["look"] = merged
            fields["spec"] = spec
    (await _db_call(save, pid, who(req), b.get("note", "manual edit"), **fields)); return (await _db_call(load, pid))

def _save_frame_reference(theme: str, pid: int, fid: str, raw: bytes) -> tuple[str, bytes]:
    from PIL import Image
    import io

    dest = THEMES / theme / "assets" / "uploads"
    dest.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", fid)
    path = dest / f"ref_{pid}_{safe}.png"
    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    # Claude takes pictures up to 5 MB and sees no more than ~1600 px anyway: a Retina screenshot pasted into the
    # chat was well over that and the edit failed. Keep the long side at 1600 px and the file under ~3.5 MB.
    img.thumbnail((1600, 1600), Image.LANCZOS)
    img.save(path, "PNG", optimize=True)
    data = path.read_bytes()
    if len(data) > 3_500_000:   # photo-like: Claude gets a 256-colour copy (still PNG, the callers label it image/png)
        buf = io.BytesIO()
        img.convert("RGB").quantize(colors=256).save(buf, "PNG", optimize=True)
        data = buf.getvalue()
    return f"uploads/ref_{pid}_{safe}.png", data


@app.post("/api/projects/{pid}/frames/{fid}/edit")
async def edit(pid: int, fid: str, req: Request):
    p = (await _db_call(load, pid))
    spec = p["spec"]
    i = next((k for k, f in enumerate(spec["frames"]) if f["id"] == fid), None)
    if i is None:
        raise HTTPException(404, "frame not found")

    ref_src = None
    ref_image = None
    replace_flag = False
    flat_paste = False
    regenerate = False
    item_index = None
    mf_path = None
    ct = (req.headers.get("content-type") or "").lower()
    if "multipart/form-data" in ct:
        form = await req.form()
        ask = (form.get("ask") or "").strip()
        replace_flag = form.get("replace") in ("1", "true", "on", "yes")
        flat_paste = form.get("flat") in ("1", "true", "on", "yes")
        regenerate = form.get("regenerate") in ("1", "true", "on", "yes")
        if form.get("item_index") not in (None, ""):
            try:
                item_index = int(form.get("item_index"))
            except (TypeError, ValueError):
                item_index = None
        mf_path = (form.get("mf_path") or "").strip() or None
        up = form.get("file")
        if up and getattr(up, "filename", None):
            raw = await up.read()
            if raw:
                ref_src, png_bytes = _save_frame_reference(p["theme"], pid, fid, raw)
                ref_image = ("image/png", png_bytes)
    else:
        b = await req.json()
        ask = (b.get("ask") or "").strip()
        replace_flag = bool(b.get("replace"))
        flat_paste = bool(b.get("flat"))
        regenerate = bool(b.get("regenerate"))
        if b.get("item_index") is not None:
            try:
                item_index = int(b["item_index"])
            except (TypeError, ValueError):
                item_index = None
        mf_path = (b.get("mf_path") or "").strip() or None

    if mf_path and ask:
        ask = (
            f"Edit ONLY the field `{mf_path}` on this frame JSON. "
            f"Return the full frame but change ONLY that path — leave all other keys unchanged. Task: {ask}"
        )
        if is_zo_theme_name(p["theme"]) and mf_path_item_index(mf_path) is not None:
            ask += (
                "\n\nZo Product IP renderer (apply to that items[] slot): "
                "heading — 72px fixed; use numeric \"scale\" (e.g. 1.2) to enlarge the block; default centered (align \"left\" for left). "
                "cards — w, icon_size, gap, scale. pillv/compare/chart — adjust copy and component fields in spec_format.md. "
                "Frame fitbox — optional frame-level \"fit\" (default 1.6) scales non-heading content."
            )
    if item_index is not None and ask:
        ask = (
            f"Edit ONLY items[{item_index}] (0-based index). Return the full frame but change ONLY that slot — "
            f"do NOT append new items[] entries. Task: {ask}"
        )
    if not ask and not ref_src and not regenerate:
        raise HTTPException(400, "ask, reference image, or regenerate required")
    if item_index is not None and not ask and not ref_src:
        raise HTTPException(400, "layer replace needs a prompt and/or reference image")
    if is_mf_theme_name(p["theme"]) and not is_zo_theme_name(p["theme"]) and item_index is not None:
        raise HTTPException(400, "MF theme: use mf_path for layer edits, not item_index")

    sb_line = _storyboard_line_for_frame(p.get("storyboard") or "", fid)
    storyboard_full = p.get("storyboard") or ""
    smart_ref = bool(ref_image) and not flat_paste
    before = spec["frames"][i]

    if item_index is not None and ref_src:
        new = apply_layer_reference_replace(before, item_index, ref_src)
        spec["frames"][i] = new
        (await _db_call(save, pid, who(req), f"{fid}: layer ref #{item_index}", spec=spec))
        return new

    edit_frame_in = copy.deepcopy(before)
    if smart_ref and replace_flag and item_index is None:
        edit_frame_in = remove_scene_illustrations(edit_frame_in)

    try:
        new = await asyncio.to_thread(
            claude_client.edit_frame,
            THEMES / p["theme"],
            edit_frame_in,
            effective_look(p),
            ask or ("Regenerate with fresh kit visuals." if regenerate else "Use the reference on this frame."),
            ref_src,
            ref_image,
            replace_illustration=replace_flag,
            smart_reference=smart_ref,
            flat_paste=flat_paste,
            regenerate=regenerate,
            storyboard_line=sb_line,
            storyboard_full=storyboard_full,
            gen_entries=_z1_frame_gen(spec, before) if z1_plates.is_theme(p["theme"]) else None,
        )
        if z1_plates.is_theme(p["theme"]):
            new, spec = await _z1_after_edit(pid, spec, new, regenerate)
        mf_item_ix = mf_path_item_index(mf_path) if mf_path else None
        if item_index is not None and not is_mf_theme_name(p["theme"]):
            if is_hindi_fa_theme_name(p["theme"]):
                new = merge_els_edit(before, new, item_index)
            else:
                new = merge_item_edit(before, new, item_index)
            if smart_ref and ref_src:
                new = strip_upload_assets(new, ref_src)
        elif mf_item_ix is not None and is_hindi_fa_theme_name(p["theme"]):
            new = merge_els_edit(before, new, mf_item_ix)
        elif mf_item_ix is not None and is_mf_theme_name(p["theme"]):
            new = merge_item_edit(before, new, mf_item_ix)
            if smart_ref and ref_src:
                new = strip_upload_assets(new, ref_src)
        elif flat_paste and ref_src and replace_flag and not is_mf_theme_name(p["theme"]):
            new = apply_flat_paste_replace(new, ref_src, ask, True)
        elif z1_plates.is_theme(p["theme"]) or (regenerate and not ref_src):
            pass
        elif mf_path and is_mf_theme_name(p["theme"]) and not ref_src:
            pass
        else:
            new = finalize_reference_edit(
                before,
                new,
                replace=replace_flag,
                ref_src=ref_src,
                smart=smart_ref,
            )
    except HTTPException:
        raise
    except Exception as e:
        try:
            _raise_claude_gateway(e)
        except HTTPException:
            raise
        except Exception:
            import traceback
            traceback.print_exc()
            raise HTTPException(500, detail=f"The edit failed ({type(e).__name__}: {str(e)[:200]}). Try again, or describe the change differently.") from e
    if not isinstance(new, dict):
        raise HTTPException(502, detail="Claude sent back no frame. Try again.")
    if is_zo_theme_name(p["theme"]) or not is_mf_theme_name(p["theme"]):
        new = normalize_cards_items(new)
    spec["frames"][i] = new
    note = f"{fid}: {(ask or 'reference')[:80]}"
    (await _db_call(save, pid, who(req), note, spec=spec))
    return new

@app.post("/api/projects/{pid}/undo")
def undo(pid: int, req: Request):
    with connect() as c:
        v = c.execute("select * from versions where project_id=? order by id desc limit 1", (pid,)).fetchone()
        if not v:
            raise HTTPException(400, "nothing to undo")
        c.execute("update projects set spec=?, storyboard=? where id=?", (v["spec"], v["storyboard"], pid))
        c.execute("delete from versions where id=?", (v["id"],))
        c.commit()
    return load(pid)

@app.get("/api/projects/{pid}/history")
def history(pid: int):
    with connect() as c:
        return c.execute("select id,author,note,ts from versions where project_id=? order by id desc limit 50", (pid,)).fetchall()

@app.post("/api/projects/{pid}/plate")
async def plate(pid: int, req: Request, file: UploadFile = File(...)):
    from PIL import Image
    import io
    p = (await _db_call(load, pid)); name = f"user_{pid}"
    cw, ch = theme_canvas.canvas_for_theme(p["theme"])
    Image.open(io.BytesIO(await file.read())).convert("RGB").resize((cw, ch)).save(
        THEMES / p["theme"] / "assets/plates" / f"{name}.png"
    )
    look = {**p["look"], "plate": name}; (await _db_call(save, pid, who(req), "uploaded anchor plate", look=look))
    if p["spec"]: p["spec"]["look"]["plate"] = name; (await _db_call(save, pid, who(req), "plate on spec", spec=p["spec"]))
    return (await _db_call(load, pid))

# ---- presenter shot behind anchor frames, changed once for the whole project (presenter.py) ----
@app.get("/api/projects/{pid}/presenter")
async def presenter_get(pid: int):
    import presenter
    p = await _db_call(load, pid)
    return {"slots": presenter.summary(p["theme"], p.get("spec"), effective_look(p))}


@app.post("/api/projects/{pid}/presenter")
async def presenter_set(pid: int, req: Request, slot: str = Form(...), file: UploadFile = File(...), fid: str = Form("")):
    """A still from this video's presenter replaces the stock photo in every frame that uses this slot."""
    import io, presenter
    from PIL import Image, ImageOps
    p = await _db_call(load, pid)
    if slot not in presenter.SLOTS.get(presenter._base(p["theme"]), {}):
        raise HTTPException(400, "this kit has no presenter shot called " + slot)
    raw = await file.read()
    try:
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    except Exception:
        raise HTTPException(400, "that file is not a picture (use a PNG or JPG screenshot)")
    cw, ch = theme_canvas.canvas_for_theme(p["theme"])
    im = await asyncio.to_thread(presenter.fit_to_slot, im, p["theme"], slot, cw, ch)   # presenter on the slot's side
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    rel = await asyncio.to_thread(asset_gen.store, p["theme"], f"presenter {pid} {slot} {time.time()}",
                                  buf.getvalue(), "jpg", "presenter")
    look = dict(p.get("look") or {})
    if look.get("toolkit") and fid:   # a toolkit template: the photo belongs to that template only
        spec = dict(p.get("spec") or {})
        spec["frames"] = [{**f, "plate_img": rel} if str(f.get("id")) == fid else f for f in spec.get("frames") or []]
        await _db_call(save, pid, who(req), f"template photo ({slot})", spec=spec)
        p = await _db_call(load, pid)
        return {"slots": presenter.summary(p["theme"], p.get("spec"), effective_look(p)), "project": p}
    look["presenter"] = {**(look.get("presenter") if isinstance(look.get("presenter"), dict) else {}), slot: rel}
    await _db_call(save, pid, who(req), f"presenter shot ({slot})", look=look)
    p = await _db_call(load, pid)
    return {"slots": presenter.summary(p["theme"], p.get("spec"), effective_look(p)), "project": p}


@app.delete("/api/projects/{pid}/presenter")
async def presenter_reset(pid: int, req: Request, slot: str):
    import presenter
    p = await _db_call(load, pid)
    look = dict(p.get("look") or {})
    pr = dict(look.get("presenter") or {}) if isinstance(look.get("presenter"), dict) else {}
    pr.pop(slot, None)
    look["presenter"] = pr
    await _db_call(save, pid, who(req), f"presenter shot ({slot}) back to the kit's", look=look)
    p = await _db_call(load, pid)
    return {"slots": presenter.summary(p["theme"], p.get("spec"), effective_look(p)), "project": p}


@app.get("/preview/{pid}/{fid}", response_class=HTMLResponse)
def preview(pid: int, fid: str, edit: int = 0):
    p = load(pid)
    frames = (p.get("spec") or {}).get("frames") or []
    f = next((fr for fr in frames if fr["id"] == fid), None)
    if not f:
        raise HTTPException(404, "frame not found")
    try:
        return frame_page(
            p["theme"],
            frame_for_render(p, f),
            effective_look(p),
            edit=bool(edit),
            all_frames=frames,
            spec=p.get("spec") if isinstance(p.get("spec"), dict) else None,
        )
    except (KeyboardInterrupt, SystemError):
        raise
    except BaseException as e:
        # Hindi kit build.py uses raise SystemExit(...) for spec errors; that does not subclass Exception
        # and would otherwise bypass this handler and kill the worker (Railway 502 on /preview).
        raise HTTPException(502, detail=f"Preview render failed: {e}") from e


@app.post("/api/projects/{pid}/storyboard-ref")
async def storyboard_ref(pid: int, req: Request, file: UploadFile = File(...)):
    from PIL import Image
    import io

    p = (await _db_call(load, pid))
    refs = list((p.get("look") or {}).get("ref_images") or [])
    if len(refs) >= 10:
        raise HTTPException(400, "Maximum 10 storyboard reference images")
    dest = THEMES / p["theme"] / "assets" / "uploads"
    dest.mkdir(parents=True, exist_ok=True)
    n = len(refs) + 1
    rel = f"uploads/sbref_{pid}_{n}.png"
    Image.open(io.BytesIO(await file.read())).convert("RGBA").save(dest / f"sbref_{pid}_{n}.png", "PNG")
    refs.append(rel)
    look = {**p["look"], "ref_images": refs}
    (await _db_call(save, pid, who(req), "storyboard ref", look=look))
    return (await _db_call(load, pid))


@app.get("/api/projects/{pid}/look-ref")
def look_ref_file(pid: int, path: str):
    p = load(pid)
    rel = (path or "").strip()
    refs = list((p.get("look") or {}).get("ref_images") or [])
    if rel not in refs or ".." in rel or not rel.startswith("uploads/sbref_"):
        raise HTTPException(404, "Reference not found")
    fp = THEMES / p["theme"] / "assets" / rel
    if not fp.is_file():
        raise HTTPException(404, "Reference file missing")
    return FileResponse(fp)


@app.delete("/api/projects/{pid}/storyboard-ref")
async def delete_storyboard_ref(pid: int, req: Request):
    b = await req.json()
    rel = (b.get("path") or "").strip()
    if not rel or ".." in rel or not rel.startswith("uploads/sbref_"):
        raise HTTPException(400, "Invalid reference path")
    p = (await _db_call(load, pid))
    refs = list((p.get("look") or {}).get("ref_images") or [])
    if rel not in refs:
        raise HTTPException(404, "Reference not found")
    refs = [r for r in refs if r != rel]
    look = {**p["look"], "ref_images": refs}
    (await _db_call(save, pid, who(req), "remove storyboard ref", look=look))
    fp = THEMES / p["theme"] / "assets" / rel
    if fp.is_file():
        fp.unlink()
    return (await _db_call(load, pid))

@app.get("/api/projects/{pid}/check")
async def check(pid: int):
    from playwright.async_api import async_playwright
    p = (await _db_call(load, pid)); m = builder(p["theme"]); warns = []
    try:
        async with async_playwright() as pw:
            b = await exporter.launch_chromium(pw)
            cw, ch = theme_canvas.canvas_for_theme(p["theme"])
            pg = await b.new_page(viewport={"width": cw, "height": ch})
            mf = is_mf_theme_name(p["theme"])
            for f in p["spec"]["frames"]:
                await pg.goto(preview_url(pid, f["id"]), wait_until="load", timeout=120_000)
                if mf:
                    try:
                        await pg.wait_for_function("window.RENDERED === true", timeout=20_000)
                    except Exception:
                        pass
                await pg.wait_for_timeout(200)
                check_js = getattr(m, "CHECK_JS", None) or getattr(m, "QA_JS", "() => []")
                warns += [f"{f['id']}: {w}" for w in await pg.evaluate(check_js)]
            await b.close()
    except Exception as e:
        raise HTTPException(502, detail=f"Layout check failed: {e}") from e
    return warns

def _export_pages(p: dict, only_ids: set[str] | None = None, layers: bool = False) -> list[tuple[str, str, bool, str | None]]:
    if not p.get("spec"):
        raise HTTPException(400, "Project has no spec")
    base = f"{preview_base()}/themes/{p['theme']}/scenes/"
    look = effective_look(p)
    all_frames = (p.get("spec") or {}).get("frames") or []
    pages: list[tuple[str, str, bool, str | None]] = []
    for f in all_frames:
        fid = str(f.get("id") or "")
        if only_ids is not None and fid not in only_ids:
            continue
        if is_mf_theme_name(p["theme"]) and not is_zo_theme_name(p["theme"]) and not mf_studio.is_mf_renderable(f):
            continue
        if is_zo_theme_name(p["theme"]) and not mf_studio.is_zo_renderable(f):
            continue
        try:
            html = frame_page(
                p["theme"],
                frame_for_render(p, f, layers=layers),
                look,
                base_href=base,
                all_frames=all_frames,
                spec=p.get("spec") if isinstance(p.get("spec"), dict) else None,
            )
        except BaseException as e:
            raise HTTPException(502, detail=f"Export HTML failed for frame {fid}: {e}") from e
        full_only = frame_wants_overlay(p["theme"], f)
        html_overlay = None
        if not full_only:
            try:
                html_overlay = frame_page(
                    p["theme"],
                    frame_for_render(p, f),
                    look,
                    base_href=base,
                    all_frames=all_frames,
                    spec=p.get("spec") if isinstance(p.get("spec"), dict) else None,
                    overlay=True,
                )
            except BaseException:
                html_overlay = None
        pages.append((fid, html, full_only, html_overlay))
    if only_ids is not None and not pages:
        raise HTTPException(404, "Frame not found or not exportable")
    return pages


def _dl_name(base: str, suffix: str) -> str:
    safe = re.sub(r"[^\w.-]+", "_", (base or "export").strip()) or "export"
    return f"{safe}{suffix}"


def _storyboard_csv_bytes(p: dict) -> bytes | None:
    sb = (p.get("storyboard") or "").strip()
    if not sb:
        return None
    spec = p.get("spec") if isinstance(p.get("spec"), dict) else None
    text = storyboard_csv.storyboard_csv_text(sb, spec, project_name=p.get("name") or "")
    return text.encode("utf-8")


@app.get("/api/projects/{pid}/storyboard-instructions.csv")
def export_storyboard_csv(pid: int):
    p = load(pid)
    raw = _storyboard_csv_bytes(p)
    if raw is None:
        raise HTTPException(400, "No storyboard text on this project yet.")
    text = raw.decode("utf-8")
    fn = _dl_name(p["name"], "_storyboard.csv")
    return Response(
        text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )


def _export_zip_filename(p: dict, ids: set[str] | None) -> str:
    if ids and len(ids) == 1:
        fid = next(iter(ids))
        return _dl_name(f"{p['name']}_{fid}", "_export.zip")
    return _dl_name(p["name"], "_frames.zip")


def _export_zip_payload(p: dict, png: int, only: str, dest: pathlib.Path | None = None) -> tuple[bytes, str]:
    ids = {x.strip() for x in only.split(",") if x.strip()} if only else None
    pages = _export_pages(p, ids)
    sb_csv = None
    raw_sb = _storyboard_csv_bytes(p)
    if raw_sb is not None:
        sb_csv = raw_sb.decode("utf-8")
    cw, ch = theme_canvas.canvas_for_theme(p["theme"])
    fn = _export_zip_filename(p, ids)
    extra = z1_plates.export_files(p) if z1_plates.is_theme(p["theme"]) else None
    if dest is not None:
        exporter.export_zip(
            pages,
            THEMES / p["theme"],
            bool(png),
            (cw, ch),
            storyboard_csv=sb_csv,
            zip_path=dest,
            extra_files=extra,
        )
        return b"", fn
    data = exporter.export_zip(
        pages,
        THEMES / p["theme"],
        bool(png),
        (cw, ch),
        storyboard_csv=sb_csv,
        extra_files=extra,
    )
    return data, fn


def _export_build_zip(p: dict, png: int, only: str, dest: pathlib.Path, fmt: str = "") -> str:
    if fmt == "bulletin":
        return _export_bulletin(p, only, dest)
    _, fn = _export_zip_payload(p, png, only, dest)
    return fn


def _export_bulletin(p: dict, only: str, dest: pathlib.Path) -> str:
    """Layered Bulletin format (html/png/layers JSON + LAYERS.txt + README + spec.json) for the ZO team."""
    if not p.get("spec"):
        raise HTTPException(400, "Project has no spec")
    ids = {x.strip() for x in only.split(",") if x.strip()} if only else None
    theme = p["theme"]
    base = (THEMES / theme / "scenes").as_uri() + "/"
    look = effective_look(p)
    spec = p.get("spec") if isinstance(p.get("spec"), dict) else {}
    frames = spec.get("frames") or []
    sb = p.get("storyboard") or ""
    pages, meta = [], {}
    for f in frames:
        fid = str(f.get("id") or "")
        if ids is not None and fid not in ids:
            continue
        if is_zo_theme_name(theme) and not mf_studio.is_zo_renderable(f):
            continue
        if is_mf_theme_name(theme) and not is_zo_theme_name(theme) and not mf_studio.is_mf_renderable(f):
            continue
        html = frame_page(theme, frame_for_render(p, f), look, base_href=base, all_frames=frames, spec=spec)
        pages.append((fid, html, f.get("mode", "fss")))
        meta[fid] = {"vo": _storyboard_line_for_frame(sb, fid)}
    skipped = [{"id": "", "beat": ln.strip(), "reason": "screen capture"} for ln in sb.splitlines()
               if re.search(r"screen ?capture", ln, re.I)]
    cw, ch = theme_canvas.canvas_for_theme(theme)
    bulletin.export_bulletin(pages, THEMES / theme, p.get("name") or "Video", meta,
                             viewport=(cw, ch), skipped=skipped, zip_path=dest)
    return _dl_name(p["name"], "_layers.zip")


def _export_job_prune() -> None:
    now = time.time()
    with _EXPORT_JOB_LOCK:
        for jid, job in list(_EXPORT_JOBS.items()):
            if now - job.get("t", now) < 7200:
                continue
            path = job.get("path")
            if path:
                try:
                    pathlib.Path(path).unlink(missing_ok=True)
                except OSError:
                    pass
            _EXPORT_JOBS.pop(jid, None)


@app.post("/api/projects/{pid}/export/jobs")
def export_start_job(pid: int, png: int = 1, only: str = "", fmt: str = ""):
    """Start export in a background thread; poll status then download (avoids long HTTP/2 streams)."""
    p = load(pid)
    _export_job_prune()
    job_id = uuid.uuid4().hex[:16]
    dest = _EXPORT_JOB_DIR / f"{job_id}.zip"
    fn = _export_zip_filename(
        p,
        {x.strip() for x in only.split(",") if x.strip()} if only else None,
    )
    with _EXPORT_JOB_LOCK:
        _EXPORT_JOBS[job_id] = {
            "pid": pid,
            "status": "queued",
            "path": None,
            "filename": fn,
            "error": None,
            "t": time.time(),
            "frames": len((p.get("spec") or {}).get("frames") or []),
        }

    def work() -> None:
        try:
            _EXPORT_RENDER_SLOTS.acquire()
            with _EXPORT_JOB_LOCK:
                st = _EXPORT_JOBS.get(job_id)
                if st:
                    st["status"] = "running"
            outfile = _export_build_zip(p, png, only, dest, fmt)
            with _EXPORT_JOB_LOCK:
                st = _EXPORT_JOBS.get(job_id)
                if not st:
                    return
                st["status"] = "done"
                st["path"] = str(dest)
                st["filename"] = outfile
                st["bytes"] = dest.stat().st_size if dest.is_file() else None
                st["t"] = time.time()
        except BaseException as e:
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass
            with _EXPORT_JOB_LOCK:
                st = _EXPORT_JOBS.get(job_id)
                if st:
                    st["status"] = "error"
                    st["error"] = str(e)
                    st["t"] = time.time()
        finally:
            _EXPORT_RENDER_SLOTS.release()

    threading.Thread(target=work, daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/projects/{pid}/export/jobs/{job_id}")
def export_job_status(pid: int, job_id: str):
    with _EXPORT_JOB_LOCK:
        job = _EXPORT_JOBS.get(job_id)
    if not job or job.get("pid") != pid:
        raise HTTPException(404, "Export job not found")
    eq, er = _export_load_snapshot()
    import socket

    return {
        "status": job["status"],
        "error": job.get("error"),
        "frames": job.get("frames"),
        "bytes": job.get("bytes"),
        "host": socket.gethostname(),
        "exports_queued": eq,
        "exports_running": er,
    }


def _stream_file(path: pathlib.Path, chunk: int = 1024 * 1024):
    with path.open("rb") as fh:
        while True:
            data = fh.read(chunk)
            if not data:
                break
            yield data


@app.get("/api/projects/{pid}/export/jobs/{job_id}/file")
def export_job_file(pid: int, job_id: str):
    with _EXPORT_JOB_LOCK:
        job = _EXPORT_JOBS.get(job_id)
    if not job or job.get("pid") != pid:
        raise HTTPException(404, "Export job not found")
    if job.get("status") != "done" or not job.get("path"):
        raise HTTPException(409, "Export not ready yet")
    path = pathlib.Path(job["path"])
    if not path.is_file():
        raise HTTPException(410, "Export file expired; start a new export")
    fn = job.get("filename") or "export.zip"
    size = path.stat().st_size
    headers = {
        "Content-Disposition": f'attachment; filename="{fn}"',
        "Content-Length": str(size),
    }
    return StreamingResponse(
        _stream_file(path),
        media_type="application/zip",
        headers=headers,
    )


@app.get("/api/projects/{pid}/export")
async def export(pid: int, png: int = 1, only: str = ""):
    p = (await _db_call(load, pid))
    try:
        data, fn = await asyncio.to_thread(_export_zip_payload, p, png, only, None)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(502, detail=f"Export failed: {e}") from e
    return Response(
        data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )


@app.get("/api/projects/{pid}/frames/{fid}/export.png")
async def export_frame_png(pid: int, fid: str):
    p = (await _db_call(load, pid))
    pages = _export_pages(p, {fid})
    try:
        cw, ch = theme_canvas.canvas_for_theme(p["theme"])
        data = await asyncio.to_thread(exporter.export_png, pages, (cw, ch))
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(502, detail=f"PNG export failed: {e}") from e
    fn = _dl_name(f"{p['name']}_{fid}", ".png")
    return Response(data, media_type="image/png", headers={"Content-Disposition": f'attachment; filename="{fn}"'})

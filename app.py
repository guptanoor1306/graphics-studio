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

import audio_transcribe, claude_client, critique, episode_audio, exporter, mf_studio, spec_enrich, storyboard_csv, storyboard_pdf, theme_canvas
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
app.mount("/themes", StaticFiles(directory=THEMES), name="themes")


@app.middleware("http")
async def cache_headers(request, call_next):
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
    d["episode_transcript_segments"] = len((tr or {}).get("segments") or [])
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
    """Merge project look with spec.look; UI props[] always wins over Claude's single prop."""
    pl = p.get("look") or {}
    spec = p.get("spec") or {}
    sl = spec.get("look") if spec else {}
    if isinstance(sl, str):
        out = {**pl, "look_line": sl}
    elif isinstance(sl, dict):
        out = {**sl, **pl}
    else:
        out = {**pl}
    if pl.get("props"):
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
    return theme == "zo-product-graphics"


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
    if is_zo_theme_name(theme):
        return (frame.get("mode") or "fss") == "fss"
    if is_mf_theme_name(theme):
        return frame.get("type") in MF_OVERLAY_TYPES
    return frame.get("mode") == "fss"


def save(pid, author, note, **fields):
    with connect() as c:
        cur = c.execute("select spec, storyboard from projects where id=?", (pid,)).fetchone()
        if not cur:
            raise HTTPException(404, "project not found")
        if "look" in fields and isinstance(fields["look"], dict):
            lk = dict(fields["look"])
            if _storyboard_pdf_on_disk(pid) and lk.get("sb_import") != "script":
                lk.setdefault("sb_import", "pdf")
            fields["look"] = lk
        if "spec" in fields or "storyboard" in fields:
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


def frame_for_render(p: dict, frame: dict, *, enrich: bool = False) -> dict:
    """Return frame JSON for preview/export. Enrich only at storyboard generation — not on render."""
    theme = p.get("theme") or ""
    f = _coerce_frame_for_studio(frame, theme)
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
def index(): return (ROOT / "static" / "index.html").read_text()

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

@app.post("/api/projects")
async def create(req: Request):
    b = await req.json()
    look = {**_DEFAULT_LOOK, **(b.get("look") or {})}
    try:
        pid = insert_project(
            b["name"], b.get("theme", "varsity-english"), b.get("script", ""),
            json.dumps(look), who(req), time.time(),
        )
    except Exception as e:
        raise HTTPException(500, detail=f"Database: {e}") from e
    return load(pid)

@app.get("/api/projects/{pid}")
def get(pid: int): return load(pid)


def _delete_project(pid: int) -> dict:
    with connect() as c:
        if not c.execute("select id from projects where id=?", (pid,)).fetchone():
            raise HTTPException(404, "project not found")
        c.execute("delete from versions where project_id=?", (pid,))
        c.execute("delete from projects where id=?", (pid,))
        c.commit()
    return {"ok": True}


@app.delete("/api/projects/{pid}")
def delete_project(pid: int):
    return _delete_project(pid)


@app.post("/api/projects/{pid}/delete")
def delete_project_post(pid: int):
    return _delete_project(pid)


@app.post("/api/projects/{pid}/storyboard")
async def make_storyboard(pid: int, req: Request):
    b = await req.json(); p = load(pid)
    look = b.get("look", p["look"]); script = b.get("script", p["script"])
    try:
        transcript = _episode_transcript_for_project(pid)
        out = await asyncio.to_thread(
            claude_client.storyboard,
            THEMES / p["theme"],
            script,
            look,
            b.get("notes", ""),
            episode_transcript=transcript,
        )
    except Exception as e:
        _raise_claude_gateway(e)
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
    elif is_hindi_theme_name(theme):
        finalize = None
        spec = out.get("spec") or {}
    else:
        plook = effective_look({**p, "look": look, "spec": out["spec"]})

        def finalize(sp):
            sp["look"] = plook
            return spec_enrich.enrich_spec(sp, sb, theme=theme)
        spec = finalize(out["spec"])
    # Render → look → fix (the skill's build/WARN/contact-sheet step) before anyone sees the frames.
    critique_report: dict = {}
    try:
        spec, critique_report = await asyncio.to_thread(
            _critique_spec, {**p, "look": plook}, spec, sb, script, finalize
        )
    except Exception as e:  # never lose a generated spec to a critique failure
        critique_report = {"error": str(e)}
    note = "generated storyboard"
    if critique_report.get("changed"):
        note += f" (auto-fixed {len(critique_report['changed'])} frame(s) after render review)"
    save(pid, who(req), note, script=script, look=plook, storyboard=sb, spec=spec)
    warn = claude_client.spec_quality_issues(spec, sb, theme=theme)
    warn += [f"layout: {w}" for w in critique_report.get("remaining") or []]
    return {**load(pid), "usage": out.get("usage"), "spec_warnings": warn, "critique": critique_report}


def _critique_spec(p_like: dict, spec: dict, storyboard: str, script: str, finalize) -> tuple[dict, dict]:
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
    if is_hindi_theme_name(theme):
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
    load(pid)
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
    save(pid, who(req), "upload episode audio")
    return {**load(pid), "ok": True}


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
    load(pid)
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
    p = load(pid)
    orig = (file.filename or "storyboard.pdf").strip() or "storyboard.pdf"
    look = {**(p.get("look") or {}), "sb_import": "pdf", "storyboard_pdf_name": orig}
    save(pid, who(req), "upload storyboard PDF", look=look)
    out = load(pid)
    return {**out, "ok": True, "has_pdf": _storyboard_pdf_on_disk(pid)}


@app.post("/api/projects/{pid}/storyboard-pdf/batch")
async def storyboard_pdf_batch_route(pid: int, req: Request):
    b = await req.json()
    p = load(pid)
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
    batch_size = min(10, max(1, int(b.get("batch_size", 5))))
    script = b.get("script", p.get("script") or "")
    transcript = _episode_transcript_for_project(pid)
    try:
        out = await asyncio.to_thread(
            claude_client.storyboard_pdf_batch,
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
    except Exception as e:
        _raise_claude_gateway(e)
    if not out.get("frames_added"):
        raw = out.get("raw_frame_count", 0)
        existing_n = len((p.get("spec") or {}).get("frames") or [])
        if not raw and existing_n:
            return {
                **load(pid),
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
    spec = _finalize_spec_after_batch(
        spec,
        storyboard,
        p["theme"],
        look if isinstance(look, dict) else {},
        p,
    )
    plook = look if isinstance(look, dict) else p.get("look")
    if is_mf_theme_name(p["theme"]) and isinstance(spec.get("look"), str) and isinstance(plook, dict):
        plook = {**plook, "look_line": spec["look"]}
    save(
        pid,
        who(req),
        f"PDF storyboard batch (+{out['frames_added']} frames)",
        script=script,
        look=plook,
        storyboard=storyboard,
        spec=spec,
    )
    warn = claude_client.spec_quality_issues(spec, storyboard, theme=p["theme"])
    return {
        **load(pid),
        "pdf_progress": out.get("pdf_progress"),
        "frames_added": out.get("frames_added"),
        "frames_dropped": out.get("frames_dropped") or 0,
        "spec_warnings": warn,
    }


@app.put("/api/projects/{pid}")
async def update(pid: int, req: Request):
    b = await req.json(); fields = {k: b[k] for k in ("name", "storyboard", "spec", "look", "theme", "script") if k in b}
    if "look" in fields:
        p = load(pid); spec = fields.get("spec") or p["spec"]
        if spec:
            merged = effective_look({**p, "look": fields["look"], "spec": spec})
            spec["look"] = merged
            fields["look"] = merged
            fields["spec"] = spec
    save(pid, who(req), b.get("note", "manual edit"), **fields); return load(pid)

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
    img.save(path, "PNG")
    rel = f"uploads/ref_{pid}_{safe}.png"
    return rel, path.read_bytes()


@app.post("/api/projects/{pid}/frames/{fid}/edit")
async def edit(pid: int, fid: str, req: Request):
    p = load(pid)
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
        save(pid, who(req), f"{fid}: layer ref #{item_index}", spec=spec)
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
        )
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
        elif regenerate and not ref_src:
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
    except Exception as e:
        _raise_claude_gateway(e)
    if is_zo_theme_name(p["theme"]) or not is_mf_theme_name(p["theme"]):
        new = normalize_cards_items(new)
    spec["frames"][i] = new
    note = f"{fid}: {(ask or 'reference')[:80]}"
    save(pid, who(req), note, spec=spec)
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
    p = load(pid); name = f"user_{pid}"
    cw, ch = theme_canvas.canvas_for_theme(p["theme"])
    Image.open(io.BytesIO(await file.read())).convert("RGB").resize((cw, ch)).save(
        THEMES / p["theme"] / "assets/plates" / f"{name}.png"
    )
    look = {**p["look"], "plate": name}; save(pid, who(req), "uploaded anchor plate", look=look)
    if p["spec"]: p["spec"]["look"]["plate"] = name; save(pid, who(req), "plate on spec", spec=p["spec"])
    return load(pid)

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

    p = load(pid)
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
    save(pid, who(req), "storyboard ref", look=look)
    return load(pid)


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
    p = load(pid)
    refs = list((p.get("look") or {}).get("ref_images") or [])
    if rel not in refs:
        raise HTTPException(404, "Reference not found")
    refs = [r for r in refs if r != rel]
    look = {**p["look"], "ref_images": refs}
    save(pid, who(req), "remove storyboard ref", look=look)
    fp = THEMES / p["theme"] / "assets" / rel
    if fp.is_file():
        fp.unlink()
    return load(pid)

@app.get("/api/projects/{pid}/check")
async def check(pid: int):
    from playwright.async_api import async_playwright
    p = load(pid); m = builder(p["theme"]); warns = []
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

def _export_pages(p: dict, only_ids: set[str] | None = None) -> list[tuple[str, str, bool, str | None]]:
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
                frame_for_render(p, f),
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
    if dest is not None:
        exporter.export_zip(
            pages,
            THEMES / p["theme"],
            bool(png),
            (cw, ch),
            storyboard_csv=sb_csv,
            zip_path=dest,
        )
        return b"", fn
    data = exporter.export_zip(
        pages,
        THEMES / p["theme"],
        bool(png),
        (cw, ch),
        storyboard_csv=sb_csv,
    )
    return data, fn


def _export_build_zip(p: dict, png: int, only: str, dest: pathlib.Path) -> str:
    _, fn = _export_zip_payload(p, png, only, dest)
    return fn


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
def export_start_job(pid: int, png: int = 1, only: str = ""):
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
            outfile = _export_build_zip(p, png, only, dest)
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
    p = load(pid)
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
    p = load(pid)
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

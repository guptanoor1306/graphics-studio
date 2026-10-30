"""Graphics Studio: a team web app around the theme skill packs.

Run:  copy .env.example to .env, set ANTHROPIC_API_KEY, then uvicorn app:app --host 0.0.0.0 --port 8000

A theme = a folder in themes/ (the skill kit: SKILL.md, references/spec_format.md, templates/, assets/, scripts/build.py).
Add a channel by dropping in another kit folder; nothing else changes.
"""
import importlib.util, json, os, pathlib, re, time, asyncio
from urllib.parse import quote
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = pathlib.Path(__file__).parent
load_dotenv(ROOT / ".env")
import copy

import claude_client, exporter, mf_studio, spec_enrich, theme_canvas
from frame_edit_util import (
    apply_flat_paste_replace,
    apply_layer_reference_replace,
    finalize_reference_edit,
    merge_item_edit,
    mf_path_item_index,
    normalize_cards_items,
    remove_scene_illustrations,
    strip_upload_assets,
)
from claude_client import _storyboard_line_for_frame
from db_store import SQLITE_PATH, backend, connect, insert_project
THEMES = ROOT / "themes"
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
    return d


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

def frame_for_render(p: dict, frame: dict, *, enrich: bool = False) -> dict:
    """Return frame JSON for preview/export. Enrich only at storyboard generation — not on render."""
    f = copy.deepcopy(frame)
    if enrich:
        spec_enrich.enrich_spec({"frames": [f], "look": effective_look(p)}, p.get("storyboard") or "")
    return f


def frame_page(theme, frame, look, base_href: str | None = None, edit: bool = False):
    html = builder(theme).frame_html(frame, look, edit=edit)
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
    out = {
        "project_count": n,
        "backend": backend(),
        "host": socket.gethostname(),
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
        out = await asyncio.to_thread(claude_client.storyboard, THEMES / p["theme"], script, look, b.get("notes", ""))
    except Exception as e:
        _raise_claude_gateway(e)
    if is_mf_theme_name(p["theme"]):
        spec = mf_studio.compact_mf_spec_for_studio(out["spec"])
        plook = {**look}
        if isinstance(spec.get("look"), str):
            plook["look_line"] = spec["look"]
        save(pid, who(req), "generated storyboard", script=script, look=plook, storyboard=out["storyboard"], spec=spec)
    elif is_zo_theme_name(p["theme"]):
        spec = mf_studio.compact_zo_spec_for_studio(out["spec"])
        if isinstance(look, dict) and look.get("plate") and isinstance(spec.get("look"), dict):
            spec["look"].setdefault("plate", look["plate"])
        save(pid, who(req), "generated storyboard", script=script, look=look, storyboard=out["storyboard"], spec=spec)
        out["spec"] = spec
    else:
        merged = effective_look({**p, "look": look, "spec": out["spec"]})
        out["spec"]["look"] = merged
        out["spec"] = spec_enrich.enrich_spec(out["spec"], out.get("storyboard") or "")
        save(pid, who(req), "generated storyboard", script=script, look=merged, storyboard=out["storyboard"], spec=out["spec"])
    warn = claude_client.spec_quality_issues(out["spec"], out.get("storyboard") or "", theme=p["theme"])
    return {**load(pid), "usage": out.get("usage"), "spec_warnings": warn}

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
            new = merge_item_edit(before, new, item_index)
            if smart_ref and ref_src:
                new = strip_upload_assets(new, ref_src)
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
        )
    except Exception as e:
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
                warns += [f"{f['id']}: {w}" for w in await pg.evaluate(m.CHECK_JS)]
            await b.close()
    except Exception as e:
        raise HTTPException(502, detail=f"Layout check failed: {e}") from e
    return warns

def _export_pages(p: dict, only_ids: set[str] | None = None) -> list[tuple[str, str, bool]]:
    if not p.get("spec"):
        raise HTTPException(400, "Project has no spec")
    base = f"{preview_base()}/themes/{p['theme']}/scenes/"
    look = effective_look(p)
    pages: list[tuple[str, str, bool]] = []
    for f in (p.get("spec") or {}).get("frames") or []:
        fid = str(f.get("id") or "")
        if only_ids is not None and fid not in only_ids:
            continue
        if is_mf_theme_name(p["theme"]) and not is_zo_theme_name(p["theme"]) and not mf_studio.is_mf_renderable(f):
            continue
        if is_zo_theme_name(p["theme"]) and not mf_studio.is_zo_renderable(f):
            continue
        html = frame_page(p["theme"], frame_for_render(p, f), look, base_href=base)
        pages.append((fid, html, frame_wants_overlay(p["theme"], f)))
    if only_ids is not None and not pages:
        raise HTTPException(404, "Frame not found or not exportable")
    return pages


def _dl_name(base: str, suffix: str) -> str:
    safe = re.sub(r"[^\w.-]+", "_", (base or "export").strip()) or "export"
    return f"{safe}{suffix}"


@app.get("/api/projects/{pid}/export")
async def export(pid: int, png: int = 1, only: str = ""):
    p = load(pid)
    ids = {x.strip() for x in only.split(",") if x.strip()} if only else None
    pages = _export_pages(p, ids)
    try:
        cw, ch = theme_canvas.canvas_for_theme(p["theme"])
        data = await asyncio.to_thread(
            exporter.export_zip, pages, THEMES / p["theme"], bool(png), (cw, ch)
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(502, detail=f"Export failed: {e}") from e
    if ids and len(ids) == 1:
        fid = next(iter(ids))
        fn = _dl_name(f"{p['name']}_{fid}", "_export.zip")
    else:
        fn = _dl_name(p["name"], "_frames.zip")
    return Response(data, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{fn}"'})


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

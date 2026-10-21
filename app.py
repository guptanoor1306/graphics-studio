"""Graphics Studio: a team web app around the theme skill packs.

Run:  copy .env.example to .env, set ANTHROPIC_API_KEY, then uvicorn app:app --host 0.0.0.0 --port 8000

A theme = a folder in themes/ (the skill kit: SKILL.md, references/spec_format.md, templates/, assets/, scripts/build.py).
Add a channel by dropping in another kit folder; nothing else changes.
"""
import importlib.util, json, os, pathlib, sqlite3, time, asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = pathlib.Path(__file__).parent
load_dotenv(ROOT / ".env")
import copy

import claude_client, exporter, spec_enrich
THEMES = ROOT / "themes"
DB = ROOT / "data" / "studio.db"
SELF_URL = os.environ.get("STUDIO_URL", "http://127.0.0.1:8000")
app = FastAPI(title="Graphics Studio")
app.mount("/themes", StaticFiles(directory=THEMES), name="themes")

# ------------------------------------------------------------------ storage (SQLite; swap for Postgres in prod)
def db():
    DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.executescript("""create table if not exists projects(id integer primary key, name text, theme text, script text,
        look text, storyboard text, spec text, updated_by text, updated_at real);
        create table if not exists versions(id integer primary key, project_id int, spec text, storyboard text,
        author text, note text, ts real);""")
    return c

def load(pid):
    r = db().execute("select * from projects where id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "project not found")
    d = dict(r); d["look"] = json.loads(d["look"] or "{}"); d["spec"] = json.loads(d["spec"] or "null")
    return d


def effective_look(p: dict) -> dict:
    """Merge project look with spec.look; UI props[] always wins over Claude's single prop."""
    pl = p.get("look") or {}
    sl = (p.get("spec") or {}).get("look") or {} if p.get("spec") else {}
    out = {**sl, **pl}
    if pl.get("props"):
        out["props"] = pl["props"]
        out.pop("prop", None)
    return out

def save(pid, author, note, **fields):
    c = db(); cur = load(pid)
    if "spec" in fields or "storyboard" in fields:   # keep a version for undo / history
        c.execute("insert into versions(project_id,spec,storyboard,author,note,ts) values(?,?,?,?,?,?)",
                  (pid, json.dumps(cur["spec"]), cur["storyboard"], author, note, time.time()))
    for k in ("look", "spec"):
        if k in fields: fields[k] = json.dumps(fields[k], ensure_ascii=False)
    fields.update(updated_by=author, updated_at=time.time())
    c.execute(f"update projects set {', '.join(f'{k}=?' for k in fields)} where id=?", (*fields.values(), pid)); c.commit()

def who(req: Request):  # put the app behind your SSO proxy; it forwards the user's email in this header
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

def frame_for_render(p: dict, frame: dict) -> dict:
    """Apply kit enrichments at render time (fixes legacy text-only specs without re-generating)."""
    f = copy.deepcopy(frame)
    spec_enrich.enrich_spec({"frames": [f], "look": effective_look(p)}, p.get("storyboard") or "")
    return f


def frame_page(theme, frame, look):
    html = builder(theme).frame_html(frame, look)
    return html.replace("<head>", f'<head><base href="/themes/{theme}/scenes/">', 1)

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

@app.get("/api/projects")
def projects():
    return [dict(r) for r in db().execute("select id,name,theme,updated_by,updated_at from projects order by updated_at desc")]

_DEFAULT_LOOK = {"anchor": "right", "fss": "blue", "props": ["coins"]}

@app.post("/api/projects")
async def create(req: Request):
    b = await req.json(); c = db()
    look = {**_DEFAULT_LOOK, **(b.get("look") or {})}
    cur = c.execute("insert into projects(name,theme,script,look,updated_by,updated_at) values(?,?,?,?,?,?)",
                    (b["name"], b.get("theme", "varsity-english"), b.get("script", ""), json.dumps(look), who(req), time.time()))
    c.commit(); return load(cur.lastrowid)

@app.get("/api/projects/{pid}")
def get(pid: int): return load(pid)


def _delete_project(pid: int) -> dict:
    c = db()
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
    """Same as DELETE (some proxies / old app builds only registered GET on this path)."""
    return _delete_project(pid)


@app.post("/api/projects/{pid}/storyboard")
async def make_storyboard(pid: int, req: Request):
    b = await req.json(); p = load(pid)
    look = b.get("look", p["look"]); script = b.get("script", p["script"])
    try:
        out = await asyncio.to_thread(claude_client.storyboard, THEMES / p["theme"], script, look, b.get("notes", ""))
    except Exception as e:
        _raise_claude_gateway(e)
    merged = effective_look({**p, "look": look, "spec": out["spec"]})
    out["spec"]["look"] = merged
    out["spec"] = spec_enrich.enrich_spec(out["spec"], out.get("storyboard") or "")
    save(pid, who(req), "generated storyboard", script=script, look=merged, storyboard=out["storyboard"], spec=out["spec"])
    warn = claude_client.spec_quality_issues(out["spec"], out.get("storyboard") or "")
    return {**load(pid), "usage": out.get("usage"), "spec_warnings": warn}

@app.put("/api/projects/{pid}")
async def update(pid: int, req: Request):
    """Manual edits from the UI: storyboard text, whole spec, look/theme switches."""
    b = await req.json(); fields = {k: b[k] for k in ("name", "storyboard", "spec", "look", "theme", "script") if k in b}
    if "look" in fields:   # a theme switch applies to every frame
        p = load(pid); spec = fields.get("spec") or p["spec"]
        if spec:
            merged = effective_look({**p, "look": fields["look"], "spec": spec})
            spec["look"] = merged
            fields["look"] = merged
            fields["spec"] = spec
    save(pid, who(req), b.get("note", "manual edit"), **fields); return load(pid)

@app.post("/api/projects/{pid}/frames/{fid}/edit")
async def edit(pid: int, fid: str, req: Request):
    b = await req.json(); p = load(pid); spec = p["spec"]
    i = next((k for k, f in enumerate(spec["frames"]) if f["id"] == fid), None)
    if i is None: raise HTTPException(404, "frame not found")
    try:
        new = await asyncio.to_thread(claude_client.edit_frame, THEMES / p["theme"], spec["frames"][i], effective_look(p), b["ask"])
    except Exception as e:
        _raise_claude_gateway(e)
    spec["frames"][i] = new
    save(pid, who(req), f"{fid}: {b['ask'][:80]}", spec=spec); return new

@app.post("/api/projects/{pid}/undo")
def undo(pid: int, req: Request):
    c = db(); v = c.execute("select * from versions where project_id=? order by id desc limit 1", (pid,)).fetchone()
    if not v: raise HTTPException(400, "nothing to undo")
    c.execute("update projects set spec=?, storyboard=? where id=?", (v["spec"], v["storyboard"], pid))
    c.execute("delete from versions where id=?", (v["id"],)); c.commit(); return load(pid)

@app.get("/api/projects/{pid}/history")
def history(pid: int):
    return [dict(r) for r in db().execute("select id,author,note,ts from versions where project_id=? order by id desc limit 50", (pid,))]

@app.post("/api/projects/{pid}/plate")
async def plate(pid: int, req: Request, file: UploadFile = File(...)):
    """Upload a frame grab of the anchor shot; it becomes this project's anchor plate."""
    from PIL import Image
    import io
    p = load(pid); name = f"user_{pid}"
    Image.open(io.BytesIO(await file.read())).convert("RGB").resize((1920, 1080)).save(THEMES / p["theme"] / "assets/plates" / f"{name}.png")
    look = {**p["look"], "plate": name}; save(pid, who(req), "uploaded anchor plate", look=look)
    if p["spec"]: p["spec"]["look"]["plate"] = name; save(pid, who(req), "plate on spec", spec=p["spec"])
    return load(pid)

@app.get("/preview/{pid}/{fid}", response_class=HTMLResponse)
def preview(pid: int, fid: str):
    p = load(pid); f = next((f for f in p["spec"]["frames"] if f["id"] == fid), None)
    if not f: raise HTTPException(404)
    return frame_page(p["theme"], frame_for_render(p, f), effective_look(p))

@app.get("/api/projects/{pid}/check")
async def check(pid: int):
    """Run the theme's automatic layout checks (anchor overlap, off-frame, colours...) on every frame."""
    from playwright.async_api import async_playwright
    p = load(pid); m = builder(p["theme"]); warns = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        for f in p["spec"]["frames"]:
            await pg.goto(f"{SELF_URL}/preview/{pid}/{f['id']}"); await pg.wait_for_timeout(200)
            warns += [f"{f['id']}: {w}" for w in await pg.evaluate(m.CHECK_JS)]
        await b.close()
    return warns

@app.get("/api/projects/{pid}/export")
def export(pid: int, png: int = 1, only: str = ""):
    p = load(pid); ids = set(only.split(",")) if only else None
    pages = [(f["id"], f"{SELF_URL}/preview/{pid}/{f['id']}", f.get("mode") == "fss")
             for f in p["spec"]["frames"] if not ids or f["id"] in ids]
    data = exporter.export_zip(pages, THEMES / p["theme"], want_png=bool(png))
    fn = f"{p['name'].replace(' ', '_')}_frames.zip"
    return Response(data, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{fn}"'})

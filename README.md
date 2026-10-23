# Graphics Studio

A team web app built on the theme skill packs. A team member:
1. pastes a script and picks the look (channel theme, anchor side, full-screen accent, topic prop, optional anchor frame grab);
2. clicks **Generate**: Claude writes the storyboard and the frame spec;
3. sees every frame rendered live, then fixes any frame by **asking Claude in plain English** ("make the table bigger", "move Rahul right") or by editing its JSON;
4. runs **Check layout** (anchor overlap, off-frame, off-palette colours, mixed headings…);
5. clicks **Export**, which downloads a zip of static, layer-ready HTML (plus PNGs) for your layer tool.

Everyone sees the same projects. Every change is versioned, with author and note, and can be undone.

```
browser UI (static/index.html)
   │  REST
FastAPI (app.py) ── SQLite/Postgres: projects + versions
   ├─ claude_client.py ─ Anthropic API (storyboard + per-frame edits, cached rules)
   ├─ themes/<channel>/   ← the skill kit, unchanged: rules, CSS, assets, build.py
   │     build.py.frame_html(frame, look) → HTML     (same renderer the Claude skill uses)
   └─ exporter.py ─ headless Chromium → static HTML (+PNG) zip for the layer tool
```

## Run it

```bash
pip install -r requirements.txt && python -m playwright install chromium
cp .env.example .env                           # then set ANTHROPIC_API_KEY in .env
uvicorn app:app --host 0.0.0.0 --port 8000     # open http://localhost:8000
```
Default model is `claude-opus-5-5` (medium effort is the API default). Set `STUDIO_MODEL` in `.env`.

Docker: `docker build -t graphics-studio . && docker run -p 8000:8000 -e ANTHROPIC_API_KEY=... -v $PWD/data:/app/data graphics-studio`

`STUDIO_URL` must be the address the server can reach itself on (default `http://127.0.0.1:8000`); export and checks render through it.

## Production checklist
- **Auth:** put it behind your SSO / reverse proxy (Google IAP, Cloudflare Access, oauth2-proxy). The app records the user from the `X-User-Email` header for history.
- **Database:** Local = SQLite in `data/`. Production = set **`DATABASE_URL`** (Postgres). See [RAILWAY.md](RAILWAY.md) (recommended) or [RENDER.md](RENDER.md).
- **Uploaded anchor plates** are written into `themes/<theme>/assets/plates/user_<id>.png`. Mount `themes/` on a persistent volume or move uploads to S3.
- **Spend:** watch Anthropic usage per key. One storyboard is a single call (cached rules ~4k tokens + script in, spec out). An edit is a small call with only one frame's JSON.

## Add another channel or theme
Make a new skill kit for the channel (the same structure as `themes/varsity-english`). Drop the folder into `themes/` and restart; it appears in the Theme dropdown. The kit is the single source of truth. Updating `SKILL.md`, the CSS or the assets there updates both the Claude skill and the app.

## Contract with your layer tool (export zip)
| Folder | Content |
|---|---|
| `html/<frame>.html` | one **static** page per frame at 1920×1080: no scripts, CSS inlined, fonts and images embedded as data URIs, characters/doodles as inline SVG |
| `html_overlay/<frame>.html` | anchor frames without the background plate (graphics only) |
| `png/` | rendered frames, plus transparent `_overlay.png` for anchor frames |

Every visual element carries `data-layer="<component>:<text>"` (e.g. `htab:Tax Calculation without HUF`, `plate:background`, `img:…building_company_3d.png`) and its rendered box `data-x / data-y / data-w / data-h` in px. Map these to layer names and positions. If your tool needs a different shape (absolute-only positioning, SVG text outlines, one file per video, a JSON layer list), change `FLATTEN_JS` in `exporter.py`; it's one function.

## Where things live
| File | Purpose |
|---|---|
| `app.py` | API, storage, versioning, preview, checks, export |
| `claude_client.py` | the two Claude calls (forced JSON via tool schema; rules in a cached system block) |
| `exporter.py` | static layer-ready HTML + PNG zip |
| `static/index.html` | the whole UI (vanilla JS, no build step) |
| `themes/varsity-english/` | the Varsity skill kit (rules, CSS, components, assets, renderer) |

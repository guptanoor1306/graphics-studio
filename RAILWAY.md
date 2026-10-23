# Deploy on Railway

## One-time setup

1. Install CLI: `npm i -g @railway/cli` (or use `railway up` from the Railway skill).
2. From this repo root: `railway login` then `railway init` (new project) or link an existing project.
3. Add **PostgreSQL** in the Railway dashboard (or `railway add --database postgres`). Railway sets **`DATABASE_URL`** on the web service automatically when you reference the plugin.
4. Set variables on the **web** service:
   - `ANTHROPIC_API_KEY` — required
   - `STUDIO_URL` — optional; defaults to `http://127.0.0.1:$PORT` inside the container (used for export/layout checks)
   - `STUDIO_MODEL` — optional
5. Deploy: `railway up` (uses `Dockerfile` + Playwright Chromium image).

## Migrate from Render

1. Export or note projects from Render Postgres if you need data (pg_dump), or start fresh.
2. Point DNS to Railway after the first successful deploy.
3. Mount or accept ephemeral **`themes/*/assets/uploads`** and **`assets/plates`** — same as Render; use a Railway volume on `/app/themes` if you need persistent uploads.

## Health

GET `/` serves the studio UI. Railway healthcheck uses `/` per `railway.toml`.

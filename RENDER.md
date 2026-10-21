# Deploy on Render (no auth)

1. Push this repo to GitHub.
2. Render → **New** → **Blueprint** → connect `graphics-studio` (uses `render.yaml`).
3. **Environment variables** (Blueprint sets `DATABASE_URL` from Postgres automatically):
   - `ANTHROPIC_API_KEY` — required
   - `STUDIO_URL` — optional; export/check use **loopback** inside the container (`127.0.0.1:$PORT`).
4. **Export** can take 1–2 minutes for many frames; wait for the download. If it fails, the error message should say why (502).

**Projects** are stored in **Render Postgres** (shared for everyone on that URL; survives redeploys).  
**Themes** stay in the Docker image. Custom **anchor plate uploads** still write to the container filesystem (may reset on redeploy unless you add a disk later).

**Local dev:** no `DATABASE_URL` → SQLite in `data/studio.db`.

**Existing Render web service (no Blueprint):** create a **PostgreSQL** instance on Render, copy **Internal Database URL** into the web service as `DATABASE_URL`, redeploy.

Check sync: `/api/status` should show `"backend": "postgres"` and the same `project_count` for all teammates.

# Deploy on Render (no auth)

1. Push this repo to GitHub (`guptanoor1306/graphics-studio`).
2. [Render](https://render.com) → **New** → **Blueprint** → connect the repo (uses `render.yaml`),  
   **or** **New Web Service** → Docker, root `Dockerfile`.
3. **Environment variables:**
   - `ANTHROPIC_API_KEY` — required
   - `STUDIO_URL` — your service URL, e.g. `https://graphics-studio-xxxx.onrender.com` (set after first deploy; needed for Export / Check layout)
4. Blueprint mounts a **1 GB disk** at `/app/data` for SQLite projects.

No login: anyone with the URL shares projects (`anonymous` in history). Same as local/Railway.

**Note:** Free tier may spin down when idle; first request after sleep can be slow. Playwright is in the Docker image for export.

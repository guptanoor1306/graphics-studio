# Deploy on Railway (no auth)

If Railway is unavailable, use **[Render](RENDER.md)** with the same repo (recommended). Vercel is not suitable — see [VERCEL.md](VERCEL.md).


1. Push this repo to GitHub (see below).
2. [Railway](https://railway.com) → **New project** → **Deploy from GitHub repo** → select `graphics-studio`.
3. **Variables** (service → Variables):
   - `ANTHROPIC_API_KEY` — required
   - `STUDIO_URL` — your public URL, e.g. `https://graphics-studio-production.up.railway.app` (copy from Railway **Settings → Networking → Public URL** after generate domain)
   - Optional: `STUDIO_MODEL` (default `claude-opus-5-5`)
4. **Volume** (recommended): mount `/app/data` so SQLite projects survive redeploys.
5. **Generate domain** under Networking if Railway did not assign one.

No login is configured: everyone with the URL shares the same projects (author shows as `anonymous`). Add auth later via a reverse proxy if needed.

**Themes** ship in the Docker image under `themes/`. **Projects** live in `data/studio.db` on the volume.

# Why not Vercel (for this app)

Graphics Studio is a **long-running FastAPI server** with:

- **Claude storyboard** calls (~1–2 minutes) — Vercel serverless **timeouts** (10s hobby / 60s Pro on functions) will cut these off.
- **Playwright + Chromium** for Export and Check layout — not supported on typical Vercel Python functions.
- **SQLite** in `data/` — serverless filesystem is **ephemeral** unless you add an external database.

So Vercel is a poor match unless you split the product (static UI on Vercel + API hosted elsewhere).

## Simple alternatives (git → deploy, no auth)

| Host | Fit |
|------|-----|
| **[Render](RENDER.md)** | Same Dockerfile as Railway; free web service + disk for `data/`. |
| **Fly.io** | `fly launch` with Dockerfile; volume for `/app/data`. |
| **Railway** | [RAILWAY.md](RAILWAY.md) when available. |

Push to GitHub first, then connect the repo on Render (or Fly).

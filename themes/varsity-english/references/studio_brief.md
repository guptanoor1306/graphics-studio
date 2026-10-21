# Graphics Studio (web app) — extra rules on top of the skill

The app renders `spec.json` directly. You are NOT in chat-only storyboard mode: **every graphic beat must be a complete frame** in `spec.frames[]`.

## Modes (required on every frame)
- **`mode: "anchor"`** — text/illustrations beside the anchor plate. Use for OST, OSA, short tables (≤5 rows), popups.
- **`mode: "fss"`** — **full-screen**, no anchor visible. Use for: large calc tables, bar charts, card rows, long lists (“things to remember”), multi-step comparisons, any beat the skill calls FSS.

If the script has comparisons, RMS rules, numbered situations, or tables → **include at least one `mode: "fss"` frame**. Do not make everything anchor.

## Visual density (match `scenes/example_spec.json`)
Text-only frames (only `title` / `htab` / `text` / `points`) are **not enough** for most beats.

| Beat type | Required in `items[]` |
|-----------|------------------------|
| Company / broker / RMS / trade | **Always** `asset` + often `person` — even when the skill calls the beat OST (text-only OST is invalid in the app) |
| Table / tax calc | `calc_table` or `glass_table` (FSS if large) |
| Chart / comparison | `bars` on **fss** |
| List recap | `nlist` on **fss** |
| Hero title | `title` stack (can be anchor-only) |

## Corner props (`look.props` array)
The skill allows **one** topic prop per video. The UI may list several; the renderer uses **only the first** as small floor dressing on frames without `asset`/`person` (never on hero **title-only** frames). Scene meaning comes from explicit `asset`/`person` in `items[]`, not from stacking every checkbox icon.

## Storyboard line format
Each graphic beat: `~M:SS – OST|OSA|FSS – description → frame_id`

# Web app overrides (read after SKILL.md)

These rules **override** the skill’s chat/token shortcuts when generating `submit_storyboard` output.

## Storyboard first, then spec
1. Write the full SB Doc (one line per beat: footage, OST, OSA, FSS, screen capture) using the script’s sections and numbers.
2. Every line marked **OSA** or **FSS** must have a matching frame in `spec.frames[]` with the right `mode` and kit items — not text-only.
3. **Do not** merge whole sections into one frame to satisfy the skill’s “~words/80” density target. In the app, prefer **one graphic per section heading / situation / table**, even if that is more frames than the density formula.

## OST vs OSA vs FSS (app)
| SB tag | Spec requirement |
|--------|------------------|
| **OST** title stack only | `title` items only; **no** corner prop clutter; usually no `asset`/`person` |
| **OST** htab + explanation | Invalid alone — use **OSA**: add `asset`/`person` from `assets/INDEX.md` that fit **this beat** (e.g. `setA/building_company_3d.png` for broker/RMS, not every prop icon) |
| **OSA** | `asset` and/or `person` + text/table; pick assets by **beat meaning**, grep INDEX |
| **FSS** | `mode: "fss"` + `calc_table`, `bars`, `nlist`, etc. |

## Topic prop (corner)
The skill allows **one** topic prop per video (`coins`, `tax`, `jar`, `house`, or `bank`). The UI may list several checkboxes; the renderer uses **only the first** selected prop as small floor dressing on frames **without** their own `asset`/`person`. Never treat checkboxes as “show all icons”.

## Broker / RMS scripts
- Hero **title** frame: title stack only.
- RMS definition / margin monitoring: **OSA** with broker building + optional persona.
- Margin **numbers**: **OSA** `glass_table` or **FSS** `calc_table` if many rows.
- “Situation 1 / 2 …” lists: **OSA** or **FSS** `nlist` when ≥4 bullets.

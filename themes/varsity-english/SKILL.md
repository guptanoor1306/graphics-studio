---
name: varsity-graphics
description: Turn a Varsity (English IP) long-form video script into a storyboard (SB Doc) and the on-screen graphics as 1920x1080 PNGs in the house style, deciding beat by beat whether a moment needs a graphic or should stay on footage.
---

# Varsity graphics: script → storyboard → PNGs

Output, in order: (1) the **storyboard in chat**, (2) **one PNG per graphic beat** named by timestamp. Anchor-shot frames also get a transparent `_overlay.png` for the editor.

## Token budget rules (follow strictly)
- Read only this file, `references/spec_format.md` and `scenes/example_spec.json`. Do **not** open `references/deep/*`, `templates/*.css/js` or `scripts/*.py` unless something breaks.
- Look at **one** image for style: `references/style_at_a_glance.jpg`. Open a `references/deep/sheet_<video>.jpg` only if a beat type is truly unfamiliar.
- Find assets with `grep -i <word> assets/INDEX.md`. Never read the whole index.
- Write **all frames in one `spec.json`** and build them with one command. Don't hand-write HTML.
- QA with the printed `WARN` lines plus **one** look at each `out/_sheet_N.jpg` (6 frames per sheet, legible). Open a full-size PNG only for a frame you are fixing, then rebuild with `--only <id>`.
- Keep the storyboard to one line per beat.

## Step 1: Setup
Work in a job folder **outside** the kit. Keep `spec.json` and `out/` there.
```bash
mkdir -p job && cd job
[ -d varsity-graphics ] || unzip -q /path/to/varsity-graphics-skill.zip    # skip if already unpacked or installed as a skill
python3 -c "import playwright" 2>/dev/null || pip install playwright --break-system-packages -q; python3 -m playwright install chromium 2>/dev/null || true
```
(If Chromium can't be installed, set `CHROMIUM_PATH` to an existing Chromium binary.) Below, `$K` is the kit folder: `K=varsity-graphics`, or the installed skill's folder if it's loaded as a skill.

## Step 2: Settle the look (state it in one line)
- **Anchor side:** right (default) or left. If the user attached a frame grab, save it as `assets/plates/user_anchor.png` (1920×1080) and set `"plate":"user_anchor"`.
- **FSS accent:** blue (default), or warm for home/loan topics.
- **Hero keyword:** e.g. ESOPs, HUF, ITR.
- **Personas:** one colour each, used all video long.
- **Topic prop:** coins / tax / jar / house / bank.

## Step 3: Make the call for each beat
| Code | When |
|---|---|
| **OST** (text over the anchor) | section heading, the hook question, a definition, a sum or total said aloud (popup) |
| **OSA** (small illustration over the anchor) | characters, a company/bank/house, ≤5-row tables, value labels, one document line |
| **FSS** (full screen) | ≥6-row or ≥3-column tables, charts, card rows, "things to remember", multi-entity scenes |
| **Footage** | hook lines to camera, lone one-liners the next title carries, bridges ("Now let's pause"), recaps, caveats with no new number, conclusion |
| **Screen capture** | websites, PDFs, govt pages, calculators, tool CTAs (give the URL) |
| **Badger / CTA** | mark only |

Rules:
1. Every section heading gets a frame: `title` stack for the video's opening/hero question, `htab` (+ `points` or a visual) for every other section.
2. Every number the VO says goes on screen, with the answer row or bar made distinct. Exception: numbers in the 15-second hook get at most **one** OSA; the rest stays on footage.
3. A list gets one element per item, revealed in VO order. A numbered series gets a chapter-marker frame re-shown before each item.
4. A document mentioned becomes a mock document built with `html` or `glass_table`.
5. Change over time becomes `bars`.
6. A calculation gets one FSS `calc_table` per table, with its owner (`person`) beside it.
7. "Continue / highlight as per VO" reuses the frame: **no new PNG**. Add `_a/_b` only when content changes. A list (e.g. Things to remember) is **one** frame with `active:"all"` unless the storyboard asks for a per-item reveal.
8. Storyboard reference images are content only; redraw in the house style.
9. When the script and storyboard disagree on a fact, follow the script and flag it.
10. Trim text to the number + label. Copy numbers exactly (₹, Indian grouping). Spell-check titles.

## Design rules from team review (apply to every frame)
1. **One heading system per video:** `htab` everywhere (anchor frames: auto-pinned top-left; FSS: centred top). Use the `title` stack only for the opening/hero title. Don't mix `pill`, `definition` or `defcard` in as headings.
2. **Hierarchy:** heading = `htab` (40 Bold, boxed). Points under it = `points` (31px plain text, numbered discs, no box). Never the same size; no invented sizes.
3. **No glass boxes for text over the anchor.** Glass is only for small tables (`glass_table`).
4. **Everything stands on the floor.** Leave `y` off assets and people and the builder seats their visible bottom on the floor line, padding included. Never float objects.
5. **Proportion:** buildings ≈ 520–600 px tall, characters ≈ 300–330 px (the builder's defaults). Objects shouldn't all be the same size.
6. **Names over the anchor** use the large dark pill (automatic).
7. **Charts:** `bars` (boxed ₹ y-axis, baseline, 26–30 px labels), centred under the heading on FSS. Key numbers go in the heading or big labels, never small captions.
8. **Declutter:** one idea per frame, at most 1–3 illustrations. Drop decorative icons (clock, magnifier) when they compete. The topic prop is skipped automatically on frames that have their own illustrations.
9. **Colours:** kit tokens only (blue #248EF7, blue-soft #64B0FC, amber #F2B233, green #A5CC65, coral #F26B5B, ink, white). The build warns on anything else.

**Density check:** aim for about one graphic per 20–40 s of VO. That is roughly `spoken_words / 80` frames, ±30%. If you are above that, merge beats.

## Step 4: Storyboard (in chat)
Estimate timestamps at **~165 spoken words per minute** (don't count headings; prefix `~`), or use real timecodes if given.
```
SB <> Doc: <title>
Look: anchor right · FSS blue · keyword ESOPs · Rahul=yellow · prop coins
~0:00 – Footage – hook to camera
~0:47 – OST – Title "What are / ESOPs / and how do they work?" → 0.47
~1:03 – OSA – continue 0:47, highlight grant details (no new frame)
~2:05 – Screen capture – incometaxindia.gov.in/… highlight "perquisite"
Totals: N graphics · M footage · K screen captures
```
If the user only asked for the storyboard, stop here.

## Step 5: Build all graphics in one go
Write `spec.json` (format in `references/spec_format.md`; working example in `scenes/example_spec.json`), then:
```bash
python3 $K/scripts/build.py spec.json --out out
```
This prints `WARN` lines (off-frame, covers the anchor, clipped, off-palette colour, mixed heading systems, glass text over the anchor, clutter) and writes `out/_sheet_N.jpg`. Fix the spec and rerun only the broken frames: `--only 0.47,2.05`. Stop when there are no WARNs and the sheet looks right.

## Step 6: Deliver
Zip `out/` (PNGs, overlays) plus `spec.json`, and send it. Close with frame counts and any assumptions. Anyone can edit text in `spec.json` and rerun.

Don'ts: no graphics over the anchor's face; no raw website screenshots (screen capture instead); no invented or re-rounded numbers; one FSS accent per video; no emoji or clip-art (use kit assets or flat SVG via `html`).

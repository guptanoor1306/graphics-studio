---
name: varsity-mf-graphics
description: Turn a Varsity Mutual Fund IP video script into a storyboard (SB Doc) and 1920x1080 PNG graphics in the GIFT City house style, deciding beat by beat between graphic, footage and screen capture.
---

# Varsity Mutual Fund IP: script → storyboard → graphics

Outputs, in order: (1) the **storyboard** in chat, one line per beat; (2) **one PNG per new graphic**, named by timestamp. Frames that sit over the anchor also get `<id>_overlay.png` (transparent) for the editor. A graphic exists only where it adds something the anchor's face can't. Most of the video stays on footage or screen captures.

## Token budget
- Read this file and `references/spec_format.md`. Open `references/gift_city_breakdown.md` when a beat type is unfamiliar. It is the worked example, with the reason behind every call.
- For the look, view **one** image: `references/style_at_a_glance.jpg` (the 13 original GIFT City frames). Open `references/examples/<id>.jpg` only when copying that layout.
- Find art with `grep -i <word> assets/INDEX.md`.
- Write **all frames in one `spec.json`** and build with one command. Don't hand-write pages.
- QA = the printed `WARN` lines + one look at each `out/_sheet_N.jpg`. Rebuild fixes with `--only`.

## Step 1: Setup
```bash
mkdir -p job && cd job
[ -d varsity-mf-graphics ] || unzip -q /path/to/varsity-mf-graphics.zip   # skip if installed as a skill
python3 -c "import playwright" 2>/dev/null || pip install playwright --break-system-packages -q
python3 -m playwright install chromium 2>/dev/null || true   # or export CHROMIUM_PATH=/path/to/chrome
K=varsity-mf-graphics   # or the installed skill folder
```

## Step 2: Read the script like a storyboard artist
Before deciding anything, mark up the script:
1. **Hero keyword**: the product or idea in the title (e.g. "GIFT City Funds").
2. **Agenda**: the "we cover N things" line. Its questions become the SOP, and each one starts a section.
3. **Section and sub-section headers**: "Question 2", "Difference 1: Taxation", a named sub-topic.
4. **Jargon** explained in one sentence (FoF, LRS, TCS, NAV…).
5. **Comparisons across many things**: funds × attributes, old term vs new term, option A vs B, rates.
6. **Named primary sources**: a fund's factsheet, a product page, RBI/SEBI/IFSCA pages, NAV pages. Also any `[NOTE: show screenshot]` in the script.
7. **Processes and loops** said in one breath ("you invest, you get units, …").
8. **Places, brands and concrete objects** in the hook.
9. **Lists** of benefits, limitations or things to watch.
10. **Everything else**: reactions, rhetorical questions, analogies, bridges, caveats, advice, conclusion.

## Step 3: Make the call for each beat
| Call | When | Template |
|---|---|---|
| **Roto big text** (ribbon over anchor) | first mention of the hero keyword; each "Difference N" or named sub-section header | `ribbon` |
| **SOP** (dark grid tiles) | the agenda line (2–3 questions); a sub-agenda inside a section ("what is X / how does it work") | `sop` |
| **Repeat** (no new PNG) | each section start → "Repeat <SOP id>, highlight Qn". Any later line about content already on screen (a table, the rates) → "Repeat <id>, highlight X" | `repeat` |
| **Definition** (OST over anchor) | a term or acronym defined in a sentence, once per term | `definition` |
| **Table** (OSA/FSS) | ≥3 items compared on ≥2 attributes; old→new term mapping; tax rates or other exact figures; any time the VO says "this table" | `table` |
| **Illustrated scene** (OSA, light) | hook lines naming brands or objects (logo cards, vault, folder…); "X is made of …" (numbered parts); a place (map, location chain) | `scene` |
| **Process** | a 3–6 step loop or flow | `cycle` |
| **List** | key benefits / limitations / things to remember, revealed item by item | `points` |
| **Screen capture** (editor, magenta in the SB) | facts that live in an official source: fund portfolio/factsheet, product page, regulator FAQ, NAV page. Give the URL + what to highlight | `screen` |
| **Footage** | opening words to camera, reactions ("But not anymore"), rhetorical questions, analogies (duty-free zone), bridges, caveats without a new number, how-to asides, conclusion | `footage` |
| Badger / CTA / disclaimer | badger after the SOP; CTA at the end; disclaimer on any frame showing real securities or brands (`"disclaimer":true`) | mark only |

Judgement rules (from the GIFT City cut):
1. **Graphic vs screen capture:** if a reader could open one official page and see the fact, capture that page and highlight it. If the fact has to be **assembled** from several sources (7 funds side by side), build a table.
2. **Graphic vs footage:** a graphic must add a noun, a number, a structure or a term the viewer needs to hold. Delivery lines (emotion, emphasis, analogy, warning) stay on the face, even in the middle of a technical section.
3. **Number rule:** an exact figure that matters later (tax rates, minimums) goes on screen, usually inside a table that is re-highlighted later. A passing figure inside a definition stretch may stay on footage. Flag it as optional for the editor.
4. **Reuse beats new:** one table re-highlighted three times beats three tables. One SOP repeated per section beats new title cards.
5. **Hook = metaphor:** in the first ~20 s, turn concrete nouns into objects (brands → logo cards in a vault, "Indian MFs" → a folder with its parts). Don't use text slides in the hook.
6. **Reveal = one frame:** a table, list or cycle that builds up over the VO is **one** PNG in its final or first state, with "reveal as per VO" in the SB. Add `-a/-b` states only when the content changes, not just the highlight.
7. **Density:** about one *new content* graphic (scene, table, definition, cycle, list) per 35–40 s of VO (≈ `words / 90`), plus screen captures and repeats. The structural frames (hero ribbon, SOP, section ribbons) don't count toward this. In short scripts (< 600 words) the structural frames plus one graphic per jargon term or comparison can exceed the target, and that's fine. If you're well over in a long script, merge (fold a small definition into a table row) or reuse.
8. Script and SB disagree on a fact → follow the script and flag it. Copy numbers exactly ($, ₹, Indian grouping, %).

## Step 4: Storyboard (in chat)
Timestamps: use real timecodes if given. Otherwise estimate at **~140 spoken words/min** (skip headings and notes), prefixed `~`.
```
SB <> Doc: <title>
Look: hero keyword "GIFT City Funds" · anchor right · scenes light / agenda dark
~0:00 – Footage – hook to camera
~0:02 – OSA scene – "Investment" pill, vault, logo cards Apple/Nvidia/Microsoft pop per VO + disclaimer → 0.02
~0:24 – Roto big text – "GIFT City Funds" → 0.24
~0:27 – SOP – 3 questions → 0.27 · Badger
~0:44 – Repeat 0:27 – highlight Q1
~1:00 – Screen capture – giftcity.dspim.com/…factsheet.pdf – highlight top holdings
~1:38 – OST definition – Fund of Funds (FoF) → 1.38
...
Totals: N new graphics · M repeats · K screen captures · F footage beats
```
Keep each line to one beat: type, what is on screen, and the PNG id. Add a 3–5 word *why* only when the call is not obvious. If the user asked only for the storyboard, stop here.

## Step 5: Build all graphics in one go
Write `spec.json` with every beat, including `footage`/`screen`/`repeat` (they are skipped by the builder but keep the plan in one file). The format is in `references/spec_format.md`, and `scenes/gift_city_spec.json` is the full worked example.
```bash
python3 $K/scripts/build.py spec.json --out out
```
The build prints `WARN` lines (off-frame, overlap, covers the anchor's face, clipped text) and writes `out/_sheet_N.jpg`. Fix the spec and rerun only what broke: `--only 0.27,1.38`. Stop when there are no WARNs and the sheets look right.

Topic art you don't have (a new map, a product, a logo): use `"TODO:<what>"` as the asset. It renders a labelled placeholder, which you list as "assets for the designer". Brands without a logo file get text logo cards (`{"text":"Tencent","color":"#e4950b"}`). Never use emoji or clip-art.

## Step 6: Deliver
Zip `out/` (PNGs + overlays + `spec.json`) and send it with the storyboard. Close with the counts, the TODO assets, any flagged facts, and the reminder that `ribbon` frames need the editor to roto the anchor in front of the ribbon (`_overlay.png` has no anchor). Anyone can edit text in `spec.json` and rebuild.

Don'ts: no graphics over the anchor's face (keep left of x≈1320 on anchor frames); no redrawn website or PDF (use a screen capture); no new frame for a re-mention; no invented or re-rounded numbers; Inter only; **purple keyword pills** (#5b55e6 gradient, white text — never green pill backgrounds), blue table headers, orange/pink/green tiles, nothing off-palette.

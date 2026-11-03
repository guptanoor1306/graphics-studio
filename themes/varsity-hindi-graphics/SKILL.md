---
name: varsity-hindi-graphics
description: Turn a Varsity Hindi IP (Technical Analysis series, Hinglish script) video script into a storyboard and English-only 1920x1080 PNG graphics in the house style, deciding beat by beat between graphic, screen capture and footage.
---

# Varsity Hindi graphics: script → storyboard → PNGs

The VO is Hinglish; **everything on screen is English**. The output is (1) a storyboard in chat, then (2) one PNG per graphic beat, named by timestamp.

## Token budget (follow strictly)
- Read this file, `references/storyboard_rules.md` and `references/spec_format.md`. Open `examples/example_spec.json` only to copy a frame pattern. Open `references/video_breakdowns.md` (the full study of 5 episodes) only if a beat type is truly unfamiliar.
- Look at **one** image for style: `references/style_at_a_glance.jpg`.
- Write **all frames in one `spec.json`** and build with one command. Never hand-write HTML.
- QA with the printed `WARN` lines + one look at each `out/_sheet_N.jpg`. Open a full PNG only for a frame you are fixing; rebuild just that one with `--only`.

## Step 1: Setup
```bash
mkdir -p job && cd job
[ -d varsity-hindi-graphics ] || unzip -q /path/to/varsity-hindi-graphics.zip   # skip if installed as a skill
python3 -c "import playwright" 2>/dev/null || pip install playwright --break-system-packages -q; python3 -m playwright install chromium 2>/dev/null || true
```
`$K` below = the kit folder. If Chromium can't install, set `CHROMIUM_PATH`.

## Step 2: Storyboard (in chat)
Read the script once. Estimate timestamps at **~150 spoken words/min** for Hinglish (prefix `~`), or use the timecodes given. Apply `references/storyboard_rules.md`. One line per beat:
```
SB <> Ep 6: Support & Resistance
~0:00 – Footage – hook to camera
~0:08 – OST main – Title "What is / Support & / Resistance?" → 0.08
~0:31 – OSA side – htab "Support" + definition → 0.31
~1:05 – FSS – Kite "Reliance" daily, support line + 2 touches boxed → 1.05
~1:20 – continue 1.05 – leaders Entry / Stoploss → 1.05_b
~2:10 – Screen capture – Kite drawing tool
~6:40 – FSS – Key Takeaways (5) → 6.40
Totals: N graphics · M footage · K screen captures
```
Then list **every number and stock name the script states**, with the frame each one goes to. If the user only wants the storyboard, stop here.

## Step 3: Build
Write `spec.json` (see `references/spec_format.md`), then:
```bash
python3 $K/scripts/build.py spec.json --out out
```
It renders every frame, writes `out/_sheet_N.jpg` (6 per sheet) and `out/_text.txt` (all on-screen text per frame), and prints `WARN` lines for:
- colours outside the house palette, or green/red used anywhere except candle/bar bodies
- impossible OHLC, or a candle labelled Bullish/Bearish against its data
- reversal patterns not at a top/bottom, patterns outside their box, multi-candle boxes too short
- a side card for a candle that isn't boxed
- Hindi/Hinglish words on screen
- clipped or off-frame text, or content over the presenter in `side` mode

Fix the spec and rerun broken frames with `--only 1.05,2.33`. Stop when there are no WARNs and the sheets look right.

**Proofread `out/_text.txt` against the script:** every number matches, tickers are spelt right (listed names), header tabs name what's shown, no duplicate list numbers.

## Step 4: Deliver (always PNG **and** HTML, named and grouped)
Every frame in `spec.json` carries a `"section"` (the storyboard section it belongs to: "Intro", "Support", "Things to Remember"…) and optionally a `"name"`. Once the sheets are clean, run one full build with `--package`:
```bash
python3 $K/scripts/build.py spec.json --out out --package Ep06_Support-Resistance_graphics
```
This writes `out/Ep06_Support-Resistance_graphics.zip`:
```
Ep06_Support-Resistance_graphics/
  PNG/01_Intro/0.10_Support-Resistance.png        ← for the edit
  PNG/02_Support/0.28_Support.png, 0.28_b_Support.png …
  HTML/01_Intro/0.10_Support-Resistance.html      ← same frame, editable, same name and folder
  HTML/_assets/                                   fonts, CSS, images the pages use
  _review/  contact sheets + _text.txt            spec.json   README.txt
```
- Name the zip `Ep<NN>_<Title>_graphics`. Files are `<timestamp>_<what it shows>`; states keep their suffix (`_b`, `_c`). Sections are numbered in storyboard order.
- **Never send PNGs without the matching HTML, or a loose folder of files.** Send the one zip.
- Close with the frame count per section and any assumptions (e.g. chart data generated to match the described trend; real prices to be checked).

## Theme guard (read before writing the spec)
- Build **only** with this kit's items. Don't load or borrow from `varsity-graphics` (English) or `varsity-mf-graphics`: their tables, callouts, floors, props and colours are not in this IP (`references/storyboard_rules.md` §6).
- **Green and red appear only on candle/bar bodies, never on boxes**: pills, tags, zones, chips, rows and bars are white/neutral. Tables are white with black text and no coloured header. There is no bar-chart component; non-price numbers go in `callout`, `table`, `typo_card` or a `trade` overlay (§5).
- Avoid `html`. If you must use it, use palette hex values only; the build warns on anything else.

## House rules
- Charts are **mock Kite windows** generated from data (never screenshots). Real stocks by listed name at a realistic price level; generic examples "XYZ Stocks".
- Every new concept gets a header tab. Concept diagrams go over the side cam in a dark glass panel; charts, tables and takeaways are full-screen on the light sky.
- Keyword yellow on dark; green/red only on candle bodies; boxes white; amber = active item; Inter only; no glow, no emoji.
- Highlight on charts = a dashed box + a thin leader label. Entry/Stoploss = dashed leader lines.
- One graphic every 30–40 s of VO; "continue as per VO" is a state of the same frame, not a new design.

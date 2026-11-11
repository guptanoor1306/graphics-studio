---
name: varsity-hindi-fa-graphics
description: Turn an elements-heavy Varsity Hindi IP script (Fundamental Analysis, Futures and other story-driven modules, Hinglish) into a storyboard and English-only 1920x1080 graphics (PNG + HTML), deciding beat by beat between graphic, screen capture and footage.
---

# Varsity Hindi FA graphics: script → storyboard → PNG + HTML

For the **elements-heavy** modules of the Varsity Hindi IP: Fundamental Analysis (annual reports, balance sheet, ratios, valuation, investor mindset), **Futures** and other story-driven modules (farmer / mill owner / mandi / exchange stories). The visuals are characters, drawn scenes, 3D buildings, logos and glass cards. Chart-heavy Technical Analysis has its own skill, `varsity-hindi-graphics`; don't mix the two kits.

The VO is Hinglish; **everything on screen is English**. You deliver (1) a storyboard in chat, then (2) one zip with a `PNG/` and an `HTML/` folder.

## Read first (token budget)
1. This file, `references/storyboard_rules.md` (the graphic/footage decision) and `references/spec_format.md`.
2. Look at `references/style_at_a_glance.jpg`, `references/characters_poses.png` (the six characters, poses, expressions) and `references/drawn_props.png` once.
3. `references/assets.md` when choosing characters/props. `references/style_guide.md` if unsure about a look. `references/video_breakdowns.md` (4 episodes studied) only for an unfamiliar beat. `examples/example_spec.json` to copy a frame pattern.
Never hand-write full HTML pages: write one `spec.json` and build.

## Step 1: Setup
```bash
mkdir -p job && cd job
K=/path/to/varsity-hindi-fa-graphics            # the unzipped kit, or the installed skill folder
python3 -c "import playwright" 2>/dev/null || pip install playwright --break-system-packages -q
pip install pyspellchecker psd-tools --break-system-packages -q 2>/dev/null || true   # spelling check (optional)
python3 -m playwright install chromium 2>/dev/null || true   # skip if Chromium exists; else set CHROMIUM_PATH
```

## Step 2: Storyboard (in chat)
Read the script once. Timestamps: use the SB/script timecodes, else estimate at ~150 Hinglish words/min (prefix `~`). Apply `storyboard_rules.md` §2 to every beat. One line per beat:
```
SB <> Ep 6: Cash Flow Statement
~0:00 – Footage – hook to camera
~0:03 – Graphic – Module page, card 6 → 0.03
~0:20 – OSA – header stack "Cash Flow" / 3 pills: Operating, Investing, Financing → 0.20
~0:41 – FSS scene – "Operating Cash Flow": factory → customers pay (coinflow) → 0.41
~1:05 – OSA – definition card (SB text) → 1.05
~1:30 – Screen capture – Bajaj report pg 150, highlight net cash from operations
~2:10 – OSA – calc card: 5,213 + 1,020 − 640 = ₹5,593 Cr → 2.10
~6:40 – Graphic – Key Takeaways (6) → 6.40
Totals: N graphics (x FSS · y OSA) · M screen captures · K footage
Numbers: <every figure the script states → frame>   ·   SB vs script differences: <list or "none">
```
For each graphic give: header text, the scene (backdrop or light set; which cast characters with which pose/expression; props; logos), the on-screen copy (English), and states (`_b`, `_c`).
Start the storyboard with the **cast** (each person → c1–c6, kept for the whole video) and end it with **New assets needed** (3D objects the kit lacks, each with the prompt from `assets.md`; institution logos not in `assets/logos`). If the user only wants the storyboard, stop here and wait for approval.

## Step 3: Build
Write `spec.json` (cast first; `"series": "futures"` for Futures; all frames; see `spec_format.md` and `examples/futures_feedback_redo_spec.json`), then:
```bash
python3 $K/scripts/build.py spec.json --out out
```
This writes `out/PNG/*.png`, `out/HTML/*.html` (self-contained: fonts and images inlined), `out/_sheet_N.jpg` (6 frames per sheet) and `out/_text.txt`, and prints `WARN` lines for:
- text off-frame, overflowing its pill/card, or crossing the presenter in `osa` mode
- Hinglish words on screen; `₹` before a percentage; "Price to Equity"
- green/coral on boxes or highlights; chart colours outside the palette; off-palette `html`
- characters marked for recolouring; missing assets and logos
- the same character twice in a frame, two people with the same pose + expression, characters in OSA frames
- flat and 3D buildings mixed, 3D buildings on drawn backdrops, one asset used for different things (`"as"`)
- bubble text overflowing; spelling (confusables such as "Floor Mill", unknown words)
Fix and rerun only the broken frames: `--only 0.41,2.10`. Look at every `_sheet_N.jpg` once. Check that people stand on the floor, nothing important hides behind a prop, every scene has distinct characters, and headers name what is shown.

**Proofread `out/_text.txt` against the script**: every number matches the script, spellings, no duplicate list numbers, English only.

## Step 4: Deliver
```bash
python3 $K/scripts/build.py spec.json --out out --package Ep06_Cash-Flow_graphics
```
`out/Ep06_Cash-Flow_graphics.zip` contains exactly two folders with the files directly inside (no sub-folders):
```
Ep06_Cash-Flow_graphics/PNG/0.20_Cash-Flow-Types.png  …
Ep06_Cash-Flow_graphics/HTML/0.20_Cash-Flow-Types.html …
```
File names are `<timestamp>_<what it shows>`; states keep `_b`, `_c`. OSA frames come as a transparent overlay (`0.37_X.png`, for the editor, works on any presenter) plus `0.37_X_preview.png` on a presenter plate. Always send PNG **and** HTML together, as that one zip. Close with the frame count, the screen captures the editor must record (page numbers / URLs), and any assumptions (numbers taken from script vs SB, illustrative chart shapes).

## Hard rules
- **English only on screen.** Script English terms stay; everything else is a short English rewrite.
- **Graphic vs footage** per `storyboard_rules.md` §2. Real documents and websites are screen captures; scenes are for analogies, people and situations; words-only content (definition, formula, calculation, list) is OSA beside the presenter.
- **Numbers from the script**, never from SB reference images; compute derived values; flag SB/script mismatches.
- **People = the six team characters** via `char` (cast first). Heads/faces/bodies never change; pick a pose and expression that fit the action; several distinct characters per scene; no characters beside the presenter unless asked. Everything stands on the floor.
- **One style family per frame**: drawn scenes (backdrop + drawn props + characters) for stories; glossy 3D buildings for institutions/companies. Never reuse one asset for different things; named organisations show their logo.
- **OSA content only through the `osa` block** (fixed positions, an icon/number on every list item). A person's facts go in their thought/speech bubble.
- **Green and red/coral only on data marks and BUY/SELL buttons.** Pills, cards, headers, highlight blocks: white, blue, yellow.
- **This kit only.** No Varsity English or Technical Analysis components, no restyling SB references from other IPs as-is.

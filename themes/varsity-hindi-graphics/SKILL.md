---
name: varsity-hindi-charts
description: Varsity Hindi Charts — turn a Varsity Hindi IP (Technical Analysis series, Hinglish script) video script into a storyboard and English-only 1920x1080 PNG graphics in the house style, deciding beat by beat between graphic, screen capture and footage.
---

# Varsity Hindi Charts: script → storyboard → PNGs

The VO is Hinglish; **everything on screen is English**. The output is (1) a storyboard in chat, then (2) one PNG per graphic beat, named by timestamp.

## What's new in v4 (team review of Futures Ep 1, Nov 2026)
Scene backdrops (`backdrop`: wheat_field, flour_mill/atta_chakki, grain_market/mandi), thought bubbles that hold a prop (`thought`), a clean callout card (`tag`; the old `callout` now renders the same way), dashed arrow labels (`pointer`), centring by `cx`, drink props (tea_glass, mug, shaker), `arrow` dir `same`, and checks for: cards not level, cards not centred over their character, a name shown twice, numbers on screen that the storyboard line doesn't have, and storyboard beats that need no graphic. Read **Following a team storyboard** below before building from an SB.

## What's new in v2 (Nov 2026)
`character` item with a spec `cast` using the team's six Varsity characters as drawn, `prop` library for story scenes, automatic floor with snapping, FSS header pinned top-centre, content-sized tables, equal-size cards, and build checks for each. Examples: the `(v2 people/props example)` frames in `examples/example_spec.json`.

## Token budget (follow strictly)
- Read this file, `references/storyboard_rules.md` and `references/spec_format.md`. Open `examples/example_spec.json` only to copy a frame pattern. Open `references/video_breakdowns.md` (the full study of 5 episodes) only if a beat type is truly unfamiliar.
- Look at **one** image for style: `references/style_at_a_glance.jpg`.
- Write **all frames in one `spec.json`** and build with one command. Never hand-write HTML.
- When the user gives a team storyboard, read **Following a team storyboard (v4)** first and put each SB line in the frame's `"sb"` field.
- Write `"cast"` first when the script has people (team characters 1-6; see *People, props and floor*).
- QA with the printed `WARN` lines + one look at each `out/_sheet_N.jpg`. Open a full PNG only for a frame you are fixing; rebuild just that one with `--only`.

## Step 1: Setup
```bash
mkdir -p job && cd job
[ -d varsity-hindi-graphics ] || unzip -q /path/to/varsity-hindi-graphics-v4.zip   # Graphics Studio: themes/varsity-hindi-graphics/ (from repo root zip)
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

## People, props and floor (v2, from team feedback, Nov 2026)
- **Characters: only the team's six Varsity characters, exactly as drawn** (`assets/chars/Character_1..6.png`, see `references/characters.jpg`). Never redraw them or change hair, face, colour, outfit or pose; only position (`x`), height (`h`) and left/right mirroring (`facing`) may change.
  | # | Look | Typical role |
  |---|---|---|
  | 1 | yellow, curly hair, cheerful | main example person (farmer, investor, Rajesh) |
  | 2 | blue, short curly hair, sceptical | second person, seller, sceptic |
  | 3 | coral, woman, bindi, hands on hips | woman / customer / family member |
  | 4 | yellow, spiky hair, glasses | young trader, seller |
  | 5 | blue, round, hat, moustache | business owner, buyer, older person (mill owner) |
  | 6 | yellow, quiff, arms out | the Varsity explainer (definitions, module cards) |
- **Cast first.** List every person in the script under `"cast"` in spec.json with a character number and name, e.g. `"rajesh": {"name": "Rajesh", "char": 1}`. A person keeps that character for the whole video, and two people on screen together never share a character (the build warns).
- **Draw people with the `character` item** (`who`, `facing`, `h`, `x`). Poses are fixed by the artwork, so show actions with props and placement: a handshake = the two characters facing each other with the `handshake` prop between them; giving = the prop (sack, money bag) beside the giver.
- **Names go in the character's name pill** (automatic, from the cast). Never add a second header tab for a person's name.
- If a storyboard needs a pose or person the six characters can't show, use the closest character as is and list it under **"Art needed"**.
- **Build the scene the storyboard describes with `prop` items.** Map the storyboard's words to props: farmer/field/crop → `wheat_field`; grain bag/sack/price tag → `wheat_sack` (+ `price`); atta chakki/mill → `flour_mill`; market/mandi/shop → `market_stall` (+ `label`, `price`); bank/exchange/NSE/BSE/SEBI building → `building` (+ `label`); weighing scale/balance → `scale` (`left`, `right`, `tilt`); locked price → `lock`; deal/agreement → `handshake` or two characters in `shake`; money → `money_bag` / `coins`; months/expiry/date → `calendar`; contract/notice/letter → `document`; app/SMS → `phone`; milk/dairy → `milk_can`; tea/coffee → `cup`; house, factory, arrow. Every storyboard element that has no prop is listed under **"Art needed"** in the delivery note; never leave it out silently.
- **Everything stands on the floor.** Characters and grounded props have no `y`: the build snaps their feet to the floor line and draws the tiled floor (full width on FSS; a soft floor patch under people and props on side and main cam). Use `"float": true` only for things held or hanging (lock, handshake, document, scale shown as an icon). The build warns when something floats.
- **FSS header:** one header tab per frame, centred at the top (the build pins it there; never pin it top-left over the Varsity logo). The header must name what the frame shows; if the storyboard says "Rajesh, a farmer in a wheat field", the frame shows Rajesh *and* the field.
- **Story scenes on FSS:** header tab top centre, characters on the floor in the lower half, props beside them, numbers in a `callout` or price tag, thought bubbles above the character's head. Split screens use one header per half (`small` tabs) and a thin divider.

## Following a team storyboard (v4)
When the user gives a storyboard (SB) made by the team, it overrides your own beat choices. 57% of frames passed review first time on Ep 1; these rules cover the rest:
1. **No graphic** when the SB line says top cam, on the board, footage, or "highlight the part from <link>" (that is a screen capture). List these beats in the storyboard table as "Top cam" / "Screen capture" and build nothing.
2. **Show only what the SB lists.** Call-outs = exactly the words given (e.g. Tea, Coffee, Protein shake), each with its own icon. No extra numbers, labels or props (no "5,000 kg, 3 months" if the SB doesn't ask). No device the SB doesn't name (no scale unless asked). Put the SB line in the frame's `"sb"` field: the build warns about numbers on screen that aren't in it, and about top-cam/screen-capture beats.
3. **A name appears once**: in the header or in a pill, never both (build warns).
4. **Settings are backdrops.** "Standing on a wheat field", "atta chakki nearby", "Indian marketplace / mandi" = a full `backdrop` (first item in the frame), with the character standing in it. Split screens keep each half's setting (`clip`).
5. **Thought bubbles hold what the SB puts in them**: `thought` with a `prop` (e.g. wheat sack with the price tag), and a price change = two states of the same frame (`3.56` ₹25 → `3.56_b` ₹20). Mirror bubbles (`flip`) so the trail points to the thinker; two thinkers' bubbles match in size and height.
6. **Alignment** (8 of 19 Ep 1 changes): info belongs to a character → centre it over that character (`cx` = the character's `cx`) or over the pair; cards on both sides of the speaker share one `y`; captions sit on the element they label. Use `tag`, not hand-made pills. The build warns when cards aren't level or centred.
7. **Over-the-anchor (main cam) characters** stand left and right of the speaker, inside x < 560 and x > 1360, h ≈ 440, and follow the speaker's hand gestures: write "follow hand gesture" in the frame notes.
8. **Reference images**: when the SB gives a reference infographic, rebuild its structure with house items and the team characters (e.g. market move chips → locked contract price → result card), never as a table.
9. **"Split the screen in N parts"** = N equal panels with thin dividers, same layout in each.

## Tables and cards (v2)
- Tables size to their content and centre under the header: give no `x`/`w` unless the layout really needs a fixed position. The build warns when a table has more than 30% empty column space.
- Cards in a row are the same width and height, never narrower than their longest word; 4–5 cards drop to 30/27px automatically. The build warns when card text touches the box edge.

## House rules
- Charts are **mock Kite windows** generated from data (never screenshots). Real stocks by listed name at a realistic price level; generic examples "XYZ Stocks".
- Every new concept gets a header tab. Concept diagrams go over the side cam in a dark glass panel; charts, tables and takeaways are full-screen on the light sky.
- Keyword yellow on dark; green/red only on candle bodies; boxes white; amber = active item; Inter only; no glow, no emoji.
- Highlight on charts = a dashed box + a thin leader label. Entry/Stoploss = dashed leader lines.
- One graphic every 30–40 s of VO; "continue as per VO" is a state of the same frame, not a new design.

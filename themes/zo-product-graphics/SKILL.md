---
name: zo-product-graphics
description: Turn a Zerodha Online (Product IP) video script into a storyboard and the full-screen graphics as 1920x1080 PNGs in the channel's house style, deciding beat by beat between a designed full-screen graphic, an anchor beat for the editor, or a screen capture.
---

# Zerodha Online · Product IP — script → storyboard → full-screen graphics

Learned from three shipped videos: **Devolvement** (MCX options → futures), **Does a lower share price mean a stock is cheaper?** (concept), **SIFs on Coin** (product + concept) — and refined on **78 newer frames** (Family Portfolio, Life Cycle Fund, MTF, Charges, Physical delivery, Minor account, Market protection; 43 PSDs in `references/psd_breakdown.md`). The newer look (**v2**, below) is the current house style.

## The look (v2 — current)
**Full-screen (FSS):** white background with a light 52px grid. Decor sits around the edges and never touches text (the renderer draws it; move pieces with frame `decor:{doodleAt, tri1, tri2, starAt, dash1, dash2}` if one lands on content, `decor:false` to drop it):
- a black hand-drawn loop doodle (often just left of the heading/hero) · two solid rounded triangles (purple / green / orange / yellow) · a grey 4-point star · an orange dash on the left and a short green dash on the right.
- Optional: a soft grey blob behind a hero (`bigphrase` has one; frame `blob:{x,y,w,h}` elsewhere) or a pale yellow glow circle behind title text (`qtitle` has one; frame `glow:{x,y,d}`).

**Type:** Inter, weights 400/500/600/700 only. Heading 72px semibold, dark ink, **≤6 words, ONE coloured keyword or number** (`++blue++` or `{o:orange}`). Optional yellow underline bar under short centred headings only (`underline:true`). Labels ≥34px, nothing under 26px.

**Colours:** blue #387FD1 · orange #F07339 · yellow #FEC02D · green #4DAB4D · purple #A77BF3 · table highlight #FFD064 · loss rows #FDE6E6 with #D23C3C text · interest/cost notes #FDE3D6 with #C4521F text. Pick 2–3 colours per frame. **Same thing = same colour across a video** (e.g. "you pay" yellow, "Zerodha funds" blue, interest blue, brokerage yellow).

**Over the presenter:** no panels and no lower-third bars. White text with a soft shadow, key words **yellow**, placed in the plate's text zone, never over the face. Formats: big title + thin underline (`ov_title`), white lead + yellow box (`ybox`), speech bubble (`bubble`), caption line across the bottom (`caption`), pill rail (`pill_rail`), title + relation (`relation`), plus the older `lower` / `punch` / `bignum` / `side_list` / `scroll_list`. Decor: one orange triangle, one purple triangle and a white doodle (automatic).

**Icons:** simple inline line art via `"svg:<name>"` anywhere an image goes — wallet, moneybag, calendar, coins, parcel, tag, gift, scale, growth, warning, down, up, tick, cross, phone, doc, bank, clock, cart, shield, rupee, man, woman, child, elder. No emoji, no real logos (Zerodha/Kite/Coin names in text are fine). Illustrations: `assets/INDEX.md` (v2 PSD cut-outs under `illus/psd/…`), else `"TODO:<what>"` and the app generates one in the house style.

**Scope:** render **FSS** (full-screen slides) and **anchor graphics** (OSA/OST/TOS — lower thirds, punchlines, side lists, TOS title) as PNGs. Screen capture and footage are storyboard-only (no PNG).

Output: (1) a short storyboard in chat, (2) one PNG per FSS frame, (3) a zip of the PNGs + `spec.json`.

## Cost rules (follow strictly)
- Read only this file and `references/spec_format.md`. Copy patterns from `scenes/example_spec.json`. Don't open `references/deep/*`, `templates/*` or `scripts/*` unless something breaks.
- Find illustrations with `grep -i <word> assets/INDEX.md` — never read the whole index, never open illustration images.
- **Fewest frames that carry the script.** One FSS frame per idea; a build state (`6a`, `6b`) only when the script adds a *new fact to the same picture*, max 3 states per scene. Never make a state just to highlight an item the voice-over reads — that's the editor's animation.
- Write all frames in **one** `spec.json`, build with **one** command, view each `_sheet_N.jpg` **once**, fix only what's wrong with `--only <ids>`. No full-size PNG views unless fixing that frame.
- Keep chat replies short: storyboard, frame count, files.
- Short script ≠ many frames: apply the density ratio below to the excerpt's word count and round **down** (a 230-word product excerpt → 2 FSS; 0 is a valid answer).

## Step 1 — Setup
```bash
mkdir -p job && cd job
[ -d zo-product-graphics ] || unzip -q /path/to/zo-product-graphics.zip     # skip if installed as a skill
python3 -c "import playwright" 2>/dev/null || pip install playwright --break-system-packages -q; python3 -m playwright install chromium 2>/dev/null || true
K=zo-product-graphics      # or the installed skill folder
```
If Chromium can't be installed, set `CHROMIUM_PATH`. No code execution → deliver storyboard + `spec.json` only and say so.

## Step 1a — Reading a storyboard (v2 rules)
- **Numbering:** if the SB has frame numbers, keep them as frame ids (`02`, `04`…). If not, number frames in script order. A skipped beat keeps its number as a gap; say which and why in the storyboard.
- **Reference images:** rebuild each in the house style with the script's exact numbers and generic names (XYZ Ltd). Never copy a screenshot.
- **Screen captures:** skip (website pages, calculators, "show the charges page", Kite/Console screens, numbered app procedures). Log each as `Screen capture` with a reason.
- **Text-on-screen beats without a ref:** make an over-presenter frame. A row of reference frames sharing a pattern ("1. Do I understand…", "2. How long…") gets **one template** reused for all of them (`qtitle` with a different `n`).
- **Build-up beats** (a list highlighting one item at a time): ONE frame in its final state — the active item full size, the others faded (`buildlist`, `pills`, `pill_rail` with `active`). The editor animates it.
- **Arithmetic:** check every number in the script (totals, percentages, interest maths) before drawing. Write numbers exactly as given, Indian grouping (₹1,00,000; ₹1.6 lakh). Pie slices must sum to 100.
- **Copy discipline:** headings ≤6 words. You may add a short clarifying subline (e.g. "Buy and sell ₹1 lakh worth of shares"), but name every added or reworded line in the storyboard notes so the team can delete it.

## Step 1b — If a team storyboard (SB doc) is attached, it is the source of truth
Learned from the SB for *Why do stock prices move every second* (V4) and the PSDs built from it:
- The SB numbers its graphics with codes (`1 - FSS`, `2 - OST`, `5 - OST & Screencapture`). **Render only its FSS items, keep its numbers as ids.** OST/OSA items → anchor notes with their exact text.
- Highlighted lines are the **design brief**; the plain paragraph is the voice-over. Common briefs and what the designer did:
  - **"Ref Img" / hand sketch** → content and layout only. Rebuild as clean vector UI in house style (`kite_*` components), never paste the screenshot. Use generic tickers (XYZ; ABC, PQR in lists) unless the script names the company, and **replace the reference's numbers with the script's example numbers**.
  - **"Repeat" / "Continue the animation"** → no new frame; storyboard it as `reuse N`. Only add a state if the frame shows numbers that change.
  - **"Highlight as per VO"** → one frame; the editor animates the highlight.
  - **"Header - X"** → heading X. **"Show something similar"** → free to redesign with the closest component.
  - Two SB items that one picture can answer may be merged (V4 merged the order-matching table and the order-book screenshot into one Kite market-depth frame with "No trade / Trade executed" tags).
  - OST formats seen: *Pop-up callout* (stacked lines, one highlighted), *Text pop-ups* (header + bullets), *Definition box* ("Order book: a list of…"), a lower-third sentence. Copy them into the anchor notes as written.
- If the SB and script disagree on a fact, follow the script and flag it.

## Step 2 — Each beat gets ONE of four labels
Split the script into beats (1–3 sentences = one idea).

### FSS — designed full-screen graphic (the only thing you render)
Use FSS only when the visual **needs the whole frame or is a thing to look at**:
| Beat | FSS component | Seen in |
|---|---|---|
| Surprising account state / positions | `positions` (Kite-like cards + status chips) | V1 #2, #7 |
| Directional rule (above/below a price) | `chart` with strike, zone, arrow | V1 #6 |
| Worked example with the script's numbers | `chart` + `positions`, or `compare` with equations under objects | V1 #7, V2 6a–6c |
| Two things side by side (prices, companies, analogies) | `compare` (objects, values, captions) | V2 1B, 2a, 10A, 16a |
| Size comparison | `bars` drawn to scale | V2 10b |
| A named formula | `formula` (definition line under it) | V2 8 |
| Classification into 2 types | `hub2` (overview, then each type) | V1 #13, V3 8a |
| Composition (what X can hold / is made of) | `hub_fan` or `cards` | V3 4a, V2 17 |
| Closing list of factors | `hub_fan` style `mind` | V2 21 |
| Two options with rules | `cards` with bullets | V3 #10 |
| Two positions interacting / netting off | `row` of objects → result `cards` | V1 #10 |
| Product communication / checks / instructions | `phone`, `status`, form `cards` | V1 #17, #18, #20 |
| Which days / who you trade with | `week` + `exchange` | V3 8b–8c |
| A number changing over a section | `objstat` on ONE object (vault), `calendar` for deadlines | V3 13a–14 |
| An everyday analogy the script spells out (price tags, pizza, puzzle, seesaw) | illustration via `compare` / `img` | V2 2a, 12A, 16a |
| A standalone broker rule that matters | `note` (Important note) | V1 #14, V3 #11 |
| Question list read aloud | `notepad` | V2 18 |
| A live price ticking / "watch any stock" | `kite_watchlist` (phone, one row popped out) | V4 #1, #9 |
| Order book / bids vs offers / why a trade happens | `kite_depth` (+ status tags per row) | V4 #4 |
| Buyers vs sellers meeting on a price (auction) | `auction` (matched or not) | V4 #3 |
| Every tick is a trade / price history | `kite_chart` with tick dots | V4 #10 |
| **v2 recipes** (Family Portfolio · Life Cycle Fund · MTF · Charges) | | |
| Title / acronym card ("MTF stands for…") | `acronym` (kicker + yellow ink-bordered box, initials bold) | MTF |
| Question title ("1. Do I understand…") | `qtitle` (240px number, key phrase blue, pale glow, green dash) — one template for the whole series | MTF |
| Numbered 2–4 steps | `steps` (blue / orange / yellow stickers, straight) | 3 steps |
| Slab / schedule table | `heading` + `slab_table` (window dots, `hl` row yellow, `loss` rows red, `subs` under headers; ≤5 cols × 6 rows) | Exit load, Life Cycle Fund |
| Split / funding bar ("you pay / Zerodha funds") | `split_bar` (stock row + tag → two-colour bar → icons + labels → bracket + total; optional interest tag) | MTF |
| Cost comparison over time | `cost_compare` (one row per option, stacked bars scaled to the max, total at the end, "Lower" tag, legend) | MTF, Charges |
| Up vs down outcome | `updown` (green bars rising left, orange bars hanging right) | MTF |
| One % stat | `donut` (+ caption) | Family portfolio |
| Allocation % | `heading` (underline) + `pie` (must sum to 100) | Asset allocation |
| One number to remember | `fbox` (blue hero card, "before" values faded with an orange strike) or `bigphrase` (huge blue number over a blob) | 30/500, 10 Family members |
| People / holders | `people` (line-face cards: `svg:man/woman/child/elder`) | Minor account |
| Category / list of items | `catgrid` (2×2 white cards, coloured bottom shadow, icon circle) | Charges |
| Checklist of charges / documents | `checklist` (blue tick rows in a window card, illustration left) | Minor account |
| Decision options | `options` (source card → arrow → 2×2 numbered boxes) | MTF |
| Build list ("Will you…") | `buildlist` (active item big with blue chevron, others faded) | MTF |
| Recap ("five things") | `recap` (numbered badges in the 5 house colours) | MTF |
| Options / categories as pills | `pills` (active colour, next yellow, rest faded) | Fundamentals / GTT |
| Things over time | `timeline` (axis + folders + captions) | Life Cycle Fund |
| Big phrase | `bigphrase` | Family members |

### OSA / OST / TOS — anchor graphics (render with plate)
Over-the-presenter moments → spec frame with `mode: "osa" | "ost" | "tos"` and anchor items (`lower`, `punch`, `bignum`, `scroll_list`, …). TOS once per video max: `title` behind the cut-out.
Storyboard: `~0:08 – OST – pop-up callout … → 2`. Use the video's anchor **plate** in `look.plate`.

### Screen capture — not designed, not rendered
- a real Zerodha/Kite/Coin screen or tool the viewer can open (option chain, Info widget, margin calculator, Coin dashboard)
- **every numbered app procedure** ("1. Search… 2. Enter amount…")

### Footage — nothing on screen
Section questions ("What is a GTT?" — the editor may add a title card), motivation and transition lines, one-line negatives, restatements of what's already shown, caveats right after a shown point, the CTA.

### Density (FSS frames incl. states)
- Product scripts: about **1 FSS per 90–180 spoken words** (V1: 9 FSS in ~1,100 words; V3: 15 in ~1,000; V4: 4 new FSS + 2 repeats in ~900).
- Concept scripts with analogies: up to **1 per 40–60 words** (V2: 26 in ~1,050).
- The table says *how* to draw a beat if it earns an FSS; density decides *whether*. Over target? Drop states first, then merge two FSS about the same subject into one, then move word-only beats to Anchor notes. Priority to keep: worked examples with numbers > mechanisms/flows > comparisons > classifications.
- The script's `[SHOW: …]` cues are mandatory FSS.

### Continuity
One subject = one scene: same objects, same colours (A blue / B green; call green / put orange), only the facts change. Choose the 1–3 hero objects before writing the spec.

## Step 3 — Storyboard (in chat, one line per beat)
Timecodes at ~150 spoken words/min (prefix `~`), or real ones if given.
```
SB: <title>
~0:00 – Footage – hook to camera
~0:08 – Anchor – lower third – "Advanced trading strategies"
~0:12 – FSS – two strategy icons + "Limited options" pill → 2
~0:40 – Screen capture – Coin app: lumpsum order steps 1–5
~1:10 – FSS – reuse 1 (Repeat, no new frame)
Totals: N FSS frames to render · M anchor notes · K screen captures
```
If the user asked only for the storyboard, stop here.

## Step 4 — Build (FSS + anchor, one go)
Write `spec.json` with **FSS and anchor frames** (format: `references/spec_format.md`), then:
```bash
python3 $K/scripts/build.py spec.json --out out
```
It renders only `mode:"fss"` frames (any other mode is skipped), auto-fits content to the frame (headings stay 72px), prints `WARN` lines and writes `out/_sheet_N.jpg`. View each sheet once; fix with `--only 7a,13`. Zero WARNs is necessary, not sufficient.

### Layout rules that caught real bugs (v2)
- Labels in fixed-width boxes stay on one line; if a label is long, shorten it rather than shrinking the box text below 34px.
- Side-by-side labels under bars collide: keep ≤4 bars per panel.
- A chart's top axis label collides with the chart title: put the title ≥40px above the plot.
- Decor must not touch the heading, cards or tables: if it does, move the piece with `decor:{…}`.
- Big numbers inside donuts/cards: size them to fit (`pct_size`).

### Review checklist (on the sheet)
1. Every heading 72px, ≤6 words — or no heading where the picture says it.
2. Text ≥36px for labels, nothing under 26px; content fills the frame.
3. Same object + colour for the same thing all video.
4. Numbers exactly as the script; Indian grouping (₹12,00,000); correct × = ≠ →; no "~"; pair labels differ; spelled right.
5. Real companies as what they make (tyre, refinery), never logos; no emoji. Nothing suitable in `assets/INDEX.md` → use its fallback and list under "Illustrations to request".

## Step 5 — Deliver
Zip `out/*.png` + `spec.json` and send it. Close with: FSS frame count, the anchor-note list and screen-capture list for the editor (already in the storyboard — don't repeat), and any illustrations to request.

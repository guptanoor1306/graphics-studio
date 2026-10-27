---
name: "zero1-reel-graphics"
description: "Use when given a Zero1 reel script or storyboard PDF to plan and generate the reel's static graphics from the team moodboard, in one theme per reel."
---

# Zero1 Reel Graphics (storyboard → graphics)

Turns a reel storyboard PDF (or a plain script) into a full set of static 1080×1920 graphics, built only from the team moodboard. Graphics only; animation is a later phase.

## Sources of truth (read before every job)
1. **Project docs** (Instagram Reels project). Read with `project_read`:
   - `claude/Reel_Graphics_Rules.md`: the team's rules (these override everything else)
   - `claude/Moodboard_Inventory.md`: every template with its ID, ⭐ status and theme
   - `claude/Zero1_Reel_Graphics_Template_Spec.md`: formats, components, measurements, colours
2. **Moodboard** (FigJam): https://www.figma.com/board/CK597ULHYwFUUsY2UhytNZ/Moodboard
   - Read it with the Figma connector: `get_figjam` (node 0:1) for the structure, `get_screenshot` per template node with `enableBase64Response: true`. figma.com downloads are blocked in the workspace, so the base64 copy saved under tool-results is the usable file.
   - The Starter plan has a low Figma call limit. Only render the templates you need for this reel. If the limit is hit, tell the user and ask for 2x PNG exports of the needed sections.
   - Templates are flattened images with no live text layers, so measure them from the renders.
3. **Fonts** (see the Fonts section below).

## Hard rules (from the team)
1. **The moodboard is the source.** Copy layouts, colours, spacing and styles exactly. Never invent templates.
2. **Unused templates are allowed.** Pick whichever moodboard template fits the script best, even if no past reel has used it.
3. **Explain the pick first.** Before generating anything, tell the user which theme and templates you picked and why, then wait for a go-ahead.
4. **One theme per reel.** A "style" = the visual theme (e.g. the green grid). Every graphic, start to end, is in the chosen theme. If a needed graphic doesn't exist in that theme, take it from its own moodboard section (e.g. Header Styles) and **restyle it into the theme**. Keep its structure and purpose; apply the theme's colours, fonts, grid, spacing and shapes.
5. **Native vs Converted.** Before generating, list every graphic as Native or Converted, with the source template ID of each converted one.
6. **When unsure, ask.** Don't guess copy, numbers, fonts or a template. Never invent figures: cite every data graphic's source on the graphic.
7. **Theme 2 (Light Pop) is excluded.** It's the right-hand "Theme 2" column on the board (grey/white with green, pink and purple accents). Never pick it, convert from it, measure from it, or offer it as an option.
8. **Font consistency across the whole reel.** Every graphic uses the same font system: the same headline family, the same body family and the same emphasis style (e.g. italic of the headline serif). Never let one graphic use a different headline or heading font than the others. A table title, CTA line or stat label follows the same roles as every other graphic.
9. **Centred and safe on every graphic** (see Safe zone). Content stays inside the safe zone **and stays centred on the canvas**. Never push a layout left to fit the zone.
10. **Every graphic is its own deliverable.** For each graphic, deliver a JPG + a self-contained HTML (+ a transparent PNG if it overlays the presenter), sent separately (see Deliver).
11. **Real objects, not vector drawings.** When a template uses a photographic object (calculator, gold bars, coins, phone, house…), use a real photo in the same style. Source order: (1) the team's original asset file; (2) a cut-out from the moodboard reference itself (keep its soft shadow, edit only its screen/label text); (3) ask the team. A vector stand-in is allowed only as a clearly labelled placeholder that's called out in the delivery.

12. **Theme choice = best fit only.** No rotation rule: repeating a theme across reels is fine if it fits best.
13. **Storyboard assets are the data source.** Numbers, labels, table structure and chart shapes come from the storyboard's ASSETS references, exactly as shown (e.g. 18.80 not 18.8, 9.93 not 9.9; keep extra rows like Sharpe Ratio). Charts trace the reference curve's shape, not a generic wave. Storyboard instructions override the asset only where they say so (e.g. "make returns 16.7%", "remove real fund names"). The PDF only holds small previews, so ask the team for full-size asset images before building data graphics.
14. **Sequence = storyboard row order**, not timecode order. Editors move segments around, so a row's `{m:ss}` refers to the source footage, not the final cut. Number the files 01, 02… in row order.
15. **Data source = the team's data sheet when one is provided** (e.g. the Zero1 calculator Excel), with exact figures as in the sheet. Without a sheet, use storyboard assets and then the VO. Flag any VO/sheet mismatch to the team, but the sheet wins on screen.
16. **Keep it simple, but keep tables.** One idea per frame. Comparisons use a simple Table Style 1 table (2 value columns, max 3 rows, only the rows the VO talks about), so viewers can follow the VO. At most one takeaway line under the table.
17. **Reference images from the team are assets, not themes.** When the team shares an outside design (e.g. a car carousel), take only the asset it was shared for (e.g. the car photos). Layout and style still come from a moodboard theme. Use product/hero photos once (usually the hook), not in every frame. Data frames stay clean: headline + table/number only.

## Fonts
- **Primary fonts (use these first):** Stack Sans Text, Manrope, Behind The Nineties, Gilmour.
- Wider board list (use only if a template clearly needs it): Jost, Google Sans, Aktiv Grotesque, Hippo, Clash Display, Instrument Serif, Thunder LC, Old Standard TT. Check licences before use.
- Files: the team's Drive link. If a font file isn't in the workspace, ask for it. Manrope and Stack Sans Text install from npm (`@fontsource/manrope`, `@fontsource/stack-sans-text`). Behind The Nineties and Gilmour are NOT on npm, so ask the user for the files.
- Never substitute a font silently. If you must use a stand-in, use it for that role in **every** graphic (still one consistent system), and name the stand-in in the delivery.
- Define the font system once per reel as CSS roles and use only those roles, for example:
  - `--headline`: display headline + italic emphasis (serif themes: Behind The Nineties)
  - `--body`: body, labels, table cells, CTA, source lines (Manrope or Stack Sans Text)
  Confirm the role of each primary font with the user once, then record it in `Reel_Graphics_Rules.md`.

## Safe zone (1080×1920): mandatory, centred
The raw IG safe zone is asymmetric: x 60–960 and y 240–1540, with the right edge at x 880 below y 720 (the action-button column). Off-limits: top 240, bottom 380, left 60, right 120. Fitting content to that zone alone pushes layouts left, which looks off. So **mirror the larger margin on both sides and centre everything on x = 540**:
- **Above y 720:** content within **x 120–960**, max width **840**.
- **From y 720 down:** content within **x 200–880**, max width **680**.
- **Vertically:** y 240–1540.
- Every text block, card, table, chart, icon row and thumbnail is horizontally centred on the canvas (`left:50%; transform:translateX(-50%)`, or `left:(1080-w)/2`). Left-aligned text is fine *inside* a centred block (e.g. table cells, list rows); the block itself is centred.
- If something is too wide for the band it sits in (e.g. a table below y 720), shrink type/columns, re-flow lines, or move it up into the wider top band. Never offset it left.
- Background fills, boards, panels and gradients may extend under the off-limits areas; content may not.
- **Automatic check before delivery:** render a background-only version of each page (hide everything except `.fill` / `.panel` and the body background), diff it with the real render, and count content pixels inside the off-limits mask `(0,0,1080,240) (0,1540,1080,1920) (0,240,120,720) (960,240,1080,720) (0,720,200,1540) (880,720,1080,1540)`. The count must be 0. Also report the content's horizontal centre offset `((min_x+max_x)/2 − 540)`, which must be within ±12 px. Add a review row to the contact sheet with the off-limits areas tinted red.

## Themes (visual languages)
The user has not yet confirmed where each theme starts and ends. Check `Reel_Graphics_Rules.md` / `Moodboard_Inventory.md` for the confirmed version. Working draft (all from the board's Theme 1 area):
| ID | Theme | Look | Moodboard sources |
|---|---|---|---|
| A | Cream Editorial | cream #FCF8EE bg, black type, serif headline + clean sans body, orange accent #F85000 | GS1, GS3, Table 1–5 panels, Steps 1–3 |
| B | Green Grid | green grid board #207C50, white grid lines, cream paper card, cut-out paper labels, gold/calculator props | GS2, Data 1 |
| C | Dark Studio | dark presenter bg, white/red type over presenter | Header 1–8, Ranking 1–2, OSA 1–2, News 1 |
| D | Burnt Orange | orange bg, cream serif/sans | Header 9–11, GS4 "GOLD" |
| E | Cinematic Film | film texture, photo scenes, oversized numbers | GS5, Data 2, OSA 3, GS6 TTP |
⭐ on the board = "can be templatized". Prefer ⭐ templates when the fit is equal. Theme choice = best fit only; repeating a theme across reels is fine.

## Theme tokens used so far
- **A · Cream Editorial:** cream `#FCF8EE`, ink `#111`, orange accent `#F85000`, highlight `rgba(248,80,0,.16)`. The Table Style 5 highlight is a green gradient from `#3DBE7A`. Purple step numeral `#6C70E8`.
- **D · Burnt Orange:** rust bg `#AE5430` with a radial lift `#B85C36` to `#9A4626`, plus fine film grain (GS4). Cream type `#FCF6F0`. Cream rules at 35% opacity. Highlight = cream block with rust text. On non-orange footage, Header 9–11 copy sits on a rust top panel (radius 40, about 780–800 px tall).
- **C · Dark Studio:**
  - **News Style 1 (T1-NW1) is not a card.** It's a black top gradient over the presenter (about 96% → 0%), then a masthead (publication name left, date right), a thin white rule, an italic serif headline in white, grey body text `#9C9EA6`, and a purple highlight block `#6C63D9` with white text on the key phrase (nowrap).
  - **Header Style 1 (T1-HS1):** a small white sans line + a big red `#E3262E` italic serif line, no box.
- Before building, crop and zoom the exact moodboard template. Never build from the inventory description alone.

## Reading a storyboard PDF
The PDF has three columns: LINES | ASSETS | INSTRUCTIONS. Extract it with `pdftotext -layout`. Render the pages with `pdftoppm -r 110` to see the colour coding and the reference thumbnails.
- Green `{m:ss – m:ss}` = kept segment. Red timecode + struck-through grey text = cut; ignore it.
- ASSETS thumbnails carry timecodes: these are visual references for that span. Links (YouTube/PIB/IEEFA) are sources to screenshot or cite. The full-size asset images live on S3, which is blocked here. Pull the link list with pypdf annotations, and ask the user for any image you need.
- INSTRUCTIONS are keyed by timecode. Glossary (OSA/FSS/SOP meanings are the working reading; confirm once with the user):
  - **Header copy:** hook title → a Header template
  - **SOP**: section opener ("What goes in the EV? / 1. Battery") → a Steps template
  - **OST**: on-screen text over the presenter
  - **OSA**: on-screen asset/animation over the presenter
  - **FSS**: full-screen still (graphic replaces the presenter)
  - **FSA**: full-screen animation (make the still now)
  - **PS**: presenter shot. "slow zoom on PS" / "only subtitle" = no graphic, subtitle only
  - "real broll / we should shoot it" = the team shoots it; no graphic
  - "show as screenshot popup" = news/doc highlight card with a `Source:` line
  - "highlight as per VO" = marker highlight on exactly the words spoken
  - "thumbnail of video link" = CTA thumbnail card
  - "IG bio ss" = CTA Instagram bio card
  - "instead of X write Y" = same template, new copy
  - Lines with no instruction = subtitle only.
- If the storyboard has no instructions at all, propose graphics from the mapping defaults and get approval first.
- Mapping defaults: every flagged spoken number → a stat/data graphic. A list of 2–6 named things → icons/badges/steps. A named source → a news/doc highlight with a `Source:` line. Ordinal structure ("First… / Risk one… / Advantages") → step openers. Check the VO's maths before putting numbers on screen.

## Formats (detect one per reel)
| Tag | Format | Signals | Backbone |
|---|---|---|---|
| TIER | Ranking / tier board | "That's a D tier", items rated | Header stays all reel + tier board; each item: big reveal card → shrinks into its tier row; CTA = presenter only |
| VS | Versus / metric face-off | Two options (or scenarios), same on one metric, different on another | Question header + option cards → number duel + winner highlight → term reveal → per-option chart → big-number card → recap table → N-option table → CTA thumbnail |
| EXPL | Story explainer | One product/idea told as a story | Hook header → title card → scenario (framed presenter + floating badges) → kinetic type lines → coverage points (object + price) → exclusions (stamp cards) → verdict → CTA thumbnail + IG bio |
| FRAME | Framework explainer (Explainer sub-type) | "Think in terms of these N buckets/rules/steps" | Hook → problem visual → step opener with all N hidden → each part revealed as the VO reaches it → per-part detail graphics → mistake/payoff → CTA |
| BRK | Multi-part / sector breakdown | Numbered parts, risks, opportunities, "should you invest" | Hook header + logo chips → pivot line → chapter openers (1., 2., 3.) with data/doc/icon graphics → red risks pivot → risk chapters → green opportunities pivot → checklist + overlap Venn → fund list → A-vs-B teaser → CTA |
If none fits, say so and propose a new format.

## Fixed chrome (all themes unless the theme's own template shows otherwise)
- Canvas 1080×1920. All content inside the centred safe zone above.
- ZERO1⚡ logo: only where the chosen template shows it, and inside the safe zone. Black on light bg, white on dark. Sponsored reels may drop it; ask.
- Subtitles: 1–4 words, centred on x = 540, in the reel's body font, white with a soft shadow, ~45 px. CTA keyword in the theme's accent colour.
- Split screen: graphic panel on top (content from y 240), presenter below.
- CTA: long-form thumbnail card (rounded, 16:9, centred, top of the safe area) + "Comment “KEYWORD” to get the full video link".
- Component measurements and colour tokens from past reels are in `Zero1_Reel_Graphics_Template_Spec.md` §3–4. Re-fit any position into the centred safe zone.

## Workflow
1. **Load context**: read the 3 project docs and the storyboard/script. List the fonts in the workspace and set the reel's font roles.
2. **Parse** the storyboard into a timeline: kept segments, VO line, instruction, asset refs.
3. **Detect the format** and say why.
4. **Choose the theme** from A–E only: give the best fit plus 1–2 runners-up, with reasons tied to the script's content (data-heavy → A/B; emotional story → A/E; opinion/listicle → C/D…).
5. **Shot list** (send to the user, then STOP for approval). Use a table:
   `Timecode | VO cue | Graphic | Template ID | Native/Converted (source ID) | Copy`
   and add open questions (missing numbers, assets, fonts).
6. **Fetch references**: render only the needed template nodes from Figma (respect the call limit). Measure positions, sizes and colours from the renders.
7. **Build**: one shared CSS block per reel (colour tokens + font roles + centred safe-zone constants) used by every graphic. One HTML per graphic at 1080×1920, rendered with Playwright (Chromium at `/opt/pw-browsers`). Mark background layers (panels, boards, PS window masks) with class `fill` so the safe-zone check ignores them. Overlays on the presenter = transparent; full-screen graphics = opaque. Real photo objects per rule 11; reference them by local path and let the deliver step embed them.
8. **Check** (all must pass before delivery):
   - safe-zone content pixels = 0 and centre offset within ±12 px on every graphic
   - font consistency: every graphic uses only the reel's font roles. Look at the whole set side by side; headlines must match.
   - text fit: no cell or label overflows its box. Crop and inspect tables and long cells at full size.
   - each graphic next to its moodboard reference: colours, spacing, theme consistency, real (not vector) objects
9. **Deliver** (every graphic separately downloadable):
   - Make each HTML **self-contained**: embed every @font-face whose family is referenced anywhere in the page (check all role names, e.g. `--head`, `--serif`, `--lcd`, not a fixed list) and every local image as base64 data URIs. Assert that no workspace path (`/home/`) remains.
   - Verify: copy each self-contained HTML to a clean folder, render it **in its own fresh browser process**, and diff it against the original render. It must be pixel-identical. (A shared browser can hide missing fonts.)
   - Export a **JPG** (quality 95, 1080×1920) for every graphic. JPG has no transparency, so overlay graphics are flattened on white **and** also delivered as a transparent **PNG**. Opaque graphics ship as JPG only.
   - Name the files `<reel>_<mm-ss>_<templateID>[_conv].jpg / .html / .png`.
   - Send them with SendUserFile **one graphic per call** (JPG + HTML [+ PNG], `display: attach`), with a caption `n/N · timecode · what it is`, in timeline order.
   - Then add a contact sheet (with the safe-zone review row) and the final shot list (with the Native/Converted column) as a preview.
   - If you find a defect in files already sent, say so plainly, fix it, and re-send the corrected files.
   - Save any new decisions to the project docs.

## Converting a template into the chosen theme
Keep: structure (element count, hierarchy, reading order, relative positions), purpose and copy.
Replace: background, palette, fonts (map each role to the reel's font roles), corner radii, strokes, texture/grid, highlight style, spacing rhythm. Re-fit into the centred safe zone.
Log: `Converted: <graphic> ← <source template ID + name> (what changed)`.

## Bundled files (this package)
- `scripts/setup.sh <work_dir>` writes `fonts.css` with absolute paths to `assets/fonts/` (Manrope, Stack Sans Text/Headline, Instrument Serif, Jost, Google Sans, Old Standard TT, VT323) and installs Playwright if it's missing. Behind The Nineties and Gilmour are NOT bundled. Ask the team for them.
- `scripts/render.py [--t] files.html…` renders each HTML to a PNG next to it (`--t` = transparent background).
- `scripts/finalize.py <out_dir> <final_dir> <sheet.png>`: `out_dir/_lists.txt` holds `T <transparent htmls>` and `O <opaque htmls>`. It runs the safe-zone and centre check, embeds fonts and images, verifies each file in a fresh browser, exports JPG + PNG, and builds the contact sheet. Set `PS_SAMPLE=/path/presenter.png` to preview overlays on a presenter frame.
- `assets/safe_zone_guide_1080x1920.png`: the team's safe-margin file. The white area is the usable zone: 240 px off the top, 380 px off the bottom, 60 px off the left, 120 px off the right, and the right edge moves in to x 880 below y 720. The centred safe zone above is built from it. Overlay it on renders to check them by eye.
- `references/`: the project docs (rules, moodboard inventory, template spec). Re-read the live project versions when you can.

## Known open items (check the project docs; they may be resolved)
- Font files for Behind The Nineties and Gilmour not yet received. Role of Gilmour (headline sans? body?) not yet confirmed.
- Theme split A–E not yet confirmed by the user.
- Theme 1 templates seen only at low res. Need 2x exports or Figma access.
- The board lists Background Typography, CTA (Visuals) and Map Style, but has no templates for them yet. Ask before inventing; convert the closest existing template instead.
# Reel Graphics: Working Rules (set by the graphics team, 2026-10-23)

These apply to every reel. When rules conflict, this document overrides the earlier template spec.

1. **The moodboard is the source.** All graphics come from the Moodboard (FigJam: https://www.figma.com/board/CK597ULHYwFUUsY2UhytNZ/Moodboard). Use its layouts, fonts, colours, spacing and styles exactly as shown. Never invent templates. See `Moodboard_Inventory.md`.
2. **Unused templates are allowed.** If an unused template fits a script better, use it. Don't limit choices to templates already used in past reels.
3. **Best fit, explained first.** For each new script, pick the most suitable theme and templates, and tell the team which ones and why **before** generating anything.
4. **One theme per reel.** A "style" means the visual **theme** of the graphics (e.g. the green grid theme). Once a theme is chosen, every graphic in the reel, start to end, uses it.
   - If a needed graphic (e.g. a header) doesn't exist in the chosen theme, take it from its own section of the moodboard (e.g. Header Styles) and **restyle it into the chosen theme**. Keep its structure and purpose. Apply the theme's colours, fonts, grid, spacing and shapes.
   - **Before generating**, list every graphic as **Native** (exists in the theme) or **Converted** (with the original moodboard source, e.g. "T1-HS6, Header Style 6").
5. **Graphics only** for now. Animation comes later.
6. **Theme 2 (Light Pop) is excluded.** Never pick it, convert from it, or offer it as an option. It's the right-hand "Theme 2" column on the board: grey/white with green, pink and purple accents.
7. **Primary fonts (what the team mostly uses):** Stack Sans Text, Manrope, Behind The Nineties, Gilmour. Prefer these over the rest of the board's 11-font list. Check licences before use.
8. **Font consistency:** every graphic in a reel uses the same font system (same headline family, same body family, same emphasis style). Never mix a different headline font into some graphics. Check the whole set side by side before delivering.
9. **Safe zone, centred (1080x1920):** content stays inside the safe zone AND is centred on the canvas (centre x = 540). Use the mirrored margins: **x 120–960 above y 720** (max width 840) and **x 200–880 from y 720 down** (max width 680), y 240–1540. Never shift content left to fit the zone; shrink or re-flow it instead. Background fills may extend under the unsafe area; content may not.
10. **Delivery format:** every graphic is delivered as its own downloadable files, sent separately: one **JPG** (1080x1920, quality 95) + one self-contained **HTML** (fonts and images embedded, no external files). JPG can't hold transparency, so graphics that overlay the presenter also get a **transparent PNG** (their JPG is flattened on white). A contact sheet is a preview only, never the deliverable.
11. **Theme choice = best fit only.** No rotation rule: repeating a theme across reels is fine if it fits best (team decision, 2026-10-23).

12. **Real objects, not vector drawings.** When a moodboard template uses a photographic object (calculator, gold bars, coins, phone, house, etc.), the graphic must use a real photo in the same style, never a flat vector drawing. Source order: (1) the team's original asset file, (2) a cut-out from the moodboard reference itself (keep its soft shadow; edit only its screen/label text), (3) ask the team. A vector stand-in is allowed only as a clearly labelled placeholder that's called out in the delivery.

13. **Storyboard assets are the data source.** Numbers, labels, table structure and chart shapes come from the storyboard's ASSETS references, exactly as shown (e.g. 18.80 not 18.8, 9.93 not 9.9, keep extra rows like Sharpe Ratio). Charts must trace the reference curve's shape, not a generic wave. Storyboard instructions override the asset only where they say so (e.g. "make returns 16.7%", "remove real fund names"). The PDF only holds small previews, so ask the team for the full-size asset images before building data graphics.

14. **Sequence = storyboard row order**, not timecode order. Editors move segments around, so a row's `{m:ss}` refers to the source footage, not the final cut. Number the files 01, 02… in row order.
15. **Data source = the team's data sheet when one is provided** (e.g. the Zero1 calculator Excel), with exact figures as in the sheet. Without a sheet, use storyboard assets and then the VO. Flag any VO/sheet mismatch to the team, but the sheet wins on screen.
16. **Keep it simple, but keep tables:** one idea per frame. Comparisons use a simple Table Style 1 table (2 value columns, max 3 rows, only the rows the VO talks about), so viewers can follow along with the VO. One takeaway line under the table at most.

## Reference images from the team are assets, not themes
- When the team shares an outside design (e.g. the "Which one is the Better Choice?" car carousel), take only the asset it was shared for (e.g. car photos). The layout and style still come from a moodboard theme.
- Use product/hero photos sparingly: once (usually the hook), not in every frame. Data frames stay clean: headline + table/number only.
- Car photos (Audi A4, Hyundai Creta) cut from the team reference: /home/claude/work/lux/asset/.

## Theme D (Burnt Orange): tokens used (EMI Step-Up, 2026-10-23)
- Rust bg `#AE5430` with a radial lift `#B85C36` to `#9A4626`, plus fine film grain (GS4). Cream type `#FCF6F0`. Cream rules at 35% opacity. Highlight = cream block with rust text.
- Header 9-11 copy sits on the orange set in the moodboard. On non-orange footage it goes on a rust top panel (radius 40, about 780-800 px tall) so the cream text stays legible.
- Fonts: same reel system, cream serif headlines (italic emphasis) plus Manrope.

## Theme A (Cream Editorial): tokens used
- Cream `#FCF8EE`, ink `#111`, orange accent `#F85000`, highlight `rgba(248,80,0,.16)`. Table Style 5 highlight is a green gradient from `#3DBE7A`. Purple step numeral `#6C70E8`.

## Theme C (Dark Studio): News Style 1 + Header Style 1 (CC reel, 2026-10-23)
- **News Style 1 (T1-NW1) is NOT a card.** It is a black top gradient over the presenter (about 96% → 0%, roughly 900–1080 px tall), then a masthead (publication name left, date right), a thin white rule, an italic serif headline in white, body text in grey `#9C9EA6`, and a **purple highlight block `#6C63D9` with white text** on the key phrase. Keep highlighted phrases on one line (nowrap).
- **Header Style 1 (T1-HS1):** a small white sans line, then a big **red `#E3262E` italic serif** line, over the presenter. No box.
- Lesson: before building, crop and zoom the exact moodboard template. Never build from the inventory description alone.

## Pre-generation checklist (output to the team every time)
- Format detected (TIER / VS / EXPL / BRK / new) and why
- Theme chosen and why (plus runners-up)
- Shot list: timecode → graphic → template ID → Native / Converted (source ID)
- Open questions

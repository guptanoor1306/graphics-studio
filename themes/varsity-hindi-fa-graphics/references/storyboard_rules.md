# Storyboard rules: which beats get a graphic, and which kind

Learned from 4 Varsity Hindi Fundamental Analysis episodes (Ep 2 Mindset of an Investor, Ep 5 Balance Sheet, Ep 8 Financial Ratios, Ep 9 How to Value a Company), 69 final graphics.

## 1. Language
The VO is Hinglish (Roman-script Hindi). **Every word on screen is English.** Never transliterate; rewrite the idea as a short English label.
- "dost ne bataya hoga" → pill **Stock Tips** · "logo achha laga" → **Nice Logo**
- "jo payments company ko milne wali hain" → **Customers** (scene) + the term in the VO
- "har ek rupee ki sales ke liye 3.75 guna" → **₹1 of sales valued at 3.75×**
English terms already in the script (EBITDA, PAT, ROE, DCF, Debt to Equity) stay as they are. When the storyboard gives English copy (definitions, takeaways), use it verbatim after fixing spelling.

## 2. The decision: graphic, screen capture or footage
Ask in order. The first match decides.

| # | The VO is… | Call | Built as |
|---|---|---|---|
| 1 | reading a **real document**: annual-report page, note number, line item, a figure "jaisa aap dekh sakte hain" | **Screen capture** | the real PDF page, highlighted in the edit. **Never rebuild the report as a graphic, and don't repeat its numbers in a separate frame** |
| 2 | doing something on a **real website/tool**: Varsity chapter, NSE index page, Excel, Kite UI action | **Screen capture** | footage of that page |
| 3 | hook line to camera, bridge ("Chaliye aage badhte hain"), conclusion, "comment karein", next-video plug | **Footage** | none |
| 4 | chapter open / next-chapter reveal | **Graphic (series)** | `module` page, current card = this episode |
| 5 | names a **list of types/categories/methods** (2–5 items) | **Graphic** | OSA: header + `pills` · or FSS: `cardset` (folders/cards, active one sharp, others tilted/blurred until reached) |
| 6 | **defines a term** in one sentence | **Graphic, OSA** | `card` kind `quote` (SB definition verbatim) left of the presenter |
| 7 | gives a **formula** | **Graphic, OSA** | `card` kind `formula` (term in a highlight block, = , fraction) |
| 8 | works a **calculation with numbers** | **Graphic, OSA** | `card` kind `calc` (labels in yellow blocks, script's numbers, result) |
| 9 | explains a term with an **everyday analogy or a business situation** (factory, customers paying, bank loan, credit card, house loan, patent approval, shareholders) | **Graphic, FSS scene** | header + characters + buildings/props on the tiled floor; money moves as `coinflow`; parts as `branch` badges |
| 10 | introduces **people types/roles** (trader / investor / speculator, customers, vendor, shareholders) | **Graphic, FSS scene** | the fixed characters, **several distinct ones**, each with an italic name `pill` + hand-drawn arrow |
| 11 | describes a **trend or comparison of numbers** (returns by year, FD vs equity, profit vs debt, D/E = 1 / >1 / <1, share price vs EPS vs P/E) | **Graphic, FSS chart** | `bar` / `line` / `pie` / `linecards` in a glass card (or standing on a landscape phone) with the script's numbers |
| 12 | a **real stock's price** | **Graphic, FSS** | `window` (Kite-style) at the stock's real price level |
| 13 | **compares companies** | **Graphic, FSS** | one building per company (Company A–D), then all side by side (`cardset` glass), or two towers with their numbers |
| 14 | "**X vs Y**" two approaches | **Graphic, FSS** | `split` with a blue divider, one `bar` header per side |
| 15 | lists **key takeaways** | **Graphic** | `takeaways` (SB copy verbatim, numbered) |
| 15b | tells a **story with people** (farmer, mill owner, buyer, seller) | **Graphic, FSS drawn scene** | `backdrop` + cast `char`s with poses + drawn `prop`s + `bubble`s for what they think |
| 16 | "continue / highlight as per VO" on the previous frame | **State** | same frame id with `_b`, `_c` (new pill active, next card sharp, bar added). Not a new layout |

**When in doubt between OSA and FSS:** words-only content (definition, formula, calculation, list) is OSA, next to the presenter. Anything with characters, buildings, props or a chart is FSS.

## 3. One ratio / concept = a mini sequence
Ep 8 runs each ratio as: header or list highlight (OSA) → definition `quote` (OSA) → `formula` (OSA) → FSS scene or chart for the meaning → `calc` with the company's numbers (OSA) → report capture if the VO reads the page. Each step is its own frame or state, so one concept takes 3–6 graphics. Ep 5 does the same for balance-sheet terms with scenes instead of formulas.

## 4. Density
- Explainer/ratio episodes: **one graphic every 20–30 s of VO** (Ep 2: 25 s, Ep 8: 20 s).
- Report-walkthrough episodes: **about one a minute**; the report captures fill the rest (Ep 5).
- Short overview episodes: scenes only for the main ideas, and OSA text left to the edit (Ep 9). Still write the OSA copy in the storyboard, marked `Edit text`.

## 5. Writing the scene
- **Lead with the concrete thing, not the term**: "Non-Current Liability" → header **Housing Loan** + house + 10-year timeline; "Share Capital" → **XYZ Company** + investors + growing coin stack. The term is in the VO and the next OSA card.
- **One idea per frame.** If the SB asks for five animations in one beat (bank lends, calendar flips, person repays, two callouts), build the main one and push the rest into `_b` states or drop them.
- **People:** every scene with people uses distinct characters (never the same one twice). Seated trio = participants/shareholders/investors; standing characters = customers, vendor, borrower, the person acting. The characters are fixed team artwork: place, scale or mirror them only.
- **Floor:** every FSS scene stands on the tiled floor (`mode: fss`, floor on). Characters and buildings have their bottoms on the floor (y ≈ 900–1040).
- **Money** moves as gold ₹ coins on a dashed curved arrow from payer to payee. Growth is a coin stack getting taller across states.
- **Labels** are white pills: italic for names on a scene (Customers, Vendor, Investor), upright bold for lists and word chips (Stock Tips, Raw Materials).

## 6. Data rules
- **Numbers come from the script.** SB reference images and SB calculations are layout only. If the SB's numbers differ from the script (Ep 8: EBITDA margin 21% vs 22.7%, P/E 20 vs 39, price 3,780 vs 10,379), use the script's and list the difference in the storyboard notes.
- Every number the VO says on a graphic beat goes on screen; compute derived values (₹100 at 6% for 10 years = ₹179).
- One price level per stock across all frames.
- `₹` only before amounts, never before a percentage. P/E is **Price to Earnings** (the SB wrote "Price to Equity" twice).
- Header = what the frame shows (Ep 8 put "Leverage Ratios" on the valuation scale).
- Keep each item on the right side of the balance sheet (Ep 5 listed "Machine" under Liabilities).
- Generic companies: **Company A/B/C/D** or **XYZ Company**. Real companies by listed name, only when the script names them.

## 7. Colour
Green and red/coral appear **only on data marks** (chart bars, pie slices, candles) and on the mocked **BUY/SELL** buttons. Pills, cards, headers and highlight blocks are white, blue or yellow. Highlight blocks: **yellow** (labels, values) or **blue** (the ratio's name). The build warns on green/coral boxes.

## 8. Not this kit
Don't borrow from `varsity-graphics` (English), `varsity-mf-graphics` or the Technical Analysis `varsity-hindi-graphics` kit: no yellow window header tabs, browser-window definition boxes, amber table headers, checkerboard floors or doodle people. SB references taken from Varsity English videos (yellow "Intrinsic Valuation" boxes) are **restyled into this kit**, never copied.


## 9. Lessons from the Futures Ep 1 review (Nov 2026)
| Feedback | Rule |
|---|---|
| "Face and hand expression same", "body language same" | Every person = a cast character with a pose that matches the action (holding, giving, pointing, thinking, worried) and a matching expression. Never two identical figures in a frame |
| "Extra character (no need)" | No characters beside the presenter unless the storyboard asks |
| "Unused space, element missing", "text box placement inconsistent" | OSA content uses the `osa` block only (fixed header + block position); every list item has an icon/logo/number; no loose pills on an empty left half |
| "Thinking bubble pe aayenge sara data" | A person's facts and worries go in their thought/speech bubble |
| "Building repeated", "same building different style", "machine repeated" | One asset = one thing per video; named organisations get their logo; one style family per frame; missing prop → New assets needed + prompt |
| "Flat wheat", scenes with no setting | Story beats get a drawn `backdrop` (farm, market, city, interior) with drawn props |
| "Charts look off", "visual clarify nhi" | One big chart per frame; relationships as cards + connectors; no tiny paired charts with extra arrows |
| "Charts and money missing" on scenario cards | Scenario frames carry the money/price element (price tag, money, scale, arrow) |
| "Graphics looks childish" | No folder cards on a road; chapter lists = module page |
| "Floor Mill" | Proofread `_text.txt`; the build flags common confusables and unknown words |

## 10. Futures and other story-driven modules
Elements-heavy modules (FA, Futures, Options basics) use this skill. Set `"series": "futures"` for the Futures presenter's look: OSA as a dark glass card with a white header underlined in blue. OSA PNGs are transparent overlays, so they work on whichever presenter the video has.

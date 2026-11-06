# Storyboard rules: which beats get a graphic, and which one

Learned from Ep1–5 of the Varsity Hindi Technical Analysis module (≈ 15 graphics per 7–10 min video, i.e. one every 30–40 s of VO).

## 1. Language
The script is Hinglish (Roman-script Hindi). **Every word on screen is English.** Never transliterate. Rewrite the idea as a short English label:
- "Kis level par stock ko kharidna ya bechna hai" → **Entry & Exit Price**
- "Yeh hamesha long-term investments ke liye optimize hota hai" → **Long term / Months to years**
- "Marubozu ka matlab bald" → In Japanese / **Marubozu means "Bald Head"**
English terms already in the script (OHLC, Bullish, Stoploss, Doji) stay as they are. When the storyboard gives English copy, use it verbatim (fix spelling). Things-to-remember bullets are rewritten in English, one line each.

## 2. Graphic vs footage
| Beat | Call | Built as |
|---|---|---|
| Section / concept start ("Ab baat karte hain X ki") | **Graphic** | `side` + `htab` X (+ definition or panel) |
| Video's main question, or a new big idea | **Graphic** | `main` + `title`/`roto` (keyword yellow, rest white, magnifier) |
| Definition said aloud | **Graphic** | `side` + `htab` + `definition` (plain or capsule) |
| Shape of a candle/pattern explained | **Graphic** | `side` + `htab` + `panel` with `diagram` (labels, Bullish/Bearish pills, 50% line) or `mini` charts |
| OHLC numbers / worked example ("Open 62, High 70…") | **Graphic** | `side` + `diagram` with `scale` (every number on the axis) |
| "X ke daily chart par…" (a named stock example) | **Graphic** | `fss` + `kite` of that stock, pattern in a dashed box at the right spot |
| Trading rule (entry, stoploss, confirmation) | **Graphic** (state of the previous chart) | same `kite` + `leaders` / `trade` |
| Timeframe / interval talk | **Graphic** | `kite` + `dropdown` with the interval selected, or `side_card` for "1 Month Candle" |
| Analogy (phone shopping, umbrella, pillars) | **Graphic** | `scene` with the character, or a prop in a panel (`umbrella`, `pillar` cards) |
| SB says top cam / on the board / footage | **No graphic** | the presenter explains on camera; list it as Top cam |
| SB says highlight the part from a link / article | **Screen capture** | no built frame |
| A setting (field, shop, mill, market) | **Graphic** | `backdrop` + characters standing in it |
| A story with people (farmer, buyer, seller, family) | **Graphic** | `fss` with `character` items (team characters 1–6, as drawn) + `prop` items for the setting, on the floor; one centred header; names in pills |
| Scenarios (price rises / same / falls) | **Graphic** | one intro frame + one frame per scenario with the same layout (same team characters, same prop, e.g. `scale` tilting); only the numbers and tilt change |
| Comparison of two approaches (FA vs TA) | **Graphic** | `blur` + `table`, magnifier on the row being read |
| A list of points (3–6) | **Graphic** | `side` + `bullets` (current bright, rest faded) or `cards` |
| Exercise ("pause the video and plot…") | **Graphic** | `side` + `htab` Exercise + `typo_card`. No candles: the viewer draws them |
| Things to remember | **Graphic** | `takeaways` (title "Key Takeaways" or "Things to Remember" as the SB says) |
| "Go to Kite and click…" (a real UI action) | **Screen capture** | footage of real Kite, no graphic |
| SB says "Screen capture" for **a chart** | **Graphic** | mock `kite` (the team rebuilt these as mocks in 6 of 8 cases) |
| Hook lines, bridges ("Toh chaliye samjhte hai"), recap, conclusion, CTA, Badger, chapter-name reveal, upcoming episodes | **Footage / Edit** | none (series templates handled by the editor) |
| "Continue / highlight as per VO" | **No new layout** | another state of the same frame: `id` `_b`, `_c` only if content changes |

## 3. Pattern episodes: concept → evidence → rule
For each pattern: (a) `side` + `htab` name + `panel` with the shape (`diagram`); (b) `fss` `kite` of the stock the VO names, the pattern boxed at a real top (bearish) or bottom (bullish); (c) the same chart with `leaders` "Entry" / "Stoploss" when the VO gives the rule. Multi-candle patterns get `days:true` on the box.

## 4. Data rules (where the finals went wrong)
- Numbers come **from the script**. Storyboard reference images are layout only; never copy their axes or prices (Ep2 copied a 1800–2000 axis; Ep5 put Nifty-level prices on Reliance).
- A real stock's chart must sit at a plausible price level for that stock, and every frame of it uses the same range.
- Daily-chart examples get a date axis (`days`), intraday examples get `intraday`; don't mix.
- Header tab = what the chart actually shows (Ep3 labelled monthly charts "Annual Timeframe").
- The label must name the pattern in the box (Ep5 labelled a hammer inside an engulfing frame).
- Spell-check tickers and titles: "HFDC", "BANKNIF", "Uper Shadow", duplicate "5." all shipped.
- Use listed names for real stocks (Zomato → Eternal) and "XYZ Stocks" for generic ones.

## 5. Colour: the whole palette (measured from all 78 Ep1–5 finals)
| Colour | Hex | Used for, and nothing else |
|---|---|---|
| White / ink | `#FFFFFF` / `#141414` | text, windows, cards, the FA-vs-TA table (white rows, black text, grey `#D8D8D8` rules, **no coloured header row**) |
| Header-tab blue | `#278BED` | the base bar of every header tab (18/18 frames); dashed target zone outline |
| Chart blue | `#307AD4` | line charts only |
| Keyword yellow | `#FFBE30` | title keywords, roto text, question keys, value tags on line charts |
| Side yellow / amber | `#EFB32E` / `#F0B32A` | side-cam headings, bullet markers, the **active** card or pillar, selected dropdown item |
| Green | `#A5CC65` | **bullish candle and OHLC-bar bodies only** |
| Coral | `#F47964` diagrams, `#ED6258` chart candles | **bearish candle and OHLC-bar bodies only**; plus the Things-to-Remember accent bar and megaphone |

**Green and red go on candles, never on boxes.** Bullish/Bearish pills, Open/High/Low/Close tags, Target/Entry/Stoploss pills, trade zones, word chips, table rows, list items and comparison bars are all neutral: white boxes with black text, the blue tab bar, yellow for keywords, amber for the active item. (A few early finals did tint pills and zones green/red. That is not the house rule; don't copy it.) The build warns if a palette green/coral appears anywhere except a candle.

**Numbers that aren't prices** (risk ₹10 vs reward ₹25, 3 touches, 52 candles) go in a `callout` pill, the white `table`, a `trade` overlay on the Kite chart, or a `typo_card`. **There is no bar-chart or coloured-table component in this IP.** Don't invent one with `html`.

## 6. This is not the Varsity English kit
The account also has `varsity-graphics` (English IP) and `varsity-mf-graphics`. Don't load them or borrow from them for a Hindi/Technical Analysis script. None of these exist in the Hindi IP:
- amber or blue **table header rows**, calc tables with bold total rows, "Less:" rows
- green speech-bubble callouts, green "net savings" result pills, highlight pills over tables
- giant coral hero keywords (HUF style), title pills in dark glass
- sky with a **checkerboard floor**, wire curves with square nodes, paper doodles, clouds
- folders, blurred paper lists, fanned cards, coins, jar, house, bank, calculator props
- the doodle `person()` generator (Hindi uses the fixed yellow character PNGs)
- gain/loss green `#3FA34D` / red `#E0463A`, blue `#248EF7` chart bars, amber `#F2B233` headers

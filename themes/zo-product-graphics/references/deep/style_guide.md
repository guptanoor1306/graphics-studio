# Zerodha Online · Product IP — style guide (learned from 3 videos: Devolvement, Share price, SIFs)

All frames are 1920×1080 (anchor PSDs are sometimes 4K; scale ÷2). Font: **Inter only** — Medium for body, SemiBold for headings/keywords, Bold for "Important note" and big numbers, Regular for lead-ins over the anchor.

## Colour tokens
| Token | Hex | Used for |
|---|---|---|
| yellow | #FFC02E (V2 used #FFB949 — normalise to #FFC02E) | keywords/numbers over the anchor; option card; value pills; 25% bar |
| light blue (on dark) | #81BBFF | alternate keyword colour over the anchor ("mistake", "holdings", "my money?") |
| blue | #4993E9 | futures card, cash-settled pill, chart line, UI headers, chips, "Company A", passive breach, long |
| zerodha blue | #387ED1 | ₹ values on FSS (strike price), calendar tile |
| green | #4CAF52 | call / above-strike zone, ✓, "Settled in cash", physically settled, "Company B", interval, active breach |
| orange | #F07339 | put / short / below-strike, "Requires margin", ✕, Important note box, falling line, risk tags |
| purple | #9B7BEA | third category pill (Open-ended SIF, SEBI hub) |
| ink | #222222 | FSS headings, card titles |
| deep grey | #424242 | FSS labels, axes |
| mute | #888888 | parentheticals, faded list items |
| white | #FFFFFF | all text over the anchor |

**Semantic colour is consistent across videos:** call/long/up = green-or-blue, put/short/down = orange; the two compared entities keep one colour each for the whole video (Company A blue / Company B green; Interval green / Open-ended purple).

## Mode A — anchor shots (OSA / OST / TOS)
The PSDs place a still of the anchor (placeholder for the real shot) at a chosen **framing**, darkened by a gradient that creates the text area. Three anchors seen so far, one per video — always use the plate for the video's anchor.

| Framing | Gradient / text area | Typical content |
|---|---|---|
| wide centre | bottom fade, lower third y≈740–960 | one-line statement / equation (`lower`), big title |
| punch-in centre | bottom fade, row y≈690–930 | two named object cards with a transformation between |
| close-up left (anchor x≈150–700) | right half solid black / soft circle | side panel: heading + list, ladder, note, punchline, big number |
| close-up right (camera 2) | grey wall on left | big number box, small table |
| centre, flanking | darker overall | two white portrait cards left/right of the anchor |

Text sizes on anchor (1080p): lower-third statement 66–72 SemiBold · lead-in 40–64 Regular · punchline keyword 150–186 SemiBold · big number 136–200 Bold · side heading 84–86 SemiBold yellow · side list rows 52 Medium · scroll list 34 inactive / 60 active.

Decor over anchor: 2 small four-point sparkles (orange, blue) + 1 blue squiggle bottom-right. Faint red/green candlestick motif behind text is allowed for market topics (V2 "Stocks are different", V3 OST).

**TOS** (title behind the anchor) — once per video at most, for the topic word (V1 "Devolvement"): 220px+ white word behind the roto cut-out with a yellow outline copy in front.

## Mode B — FSS (full-screen slide)
- Background: white with a faint 52px grid; decor kit — orange 4-point star top-left, small triangle (blue/yellow) bottom-right, short dashes on the left (green) and right (orange) edges, two pale-blue dots.
- **Heading: 72px SemiBold #222, one size on every FSS** (channel decision, Oct 2026). Centred top, or left-aligned with yellow underline ("Look at the market cap"), or icon + title left ("Crude oil / Strike price ₹7,900"), or inside a light-grey pill. Sub-heading 48px, coloured only when the colour means something. ≤6 words. Many FSS have **no heading** — the illustration carries it.
- Labels ≥36px; secondary ≥30px; nothing readable under 26px (axis ticks 28px).
- Illustration styles (keep one per object across a video):
  - **3D-ish glossy objects** for commodities/money: gold bars, oil barrel, coins, cash bundle, vault, money bag.
  - **Flat buildings** for companies, tinted circle behind optional.
  - **Flat colour icon sets** (asset classes, business fundamentals) in white bordered cards or tinted circles.
  - **Black line icons** inside light-blue pills for "mind-map" lists.
  - **Metaphor illustrations**: pizza, puzzle pieces, seesaw, shirts/coffee with price tags.
  - **Mock UI** (Kite-like): positions cards with status chips, account-status checklist, phone notification, monitor quote card, scheme list.
- Pills: rounded, solid colour with a soft same-colour outer glow (value pills, category pills).
- Charts: blue line, light-blue fill, dashed grey strike line + label chip, green zone above / orange below, coloured tag callouts, a big up/down arrow at the right edge for direction. Generic axes when no real data.
- Diagrams: hub circle → two pills (classification); hub → fan of icon cards (composition); hub → ring of pills (mind map).
- Every FSS should fill the frame: content block centred, scaled up when sparse; nothing pinned to the top with an empty bottom half.

## Text rules
- ₹ with **Indian grouping** (₹12,00,000; 10 lakh; ₹18,00,000 crore). Never "1,200,000".
- Correct operators: × for multiplication, = for results, ≠ for "is not", → for "becomes". (V2 shipped "+" in a product formula — error.)
- No "~" and no invented figures; if the script says "around", write "About".
- Acronyms in caps (ITM, CTT, DNE, SIF, AMC, SIP, PMS, AIF); otherwise sentence case.
- Labels of a pair must differ ("Lower cost shirt" / "Higher cost shirt") — copy-paste errors shipped twice.
- Spell-check (shipped typos: "squar off", "satisying"). Don't carry script typos onto screen.
- Real companies are shown by what they make (MRF → tyre, Reliance → refinery) — no logos.
- Zerodha product names as written: Kite, Coin, Console; "Zerodha" in mock UIs.

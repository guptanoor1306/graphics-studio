# Zerodha Online · Product IP: learned examples (script → storyboard → designed frame)

Each row is one beat of the script, in order. **Outcome** says whether the beat got a designed frame (PSD) or stayed on **Footage** (the anchor on camera, no design).

The PSD filename is `<sequence><state letter>-<code>`. The number is the order of the graphic in the video. The letter is a build state inside the same file (`2a`, `2b`, `2c` are layers revealed one after another as the voice-over moves).

## Storyboard codes

| Code | Meaning | Screen |
|---|---|---|
| **OSA** | On-screen animation | The anchor stays on screen. The shot is reframed and darkened by a gradient, and the graphic sits in the dark area: a **lower third** under a centred anchor, or a **side panel** beside an anchor pushed left. |
| **OST** | On-screen text | One sentence or term as a lower-third caption over the anchor, with white text and yellow keywords. |
| **TOS** | Title on screen | The topic name as a giant word placed *behind* the anchor (roto cutout), with an outlined copy in front. Used once, for the topic reveal. |
| **FSS** | Full-screen slide | The anchor is off screen. A white background with a faint grid, flat UI-style graphics and sparkle decor. |

The anchor in every OSA/OST/TOS PSD is a placeholder still (`DSC03448` plus `Roto Layer`) placed at the framing the designer wants. The editor swaps in the real shot. So the PSD sets two things: **the framing** and **where the graphic goes**.

---

## Video 1: What happens when an MCX commodity option expires In The Money? (Devolvement)

About 1,100 words. **21 graphics** (22 PSD files): 9 FSS, 10 OSA, 1 OST, 1 TOS. That is about one graphic per 2–3 script sentences. The reference sheets are `sheet_v1_devolvement.jpg` (all frames, labelled) and `sheet_v1_hidden_states.jpg` (the build states hidden inside the PSDs).

| # | Script beat | Outcome | What was built | Why this treatment |
|---|---|---|---|---|
| 1 | "Say you buy a commodity option by paying a relatively small premium." | **1 OSA**, anchor close-left, card on the right | White rounded card styled as an order ticket: gold-bar icon in a blue circle, "**Gold**" + blue "Call Option" chip; rows Strike price ₹6,000 / Expiry (blank) / **Premium ₹150** in blue; blue buy-button with an arrow | The hook needs a concrete object the viewer recognises (a trade ticket). The designer swapped the script's generic option for Gold so the hook has a face. The script's later example is crude oil, so the hook's commodity need not match it. |
| 2 | "The trade moves in your favour… expires ITM… expect profit settled in cash. But the next day… a futures position… far more margin" | **2a FSS** (states 2a→2b; 2c unused) | "Gold" header with icon; a rising green area chart Day 1 → Expiry behind a "Your positions" panel. Card 1: **Gold option** (Expired) + green chip "Settled in cash" +₹12,000. Card 2 (revealed next): **Gold futures** (New position) + orange chip "Requires margin". Hidden 2c: coin stacks "Option margin ~₹150" vs "Futures margin ~₹7,000+ (Illustrative)" | A surprise in the account is shown *as the account*: a positions list in Kite-like cards. The two cards appear on the two script beats ("you expect cash" → "but the next day…"). The 2c state was dropped: it uses invented figures and "~". |
| 3 | "This happens because of devolvement." | **3 TOS** | "Devolvement" in 223px Inter Medium behind the anchor (roto), with a yellow/white outline copy in front; wide centred framing | The topic name gets a single title moment. |
| — | "If you trade commodity options on MCX, you need to understand this before holding a position until expiry." / "What is devolvement?" | **Footage** | — | Motivation and a section question straight after the title card. The anchor carries it. |
| 4 | "Commodity options are based on futures contracts. When… ITM… exercised and converted into the corresponding futures position." | **4 OSA**, anchor mid-centre, lower third | Yellow card "Commodity option" (barrel + chart icon) → a circle of blue/yellow pixels dissolving → blue card "Futures position" (document + chart icon); caption "ITM (In The Money)" under the circle | This is the core mechanism, so it gets two named cards and a transformation in between. The pixel dissolve shows the conversion. |
| — | "An out-of-the-money, or OTM, option expires worthless." | **Footage** | — | A one-line negative case. Nothing to show. |
| 5 | "Whether an option is ITM… depends on the underlying futures contract, not the commodity's spot price." | **5 OSA**, anchor wide-centre, lower third | Lightbulb icon + "ITM or OTM is based on" (white, small) / "**Futures price** or **Spot price**" (yellow, large; the wrong option is struck or faded in the animation) | Corrects a likely misconception, so the key distinction is put on screen in words. |
| 6 | "A call option is ITM when futures price is above the strike. A put… below." | **6a FSS** (6a call → 6b put) | "ITM scenarios" heading + green "(Call option)" subheading; price line chart with a dashed strike line; area above the strike filled green + green up arrow. 6b: "(Put option)" in orange, area below filled orange, orange down arrow | A directional rule is easiest to grasp on a chart. The same frame shows call then put, with only the colour and direction flipped. |
| 7 | "Say you hold a Crude Oil 7900 call… futures settles at 8,000… the call is ITM… turns into a long crude oil futures position." | **7a FSS** | Crude oil barrel icon + "Crude oil / Strike price ₹7,900". Intraday chart 9:15 AM → Expiry with ₹7,700–₹8,100 axis, blue strike line "Strike price – ₹7,900", green tag "Expiry settlement ₹8,000". Over it, the same "Your positions" cards as #2: Crude oil option (Expired, Settled in cash) / Crude oil futures (New position, Requires margin) | The worked example reuses the hook's position cards (continuity) and puts the script's real numbers on a chart. |
| — | "Btw, you can check the underlying futures contract… using the option chain or the commodity Info widget on Kite." | **Screen capture** (no PSD) | Kite UI recording: option chain / Info widget | A product aside that names a real screen. Show the real UI rather than designing it. |
| 8 | "Which futures position will be created?… long call → long futures; short call → short futures; long put → short futures; short put → long futures." | **8 OSA**, anchor close-left, side panel right | "Position conversion" (yellow 86px) + 5 rows "Your option → Futures position", "Long call → Long futures"… in white 53px, revealed row by row | A 4-item mapping is a list, so it goes in the side panel and builds with the voice-over. |
| — | "In our example, the Crude Oil 7900 long call becomes a long crude oil futures position. On Zerodha, the new position is reflected at the settlement price of 8,000." | **Footage** | — | Restates what #7 already showed. |
| 9 | "Intrinsic value—the 100-point difference between 8,000 and 7,900—is settled in cash… multiplied by lot size" | **9 OSA**, anchor wide-centre, lower third (two states) | "₹8,000 − ₹7,900 = **100 points** (Intrinsic value)", then "100 points × Contract lot size = Total amount" | Arithmetic goes on screen as an equation, with the result in yellow. The second state answers "this does not mean ₹100". |
| — | "Depending on the commodity… current futures contract or the next available month's contract." | **Footage** | — | A caveat. |
| 10 | "If you already hold an opposite open futures position… e.g. 1 lot ITM long call + 1 lot short futures… offset each other completely." | **10 FSS** | Two document icons, "Long call" (blue, ↑) and "Short futures" (orange, ↓), connected by an arc; two arrows into a grey card with a refresh icon: "Contracts will offset / **Completely**" | Two positions interacting are shown as two objects merging into a result. |
| — | "Why can this create a margin problem?" | **Footage** (section question) | — | — |
| 11 | "When you buy an option you pay only premium. A futures position… SPAN and exposure margins… may not have enough funds" | **11 OSA**, anchor mid-centre, lower third | The same yellow "Commodity option" card + "(Premium)" and blue "Futures position" card + "(SPAN + Exposure margins)"; green up arrow; an arc over them with a red warning triangle: "Not enough funds" | Reuses #4's cards (same objects, new property). The cost contrast sits under each card. |
| 12 | "The exchange starts blocking margin… T−2: 25%, T−1: 50%, expiry day: full margin." | **12 OSA**, anchor close-left, side panel right | Vertical stacked bar: yellow (T−2, 25% margin) → blue (T−1, 50%) → grey (Expiry day, 100%), labels left (white) and right (yellow), caption "Futures margin" | A schedule with percentages becomes a filling bar. |
| — | "This means the margin requirement can rise sharply…" / "What happens after the option becomes a future? The trade does not end… You now hold a regular futures position…" | **Footage** | — | A summary line, a section question and transitions. |
| 13 | "Some commodity futures are cash-settled… exchange calculates final settlement price… Crude oil and Natural gas… Other commodity futures are physically settled… obligation to take/deliver" | **13 FSS** (builds; crude oil and natural gas icons in a hidden state) | Heading pill "Commodity futures"; arc splitting into two glowing pills "Cash settled" (blue) and "Physically settled" (green); bullet points under each with bold key phrases; crude-oil barrel and natural-gas flame icons under Cash settled | A classification into two types gets a 2-branch diagram with bullets. The examples arrive as icons when the script names them. |
| — | "So, if you hold the futures position… you will not receive barrels of crude oil." | **Footage** | — | An intuitive consequence. |
| 14 | "Zerodha does not facilitate physical delivery… must be closed before tender/delivery period… may square them off." | **14 FSS** | "**Important note**" (Bold 91px, hand-drawn underline, curly doodle) over an orange rounded box with white SemiBold text (the script sentence almost verbatim) | A broker rule or warning gets the **Important note** pattern. |
| 15 | "CTT, is charged at 0.01% when devolvement creates a short futures position… CTT is not charged… long futures position." | **15a/15b OST**, anchor wide-centre | 15a: "Commodities Transaction Tax" with C, T, T in yellow (acronym), then "CTT, is charged at **0.01%**" (huge 201px yellow number). 15b: "**CTT** is not charged at conversion when devolvement creates a **long futures** position." | An acronym, a rate and a rule: text over the anchor is enough. |
| 16 | "The amount is calculated using the settlement price, number of lots and contract lot size." | **16 OSA**, anchor close-left, side panel | Vertical list with a scroll bar and a yellow active marker: Settlement price / **Number of lots** (yellow, larger) / Contract lot size | Three inputs become a list, highlighted as the voice-over names each one. |
| 17 | "On expiry day, Zerodha sends an SMS and in-app alert before 1 PM… maintain margin before 7 PM or close the option." | **17 FSS** (states: in-app → SMS) | Phone mock-up (Zerodha header) with an orange "Option expiry alert" notification card and the message text; a hidden state shows an SMS thread + blue "SMS" chip | Product communication is shown as the product (a phone notification). |
| 18 | "After 7 PM, Zerodha checks… short options generally not squared off… enough margin → allowed to devolve; if not → square off." | **18 FSS** (states) | "Account status" panel, Kite-like, with a blue header and collapsible rows: **Short option** ✓ SPAN/Exposure margins collected, ✗ No square off; **Future option** ✓ Exposure margins collected, ✓ Allowed to devolve (alt state: ✗ Not enough margin, ✗ Square off) | Broker checks become a status checklist in a UI panel. |
| 19 | "CTM… is only a risk-management classification… Under MCX… only ITM options are automatically exercised." | **19 OSA**, anchor close-left | The **Important note** pattern again, on the anchor (white title, orange box) | Same pattern as #14 for a clarification. Used as OSA because the anchor is mid-explanation. |
| — | "What if the option cannot be squared off? Commodity options can become illiquid… no buyers." | **Footage** | — | Sets up the scenario. |
| 20 | "Zerodha may submit a Do Not Exercise, or DNE, instruction during the post-market exercise window." | **20 FSS** | "Post-market exercise window" heading; document "DNE" in a yellow folder; blue "Submit" button | An action is shown as a form being submitted. |
| — | "However, if you have sufficient margin… Zerodha will not submit DNE… For a short option, depends on the buyer…" | **Footage** | — | Edge cases after the main point. |
| 21 | Takeaway: "An MCX commodity option expiring ITM may not be the end of the trade. It can first turn into a futures position… cash or physical delivery" | **21a OSA**, anchor wide-centre, lower third (2 states) | "**ITM option** ≠ **Trade ends**" (yellow 71px, white operator), then "ITM option → Futures position → Settlement / Delivery" | The thesis as an equation, then the whole journey as a chain. |
| 22 | "Before holding… ask yourself four questions…" | **21b OSA**, anchor close-left, side panel | "Before holding a commodity option till expiry, ask:" + 4 questions in a scroll list, active one yellow and larger | A checklist with the scroll-highlight pattern, as in #16. |
| — | "Check contract details in Kite's Info widget… margin calculator…" | **Screen capture** (no PSD) | Kite Info widget, then Zerodha margin calculator | A named product tool is shown as the real UI. |
| — | "If you have any questions, post them in the comments…" | **Footage** | — | CTA and close. |

### What this video teaches about *when* to design

**Designed** (each one *shows* something the viewer can't easily hold in their head):
1. The hook's concrete object: a trade ticket.
2. A surprising state of the account: a positions list.
3. The topic name, once: TOS.
4. A mechanism or transformation: A → B cards.
5. A misconception or distinction: a lower-third statement with yellow keywords.
6. A directional rule: a chart with a strike line and coloured zones.
7. A worked example with the script's numbers: chart plus positions.
8. A mapping or list of 3–5 items: a side-panel list built row by row, or a scroll highlight.
9. Arithmetic: an equation in the lower third.
10. Two things interacting: two objects → a result card.
11. A schedule or percentages: a filling bar.
12. A classification: a 2-branch diagram with bullets.
13. A rule or caveat from the broker: the **Important note**.
14. An acronym or rate: OST.
15. A product flow (alerts, checks, submissions): a UI mock (phone, status panel, form).
16. The thesis and the checklist at the end.

**Left on footage**:
- section questions ("What is…?", "Why can this…?");
- motivation lines;
- one-line negative cases;
- restatements of an example already on screen;
- transitions ("The trade does not end…");
- obvious consequences ("you won't receive barrels");
- secondary caveats and edge cases that follow a designed point;
- the CTA.

**Screen capture** (a third outcome, no designed frame): when the script names a real Zerodha/Kite screen or tool the viewer can open (option chain, Info widget, margin calculator), show a recording of the real UI. A *mock* UI is designed only when the script describes a process or state that can't simply be recorded, such as an expiry alert, a post-7 PM account check or a DNE submission.

### Where the treatment goes (FSS vs OSA)
- **FSS** when the visual needs the whole frame or is a "thing": charts, UI mock-ups (positions, phone, account status, forms), diagrams with several parts, and the Important note when it is a standalone rule.
- **OSA lower third** (anchor centred) for one-line statements, equations and A → B chains.
- **OSA side panel** (anchor pushed close-left, right side darkened) for vertical lists, ladders and notes.
- The video alternates: it rarely has more than 2 FSS in a row before returning to the anchor. Runs: 6a-7a, 13-14, 17-18.

### Continuity seen
- **Recurring objects:** the yellow "Commodity option" and blue "Futures position" cards (#4, #11); the "Your positions" cards (#2, #7); the Important note (#14, #19); the scroll-highlight list (#16, #21b).
- **Colours:** call = green, put = orange, long = blue/up, short = orange/down.

---

## Video 2: Does a lower share price mean a stock is cheaper? (concept explainer)

About 1,050 words, a different anchor (female, orange top, dark-grey set; plus a second-camera side-profile close-up). **34 frames in 21 numbered graphics** (`Copy of N a/b/c.psd`): 26 FSS and 8 OSA. Unlike Devolvement, this script has no product flows, so it leans heavily on **FSS illustration metaphors**. The folder also holds an **earlier, rejected round** (`1–16.psd`, `Stock list`, `Total outstanding shares`, `massive company`); see "What the revision changed" below. The reference sheets are `sheet_v2_final.jpg`, `sheet_v2_rejected_round.jpg` and `sheet_v2_hidden_states.jpg`.

The script had three explicit `[SHOW: …]` cues. All three were honoured (6a–c, 10A/b, 16b). **Most of the other graphics had no cue.** The designer storyboarded every analogy and every number pair.

| # | Script beat | Outcome | What was built | Why this treatment |
|---|---|---|---|---|
| 1A | "Say you've got ₹10,000 to invest, and you're looking at two stocks." | **FSS** | Two flat building illustrations in light-blue framed cards tagged "STOCK A" / "STOCK B" (blue tags); a ₹10,000 cash bundle with a glow and sparkle in the middle | The hook names money and a choice, so both get an object. |
| 1B | "One trades at ₹100. The other trades at ₹5,000." | **FSS** (same scene) | The same two cards, now larger; yellow price pills **₹100** / **₹5000** (70px Bold) | Continuity: same objects, now with the new fact. |
| 1b-2 | "Most people… lean towards ₹100… You get 100 shares instead of just 2" | **FSS** | Left: ₹100 above a 10×10 grid of green squares; right: ₹5,000 above 2 big blue squares; a vertical divider; yellow pills under each. ⚠ Both pills say "100 Shares" (the right one should say 2) | Quantity is made literal: you can count the shares. |
| 2a | "In everyday life, price is a shortcut. A ₹500 shirt… ₹5,000 shirt. A ₹50 coffee… ₹300 coffee." | **FSS** (2 states: shirt → coffee) | Two flat shirts with grey price tags, a dashed divider, yellow pills. ⚠ Both say "Lower cost shirt". Hidden state: coffee cups ₹50 / ₹300, "Lower cost coffee" / "Higher cost coffee" | Everyday analogies are drawn. Each analogy is a state of the same frame. |
| 2-b | "Lower price usually means lower cost." | **FSS** | A seesaw: a heavy gold coin stack on the "Higher price" side, a single green ₹ coin on the "Lower price" side | The idea that price signals cost becomes a balance metaphor. |
| 3 | "But stocks are different." | **OSA** anchor left, text right | "Stocks are" (65px white) / "**different**" (186px SemiBold yellow #FFB949); faint candlestick bars behind the text; white sparkle | The turn of the argument is a punchline, so it goes big over the anchor. |
| 4a | "The price you see on the screen is not the price of the company. It is only the price of one small piece… unless you know how many pieces…" | **FSS** (states) | Centre: "ABC Limited" building in a pale circle (hidden state: a monitor showing a Kite-like quote card "ABC LTD ₹100 +2.30 (2.35%) Buy/Sell"). Left: one blue puzzle piece, ₹100, "1 Share" pill. Right: a full puzzle circle with one piece highlighted, "Many shares" pill | "Piece of the company" → a literal puzzle piece. "Price on the screen" → a screen state. |
| 5 | "This is where many new investors get misled. They confuse a low share price with a cheap stock." | **FSS** | Illustrated investor at a laptop with a scribble thought bubble, next to a falling intraday price chart card | The "new investor" persona confused. A character makes the misconception human. |
| — | "Let's take a simple example." | **Footage** | — | Transition. |
| 6a | [SHOW] "Company A has 10 lakh shares… ₹100. Company B has 1 lakh shares… ₹1,000." | **FSS** (3 states 6a→6b→6c, then 7) | 6a: two flat buildings, **Company A blue** / **Company B green**, a dashed divider. 6b: the buildings in tinted circles, "10 lakh shares" / "1 lakh shares" above, "₹100 per share" / "₹1000 per share" pills below | One scene builds fact by fact. Colour identifies the company for the rest of the video. |
| 6c | "Company A: 10 lakh × ₹100 = ₹10 crore. Company B: 1 lakh × ₹1,000 = ₹10 crore." | **FSS** (same scene) | Equations under each building; result pills **₹10 crore** (blue) / **₹10 crore** (green) | Arithmetic sits on the objects it describes. |
| 7 | "One company has more shares at a lower price. The other has fewer shares at a higher price." | **FSS** (same scene) | Pills change to "More shares / Lower price" and "Fewer shares / Higher price" with tiny icons | Same scene, conclusion text. |
| 8 | "That total value… is called market capitalisation… what the market thinks the whole company is worth" | **FSS** (2 states) | Definition state: "Market Capitalisation" (heading) + "Total shares outstanding × Current market price". Then a formula row of three yellow cards: "1,000,000 Shares outstanding" · "₹100 Current market price" · "₹100,000,000 Market cap". ⚠ The operators are "+" and "×" (should be × and =). ⚠ The numbers use Western grouping (should be 10,00,000 / ₹10,00,00,000) | A named term → definition → formula with the example's numbers. |
| 9 | "Not one share. The whole business." | **OSA** anchor centre, text both sides | Left: "Not one" / "**share**" (149px yellow); right: "The whole" / "**business**" (117px yellow); thin rule lines with dotted leaders toward the anchor | A two-part punchline split around the anchor. |
| — | "And once you see this, a lot of things in the market start making more sense." | **Footage** | — | Transition. |
| 10A | [SHOW] "Take MRF… share price over ₹1 lakh… Reliance… only around ₹1,300" | **FSS** | Two halves with a divider: yellow "MRF" pill + a tyre illustration + "Share price : ₹1,00,000+"; yellow "Reliance" pill + a refinery illustration + "Share price : ₹1,300" | Real companies are represented by **what they make** (tyre, refinery), never logos. |
| 10b | "But look at the market cap. MRF ~₹55,000 crore. Reliance ~₹18 lakh crore." | **FSS** | Left-aligned heading "Look at the market cap" (85px, underline); a bar chart: a tiny orange MRF bar vs a huge blue Reliance bar, values on lollipop markers, pills under the bars | The size difference is the point, so a to-scale bar chart is used. |
| 11a | "So the company with the much lower share price is actually many times larger…" | **FSS** | MRF card (green border) "Higher price / Smaller company" **<<** Reliance card (blue border) "Lower price / Larger company" | A conclusion card pair with a comparison operator. |
| 11b | "That's the mistake share price can make you commit." | **OSA** anchor left | "That's one" / "**mistake**" (186px light blue #81BBFF) + an orange ✗ coin | A punchline. |
| 12A | "It makes you look at the size of one slice and forget the size of the whole pizza." | **FSS** | A pizza illustration, all slices greyed (Black & White adjustment) except one in full colour | The script's own metaphor, drawn. |
| 12B | "A ₹1 lakh share does not automatically mean a massive company. A ₹1,300 share does not… smaller one." | **FSS** | Company A: a big slice + green pill ₹1,00,000 "Per share"; whole pizza centre; Company B: a small slice + ₹1,300 pill | Ties the pizza metaphor back to the numbers. |
| — | "There's another reason low-priced stocks pull people in: owning more shares feels better." | **Partly** → 12c heading | — | — |
| 12c | "With ₹10,000, buying 100 shares of a ₹100 stock feels more satisfying than 2 shares of ₹5,000" | **FSS** | Heading "Owning more shares feels better"; "High-priced stock" whole pizza in 4 slices "4 Shares", "Low-priced stock" 8 slices "8 Shares", cash bundle "Total invested amount" centre | Continues the pizza scene with a new comparison. |
| 13a | (same beat, the share counts) | **FSS** | "Total Investment ₹10,000" header pill; grid of 100 green squares "100 Shares — More shares, more satisfying" vs 2 blue squares "2 Shares — Fewer shares, less satisfying" | Reuses the counting grid from 1b-2 (continuity). |
| 13b | "The number in your holdings looks bigger. It feels like you own more." | **OSA** anchor left | "The number in your" / "**holdings**" (186px blue) + holdings icon / "looks bigger" | A punchline. |
| 14 | "But you don't own more value. You still own ₹10,000 worth." | **OSA** close-up camera 2 (anchor right) | "You still own" (90px white) + a yellow box "**₹10,000** worth" (136px ink on #FFB949 with an outer glow frame) | The key number is boxed over the anchor. |
| — | "And the market does not reward you for the number of shares… rewards you when value grows." | **Footage** | — | — |
| 15 | "If your ₹10,000 rises 10%, it becomes ₹11,000—whether 2 shares or 100 shares." | **OSA** close-up camera 2 | A table over the anchor: column headers "Low price stock" (blue) / "High price stock" (yellow); rows Share price / Shares you buy / Value after 10% rise; both ₹11,000 | A small comparison table can live on the anchor. Row labels are white on dark; cells sit in a white table. |
| — | "More shares may feel better psychologically. They do not make the investment better financially." | **Footage** | — | — |
| 16a | "Think of it like a pizza… eight slices instead of four… you don't have more pizza." | **FSS** | Two pizzas, 4 slices vs 8 slices, a dashed bracket to the pill "Same amount of pizza" | The metaphor, drawn literally. |
| 16b | [SHOW] "1:10 split… ₹2,000… ten times as many shares… roughly ₹200" | **FSS** (alt state dropped) | Green pills "Before split" / "After split"; one puzzle piece "1 share" ₹2,000 → a piece above a grid of 10 small pieces "10 shares" ₹200, in pale circles. Hidden alt: person avatars "You own 10 shares / 100 shares" | Reuses the puzzle-piece metaphor from 4a for "share". |
| 17 | "The business hasn't changed… factories, profits, debt, assets, customers, future prospects…" | **FSS** | Heading "Business is still the same"; a grey rounded panel with 6 icon circles (Factories, Profits, Debts, Assets, Customers, Future prospects) | A list of 6 nouns becomes an icon grid. |
| — | "That's why a lower share price after a split does not mean… bargain. So if share price doesn't tell you…, what does? You have to ask what you're paying for the business itself." | **Footage** | — | Transition + section question. |
| 18 | "How much does the company earn? How fast… profitable… debt… strong enough…" | **FSS** | A spiral notepad (blue spine) with 5 questions; the active one large and bold with a blue bullet, the others grey; lightbulb doodle | A question list highlighted as the voice-over reads it (the FSS version of the scroll list). |
| — | "That is what valuation is about." | **Footage** | — | — |
| 19A | "A ₹50 stock can be expensive if the business is weak or overpriced." | **FSS** | Company A building in a pale-blue circle, a blue "₹50" price tag on its side, a big orange down-trend arrow behind; caption "Weak and overpriced" | Each counter-example gets a building + price tag + trend arrow. |
| 19B | "A ₹50,000 stock can be reasonable if the business is strong, profitable, and valued sensibly." | **FSS** | Company B (grey), tag "₹50,000", green up arrow; left list "Strong / Profitable / Valued sensibly" (72px Bold) | The mirror of 19A. |
| 19c | "The number on the ticker does not decide… The business behind that number does." | **OSA** anchor centre, lower third | "Ticker price ≠ Business value" (94px Medium white) + a thin orange rule + sparkle | The thesis as an equation, as in Devolvement's "ITM option ≠ Trade ends". |
| 20 | "Don't ask, 'Which one has the lower share price?' Ask, 'What business am I actually getting for my money?'" | **OSA** anchor left (2 states) | State 1: "Which one has the" / a yellow box "lower share price?". State 2: "What **business** / am I actually getting for / **my money?**" (blue keywords) + a yellow coin | Wrong question → right question as two states of one frame. |
| — | "Because when you buy a stock, you're not buying a price on a screen…" | **Footage** | — | — |
| 21 | "…look beyond the share price — at its business, earnings, debt, growth, profitability, and valuation." | **FSS** | A mind map: yellow "Share" sun in the centre, 6 blue pills with small icons (Business, Earnings, Debt, Growth, Profitability, Valuation) linked by short blue lines | The closing list of 6 factors becomes a hub diagram. |
| — | "We've covered all of this… Fundamental Analysis module on Varsity…" | **Footage / editor end card** | — | CTA. |

### What the revision changed (rejected round → final)
The older files are a first pass the team did not ship. The changes show the channel's preferences:
- **Stock certificates → buildings and puzzle pieces.** Certificates (2, 8, 14, `massive company`) were replaced by a company building + puzzle piece for "one piece of the company". Prefer **one simple metaphor carried through the video** over a literal document.
- **A shopping-app phone mock-up (3, 4) → simple shirts and coffee with price tags.** An everyday analogy is drawn as the objects, not as an app UI. Mock UIs are kept for real Zerodha product flows (video 1).
- **A Kite-like stock list (`Stock list`) and a pie slice of a price bar (6) → dropped.**
- **Dense "Before split / After split" comparison table (11) → two simple states with one number each (16b).**
- **A margin-style OSA with bar charts on both sides of the anchor (9) → a clean OSA table (15).**
- **"Valuation" title OSA (13) and an OSA question list (12) → footage + an FSS notepad list (18).**
- **"Total outstanding shares" OST using video 1's male-anchor template** was not used here. Templates are per anchor and per set.

### What this video adds to the rules
1. **Concept scripts are FSS-heavy** (26 of 34 frames). Product scripts mix more OSA and mock-up UI.
2. **Every everyday analogy in the script gets drawn** (shirt, coffee, seesaw, pizza, puzzle), with each analogy as a state of one frame.
3. **Punchline sentences** (≤6 words, the "turn" of an argument) go **OSA with one giant keyword**: "Stocks are **different**", "That's one **mistake**", "Not one **share** / The whole **business**".
4. **Scenes:** one subject keeps its objects and colours for several frames (Company A blue / B green; pizza; puzzle pieces; the 100-vs-2 grid), and only the facts change.
5. **Real companies are shown by what they make** (MRF → tyre, Reliance → refinery), never by logo.
6. **Scale comparisons are drawn to scale** (₹55,000 cr vs ₹18 lakh cr bars).
7. **A definition comes before its formula**, then the formula is filled with the example's numbers.
8. **"Don't ask X, ask Y"** → two states of one OSA frame.
9. The scriptwriter's `[SHOW]` cues are mandatory, but they're a minimum: the designer adds graphics wherever there is an object, a number pair or an analogy.

### Errors in the shipped PSDs (feed the review checklist)
- Wrong labels copied across a pair: "Lower cost shirt" ×2; "100 Shares" ×2 where one side is 2.
- Wrong math operators ("+" in a product formula; a missing "=").
- Western digit grouping (1,000,000) in an Indian-number video; the script said "10 lakh".
- Typos: "satisying" (13a) and, in video 1, "squar off".

---

## Video 3: Specialized Investment Funds (SIFs): how to invest via Zerodha Coin (product + concept)

About 1,000 words, a third anchor (bald male, orange shirt, mic, wooden set). **20 PSDs**: 15 FSS, 4 OSA, 1 OST. The OSA/OST PSDs are **4K canvases (3840×2160)**; FSS are 1920×1080; `3b` is an extra-wide canvas built for a **horizontal pan**. The reference sheets are `sheet_v3_sifs.jpg` and `sheet_v3_hidden_states.jpg`.

New pattern: **dual delivery.** Some beats come as both an FSS and an OSA build of the same element (`3a-FSS` + `3a-OSA`, `5-FSS-OSA` + `5-OSA`). The OSA version shrinks the same cards onto the empty side of the anchor shot, so the editor can choose by pacing.

| # | Script beat | Outcome | What was built | Why this treatment |
|---|---|---|---|---|
| 1 | "Mutual fund investors looking to invest in advanced trading strategies like directional long-short equity or derivative hedging had limited options." | **1 OST**, anchor centre | "Advanced trading strategies" (215px@4K ≈ 108px@1080, white) lower third; a red/green candlestick cluster rising from behind the anchor; hidden alt: "Goal planning / Risk management / Options strategies" bubbles | The topic phrase of the hook, over the anchor, with a market motif. |
| 2a | (same beat) "directional long-short equity or derivative hedging… limited options" | **FSS** | Two icons on candlestick backdrops: an orange coin with a green up / orange down double arrow ("Directional long-short equity") and a blue shield with a chart ("Derivative hedging"); a yellow pill with a lock: "Limited options" | Two named strategies → two icons + a verdict pill. |
| 2b | "Regular mutual funds can use derivatives, but only within certain limits." | **FSS** | A big green circle "Regular mutual funds" inside a dotted yellow boundary; a "Derivatives" doodle-loop label; a yellow lock pill "Limited usage" on the boundary | "Within limits" → a literal boundary. |
| 3a | "PMS and AIFs offer more flexibility. But they also require a much higher minimum investment." | **3a FSS + 3a OSA** (both delivered) | Big blue glowing circle "Portfolio Management Services" + a small green circle "Alternative Investment Funds" (hidden states: acronyms "PMS" / "AIF"). The OSA version puts the same circles on the left of the anchor shot | Named products = labelled circles, sized by prominence. The acronym states let the label switch when the voice-over says "PMS". |
| 3b | "…much higher minimum investment. SEBI introduced Specialized Investment Funds, or SIFs, to fill this gap." | **FSS**, wide **pan** canvas | Left → right: a small purple "Mutual funds" coin → a curved arrow up to a tall gold coin stack between "PMS" and "AIF" pills ("offer more flexibility", "Higher minimum investment") → a dotted arc → "SEBI introduced **Specialized Investment Funds,** or SIFs" (blue 84px) with a money bag (hidden state) | The "gap" is shown as a journey on a pan: low entry → high stack → the new product. |
| — | "SIFs are regulated under SEBI's mutual fund framework, but give fund managers more flexibility…" | **Footage** | — | Restates the definition. |
| 4a | "Depending on the strategy, a SIF can invest in equity, debt, REITs, InvITs, and derivatives." | **FSS** | A big blue "SIF" circle at the bottom with 5 curved arrows up to 5 rounded icon cards (Equity, Debt, REITs, InvITs, Derivatives) | A list of 5 asset classes → a hub fanning out to icon cards. |
| 5 | "Fund managers may take both long and short positions, use derivatives to manage risk, or change the portfolio based on market conditions." | **5-FSS-OSA + 5-OSA** (both delivered) | Three tall white cards with icons on candlestick backdrops: "Take both long and short positions" / "Use derivatives to manage risk" / "Change the portfolio based on market conditions". The OSA version is a fanned card stack in front of the anchor, the middle card enlarged (active) | Three abilities → three cards highlighted in turn. |
| 6 | "But more flexibility also means more complexity. SIFs can be more volatile and may carry higher risk… possibility of losing money." | **FSS** | Heading "Specialized Investment Funds"; a volatile line chart (blue rising, turning orange falling); orange pills "Higher risk", "Possibility of loss" on the fall | Risk shown as a chart, not text. Generic axes ("Year"); no real data is invented. |
| — | "That is why SIFs may not be suitable for everyone." | **Footage** | — | — |
| 7 | "This is why the minimum investment is ₹10 lakh." | **OSA** anchor left, text right | "SIFs" (242px@4K white) / "Minimum investment is" / "**₹10 LAKH***" (282px@4K Bold yellow #FFC02E) | The key product number gets a big-number OSA. |
| 8a | "SIFs come in two broad structures. Interval SIFs and open-ended SIFs." | **FSS** (3 states 8a→8b→8c) | Heading "**SIFs** in two broad structures" (blue keyword); a "SIFs" hub circle splitting into a green "Interval" pill and a purple "Open-ended" pill, with one-line facts under each | A two-type classification → the same 2-branch diagram as video 1's cash/physical. |
| 8b | "Interval SIFs… listed on stock exchanges… buy or sell only during specific windows… typically twice a week…" | **FSS** (same file) | The "Interval" pill on top; Investor avatar ⇄ "BUY / SELL" ⇄ Stock Exchange building; below, a weekly calendar strip "Trading window (Set by the Fund House)" with Monday and Wednesday green, the rest grey | A rule about *when* you can trade → a week strip with the allowed days lit. |
| 8c | "Open-ended SIFs… no exchange listing… buy or redeem directly through the fund house whenever you want… continuous liquidity" | **FSS** (same file) | The same layout: "Open-ended" pill; Investor ⇄ BUY / SELL ⇄ Fund house; all 7 days green, "Continuous liquidity" | Mirror state: only the counterparty and the lit days change. |
| — | "How to invest in SIFs" (section title) | **Footage** | — | Section question. |
| 9 | "Coin currently has thirteen open-ended Direct Plan Growth schemes." | **FSS** | Heading "**Open-ended** SIF scheme list"; a white scrolling card listing all 13 scheme names with green dot bullets | A count of named items → show the list itself (designed, not captured). |
| — | "We've also added a dedicated SIF category to the Coin dashboard." | **Screen capture** (no PSD) | Coin dashboard, SIF category | A real screen. |
| — | "Lumpsum… ₹10 lakh or more… place a lump sum order on Coin: 1. Search… 2. Enter amount… 5. Pay now" | **Screen capture** (no PSD) | Coin app walkthrough | A numbered app procedure is never designed; it's recorded. |
| 10 | "On Coin, you can invest in SIFs through an AMC SIP or a Coin SIP. The rules are different for each… AMC SIP ≥ ₹10 lakh each… Coin SIP: lumpsum ₹10 lakh first, then smaller SIPs" | **FSS** | Heading "SIP Investment Requirements"; two side-by-side bordered cards with icons ("AMC SIP" calendar/document, "Coin SIP" jar of coins), each with 2 blue-bullet rule lines | Two options with rules → a two-card comparison with bullets. |
| — | "The minimum amount… decided by the AMC…" + "Create a SIP on the Coin app: 1… 5…" | **Footage + screen capture** | Coin SIP creation walkthrough | Caveat + an app procedure. |
| 11 | "Before you invest in SIFs, there is one thing you need to know. The ₹10 lakh minimum is not just the amount to get started. It also affects… if the value later falls below." | **FSS** | The **Important note** template (Bold 91px "Important note", orange box): "Before investing in SIFs / Remember this:" + body. The hidden layer shows the template is reused from another video | A caveat that sets up the next section → Important note (the third video using it). |
| 12 | "It may happen because you redeemed or transferred some units. Or… because the market value declined." | **12 OSA** anchor centre | Two white portrait cards on either side of the anchor: "You redeemed or transferred some units" (form + bank icon) / "The market value of your investment declined" (falling-chart screen icon) | Two causes → two cards flanking a centred anchor. |
| 12b | "SEBI treats these two situations differently. They are called an active breach and a passive breach." | **FSS** (states) | "SEBI treats" (blue) / "these two situations differently" heading state; a purple "SEBI" hub → green "Active breach" pill and blue "Passive breach" pill | The same 2-branch hub as 8a, reused for the next classification. |
| — | "Let us start with an active breach." | **Footage** | — | Transition. |
| 13a | "An active breach happens when a transaction made by you causes your total investment to fall below ₹10 lakh… redemption, sale, transfer, or switch." | **FSS** (13a→13b) | 13a: a blue vault/safe icon "SIFs investment" with the balance pill **₹1,200,000**; above, 4 action cards Redemption / Sale / Transfer / Switch (the first active, the rest faded) | One object (a vault = your investment) is introduced and carried through the whole section. |
| 13b | "Suppose your investment is worth ₹12 lakh and you redeem ₹4 lakh. The remaining value will be ₹8 lakh, resulting in an active breach." | **FSS** (13b → 13c) | The vault with an **odometer-style rolling number** (₹12,00,000 → ₹10,00,000 → ₹8,00,000); a dotted arc to a "Redemption" wallet card. 13c: ₹8,00,000 + "Active breach" in blue | Arithmetic over time → a rolling counter on the same object. |
| 13c | "All your units across the strategies offered under that SIF are frozen for debit…" | **FSS** | Below the vault: 4 yellow pills with locks "Strategy - A … D" | "Frozen" → locks on every strategy. |
| 14 | "You then have 30 calendar days to bring the total back to at least ₹10 lakh… additional investment under the same SIF… if not, the AMC automatically redeems" | **FSS** | The vault ₹8,00,000 with tiny locked strategy pills; a dotted arc "Additional investment" toward a calendar tile "July **30**" (hidden "30 days" label) | A deadline → a calendar tile. The vault continues the scene. |
| — | "If you restore the value within 30 days, the units are unfrozen… If you do not…, the AMC automatically redeems…" | **Footage** | — | Outcome branches are spoken; the frame stays on 14. |
| 15 | "A passive breach… falls below ₹10 lakh because of market movements… suppose you invest ₹10 lakh and it falls to ₹9 lakh because the market declines." | **FSS** | Heading "Specialized Investment Funds"; the same rising-then-falling line chart as #6, with a ₹ axis (0 → ₹1,00,000) | Market-driven decline → reuses the chart template. |
| — | "Your investment is not automatically redeemed… you cannot make a partial redemption… continue holding or redeem completely." + CTA | **Footage** | — | Rules spoken over the anchor; CTA. |

### What this video adds to the rules
1. **App procedures (numbered "tap X, then Y" steps) are always screen capture.** Neither walkthrough got a PSD. A *rule about* the product (minimums, SIP types, breach rules) does get a designed graphic.
2. **One object carries a whole section:** the vault = "your SIF investment" across 13a → 14, with only the number, locks and calendar changing.
3. **Numbers that change in the script become a rolling counter** on the same object (₹12L → ₹8L).
4. **Classifications reuse the hub → two coloured pills diagram** (8a, 12b; video 1's 13). It's a channel component.
5. **"When can you trade" rules become a week strip** with the allowed days lit.
6. **Named products and acronyms:** a circle with the full name, with an acronym state for when the voice-over switches to "PMS"/"AIF".
7. **Dual delivery (FSS + OSA of the same element)** when the beat could go either way; the OSA version shrinks the cards beside the anchor.
8. **Pan canvases** for a left-to-right story (3b).
9. **Charts without real data use generic axes** ("Year") and annotate only with the script's words (Higher risk, Possibility of loss).
10. **The Important note is a shared template** across all three videos.

### Errors in the shipped PSDs
- Mixed digit grouping inside one frame: "₹1,200,000" next to "10,00,000" / "8,00,000". Always use Indian grouping (₹12,00,000).
- "No exchange listing required (NSE / BSE)": the bracket contradicts the sentence. Write "Not listed on an exchange".
- Script typo carried in ("Zerodha customers **and** invest…"). Don't copy script typos onto screen.

---

## Cross-video summary (feeds SKILL.md)

| | V1 Devolvement (product mechanics) | V2 Share price (pure concept) | V3 SIFs (product + concept) |
|---|---|---|---|
| Frames | 22 (9 FSS, 13 anchor) | 34 (26 FSS, 8 anchor) | 20 (15 FSS, 5 anchor) |
| Typical anchor uses | lower-third equations, side-panel lists, notes | giant-keyword punchlines, a small table | big number, flanking cards, OST topic |
| FSS style | mock Kite UI, charts, diagrams | illustrated metaphors (pizza, puzzle, buildings) | hubs, icon cards, a vault object, a calendar |
| Screen capture | Kite option chain / Info widget / margin calculator | none | Coin dashboard + 2 app walkthroughs |

---

## Video 4 — Why do stock prices move every second? (concept + Kite UI; storyboarded by the team)

The first video with a **team storyboard (SB doc)**. It has 10 numbered SB items and **8 PSDs** (1, 2, 3, 4, 5, 7, 8, 10). Items 6 and 9 are marked "Repeat", so no new file was made. The presenter is the V1 male anchor. All UIs are rebuilt as vector Kite mock-ups with generic tickers (XYZ, ABC…), even though the SB references a real HDFC Bank screenshot.

| SB # | SB code + brief | PSD built | What the designer did with the brief |
|---|---|---|---|
| 1 | FSS – "Show price fluctuation of a stock in Zerodha UI · Ref Img" (hand sketch of a list with XYZ ₹100) | `1- FSS` | Phone with a Kite watchlist (NIFTY/SENSEX header, ~17 rows with generic tickers). The XYZ row is popped out as a wider highlighted card showing 100.0. The sketch was used for layout, and the UI was rebuilt. |
| 2 | OST – "Pop-up Callout: No new announcement / No change in profits / No change in the business" | `2-OSA` | Built with the same side-panel scroll list as V1 (close-left anchor, active line yellow 78px, others white 46px). The SB said OST; the designer chose the list template. |
| 3 | FSS – "Show something similar · Keep 'Stock Market' as header" (auction cartoon ref) | `3-FSS` | Header "Stock Market". Buyers (green) with price chips ₹101/₹102/₹100 and sellers (orange) with ₹103/₹102/₹104; ₹102 shown bigger on both sides; dashed arrows into a blue ✓ circle, "Trade executed". The cartoon was redrawn in the flat avatar style. |
| 4 | FSS – "Header - Order Matching Mechanism" (sketch: Buyer bid / Seller ask / Trade status table) | `4- FsS` | **Merged with SB 5's screenshot:** a phone showing Kite market depth for XYZ. Bids 99.00/99.50/99.80/100.00 and offers 100.50/100.80/100.10/100.00 come from the script's example. Tags with dotted leaders sit outside the phone: No trade ×3, Trade executed. The header was dropped because the UI carries the meaning. The phone is cropped at the bottom of the frame to zoom into the depth. |
| 5 | OST & Screencapture – "Definition box – Order book: …" + Kite depth ref "replace the numbers with what's given in example" | `5-OST` | Definition box over the anchor: an icon in a circle, "Order book:" (63px), and the definition (45px white). The screenshot part went into PSD 4. |
| 6 | FSS (Repeat) – "Continue the animation and highlight as per VO" | — | No new file; PSD 4 is reused and animated. |
| 7 | OST – "Text pop-ups · Header: What moves stock prices? + 10 bullets" | `7- OST` | Side-panel scroll list: header "What moves **stock prices?**" (yellow keyword), 10 items with the active one yellow 57px. All 10 bullets are shown, with no trimming. |
| 8 | OST – "Every price reflects the latest trade between a buyer and a seller." | `8-OST` | Lower third on the wide-centre shot, with "latest trade" and "a buyer and a seller" in yellow. A big blue four-point sparkle sits over the text, probably an animation frame. |
| 9 | FSS (Repeat) – "Repeat this animation" | — | Reuses PSD 1. |
| 10 | FSS – "Show this on screen – highlight lines of the chart as per VO 'Tick'" (Kite chart screenshot) | `10- FSS` | A Kite desktop chart window rebuilt as vector (top bar, Chart / Option chain / Fundamentals tabs, BUY/SELL, price axis ticks). Orange glowing dots on 5 points of the line mark the "ticks". |

### Rules this adds
1. The SB is the source of truth for **which** beats get graphics and their numbers. The designer still decides **how**, and may merge two SB items into one stronger frame.
2. A reference image or sketch gives content and layout only. Rebuild it in house style, with generic tickers and the script's numbers.
3. "Repeat" means no new file.
4. Recurring OST briefs (pop-up callout, text pop-ups) become the side-panel scroll list. A definition box is an icon + "Term:" + definition.
5. FSS headings in V4 ran 91px ("Stock Market"). The channel decision is still **72px**.

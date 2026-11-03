# Varsity Hindi IP (Technical Analysis series): script → storyboard → final graphic

**Status:** 5 videos analysed (Technical Analysis module, Ep1–5). The `varsity-hindi-graphics` skill is built from this file. This is the working file the skill will be built from once all 4 are in.

**Language rule:** the VO and script are in **Hinglish (Hindi written in Roman script)**, but **every word on screen is English**. On-screen copy is never a transliteration of the script. It is a short English rewrite of the idea, often shorter than an English script would give:
- "Kis level par stock ko kharidna ya bechna hai" → pillar label **Entry & Exit Price**
- "Company ki financial health aur intrinsic (asli) value ko evaluate karta hai" → table cell **Company's financial health / Intrinsic value**
- "Yeh hamesha long-term investments (months to years) ke liye optimize hota hai" → **Long term / Months to years**
- Questions spoken in Hindi become English title stacks ("What does this / **Chart actually tell you?**")
- Things-to-remember bullets are rewritten in English, each starting with a **bold lead term** ("**Bar Charts** offer less visual clarity…")
- Script English terms (OHLC, Bullish, Stoploss, Entry, Target) are used as-is.

The storyboard is the bridge: the storyboard writer has already done the English rewrite for most beats, and the designer copies it. When the storyboard gives no English copy, write it in the same short, label-style English.

Storyboard shorthand (same as Varsity English): **OSA** = graphic over the anchor shot; **OST** = on-screen text/title over the anchor; **FSS** = full-screen slide; **Badger** = chapter/episode cut-in; **Roto Bigtext** = giant title with the anchor rotoscoped in front of or behind the letters; **"Highlight / animate as per VO"** = one master frame plus hidden states; **Screen capture** = footage of the real Kite/website; **CTA** = edit template.

---

## Video 1: What is Technical Analysis? (≈6:40, 12 PSDs)

| TS | Script cue (Hinglish, paraphrased) | SB code | Outcome | What was built |
|---|---|---|---|---|
| 0:01 | "Do sawal aayenge: kis price par buy, kis price par sell" | OSA, "Line chart (Zerodha UI)" | Graphic `0.01` | FSS light-sky: browser window with a **mock Kite chart** (toolbar, left side panel, Kite chevron top-right, "XYZ Company", blue line chart, bold Y axis, dotted LTP line with blue LTP label). **Buy** and **Sell** flag tags at the trough and peak. The SB's "Buy Price? / Sell Price?" became two small flags on the chart, not big text |
| 0:17 | "rewarding trade, unnecessary losses na ho" | OSA, "green for profit, red for loss" | Graphic `0.17` | Same chart window, new data; a **trade-position overlay**: green target zone + green "Target 21.0 (1.56%)" pill, red stop zone + red "Stop 7.0 (0.52%)" pill, centre pill "Opened P&L / Risk/Reward Ratio 3", yellow price tags on the axis |
| 0:24 | "Technical analysis… entry/exit… risk, reward, trends, sentiment" | Roto Bigtext + callouts | Graphic `0.24` (3 states) | State 1 (hidden group "Part 1 Typo"): giant **Technical** (white) / **Analysis** (yellow) over the main cam, magnifying glass, bottom vignette. State 2: the 0.17 chart relabelled **Target / Entry / Stoploss** (words + prices). State 3: a cream **"Market Sentiments" meter card** slides up over the chart: gradient bar, triangle pointer, "Fearful ↔ Optimistic". One file, three VO beats |
| 0:37 | reveal upcoming episodes | "Add in SOP" | Edit | Series template, not designed |
| 0:39 | — | Badger | Footage | |
| 0:43 | "Sabse pehle… TA kya hai aur FA se alag kaise" | OST | Graphic `0.43` | Main cam, two title stacks either side of the anchor: "What is / **Technical** / **Analysis?**" and "**Technical** [vs chip] **Fundamental** / **Analysis?**"; keyword word in yellow; magnifier props; floating paper/chat doodles |
| 0:49–1:18 | Smartphone analogy: research every spec vs check best-sellers | FSS animation brief (character, store, clock, laptop) | Graphic `0.49` (4 states in one PSD) | (a) "part 0": character with a phone thought-bubble. (b) "Part 1": AI-rendered **blue phone store**, header tab **Approach 1**, yellow character pointing at phones. (c) "Part 2": side cam, anchor left, three **phone outlines** (Phone X / Y / Z yellow pills) listing Processor, Camera, Battery, RAM & Storage, Display, Build: the 6 specs from the SB, filled with realistic values. Hidden clock group for "time-consuming". (d) "Part 3": night-desk scene with a **mock e-commerce page** (search bar, product card, ★4.5 (1,693), "-27% ₹94,999", "100K+ bought in this month", Best Seller tag, Buy Now) + header tab **Approach 2** → **Technical Analysis**; caption "If so many people are buying it, it must be good." |
| 1:46 | FA definition | reveal approach 1 = FA | Graphic `1.46` | Side cam, anchor left, dark right half. Header tab **Fundamental Analysis**; **amber glass capsule** with the one-line English definition (from the SB, not the script); yellow character holding a magnifier over it; white tiled floor strip at the bottom. Hidden state = TA definition |
| 1:57 / 2:10 | TA definition | reveal approach 2 + OST definition | Graphic `2.10` | Same layout without the capsule: title stack **Technical** (white) / **Analysis** (yellow) + the definition as plain white text. The SB had two TA definitions (1:57 and 2:10); one frame was built |
| 2:25 | "market participants ke actions charts par… patterns" | OSA, "highlight multiple patterns" | Graphic `2.25` | FSS: header tab **Technical Analysis** above the Kite window; line chart with **dashed range boxes** around three consolidation zones |
| 2:39 | "technical analyst… point of view develop karna" | OSA, character at desk + thought bubble | Graphic `2.39` | FSS AI scene: night home office, 3 monitors (Market Overview list with XYZ/ABC/DEF/GHI, Support & Resistance, Volume Profile); character from behind in a chair; cloud thought bubble "Develop a point of view" |
| 2:52–4:35 | FA vs TA, 6 rows | FSS table | Graphic `2.52` | Glass browser window over a blurred anchor: 3-col table (Feature / FA / TA), bold header row, thin row rules, bold lead line per cell; **magnifier over the row being read**. Copy is the SB's English condensation of the Hinglish table |
| 4:35 | repeat 0:37 | | Edit | |
| 4:44 | CTA to FA playlist | CTA | Footage/edit | |
| 5:02–5:42 | 4 pillars of a trade | OSA, "ref img, will highlight" | Graphic `5.02` | Side cam; header tab **4 Pillars of Trade**; four white **3D pillars** on a tiled floor, label card on each; the active pillar card is **yellow**, the rest white |
| 5:42 | Things to remember (5 points) | FSS/OSA | Graphic `5.42` | FSS light: big white swoosh; coral **megaphone** bottom-left; title "Things to / Remember" with coral left bar; numbered list, bold lead term + regular rest |
| 6:34 | next chapter name | reveal | Edit | Series template |
| — | "Ab yeh debate krna bekaar hai…", "Inn sab ko aane vali videos mei…", conclusion | — | Footage | Bridges and wrap-up |

## Video 2: Charts & Candlesticks (≈11:00, 18 PSDs)

| TS | Script cue | SB code | Outcome | What was built |
|---|---|---|---|---|
| 0:02 | "Iss chart ko dekho" | OSA, line chart | Graphic `0.02` (hidden state) | Side cam, dark right half with a faint candlestick chart rising from the bottom |
| 0:17 | three questions | OST, continue | Graphic `0.02` | Three stacked question pairs: small white lead ("What does this") + yellow bold line ("**Chart actually tell you?**"); the current question bright, the next ones faded (stepped with VO) |
| 0:27 | chapter name | Badger | Footage | |
| 0:31–1:01 | OHLC = Open/High/Low/Close; Close matters most | OSA, Big Text "OHLC", highlight C | Graphic `0.31` | Roto bigtext over the main cam: small "Candlesticks" + giant yellow **OHLC**, with **word chips** pinned to the letters: Open (white), High (green), Low (coral), Close (white). Candlestick chart faint in the background |
| 1:15–1:47 | open/high/low/close of a day, close vs open | OSA, highlight per VO, repeat 0:31 | Graphic `1.01` (states Day 1 / Day 2) | FSS light: Kite window, **SBI**, intraday 09:15–15:15 line for two days (red and green), white Open/Close label boxes, green High and coral Low tags; magnifier |
| 1:26 | "Line chart… jaise school maths" | Header, line chart | Graphic `1.26` | FSS: header tab **Line Chart** above a gridded generic line chart with green end dots. ⚠ The axis (1800–2000, 0–110,000) was copied from the SB's reference image, not from the script |
| 1:52–2:07 | SBI 5 closes; line up = rise, down = fall | Header + "highlight closing prices" | Graphic `1.52` (+ hidden "Chart 1 copy") | Header tab + Kite window, SBI line through 5 points, each with a **yellow value tag** and dashed drop lines to the X axis (1–5). ⚠ Built values 1,070 → 998 (falling); the script says 1010, 1023, 1045, 1040, 1050 and the SB says something else again. **Always use the script's numbers** |
| 2:24 | "Zerodha Kite pe… charts" | Screen capture, CTA | Footage | Real Kite capture |
| 2:40 | "school wala bar chart se alag" | Header | Graphic `2.40` | Side cam: header tab **Bar Chart** + a plain school bar chart (A–E, green/coral gradient bars, axis arrows) to show what it is *not* |
| 2:49–3:27 | bar components; O65 H70 L60 C68 | highlight + "use same graph" | Graphic `2.49` | Side cam: header tab + a **line-drawn OHLC bar** (green), left tick Open, right tick Close, dashed leaders to a 60–70 scale, "Time" axis, green **Bullish** pill |
| 3:49–4:54 | left tick below right tick = bullish (46/51/45/49), opposite = bearish (74/76/70/71); range | OSA "animate ticks", 2 examples | Graphic `3.49` (+ Bearish state), `4.54` | Same diagram system: bullish bar in **blue** with "Open: ₹46"; bearish state; `4.54` repeats with "Example 1" label and Part 2 states |
| 5:16 | "bohot saari bars… patterns spot karna mushkil" | OSA, "make 3 different charts" | Graphic `5.16` (states Reliance / SBI / HDFC) | FSS: Kite window with an OHLC **bar chart**; three stock states, one per name, as the SB asked |
| 5:38 | Japanese candlestick chart | Header | Graphic `5.38` | Kite candlestick chart (SBI) sliding in over the header tab and anchor: a transition frame |
| 5:48 | "default option" | Screen capture | Footage | |
| 5:58–6:48 | bullish/bearish colours; body, upper/lower shadow | OSA, legend + highlight segments | Graphic `5.58` | Side cam: header tab **Japanese Candlestick Chart**; green and coral candle side by side, labels Open/Close/High/Low, "Central Body", "Upper/Lower Shadow"; **Bullish** green and **Bearish** coral pills. ⚠ "Uper Shadow" typo shipped |
| 6:48–7:16 | O62 H70 L58 C67 (+ continue with other values) | OSA | Graphic `6.48` (states) | Same candle-diagram system with scale and dashed leaders; Bullish/Bearish states |
| 7:51 | O456 H470 L420 C435 | OSA | Graphic `7.51` | Bearish candle diagram, "Example" label, coral Bearish pill under it |
| 8:25 | Exercise: 3 days of OHLC | "Typography, don't make candlestick" | Graphic `8.25` | Header tab **Exercise** + a dark glass rounded card; bold "Day 1:" lines, values separated by thin vertical bars |
| 8:44 | comment below | CTA | Edit | |
| 8:50 | long body = strong, short body = weak | highlight 2 candles, callouts | Graphic `8.50` | Side cam: two green candles, labels **Strong Signal** / **Weak Signal**. The SB asked for red+green callouts on a real chart; the designer simplified to one clean diagram |
| 9:06 | split screen bar vs candle | Split screen | Edit | Not designed |
| 9:20 | repeat 5:48 | | Footage | |
| 9:39 | Things to remember (6 points) | OSA/FSS | Graphic `9.39` | Same template as Ep1 5.42. ⚠ numbering "5." used twice shipped |
| 10:47 | timeframes (1 month, week, day, hour) | Screen capture | Graphic `10.47` | Built as a **mock Kite chart with the interval dropdown open** (Seconds / Minutes / Hours / Days, "01 Day" highlighted yellow) instead of a screen capture |
| 10:56 | next chapter | Reveal | Edit | |

## Video 3: Timeframes (≈7:20, 15 PSDs)

Nearly the whole video is mock Kite charts. **Every SB "Screen capture" except the 1-min/10-min dropdown (4:54) was rebuilt as a mock chart.**

| TS | Script cue | SB code | Outcome | What was built |
|---|---|---|---|---|
| 0:01 | "sahi time frame choose karna" | OSA, highlight timeframes | Graphic `0.01` | FSS: header tab **Timeframe** + Kite window with the **interval dropdown open** (Seconds / Minutes / Hours / Days, "01 Month" in yellow). Reuses the Ep2 10.47 frame |
| 0:11–0:27 | "pichle video ki candle (OHLC) ek din ki thi… month, week" | OSA, highlight Month/Week | Graphic `0.11` | Side cam: candle anatomy **reused from Ep2 5.58** (header "Japanese Candlestick", one green candle, Bullish pill) |
| 0:31 | "Timeframe ka seedha matlab…" | OST + definition | Graphic `0.31` | Main cam, roto big text: "What is a" (white, light) / **Timeframe?** (giant yellow), faint candles behind. The SB's English definition was left to a separate beat/edit |
| 0:39 | split: line chart vs one candle for the whole day | FSS, "Screen capture, ref img" | Graphic `0.39` (Part 1–3) | Rebuilt as a mock: header tab **Monthly Timeframe**, Kite window of monthly candles with a dashed box on one month, plus a side card **"1 Month Candle"** (candle + Open/Close/High/Low values). ⚠ The boxed candle is red but the card shows a green candle with Close > Open: the card must match the boxed candle |
| 1:03 | monthly OHLC: first day open, month high/low, last day 3:30 close | OSA | Graphic `1.03` (+ Part 1) | Weekly candles labelled Week 1–4 with an intraday line under them; **Open / High / Low / Close tags** on the points that make the month's candle; X axis "Week 1 09:15 … Week 4 03:30" |
| 1:38 | "ek saal mein sirf 12 candles… 2011 se 2025" | OSA, highlight 12 candles | Graphic `1.38` (+ "Montly" state) | Kite window 2011–2025, **dashed box around one year** of candles. ⚠ Header tab says **Annual Timeframe** for a monthly chart, and the state group is spelt "Montly" |
| 1:57–1:58 | "kab bada bull run aaya aur kab market gira" | OSA, arrows on the bull run and the fall | Graphic `1.58` | Kite window (HDFC Bank 2016–2023) with Open/High/Low/Close tags; a **3D purple bull** bottom-left, **3D coral bear** bottom-right, flying cash notes. ⚠ "HFDC Bank" typo shipped |
| 2:04–2:42 | weekly: Monday open, Friday 3:30 close, holiday → Thursday; 52 candles | Weekly timeframe, callout "National Holiday" | Graphic `2.04` (states Weekly / 2.42) | Same monthly-chart + "1 Month Candle" card system with a different month boxed (Aug). ⚠ Header still "Annual Timeframe"; the Friday/holiday callout is not in the static PSD |
| 2:49 | weekly is for long-term investors + active traders, 1–6 months | OST callout | Graphic `2.49` | Same chart; **callout pill bottom-left** (white, coral outline): "Best for identifying medium to long-term market trends" + "Holding Period / 1 Month – 6 Months". The SB copy, verbatim |
| 3:00–3:35 | daily: one candle per day, 252 a year; swing traders | OSA, header Daily Timeframe + callout | Graphic `3.00` (states Daily Timeframe / Annual) | Kite window 2024–2026 daily candles; hidden header **Daily Timeframe** state; hidden "252 Candlestick" label |
| 3:40–4:26 | intraday: 30/15/5-minute candles from 9:15 | OSA/FSS, highlight time on timeline | Graphic `3.40` (states 30 / 15 / 5 min) | Header tab **Timeframe**; candles on a 09:15 → 10:10 axis, the first candle(s) in a **dashed box**; one heading state per interval |
| 4:54 | "1-minute ya 10-minute chart" | Screen capture, highlight dropdown | Footage | Real Kite capture |
| 5:04 | multi-timeframe analysis definition | OST | Graphic `5.04` | Side cam: **Multi-Timeframe Analysis** (yellow, bold) + one-line English definition in white |
| 5:14–5:43 | Zomato: 30-min up, daily down, weekly up | Screen capture ×3 | Graphic `5.14` (states 30 Min / Weekly / Timeframe) | Rebuilt as a mock Kite chart of **"Eternal"** (Zomato's listed company name, not the brand the VO says), a dashed boundary around the plot, one state per timeframe |
| 5:57 | no single right timeframe (3 points) | OST, header + bullets | Graphic `5.57` | Side cam: yellow title **Understanding Timeframes** + 3 bullets with small **yellow triangle markers**; the current bullet white, later ones faded |
| 6:25 | Things to remember (5 points) | FSS/OSA "Key Takeaways" | Graphic `6.25` | Same megaphone template; heading **Key Takeaways** (the SB's word); plain sentences, no bold lead terms this time |
| 7:18 | next chapter: Single Candlestick Patterns | reveal | Edit | |

## Video 4: Single Candlestick Patterns (≈9:40, 18 PSDs)

Two alternating modes: **concept** beats over the side cam inside a **dark glass panel** (shape of the pattern), then **evidence** beats as FSS mock Kite charts of a real stock with the pattern boxed and labelled.

| TS | Script cue | SB code | Outcome | What was built |
|---|---|---|---|---|
| 0:06 | chapter name | Introduce chapter | Edit | Series template |
| 0:10 | single candlestick pattern = one candle signals psychology/reversal | OST definition | Graphic `0.10` | Side cam: header tab **Single Candlestick Pattern** + the SB's English definition in white bold + one green candle under it |
| 0:18 | "Marubozu ka matlab bald" | Header + OST | Graphic `0.18` | Header tab **Marubozu Candle**; "In Japanese" (light) / **Marubozu means "Bald Head"** (big bold white) |
| 0:27 | candle with no shadows/wicks | Header | Graphic `0.27` | Same header; **dark glass panel** with a mini candle chart; one wickless candle in a dashed box with a thin curved leader → "Bullish Marubozu Candle" |
| 0:53 | bullish: Open = Low, Close = High; bearish: Open = High, Close = Low | OSA, highlight | Graphic `0.53` | Header tab **Marubozu**; dark glass panel; two wickless candles with corner labels "Close = High / Open = Low" and "Open = High / Close = Low"; big **Bullish** green and **Bearish** red pills below |
| 1:04–1:45 | real-world small wick; continuation vs reversal | FSS, screen capture + ref chart | Graphic `1.04` (Part 1/2) | FSS mock Kite: **HDFC Bank**, an **OHLC readout** in the chart header ("O: … H: … C: … L: …"), "Bearish Marubozu candle" leader label, **Stoploss** and **Entrylevel** leaders. ⚠ Readout values are impossible (H 1048 < O 1062; L 1068 > H) |
| 1:52 | Bajaj Finserv daily: open = low, close = high | Screen capture, highlight Day | Graphic `1.52` | Mock Kite **BAJAJFINSV**, readout line, dashed box + "Bullish Marubozu candle". ⚠ Readout (C 1044 < O 1060) contradicts "bullish marubozu" |
| 2:05 | 5-minute intraday: first 5-min candle a long green bar | Continue, highlight 5 min | Graphic `2.05` | Same window with the **interval dropdown** open, "05 Minutes" in yellow; 09:15 → 10:00 axis; dashed line at the opening low with a yellow price tag |
| 2:23–2:52 | paper umbrella: small body, long lower wick, wick ≥ 2× body | OST + split "pattern vs umbrella" | Graphic `2.23` (Part 1) | Side cam: header tab **Paper Umbrella Pattern**; subtitle "Body to wick ratio ≥ 2"; dark glass panel: candle (Body / Wick labels) **=** a blue umbrella illustration |
| 3:17–3:55 | hammer after downtrend, Bank Nifty example | OSA continue, Bank Nifty chart | Graphic `2.58` (+ Hanging man state) | FSS mock Kite **Bank Nifty**: faded candles except the boxed **Hammer** with leader label |
| 4:16–4:58 | hanging man after uptrend; confirmation, stoploss | "Aman bhai chart banana hai", highlight OHLC | Graphic `3.55` (+ part 1) | Mock Kite with the boxed hanging man at the top of an uptrend, intraday axis. ⚠ Ticker cut to "BANKNIF" |
| 5:39–6:16 | inverted hammer & shooting star | OSA header | Graphic `5.39` | Side cam: header tab **Inverted Hammer and Shooting Star**; dark glass panel with two mini charts, each with a dashed box on the pattern and a white label |
| 6:16–7:23 | psychology; Piramal shooting stars; M&M inverted hammer | Animate + ref charts | Graphic `7.23` (+ Shooting Star state) | Mock Kite **M&M**: downtrend, boxed inverted hammer, leader label |
| 7:40–8:10 | Piramal: shooting star at the top; sell below low, stoploss = high | OSA, "Aman - need to make this" | Graphic `8.10` (+ Inverted Hammers state) | Mock Kite **PIRAMAL**: bull run then fall; dashed leader lines to **High** and **Stoploss**. ⚠ Header "Shooting Stars" (plural); X axis is intraday times for a "daily chart" |
| 8:20–8:23 | Doji = indecision | Header + OST | Graphic `8.20` | Side cam: header tab **Doji** + "Doji means market indecision" + dark glass panel: green and red doji crosses labelled "Bullish Doji" / "Bearish Doji" |
| 8:26–9:05 | doji after a trend → reversal; wait for the next candle | Animate, highlight doji then next candle | Graphic `8.47` | Mock Kite **XYZ Stocks**: boxed doji at the bottom of a downtrend, label "Dragonfly Doji" (a term the script never uses) |
| 9:10–9:21 | Varun Beverages: some dojis reversed, some continued | FSS, highlight dojis | Graphics `9.10`, `9.21` | Two mock Kite charts **VBL**, each with one boxed doji: one where the trend reversed, one where it continued |
| 9:28 | Things to remember (6) | OST/FSS Key Takeaways | Graphic `9.28` | Megaphone template, heading **Key Takeaways**, SB copy verbatim. ⚠ "5." used twice again |
| end | next chapter: Multiple Candlestick Patterns | reveal | Edit | |

## Video 5: Multiple Candlestick Patterns (≈9:40, 15 PSDs)

Same two-mode rhythm as Video 4: a **concept panel** over the side cam for each pattern's shape, then a **mock Kite chart of a real stock** with the pattern boxed, then entry/stoploss leaders when the VO gives the trading rule.

| TS | Script cue | SB code | Outcome | What was built |
|---|---|---|---|---|
| 0:06 | multiple candlestick patterns | OSA "show these candles" | Graphic `0.06` | Side cam: header tab **Multiple Candlestick Patterns**; dark glass panel with three mini pattern groups captioned "Morning Star / Bullish", "Evening Star / Bearish", "Piercing Pattern" |
| 0:21 | link to single-candle episode | CTA | Edit | |
| 0:28 | engulfing = "dhak lena"; bullish and bearish | Header | Graphic `0.28` | Header tab **Engulfing Pattern**; panel with two 2-candle diagrams, each candle labelled Open/Close/High/Low, captions "Bullish Engulfing" / "Bearish Engulfing" |
| 0:42 | bullish engulfing after a downtrend; Day 2 opens below Day 1 close and closes above Day 1 open | Header + animate, mark OHLC | Graphic `0.42` | Header tab **Bullish Engulfing**; panel with two mini trend charts (downtrend → bullish engulfing; uptrend → bearish engulfing), the pair boxed, OHLC labels |
| 1:27 | Reliance daily example; aggressive vs conservative entry; stoploss = Day 2 low | FSS, callouts entry & stoploss | Graphic `1.27` | Mock Kite **Reliance**: boxed pattern + leaders **Entry**, **Stoploss**, **Potential Entry**, **Candlestick Closure Confirmation**. ⚠ Also labelled "Hammer Candlestick" (wrong pattern) and the axis is intraday times for a "daily chart" |
| 2:05–2:33 | bearish engulfing at a top; Nifty 50 example; stoploss = Day 2 high | FSS | Graphic `2.33` | Mock Kite **Nifty 50**: inverted-V trend, boxed pair at the top, leaders **Stoploss** and **Entry** |
| 3:02 | piercing: Day 2 gap down, closes above 50% of Day 1 body | OSA header | Graphic `3.02` | Header tab **Piercing Pattern**; panel: red then green candle with a dashed **50%** line through Day 1's body |
| 3:52 | continue | continue | Graphic `3.52` | Mock Kite with "Bullish Engulfing" header (reused from 1.27). ⚠ Ticker "Reliance" but the Y axis is 31,500–33,500 (Nifty-level prices copied from another frame) |
| 3:59–4:09 | dark cloud cover = inverted piercing | OSA header + continue | Graphics `3.59`, `4.09` | Panel: green then red with the 50% line, labels "Bullish / Bearish" (better: Day 1 / Day 2); FSS chart **XYZ Stock** with the pair boxed at a top. ⚠ Same copied 31,500–33,500 axis |
| 4:46 | Havells: dark cloud cover at the top, then a piercing pattern that failed | Header both, ref img | Graphic `4.46` | Mock Kite **Havells**: two boxes, labels **Dark cloud cover** and **Pattern failed**: the "patterns can fail" lesson is shown, not just said |
| 5:55 | morning star: long red, gap-down doji/spinning top, long green | OSA header ("keep doji day 2") | Graphic `5.55` | Panel: red / doji cross / green with Open/Close labels |
| 6:58 | IndusInd Bank example | continue, replace chart | Graphic `6.58` | Mock Kite **Indusind Bank** (sic): U-shaped trend, 3 candles boxed with tiny **Day 1 / Day 2 / Day 3** labels |
| 7:18 | evening star | OSA header | Graphic `7.18` | Panel: green / small red / red |
| 8:00 | example | highlight with ref | Graphic `8.00` | Mock Kite **SBI**: inverted-V, 3 candles boxed with Day labels |
| 8:18 | Things to remember (5) | OSA/FSS Key Takeaways | Graphic `8.18` | Megaphone template, SB copy verbatim |
| 9:31 | next chapter: Support & Resistance | reveal | Edit | |

---

## What decides graphic vs footage (patterns so far)

1. **Anything on a price chart is a graphic, built as a mock Kite chart** in a browser window, never a real screenshot: generic names (XYZ Company) or real tickers (SBI, Reliance, HDFC), the Kite chevron top-right, toolbar placeholders. The only true screen captures are "go do this on Kite" CTAs (2:24, 5:48).
2. **Every number the VO says goes on screen**: prices as tags on the chart, OHLC as a labelled diagram with a scale, exercises as a typography card.
3. **Every new concept gets a header tab** (white box, "–×" window tab, blue base bar): Approach 1, Line Chart, Bar Chart, Japanese Candlestick Chart, Exercise, 4 Pillars of Trade.
4. **Explainer diagrams sit over the side cam** (anchor left third, right two-thirds darkened to near-black): bars, candles, definitions, pillars. **Chart windows, tables and things-to-remember are FSS** on the light-sky background.
5. **Section openers are title stacks or roto big text** over the main cam: small white lead words, keyword in bold **yellow**, magnifier prop (Ep1 0.24/0.43, Ep2 0.31).
6. **Analogies get illustrated scenes**: AI-rendered environments (phone store, night desk) with the yellow stick character composited in; product/web UI is mocked (e-commerce card) not screenshotted.
7. **One PSD per beat cluster, many hidden states.** "Highlight / continue / repeat as per VO" = new state in the same file (Ep1 0.24, 0.49; Ep2 1.01, 3.49, 5.16).
8. **Footage only** for: Badger, CTA/playlist plugs, upcoming-episode/next-chapter reveals (series template), screen captures, rhetorical bridges and the conclusion.
9. **The designer trims or simplifies the SB when it would clutter** (Buy/Sell as flags, strong/weak signal as two candles, one TA definition instead of two).
10. **Failure modes to prevent in the skill:** numbers copied from the SB's reference images instead of the script (Ep2 1.26, 1.52); typos ("Uper Shadow", "HFDC Bank", duplicate "5."); wrong header tab for the content ("Annual Timeframe" on monthly/weekly charts, Ep3); a detail card that contradicts the highlighted candle (Ep3 0.39); inconsistent ₹ on prices (only "Open: ₹46" has it).
11. **"Screen capture" in the SB usually becomes a mock Kite chart** (Ep2 10.47; Ep3 0:39, 5:14–5:43). It stays real footage only when the point is a specific Kite UI action (a dropdown, a "do this on Kite" CTA).
12. **Frames are reused across episodes.** The interval dropdown (Ep2 10.47 → Ep3 0.01), candle anatomy (Ep2 5.58 → Ep3 0.11) and the Things-to-Remember template recur. In the skill, keep a component library: Kite window, header tab, OHLC candle/bar diagram, interval dropdown, detail side card, callout pill, title stack, megaphone list.
13. **Highlighting on a chart is a dashed box** around the candle(s) or period being discussed (one month, one year of candles, the first 15-min candle), plus Open/High/Low/Close tags (white = open/close, green = high, coral = low) where the VO names them.
14. **Callout copy comes from the SB verbatim** when the SB gives English text (Ep3 2.49, 5.04, 5.57, 6.25).
15. **Real stocks are named by their listed name:** Zomato → "Eternal", SBI, HDFC Bank, Reliance. Generic examples use "XYZ Company" / "XYZ Stocks".
16. **Pattern episodes alternate concept → evidence → rule** (Ep4, Ep5): (a) side cam + header tab + dark glass panel showing the pattern's shape; (b) FSS mock Kite chart of the stock the VO names, pattern in a dashed box at a real top or bottom; (c) same chart with Entry / Stoploss leaders when the VO gives the trading rule. "Continue the same animation" = new state of the same chart, not a new layout.
17. **Prices on a mock chart must match the stock's real price level**, and every frame of the same stock uses the same axis. Ep5 copied a Nifty-level axis (31,500–33,500) onto Reliance and XYZ.
18. **Label the right pattern.** Ep5 1.27 labelled a hammer inside a bullish engulfing frame, and 3.59 used "Bullish/Bearish" where "Day 1/Day 2" was meant.
19. **Daily-chart examples need date axes**, not intraday times (Ep4 8.10, Ep5 1.27).

## House style observed (to confirm against videos 3–4)

> **Superseded on colour:** the team's rule is that green/red appear only on candle and bar bodies, never on boxes. Where the finals below tinted pills, tags or zones green/red, the skill makes them neutral. The palette in `storyboard_rules.md` §5 is authoritative.

- **Font:** Inter only. Titles Bold; header tabs Bold black; body Regular/Medium; chart axes Inter Bold (Ep1) or Regular (Ep2).
- **Colours:** keyword yellow `#F4D006`; active/selected pill amber `#F0B32A`; header-tab base bar blue `#4CA3F8`; bullish/profit green `#A5CC65` (zone `#E4F0D0`); bearish/loss coral `#F47964` (zone `#FCD7D0`); chart line blue; window traffic lights `#EF2A41 #FEBE09 #01D73D`; things-to-remember accent coral `#F67964`.
- **FSS background:** near-white centre `#FAFCFD` fading to pale blue `#D2E4F0` at the edges, with fine **wavy line-art** at the left and right edges.
- **Constant chrome:** top-left Varsity "eye" capsule (outlined pill with yellow dot) at ~(58,61)–(204,98) on every frame; small sparkle/asterisk doodle on the right edge.
- **Anchor shots:** main cam (anchor centre on grey sofa, bookshelf) for titles; side cam (anchor left, black gradient right) for diagrams.
- **Character:** the Varsity stick figure: round white face, black quiff, yellow triangle body, line legs, white shoes; often holding a magnifier.
- **Props:** magnifying glass (recurring), megaphone (things to remember), 3D pillars, phone outlines, 3D bull (purple) and bear (coral) for bull run / fall, flying cash notes.
- **Side-cam lists:** yellow bold title, white bullets with small yellow triangle markers; the current item bright and the rest faded.
- **Detail side card:** a narrow white glass card beside the chart window ("1 Month Candle": one candle diagram + Open/Close/High/Low values).
- **Callout pill:** white rounded pill with a thin coral outline, bold claim on the left and a small label + value on the right ("Holding Period / 1 Month – 6 Months").
- **Kite chevron logo** appears on chart windows (unlike ZO Product IP, where logos are banned).

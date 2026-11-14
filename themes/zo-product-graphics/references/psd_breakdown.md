# v2 PSD breakdown (Family Portfolio · Life Cycle Fund · MTF · Physical delivery · Charges · Kite UI)

43 shipped PSDs, read frame by frame. Each line: what the frame shows → the spec item that rebuilds it. Use this to pick a component for a beat; the look itself is in SKILL.md "The look (v2)".

## Full-screen (white 52px grid + edge decor)
- **3 steps** — "This takes three steps" + three numbered sticker steps (blue / orange / yellow, ink border, hole at the right) → `heading` (left) + `steps`.
- **Exit period Exit load** — "{o:Exit load} reduces over time", window card with dots, 2-col slab table, row 3 highlighted yellow, orange curly lines beside the card → `heading` + `slab_table` (`hl:2`) (+ `img` illus/psd/line_orange_curl_left as decor if wanted).
- **Zerodha Life Cycle Fund 2036 / 2041** — heading with orange year + "Allocation schedule" sub, 5-col table with small grey sublabels under headers, one highlighted row → `heading` (sub) + `slab_table` with `subs`.
- **c-1 Asset allocation** — centred heading + yellow underline bar, pie 75/10/10/5 with % on slices and labels outside → `heading` (underline) + `pie`.
- **family account / 1_new / 2** — three pies side by side ("Spouse / Your / Family account"), table header strip "Invested · Present value · Unrealized P/L" → `row` of three `pie` (small) + `text` labels; one pie + "P/L 30,000" orange tag → `pie` + `pillv`.
- **3 Family portfolio** — big blue ring with line faces around it → `donut` (+ `img` illus/psd/face_* around via `row`).
- **4 "10 Family members"** — huge blue number over a grey blob, ink phrase under it, doodle → `bigphrase` (blob on by default).
- **5 / 6 / 7 Family portfolio** — member cards (one blue = your account, others grey) with ₹ amounts; stock list with allocation row highlighted orange; holdings columns with orange rings around "ABC stock" → `cards`/`img` illus/psd/profile_card_* in a `row` + `slab_table`; rings = `img` illus/psd/ring_orange placed with x/y.
- **1 Family Portfolio feature** — window card with three member cards + orange arrow-circle callout "Family Portfolio feature on Console" → `img` illus/psd/profile_card_* + `img` illus/psd/arrow_circle_orange + `text`.
- **11 Physical delivery** — big green pill in the middle, commodity pills scattered around it (Mentha oil, Silver, Zinc, Copper, Cardamom, Gold) → `pillv` items placed with x/y, or `pills`.
- **8 Cash settlement** — single orange pill + doodle + faded arrow circle → `pillv` (orange) / `acronym`-style title card.
- **d Fundamentals / Good till triggered / Accounts with analytics** — stacked tilted pills, first orange, second yellow, third faded lavender → `pills` (active 0, `color:"orange"`).
- **6 FSS Important note** — doodle + "Important note" with underline, orange rounded box with white text, rule under it → `note`.
- **30 500** — "₹500" faded/struck above a big orange "₹30" box on a price line, "Per stock" → `fbox` (hero + before) or `bignum`-style FSS.
- **12-FSS Understanding LTV Risk** — heading with blue keyword + yellow underline, stacked holding cards on the left, one tall blue bar with "50%" tag → `heading` + `row` of `positions`-like cards + `bars`.
- **2_1 / 2_2 / 2_3 personal loan story** — one illustration scene per beat: clipboard "Personal loan" + coin + notes, blue shopping bag "Spend today", "Repay loan" paper + calendar; small blue label chips ("Extra money", "Spend today") → `img` illus/psd/clipboard_personal_loan, shopping_bag_blue, paper_repay_loan, coins_rupee_stack + `pillv` (blue) label.
- **account credited** — yellow folder with "₹50,000", black "Account credited" tag, cursor, "Trading account" caption → `img` illus/psd/folder_yellow_cash + `pillv` (grey/ink) + `text`.
- **4.jpg Choose a few mutual funds** — heading with blue keyword, stacked fund pills (active green + cursor, rest light blue) → `pills` (`color:"green"`).
- **file (1) Allocation that shifts over time** — blue/yellow area chart crossing over, legend under it, fund card on the right → `chart` (two series) + `ticket`.
- **gtt level** — dashed chart frame, orange price line, "₹500 Bought" + blue "Order placed" tag at a point → `chart` with `tags`.
- **Mobile mockup_2** — phone with the Kite order form, market-protection toggle → `img` illus/psd/phone_kite_order (or rebuild with `phone`).
- **Player** — YouTube player mock with suggestions → screen capture; do not design.
- **ui (1)–(6) Kite Terminal** — desktop terminal screens (orders, alerts, option chain, chart, positions) → screen capture beats; skip and log.

## Over the presenter (plate + white text, yellow keyword, never over the face)
- **1-TOS** — "How much can I **borrow?**" left, small purple/orange triangles, faded second line → `ov_title` / `punch`.
- **file (5)** — white lead "Kite's Option Chain is now available" + yellow box "NSE Commodity derivatives" → `ybox` (lead + text).
- **file (3)** — "Start investing with ₹100" card + "Microsavings on **Coin**" big yellow word → `ticket` + `punch`.
- **file (4)** — gold & silver bars above "Gold and Silver ETFs / take part in the pre-open session" → `img` illus/psd/bars_gold_silver + `lower`.
- **trasfer** — blue transfer arrows above yellow "Trasferring…" + white "takes 1-2 days" → `img` illus/psd/arrows_transfer_blue + `caption`/`punch`. (PSD spelling is wrong — always spell "Transferring".)
- **file (2) / file (6)** — Life Cycle Fund cards ("Your Dream Home", "Child's Higher Education" yellow tabs) on both sides of the presenter → `ticket` ×2 with `objcards` layout, or `side_list`.
- **two ways to do** — "**Two** ways / to do this" title above the presenter with blue dashes → `ov_title` (centred).

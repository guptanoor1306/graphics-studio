# spec.json format

```json
{"episode": "Ep10", "title": "Cash Flow Statement",
 "series": "fa",
 "cast": {"rajesh": {"char": "c1", "name": "Rajesh · Farmer"}, "mill": {"char": "c5", "name": "Mill Owner"}},
 "frames": [ {"id": "0.21", "name": "Operating-Cash-Flow", "mode": "fss", "els": [ … ]} ]}
```
- **series**: `fa` (default) or `futures` (dark OSA cards).
- **cast**: every person in the script gets one of the six team characters (c1–c6, see `assets.md`) for the whole video; two people never share one (the build warns).
- **OSA frames are delivered as transparent overlays** (`<id>_<name>.png`, works on any presenter) plus `<id>_<name>_preview.png` on a presenter plate for review. `"osa_overlay": false` at spec level turns this off.
Canvas 1920×1080. Coordinates in px. Elements draw in list order (later = in front); set `"z"` to override.

## Frame
| key | values |
|---|---|
| `id` | timestamp `M.SS`; states `0.25_b`, `0.25_c` |
| `name` | short English slug → file `0.25_Trader-Mindset.png` |
| `mode` | `fss` (light set + tiled floor) · `osa` (presenter on the right half; keep everything left of x≈1000) · `osa_center` (presenter centred; content at the sides) · `blur` (blurred `blur_src` image behind, for a title over a recap) · `takeaways` |
| `floor` | default on for `fss`; `false` for charts/cards that don't need a floor |
| `eye` | `"right"` to move the logo capsule; auto-moves when a header sits top-left |
| `deco_coins` | list of `[x, y, size]`; default two floating coins; `[]` for none |
| `sparkle_at` | `[x, y]` |
| `anchor_front` | `true` to put the presenter cutout in front of the content (rare) |
| `backdrop` | `farm` · `market` · `city` · `interior`: a drawn environment (replaces sky + floor); `seed` varies it |
| `allow_chars` | `true` to allow characters in an OSA frame (only when the storyboard asks) |
| `allow_repeat` | `true` to allow the same building twice in one frame |

## Text markup (any text field)
`==yellow block==` · `^^blue block^^` · `**bold**` · `__coral underline__` · `\n` line break

## Elements

**char** (people, always) `{"type":"char","who":"rajesh"|"c1","pose":"idle","expr":"neutral","cx","by","h":420,"flip":false,"label":"…"|false,"label_dy":-70,"holding":"props/…","hold_side":"a","hold_h":90}`
- poses: `idle point_left point_right point_up happy hips think worried hold give shrug explain`; expressions: `neutral smile happy worried surprised talk`.
- The characters face the viewer's left; `"flip": true` mirrors one to face right (handshakes, two people talking). Two `give` poses facing each other about 300 px apart read as a handshake.
- The name pill comes from the cast; `"label": false` hides it when a header or another pill already names the person.
- Pick the pose from what the person does in that beat and vary expressions; never two people in one frame with the same pose + expression.

**prop** (drawn story props, see `drawn_props.png`) `{"type":"prop","kind":K,"cx","by","w", …args, "as":"what it is"}`
- `sack` (label, price) · `stall` (awning colour, goods sacks|boxes, sign, price) · `shop` (sign, inside mill|goods|counter, color) · `calendar` (month, mark) · `document` (title, stamp, signed) · `timeline` (left, right, pos 0–1) · `handshake` · `lock` (locked) · `price_tag` (text, strike) · `arrow` (direction, color green|coral|blue) · `truck` (label) · `money` (amount)

**bubble** `{"type":"bubble","kind":"thought"|"speech","x","y","w":420,"h":260,"tail":[x,y],"text"|"items":[…],"prop":{"kind":"sack","w":120,…},"img","logo"}`: a person's facts, worries and numbers go **in their bubble**, not in loose pills. `tail` points at the head.

**logo** `{"type":"logo","name":"SBIN"|"State Bank of India"|"nse","x","y","h":80,"align","card":true}`: every named company/organisation shows its real logo (listed companies by NSE/BSE ticker or name; institutions from `assets/logos/<name>.svg`). Missing → dashed placeholder + warning.

**osa** (the only layout for content beside the presenter) `{"type":"osa","header":"Hedging","kind":"quote|list|tags|formula|calc|text", …}`
- fixed positions: header at (120, 250), block at (120, 370), width 820. Same spot every frame.
- `list`: `items` as text or `{"text","icon"}`; icon = asset path, `logo:<name>` or `prop:<kind>`; no icon → numbered badge. `active` highlights the item being read.
- `tags`: `items: [{"label","value"}]` (price tags, key facts). `quote`: `text`. `formula` / `calc`: same fields as `card`.
- the theme follows `series` (futures = dark glass card + white header with a blue bar).
**header** `{"type":"header","style":S,"text":…,"x","y","align":"center"?,"size"?}`
- `bar`: coral bar + ExtraBold Italic (section header over charts/comparisons: "Trader Mindset", "Fixed Deposit"). Size 44–60.
- `giant`: huge ExtraBold word; put a building/prop overlapping it (concept scene: "Assets", "Liabilities", "Housing Loan"). Size 90–150.
- `plain`: Bold black; use `__word__` for the coral underline ("Leverage __Ratios__"). Size 64–80.
- `stack`: coral bar + two lines `text` / `sub` ("Financial Ratios" / "Profitability Ratios"), OSA.
- `title`: `lead` small / `text` big ExtraBold Italic / `tail` small, right-aligned ("What kind of / Market Participant / Are You?").
- `box`: white rounded box ("Option-Based Valuation", pie titles).
- `label`: light-blue block ("Intrinsic Valuation").
- `glass`: big glass title card with `w` ("EBITDA Margin of\nBajaj Auto", "Valuation Ratios").

**pill** `{"type":"pill","text","x","y","italic":true,"bold"?,"size":32,"tilt"?,"active"?,"faded"?,"arrow_to":[x,y],"arrow_from":[x,y],"bend":0.3}`
Italic name label on scenes; `"italic":false,"bold":true` for word chips. `arrow_to` draws a hand-drawn arrow (negative `bend` curves the other way).

**pills** `{"type":"pills","items":[…],"x","y","gap":96,"size":32,"active":0,"fade_rest":false,"stagger":0}` stacked list pills (OSA lists). `active` may be a list (`[0,1]`). `stagger` offsets every other pill sideways (Ep 8 1.28 look).

**card** `{"type":"card","kind":K,"x","y","w",…}` frosted glass card (`"glass":false` = solid white)
- `quote`: `text` (definition; quotes added)
- `text`: `text`
- `bullets`: `items`, `title`, `title_hl` (`yellow`/`blue`), `marker` (`dot` blue · `square` coral · `triangle` coral), `active`, `fade_rest`
- `formula`: `term`, `hl` (`blue` default / `yellow`), then `num` + `den` (fraction) or `rhs` (inline); optional `result`
- `calc`: `lines`: `[{"label","value"}]` or `[{"label","num","den","result"}]`; labels get a yellow block (`"hl":false` to skip)
- `lines`: `items` with coral triangle bullets, no card background (use `==₹400==` for highlighted values)

**img** `{"type":"img","src":"chars/trader_seated","cx","by","h"|"w","flip"?,"tilt"?,"opacity"?,"blur"?,"z"?,"shadow"?}`; see `assets.md`.

**bigword** `{"type":"bigword","text","x","y","align":"center","size":260,"z":4}` giant black word behind a character (put the character after it with a higher `z`).

**coinflow** `{"type":"coinflow","from":[x,y],"to":[x,y],"coins":2,"bend":-0.25}` dashed arc + coins (payer → payee).

**branch** `{"type":"branch","from":[x,y],"badge_x":1180,"joint_x":1000,"items":[{"y":400,"icon":"props/icon_building","text":"Property"}, …]}` blue elbow connectors to round icon badges with labels.

**split** `{"type":"split","x":960}` thin blue vertical divider.

**arrow** `{"type":"arrow","from":[x,y],"to":[x,y],"bend":0.25,"dashed":false}` · **tri** `{"type":"tri","x","y","size":44}` coral triangle arrow · **shape** `{"type":"shape","x","y","w","h","color":"blue","radius":999,"opacity":1}`

**text** `{"type":"text","text","x","y","size":40,"weight":600,"italic"?,"align"?,"w"?,"color"?}`

**bar** `{"type":"bar","x","y","w","h","title"?,"glass":true,"stand":"phone"?,"ymax"?,"bars":[{"label","value","color","tag"}],"yticks":[{"v","label"}],"legend":[{"label","color"}],"bubbles":true}`
Colours: `green` (up/positive/profit), `coral` (negative/loss/debt), `blue`, `orange`, `yellow`, `pale_*`, `grey`. Negative values draw downward. `tag` = value bubble ("15%").

**line** `{"type":"line","x","y","w","h","points":[…] | "trend":"up|down|flat|smooth|lumpy","n":40,"seed":3,"ymin","ymax","marks":[{"i","label","drop":true,"dx":0,"dy":0,"anchor":"middle"}],"xlabels":[{"i","label"}],"levels":[{"v","label","note"}],"axis_label"?,"glass"?,"stand"?,"color":"blue"}`
Use real `points` whenever the script gives numbers; `trend` only for illustrative shapes. `i:-1` = last point.

**window** (Kite-style chart for a real stock) `{"type":"window","x","y","w","h","ticker","points"|"trend","ymin","ymax","yticks":[…],"marks"?}`

**linecards** `{"type":"linecards","x","y","w":540,"gap":50,"cards":[{"title","trend"}]}` three mini line charts side by side.

**scale** `{"type":"scale","cx":960,"by":1000,"w":1150,"left":"Stock Price","right":"Valuation"}` balance scale with the two box labels placed for you (valuation vs price, any two-sided comparison).

**pie** `{"type":"pie","cx","cy","r":220,"slices":[{"label","value","color","explode"?,"hidden"?}]}` (`hidden` removes a slice, e.g. assets minus liabilities = book value).

**phone** `{"type":"phone","x","y","w":380,"title","rows":[{"ex":"NSE","name"}],"card":{"name","price"}}` watchlist with green BUY / coral SELL.

**cardset** `{"type":"cardset","style":"folder|glass","items":[{"label","img"?}],"active"?,"y","cw","ch","gap","blur_rest":3}` blue folders (method reveal; the road version was rejected as childish, chapter lists use `module`) or glass cards with a building each (company comparison). Put a `lamp_blue` img with its `cx` over the active card; one state per card as the VO reaches it.

**module** `{"type":"module","module":"Module 3","chapters":[4 titles],"current":2,"start":1}` chapter page.

**takeaways** `{"type":"takeaways","title":"Key\nTakeaways","items":[…]}` (frame `mode: takeaways`, `floor:false`).

**html** escape hatch: `{"type":"html","x","y","w","html":"…"}`, palette colours only (the build warns).

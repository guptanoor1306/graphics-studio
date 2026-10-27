# spec.json format (FSS + anchor)

```json
{"look": {"plate": "anchor_plate_name"}, "frames": [ {"id": "6a", "mode": "fss", "items": [ … ]}, {"id": "2", "mode": "ost", "items": [ … ]} ]}
```
- `id`: graphic number, with a/b/c for build states of the same frame (`"6a"`, `"6b"`). It becomes the PNG name.
- `mode`: `"fss"` (default) full-screen white grid, content zone x 120–1800, y 60–1020 · `"osa" | "ost" | "tos"` anchor shot (dark plate + text zone from `look.plate` or frame `plate`). TOS adds `title` (+ optional `title_y`, `title_size`).
- `zone`: override the zone, e.g. `{"x":120,"y":60,"w":1680,"h":960,"valign":"center"}`.
- `gap`: px between stacked items (default 40). `decor:false` hides sparkles.
- **Auto-fit:** `heading` items stay 72px. Everything else is scaled to fill the frame, up to `fit` (default 1.6) and down to 0.55 if it overflows. `"fit": false` turns this off. Design at natural size and let fit scale it. If a WARN says "content shrunk to 0.7…", split the frame or cut text.
- Items stack top-to-bottom. Give an item `"x"`/`"y"` to place it absolutely.
- **Text markup** inside any string: `**yellow**`, `++blue++`, `__bold__`, `{g:green}`, `{o:orange}`, `|` for a line break.
- Illustrations: a bare name from `assets/INDEX.md` (`"vault_blue"`), or an `"illus/…"` path.

## Items — FSS
| t | keys | use for |
|---|---|---|
| `heading` | text, sub?, sub_color, align ("left"), underline?, pill?, icon?+line2? | 72px heading (fixed). `icon` → "Crude oil / Strike price ₹7,900" icon header |
| `compare` | left/right: {top?, tag?, tag_color, img, disc?, ih?, squares?, sq_color, value, value_color, caption}, divider ("dashed"/"solid"/"none"), op ("<<", "≠") | two things side by side — the most used FSS layout |
| `hub2` | hub? (omit for no circle), hub_color, hub_size, active? (0/1 dims the other arm), arms:[{label, sub?, color, fact?, bullets?, imgs?}] ×2 | classification into two types. **Default: ONE frame with both arms and their bullets.** Add states only if the script spends a paragraph on each type with new facts (then `Xa` overview → `Xb` type 1 with bullets → `Xc` type 2) |
| `hub_fan` | hub, hub_color, style ("fan"/"mind"), items:[{label, icon}] | a list of 4–6 things that belong to one thing |
| `cards` | items:[{icon, label, disc?, bullets?}], active?, w, icon_size | 2–4 bordered icon cards (abilities, SIP types, fundamentals) |
| `positions` | label ("Your positions"), cards:[{icon, title, sub, chip, chip_color, value}] | Kite-like positions panel |
| `chart` | see "chart units" below · strike_label_pos (right/left/centre), split_at (index where the line turns orange), tags:[{text ("a\|b" for 2 lines), at (index), color green/orange/blue/purple/grey, dy, dx}], arrow (up/down), x_labels, y_labels, y_hl (label to colour blue), w, h, seed | price/strike charts, risk charts |
| `bars` | items:[{label, value, display, color}] | to-scale size comparison (market cap) |
| `formula` | terms:[{value,label,color}], ops ["×","="], definition? | a named formula filled with numbers |
| `status` | title, sections:[{name, rows:[[true/false, text]]}] | broker checks as an account-status panel |
| `phone` | app, title, text, time, chip? | SMS / in-app alert |
| `week` | label, on:["Monday","Wednesday"] | trading windows / which days |
| `exchange` | left:{img,label}, right:{img,label}, action | who you transact with (Investor ⇄ Exchange) |
| `notepad` | items, active | question list read aloud |
| `objstat` | title?, img, ih, value, tag?, chips? (locked pills) | one object carrying a number through a section (vault + ₹8,00,000 + "Active breach") |
| `calendar` | month, day, sub? | deadline |
| `note` | title ("Important note"), lead?, text, w (1100), size (44) | a standalone broker rule / caveat |

### Chart units (read before using `chart`)
- **Generic line** (no real data): `shape` = up / down / up_then_down / flat_then_up. Add `y_range:[lo, hi]` in ₹, then give `strike` in ₹ and `y_labels` as evenly spaced ₹ labels from lo to hi. Example: `"shape":"down","y_range":[1350,1550],"strike":1400,"y_labels":["₹1,350","₹1,400","₹1,450","₹1,500","₹1,550"]`. Without `y_range`, `strike` is a 0–1 fraction of the height.
- **Real data:** `values:[…]` + optional `min`/`max`. `strike` is in the same units as values.
- Put `strike_label_pos:"left"` when the line meets the strike at the right edge, so the label doesn't hide the moment the example is about.
- `zone:"below"` + a falling `shape` gives the orange area under the strike (puts, stop-loss).
- The generic line has **60 points** (index 0–59). A tag's `at` is a point index; omit it for the last point; `"at":"strike"` puts the tag where the line first crosses the strike.
- More price levels (target + stop-loss): `levels:[{"value":1600,"label":"Target ₹1,600","color":"green"},{"value":1300,"label":"Stop-loss ₹1,300","color":"orange","pos":"left"}]` (same units as `strike`).

### Kite / market UI (rebuilt as vector, never screenshots; generic tickers unless the script names one)
| t | keys | use for |
|---|---|---|
| `kite_watchlist` | hl:{name, change, pct, price, dir up/dn}, hl_at (row index, 7), rows (17), seed | a phone watchlist with the stock in focus popped out |
| `kite_depth` | name, exchange, ltp, change, bids:[[price,orders,qty]…], offers:[[…]…], status:["No trade",…,"Trade executed"], hl:[row index] | market depth / order book; status tags sit outside the phone with dotted leaders |
| `kite_chart` | name, shape ("volatile"), points (140), ticks:[point indices for orange dots], x_labels, seed, w, h | Kite desktop chart; dots = individual trades/ticks |
| `auction` | buyers:[3 prices], sellers:[3 prices], match (price shown big on both sides), matched (true/false), result ("Trade executed"/"No trade yet"), left/right labels | buyers vs sellers meeting on a price |

## Items — anchor (osa / ost / tos)
| t | keys | use for |
|---|---|---|
| `lower` | text, lead?, size | lower-third statement / equation |
| `punch` | key, lead?, tail?, color, align, key_size | one big keyword punchline |
| `bignum` | value, lead?, sub?, size, align, boxed?, unit | hero number beside presenter |
| `side_list` | rows:[[left,right]…], heading?, op, active?, only_active? | mapping list in side panel |
| `scroll_list` | items:[strings], heading?, active | pop-up callout stack (one line highlighted) |
| `objcards` | items:[{icon,label,color?,caption?}], between?, alert?, gap | two object cards + transformation |
| `ticket` | title, rows, icon?, chip?, button? | form / ticket beside anchor |
| `mini_table` | head, rows, head_colors? | small comparison table |
| `ladder` | segments:[{left,right,pct,color}], caption? | stacked bar metaphor |
| `note` | title, text, lead?, w, size | Important note over anchor (same as FSS) |

## Other items
`text` (text, size, weight, color, align) · `img` (src, w|h) · `pillv` (text, color yellow/blue/green/orange/purple/grey) · `row` (items:[…], gap) to put items side by side · `html` (raw, last resort).

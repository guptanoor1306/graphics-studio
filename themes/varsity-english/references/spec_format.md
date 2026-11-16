# spec.json format (read this once; it is all you need to build frames)

```json
{"look": {"anchor": "right|left", "fss": "blue|warm", "props": ["coins","tax","house"], "plate": "<optional plate name>"},
 "frames": [ {"id": "0.47", "mode": "anchor|fss", "items": [ {...}, {...} ]} ]}
```
(`prop` as a single string still works; prefer **`props`**: multiple values stack corner props for richer dressing.)
- `id` is the output filename: `0.47`, `0.28_a` (content state), `1.19-Table1` (one of several tables).
- **anchor** frames: items stack top-to-bottom in the safe zone beside the anchor (x 140–900 for anchor right; mirrored for left). Dressing, the topic prop and the overlay PNG are automatic.
- **fss** frames: put `htab` first. The builder pins it top-centre and centres everything else in the space between the heading and the floor (y 175–975), so short content sits mid-frame. Don't add spacer items or `y` to push content down. Set `"person_left": true` when a `person` stands at the left. If content is too tall the build prints `too tall for the space under the heading`: trim rows or split the frame.
- Topic props are placed automatically on the floor line (bottom corner); they may touch the frame edge by design.
- Frame options: `top` (anchor: start y, default 110 / 200 under a heading; on FSS it switches off the centring and stacks from that y), `gap` (default 30), `zone_w` (default 760), `prop:false`, `anchor` (override), `plate`.
- Sizes: leave `w` and `size` off FSS tables, lists, cards and charts. The defaults fill the frame like the house videos (calc_table 1300 px wide, 1120 beside a person; font 32 for ≤4 rows, 28 for ≤6, 24 above; nlist 42 px for ≤4 items; cards share the row width; bars 1300×640 with round axis steps).
- Assets and people standing on the floor are moved sideways if they would overlap one placed earlier in the same frame.
- Any item can take `"x":…, "y":…` to pin it absolutely instead of stacking.

## Items (`t` = type)
| t | fields | notes |
|---|---|---|
| `title` | `lead`, `key`, `tail`, `color` (white/coral/amber/green), `size` (``/md/xl), `bold_lead` | section title; hero keyword big. `xl`+`coral` = the giant HUF style |
| `pill` | `text` | title pill. Avoid over the anchor (review rule 3); FSS only |
| `htab` | `text`, `color` (blue/amber/green), `small` | **the** heading. On anchor frames it is pinned top-left automatically (content starts below it); on FSS put it first |
| `points` | `items` [..], `w` | body points under a heading: 31px plain text with numbered discs, no box |
| `num` | `n`, `text` | ① numbered sub-heading |
| `label` / `text` | `text`, `size`, `weight`, `align` | plain label or a sentence |
| `definition` / `defcard` | … | legacy definition styles. Prefer `htab` + `text` (review rules 1/3) |
| `glass_table` | `head` [..], `rows` [[..]], `result` (last row inverted, default true), `w`, `dark`, `size` (font px, default 24) | ≤5 rows over the anchor; use `""` for an empty cell |
| `calc_table` | `head`, `rows`, `less` [row idx], `hl` [row idx], `total` (default true), `widths` ["34%","44%"], `color` (``/blue), `w`, `size` | FSS table. `total` bolds the last row (the answer); `hl` tints the row the VO is reading. Leave one fewer width than columns. Font auto-sizes (30px for ≤5 rows, else 24px). A cell with `•` becomes a bullet list |
| `popup` | `title`, `value`, `bullets` [..] | window card for a sum said aloud |
| `callout` | `text`, `white` | green speech bubble (white = FSS variant) |
| `hpill` | `label`, `value` | highlight pill over a table ("Interest Saved ₹9.22L"); give x/y |
| `result_pill` | `text` | green "Net savings…" under a table |
| `nlist` | `items` [..], `active` (index or "all"), `w` | numbered list; non-active items faded |
| `folder` | `items` [..], `active` | blurred list on paper in a blue folder |
| `cards` | `items` [{`img` (asset path) or `svg`, `label`, `sub`}], `active` | row of icon cards |
| `bars` | `labels`, `values`, `value_labels`, `highlight` [idx → amber], `target`, `target_label`, `unit_fmt` ("₹{} cr"), `w`, `h` | bar chart vs a dashed target |
| `person` | `color`, `hair` (spiky/long/none), `hat`, `moustache`, `bindi`, `name`, `h` (default 315), `x`, `facing` | doodle character, auto-stood on the floor. Give only `x` |
| `asset` | `src` (e.g. `setC/house_home_loan.png`), `x`, `h` (visible height; default by role: building 560, house 360, character 315, jar 230, coin 100), `z` | kit PNG, auto-stood on the floor (transparent padding handled). Give `y` only for things that really float (cursor, pill). `grep` assets/INDEX.md to find one |
| `html` | `html` | escape hatch: raw HTML using varsity.css classes |

Colours for `person`: yellow `#F2B233`, blue `#248EF7`, green `#A5CC65`, coral `#F26B5B`.
See `scenes/example_spec.json` for 8 working frames (title stack, htab + text, htab + points + building + person, calc table + person, popup, bars, glass table, list).

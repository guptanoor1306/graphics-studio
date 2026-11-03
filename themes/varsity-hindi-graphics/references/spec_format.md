# spec.json format (everything needed to build frames)

```json
{"frames": [ {"id": "2.49", "mode": "side", "items": [ {...}, {...} ]} ]}
```
- `id` = output filename = storyboard timestamp: `0.43`, `3.49_b` (a second state), `9.10`.
- `section` = the storyboard section the frame belongs to ("Intro", "Marubozu", "Things to Remember"). The delivery zip groups PNG/ and HTML/ by section, in storyboard order. Optional `name` overrides the file-name slug (default: the frame's header tab or title).
- `mode`:
  | mode | background | use for |
  |---|---|---|
  | `side` | side cam: presenter left, right ⅔ near-black | diagrams, header tabs, definitions, bullets, panels. Items stack centred in x 940–1840 |
  | `main` | main cam: presenter centre, bottom vignette | section titles, roto big text. Pin items with `x`,`y` either side of the presenter |
  | `fss` | light sky, wavy line-art edges | Kite charts, timelines, anything with a chart window |
  | `blur` | main cam blurred and darkened | big table windows (FA vs TA) |
  | `scene` | `"plate": "scene_desk_night"` or `"scene_phone_store"` | analogy scenes with the character |
  | `takeaways` | sky + white swoosh + megaphone | Things to remember / Key Takeaways: fields `title`, `items` [..], `active` |
- Frame options: `gap` (px between stacked items), `justify` (`center`/`flex-start`), `zone` [x,y,w,h] to override the stacking area, `sparkle:false`.
- Any item with `"x"` and `"y"` is pinned absolutely (add `"z"` for stacking). Others stack in the frame's zone.
- Text fields accept `**bold**` and `\n`.

**Colour rule:** green/red are drawn by the kit on candle and bar bodies only. Every pill, tag, zone, chip, row and box is neutral. Don't pass colours to items.

## Items (`t` = type)

### Charts
| t | fields |
|---|---|
| `kite` | Mock Kite chart window. **Data**: `candles` [[o,h,l,c],…] **or** `closes` […] (line chart) **or** `gen` {`n`, `path`:[waypoint prices], `seed`, `vol` (0.003–0.012), `patterns`:{"index":"name"}}. `type`: candle (default) / bar / line. `ticker`, `readout` (true = last candle, or an index → "O: H: L: C:" line computed from the data), `tab` (header-tab title centred on the window), `x_axis` (list of labels, or {`type`: days/intraday/months/years/weeks, `start`, `step`, `every`, `per_year`}), `decimals`, `y_range` [lo,hi]. **Annotations**: `boxes` [{`from`,`to`,`label`,`pos` right/left/above/below, `days`:true → Day 1/2/3 labels}], `tags` [{`i`,`kind` open/high/low/close}] (white boxes), `points` [{`i`,`text`}] (yellow value tags on a line chart), `leaders` [{`i`,`at` high/low/open/close,`text`}] (dashed line → "Stoploss", "Entry"), `hlines` [{`price`,`label`,`style` dotted/dashed/solid}], `ranges` [{`from`,`to`}] (consolidation band), `trade` {`entry`,`target`,`stop`,`from`,`labels`:"words"/"pnl"}, `fade_except` [indices], `side_card` {`i`,`title`} (narrow card with that candle + its OHLC values), `dropdown` {`selected`:"05 Minutes"} (Kite interval menu). Geometry `x`,`y`,`w`,`h` (default 240,150,1440,880; use y≈170 when there is a `tab`) |
| `mini` | Bare chart for a dark glass panel (white ink, no axes): same data/annotation fields as `kite` + `caption`, `w`, `h` |
| `diagram` | Concept candle/bar drawing on dark. `candles` [{`o`,`h`,`l`,`c`, `kind` candle/bar, `labels` ohlc/parts/eq/none, `pill` "Bullish"/"Bearish" (white pill), `note`, `title` (e.g. "Day 1")}]. `scale`:true (default for one candle) draws a price axis + dashed leaders + "Time". `spacing` (px between candles), `body_w`, `half_of` (index → dashed 50% line through that body), `caption`, `w`, `h`, `step`, `y_range` |

Pattern names for `gen.patterns`: single: `marubozu_bull`, `marubozu_bear`, `hammer`, `hanging_man`, `inverted_hammer`, `shooting_star`, `doji`, `dragonfly_doji`, `gravestone_doji`, `long_bull`, `long_bear`, `short_bull`, `short_bear`. Multi (occupy 2 or 3 candles from the index): `bullish_engulfing`, `bearish_engulfing`, `piercing`, `dark_cloud`, `morning_star`, `evening_star`.
Put the pattern index at the **trough** (bullish) or **peak** (bearish) of `path`: e.g. n=40, path [790,712,780] → trough at index ≈19. The build warns if it isn't; change `seed` or the index.

### Text and layout
| t | fields |
|---|---|
| `htab` | `text`, `small` (header tab: white box, blue base bar) |
| `title` | `lead`, `key` **or** `lines` [{`text`,`color` white/yellow,`size`,`indent`}], `tail`, `align`, `key_size`, `lead_size` (title stack over main/side cam) |
| `roto` | `lead`, `lead_size`, `lead_weight`, `words` [{`text`,`color`,`size`}], `chips` [{`text`,`x`,`y`}] (giant word with white chips pinned on it) |
| `questions` | `items` [{`lead`,`key`}], `active` (stacked questions, later ones faded) |
| `big` | `lead`, `text`, `sub` (e.g. In Japanese / **Marubozu means "Bald Head"**) |
| `definition` | `text`, `style` plain/capsule, `w`, `size` |
| `bullets` | `title` (yellow), `items`, `active` ("all" or index; later items faded), `w` |
| `callout` | `claim`, `label`, `value` (white pill, thin dark outline) |
| `panel` | `items` [..], `direction` column/row, `w`, `gap` (dark glass panel) |
| `row` | `items` [..], `gap`, `align` |
| `cards` | `items` [..], `active`, `pillars`:true (3D pillars under the cards) |
| `typo_card` | `rows` [{`head`,`text`}] (dark glass text card, e.g. Exercise) |
| `table` | `head`, `rows` (cells accept `**bold**`/`\n`), `hl` (row index → magnifier), `dim_others`, `tab`, `x`,`y`,`w` |
| `sentiment` | `title`, `left`, `right`, `pos` 0–1 (meter card; pin with x/y over a chart) |
| `bubble` | `text`, `w` (thought bubble with text) |
| `label` / `text` | `text`, `size`, `weight`, `color`, `align` |
| `asset` | `src` (props/…png), `w`, `flip`, `opacity` |
| `html` | `html` (escape hatch, e.g. a mock e-commerce card) |

### Props (assets/props/)
`magnifier`, `megaphone`, `character_magnifier` (yellow stick figure holding a magnifier), `character_pointing`, `character_desk_back` (seated at a desk, seen from behind), `thought_bubble`, `bull_3d`, `bear_3d`, `cash_note_1`, `cash_note_2`, `umbrella`, `pillar_3d`, `tile_floor`, `paper_doodle`, `kite_chevron`, `varsity_eye`, `sparkle`.
Plates (assets/plates/): `sidecam`, `maincam`, `fss_sky`, `scene_desk_night`, `scene_phone_store`.

Working examples of every item: `examples/example_spec.json` (28 frames rebuilt from Ep1–5).

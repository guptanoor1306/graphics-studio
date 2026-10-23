# spec.json format

```json
{ "title": "…", "look": "one line", "frames": [ { "id": "0.27", "type": "sop", … }, … ] }
```
- `id` = timestamp `m.ss` (add `-a`, `-b` for states). It becomes the file name `out/<id>.png`.
- Every frame may carry `vo` (the line) and `why` (one clause). They are ignored by the renderer but keep the storyboard and spec in one place.
- Types `footage`, `screen`, `repeat` are storyboard-only and are skipped by the builder. `screen` takes `url` + `highlight` (what the editor marks). If the script names a source without a link, write `"url":"TBD – <site> <page>"`. `repeat` takes `of` + `note`.
- Two beats at the same second: give the later one the next second, or a suffix (`0.24`, `0.24-b`). Ids must be unique.
- Asset paths are relative to `assets/` (see `assets/INDEX.md`). An asset you don't have is `"TODO:<what>"`, which renders a dashed placeholder box.
- Text supports `\n` for line breaks and `**bold**`.
- Anchor frames (`ribbon`, `definition`, `anchor`) also produce `<id>_overlay.png` (transparent, without the anchor plate) for the editor.

## Types

### `scene`: illustrated full frame (light by default)
```json
{"id":"0.10","type":"scene","bg":"light","decorset":"light|light-frames|light-min|dark|none",
 "pill":{"text":"Indian Mutual Funds","icon":"search|coin|none","x":"center|left|right|<px>","y":75,"size":"lg|sm"},
 "hero":{"asset":"illus/folder_docs.png","x":694,"y":416,"w":691,"bleed":false},
 "floor":true, "burst":{"x":492,"y":316},
 "props":[{"asset":"illus/coins_notes_flat.png","x":1015,"y":839,"w":366,"rot":0}],
 "cards":[{"asset":"illus/logo_card_apple.png","x":913,"y":537}, {"text":"Tencent","color":"#e4950b","x":1200,"y":500,"w":170,"rot":-6}],
 "labels":{"layout":"orbit|free","active":1,"dimOthers":false,"items":[{"text":"International Equity","x":112,"y":608,"align":"left|center|right"}]},
 "chain":{"y":900,"items":["India","Gujarat","Gandhinagar","GIFT City"],"active":"all"},
 "cursor":{"x":1319,"y":703,"style":"pixel|outline"},
 "disclaimer":true, "html":"<div class='abs' style='left:..'>…</div>"}
```
`disclaimer`: `true` gives the standard line ("The securities quoted are for illustration only…"); a string sets custom text. It is drawn on a solid strip at the bottom centre.
`labels.layout:"orbit"` arranges N labels on an arc above the hero automatically (omit x/y). Logo-card colours come from the palette only: `#2f4fd0` blue, `#e4950b` orange, `#5aa86d` green, `#4b3fd8` purple. A logo card with `text` instead of `asset` draws a tilted coloured frame with the name, which is the safe default for brands without a logo file.

### `ribbon`: Roto big text over the anchor
`{"id":"6.04","type":"ribbon","text":"Taxation"}`. Optional `size` (px), `maxlen` (default 960), `offset` (% along the ribbon, default 50), `plate` (path to a 1920×1080 frame grab of the real anchor).

### `definition`: term + one-line meaning over the anchor
`{"id":"1.38","type":"definition","term":"Fund of Funds (FoF)","text":"line 1\nline 2"}`. Keep it to 2 lines and under ~120 characters. The font shrinks to fit `maxw` (1100).

### `anchor`: over-anchor frame with free html (e.g. a number popup)
`{"type":"anchor","pill":{…},"html":"…"}`

### `sop`: agenda tiles on the dark grid
`{"id":"0.27","type":"sop","questions":["Q1","Q2","Q3"],"active":null}`. Use 2 or 3 questions. `active:n` dims the others and adds a cursor (for a repeat you must render, e.g. `0.44-q1`).

### `table`
```json
{"type":"table","bg":"light|dark","pill":{"text":"GIFT City Fund Rates","icon":"coin"},
 "columns":["Scheme","Style"],"rows":[["DSP Global Equity Fund","Active"]],
 "widths":[0.6,0.4],"box":{"x":70,"y":180,"w":1773},"row_h":98,"head_h":110,"font":27,"head_font":36,
 "highlight_rows":[2,3],"highlight_cells":[[1,4]],"highlight_col":4,
 "reveal_upto":1, "marker":true, "tags":{"Hybrid":"tag-fof"}, "stairs":true, "caption":"*source…"}
```
Defaults: width 1200 (2 cols) / 1640 (3 cols) / 1760 (4+ cols), centred, body 30 px, header 40 px. Set `font`/`row_h` only for dense tables (≥6 rows). For an "attribute | Option A | Option B" comparison, make the first header `""`: that corner cell turns white and column 1 becomes bold row labels (or force it with `"row_header":true`). Hyphenated words never break at the hyphen.
`reveal_upto:k` keeps columns 1..k sharp and blurs the rest (a reveal state). Cells reading `Active` / `Passive` / `Passive FoF` / `FoF…` are coloured automatically. Fits ≤ 8 rows × 5 columns. Split anything bigger.

### `cycle`: process loop
`{"type":"cycle","pill":{"text":"Indian Mutual Funds"},"active":4,"steps":[{"label":"You invest","asset":"illus/notes_coins_stack.png"},…]}`. 3–4 steps read best (up to 6). Render `-a/-b` states with `active` 1..N only if the storyboard asks.

### `points`: Key benefits / limitations / things to remember
`{"type":"points","title":"Key Limitations of GIFT City Funds","items":["…"],"active":null,"reveal":null,"bg":"dark|light"}`. Up to 8 items. More than 4 items switch to two columns. `active:n` highlights one item. `reveal:n` shows the first n.

### `html`: escape hatch
`{"type":"html","bg":"light|dark","pill":{…},"html":"…"}`. Use the house classes: `.pill`, `.defbox`, `.tile.orange|pink|green`, `.qbox`, `.chip.darkbg|lightbg`, `.nlabel`, `.tbl`, `.abs`, `.grain`. Position with inline `left/top` in px.

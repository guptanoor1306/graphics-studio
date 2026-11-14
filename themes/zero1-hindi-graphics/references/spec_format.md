# spec.json format

```json
{
  "episode": "Ep05_Gold-Loans",
  "arjun": "city",                      // default Arjun variant for prompts: city | kerala | andhra | meghalaya
  "gen": {                              // every image the kit can't render: one entry per plate / cut-out
    "kirana": {"prompt": "Arjun behind the counter of a half-empty kirana store, empty shelves", "arjun": "andhra", "expr": "worried", "aspect": "16:9"},
    "gold_bars": {"prompt": "A stack of gold coins and two gold bars", "cutout": true, "aspect": "1:1"},
    "crowd": {"prompt": "Crowd of 40 home-buyers holding blank placards outside a locked gate", "people": true}
  },
  "frames": [ { "id": "0.12", "section": "Intro", "name": "meet-arjun", "type": "scene", "bg": "sky", "layers": [] } ]
}
```
- `id` = timestamp (`m.ss`); a state of the same set gets `_b`, `_c`. `section` = storyboard section ("Intro", "SOP", "Ch1 The Noida Paradox", "Conclusion"). `name` = 1–3 words for the filename.
- `allow_words`: optional top-level list of words the spell-check should accept (names, Hinglish words it doesn't know).
- `gen` keys: `prompt` (what is in the image, plain English), `arjun` (variant, or `""` for the episode default; omit if Arjun isn't in it), `expr` (neutral | worried | happy | thinking | aged | crying), `people:true` (other people present), `cutout:true` (isolated on white for compositing), `aspect`. The build composes the full prompt (style + character bible) into `out/_image_prompts.md`.

## Image references (anywhere an image goes)
- `"asset:characters/arjun_city_worried_scratch.png"`: a kit asset (see `assets/`).
- `"gen:kirana"`: uses `gen/kirana.png|jpg` next to spec.json once generated. Until then the build draws a labelled dashed placeholder, so the layout can be approved before images exist.
- `"photos/x.jpg"`: any path relative to spec.json (real photos, logos, screenshots supplied by the user).

## Common frame fields
| field | meaning |
|---|---|
| `bg` | `"sky"` · `"paper"` · `"desk"` · `"dark"` · an image ref · `{"img": ref, "look": "grey"\|"sepia"\|"dark"\|"blur"}` |
| `under` / `layers` | free layers drawn before / after the type's own content (list) |
| `tint` | `{"color":"red","opacity":0.35}`: crisis flood over the whole frame |

**Layer kinds**
- image `{"img": ref, "x":, "y":, "w":, "h": (placeholder only), "shadow": true, "look": "grey"|"sepia", "rot":, "flip": true, "opacity":, "z":}`
- text `{"text": "…", "x":, "y":, "size":, "font": "br"|"imp", "weight": 200–800, "color": "red"|"ink"|…, "w":, "align":, "italic": true}`
- arrow `{"arrow": [x1,y1,x2,y2], "curve": -0.3..0.3, "dashed": true, "color": "ink"}`
- dot `{"dot": [x,y], "color": "red"}` · rect `{"rect": [x,y,w,h], "color": "xblue", "opacity": .55, "radius": 0}`

**Sizing kit characters:** the PNGs come at different native sizes; always set `w` (full-height Arjun ≈ 300–420 px wide on a 1080 canvas) and don't upscale a small asset past ~1.5×. Use a `gen` plate for big close-ups.

**Text markup:** `*word*` = accent (red, or gold on dark frames) · `_word_` = italic · `**word**` = bold · `\n` = line break.
**Colours:** use names only: red, ink, black, white, gold, blue, tblue, teal, navy, yellow, tagbrown, xblue, olive, sand, grey.

## Types
| type | fields |
|---|---|
| `scene` | just `bg` + `layers` (DIO, CHR, CUTOUT, GREY-FOCUS, MAP, EXPLODE, OTS…) |
| `chapter` | `n`, `title` ("Line 1\nLine 2"), `kicker` (default "Chapter-n"), `pos` [139,170], `size` 139, `scrim` true (soft white fade behind the text on busy plates) |
| `word` | `text`, `font` imp\|italic\|br, `size` 300, `color`, `pos` [x,y] (omit = centred), `kicker`, `sub`, `w`, `nowrap` true, `runoff` true (number deliberately runs off the right edge; silences the off-frame warning) |
| `stat` | `value`, `label`, `label_pos` below\|above, `pos`, `align` left\|center\|right, `size` 136, `label_size` 50, `color`, `w`. Dark bg → gold value, white label, `*gold*` keywords |
| `timeline` | `year`, `year_sub`, `year_y` 400, `size` 150, `grid` true, `caption`, `caption_pos`, `caption_size`, `curve` `{"points":[[x,y]…], "label":"MFI", "label_at":[x,y]}` + layers for the cut-out scene |
| `table` | `title`, `header` blue\|red, `cols` (optional yellow sub-header row), `rows` [[label, value, …]], `row_styles` {"4":"hl"\|"total"}, `upto` (rows shown, for reveal states), `mount` hung\|desk, `x`,`y`,`w`, `font_size`, `pad`. Rows beyond `upto` are not drawn (the table grows downward as rows reveal) |
| `idtag` | `tags`: [{`x`, `top` -516, `scale` 1, `fields` {Name, Age, Salary, Info, State}, `highlight` ["State"]}] (value "?" renders as big red ?) |
| `hangtags` | `tags`: [{`x` (centre), `y` (card top), `kicker`, `title`, `size`, `color`, `w`}]: price tags (no kicker, black Impact) or boards (kicker + red Impact) |
| `placards` | `items`: [{`text`, `x` (centre), `y` (top), `rot`, `size`, `w`, `stake`}] |
| `checklist` | `title`, `items` [..], `checked` n, `x`,`y`,`w`, `photo` ref, `photo_pos` [x,y,w] |
| `sop` | `items`: [{`n`, `kicker`, `title`, `img`, `x`,`y`, `w` 230, `rot`, `text_pos`, `size`}] + layers (Arjun / "?") |
| `news_wall` | `items`: [{`source`, `headline`, `x`,`y`,`w`,`size`}] (auto-staggers if x/y omitted) |
| `article` | `source`, `title`, `body`, `highlight` (exact substring of body), `date`, `mount` hung\|plain, `x`,`y`,`w`, `title_size` 52, `body_size` 34 |
| `calc` | `equation` + `answer` ("?" or "₹50 Lakh") + `pos` [x,y] (give x so the equation stays put when the answer swaps; x=0 centres it); or `lines` [{`l`:"Current value", `r`:"= ₹1.48 Lakhs", `color`}] + `pos` [x,y] + `size` |
| `dots` | `title`, `groups` [{`label`, `n`, `cols`, `color`, `x`,`y`, `d` 44, `gap` 32, `filled`, `pct`}], `sign` "<"\|">"\|"=", `sign_pos` |
| `callouts` | `labels` [{`text`, `x`,`y`, `to` [x,y], `style` pill\|leader\|dpill, `n`}] |
| `compare` | `board` {`kicker`,`title`,`x`,`y`}, `left`/`right` {`img`,`x`,`y`,`w`,`list` [[text, true/false]], `list_pos`} |
| `hub` | `title`, `center` {`label`,`value`,`x`,`y`}, `items` [{`img`,`x`,`y`,`w`,`label`,`value`,`label_pos`}] |
| `flow` | `items` [{`img`,`label`}], `y`, `w`, `margin` |
| `pie` | `pies` [{`title`, `data` [[label, pct]…], `x`,`y`,`r`}], `legend` [labels], `legend_pos` (use bg `desk`) |
| `vignette` | binocular mask over `bg`; `color` |

See `../examples/example_spec.json` for one working frame of every type.

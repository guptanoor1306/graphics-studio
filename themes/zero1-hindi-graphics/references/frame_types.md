# Frame types: what each looks like and how to build it

Every code below has original frames on the labelled contact sheets `frames/_atlas_1..7.jpg` (each tile is labelled `<CODE>__v<video>_<psd>`). The same frames without their text are in `assets/plates/` (see `plates_index.md`). Look at the reference before building a type you haven't built yet.

**Build** names the `type` to use in `spec.json` (fields in `spec_format.md`).
**Gen** means the visual needs an image-model plate (`gen:<key>`) because the kit can't paint dioramas. Everything else is rendered by the kit from fonts, assets and CSS.

## Backdrops (`bg`)
| bg | Look | Use for |
|---|---|---|
| `sky` | crumpled white paper with a painted sky/cloud band across the top (`assets/backdrops/sky_paper.jpg`) | default for characters, boards, tables, typo, objects |
| `paper` | crumpled white paper, no sky | timelines, cut-out scenes floating on paper, data, memories |
| `desk` | grid-paper sheet on a wooden desk with blueprints, steel ruler, red scissors | pie charts, desk tables (taxation, selling-side breakdown) |
| `dark` / `{"img":…, "look":"dark"}` | flat dark, or a scene dimmed to ~30% | STAT-DK, pivot words |
| `{"img":"gen:key"}` | full-bleed diorama | DIO scenes |
| `{"img":…, "look":"grey"\|"sepia"\|"blur"}` | the same plate graded | GREY-FOCUS, PAST, blurred chart behind dark stat |

## Catalogue
| Code | What it is | Build | Gen? | Reference |
|---|---|---|---|---|
| CHR | Arjun(s) standing on Sky-Paper with a soft shadow, up to 3 abreast | `scene` + character layers | no (kit characters) or yes (new pose) | CHR__v1_1-2 |
| CUTOUT | a scene trimmed to an irregular ground patch, floating on plain paper | `scene` bg `paper` + `gen` cutout layer | yes (`cutout:true`) | CUTOUT-INTRO__v3_1, CUTOUT-SCENE__v3_50 |
| DIO | full-bleed toy diorama (shop, office, street, village, interior) | `scene` with `bg:{img:gen:…}` | yes | DIO__v1_10-11 |
| COLLAGE | real-photo cut-outs of a city's landmarks + giant Impact city name behind | `scene` (photo cut-outs supplied, or gen) | photos/gen | COLLAGE__v2_2 |
| MAP-W | wooden 3D India map, focus state olive, Arjun figurine on it, Impact labels | `scene` + `asset:maps/…` + text layers | AP map in kit; other states gen | MAP-W__v1_7-8 |
| MAP-F | flat ochre/cream map with thin-leader state labels; greyed rest; red "?" | `scene` + map image + `callouts` | map image | MAP-F__v1_62 |
| MAP-D | map with coloured dots + legend "● Yellow Dot = **Other sources.**" | `scene` + `dot` layers + text | map image | MAP-D__v1_40-41 |
| CHAP | "Chapter-N" kicker + 2-line Impact 139 title, top-left, over that chapter's world | `chapter` | plate if a scene | CHAP__v1_9, CHAP__v2_20.1 |
| WORD-FX | one giant word ("Lekin!", "SALARY?", "₹2 Crore"), red Impact or red italic, can sit behind buildings | `word` | no | WORD-FX__v2_6 |
| PIVOT | red Impact "But…" + Bricolage line, Arjun close-up beside | `word` with `kicker`/`sub`, or `stat` | char | PIVOT__v3_25 |
| SOP | numbered polaroids (coloured frame, black number badge) + kicker + Impact phrase, around Arjun or a "?" | `sop` | polaroid photos | SOP__v2_8, SOP__v3_5-6-7 |
| QMARK | the previous frame cut into shards that form a giant "?" | `scene` with a gen/edited plate, or mark `DESIGNER` | designer/edit | QMARK__v1_6 |
| TAG | hanging ID tag (NAME / AGE / SALARY / INFO / STATE) above each Arjun; unknown = red "?" | `idtag` | no | TAG__v1_3-4-5 |
| PRICE-TAGS | cream tags on strings hanging over buildings ("₹3 Crore") | `hangtags` | plate | PRICE-TAGS__v2_13 |
| OPTION | hanging board "Option-N / NAME" + two objects with ✅/❌ lists | `compare` (or `hangtags`) | object cut-outs | OPTION__v3_36 |
| STAT | Impact number (red) + Bricolage label, curved hand-drawn arrow to the object | `stat` + `arrow` layer | — | STAT__v1_31 |
| STAT-DK | dimmed scene, gold Impact number, white line with gold keywords | `stat` with dark bg | plate | STAT-DK__v1_51new, STAT-DK__v2_12 |
| RUNOFF | a number too big for the frame running off the right edge | `word` with `runoff:true`, huge `size`, left `pos` | — | RUNOFF__v2_18.1 |
| TL / TL-SPINE | vertical line x≈165, red dot, Impact year, grid-paper patch, mini cut-out scene + caption per stop | `timeline` + layers | cut-outs | TL__v1_16, TL-SPINE__v3_9-10-11 |
| CURVE | clean axes / growth curve with a red circle label | `timeline` with `curve` (or `scene` + arrow) | — | CURVE__v2_5, TL-STAT__v1_28 |
| TABLE-HUNG | white table hung by two ropes; blue header (neutral) or red (verdict); rows reveal | `table` (`mount:"hung"`) | — | TABLE-HUNG__v2_27-31 |
| TABLE-DESK | table on grid paper on the desk; red header + yellow column sub-header | `table` (`mount:"desk"`, bg `desk`) | — | TABLE-DESK__v3_32 |
| CHART-DESK | pie charts + legend on grid paper on the desk | `pie` | — | CHART-DESK__v2_10 |
| PICTO | pictogram (building silhouette with red windows) + huge numbers | `scene` + text (pictogram as asset/gen) | small gen | PICTO__v2_10.1 |
| DATA | flat dot grids (women red / men blue / white neutral), comparison sign, % | `dots` | — | DATA__v1_66, DATA__v1_74-75-76-77 |
| CALC | big-type equation, answer swaps in red; or calc printed on a banner draped over a building | `calc` | — | CALC__v2_26, BANNER-CALC__v2_34 |
| EXPLODE | object split into parts by translucent blue blocks, each with a label + red ₹ | `scene` + translucent rects (`text` with bg) + labels | object | EXPLODE__v3_26 |
| SIGN | white placards on wooden stakes in front of a building | `placards` | building plate | SIGN__v1_35-36 |
| CHECKLIST | wooden clipboard, Impact "Checklist", ticks one by one, taped polaroid of the current item | `checklist` | photo | CHECKLIST__v2_55 |
| CALLOUT | white pills with red text pinned on an aerial (often greyscale); or italic labels on thin leader lines with a dot | `callouts` (`pill` / `leader` / `dpill`) | plate | CALLOUT__v2_45, CALLOUT-LEADER__v3_3 |
| SRC | re-typeset article (source, title, body, highlighted sentence), on a hung card / held by a hand / with a torn photo | `article` | optional photo | SRC__v2_18, SRC-HUNG__v1_67 |
| NEWS-WALL | 4–6 headlines re-set in Bricolage SemiBold, staggered, each with its publication name | `news_wall` | — | NEWS-WALL__v2_41 |
| NEWSPAPER | open newspaper / magazine spread, page flips per beat | `scene` (gen/designer) + text | yes | NEWSPAPER__v2_14-15-16 |
| DOC-STAMP | aged paper, Impact heading, a suited hand stamping a red seal ("REPEALED", "NOT REGISTERED") | `scene` + gen paper/hand + text | yes | DOC-STAMP__v1_24, DOC-STAMP__v2_61 |
| HUB | teal centre box "Current value of Gold ₹X" + 4 instruments around it with red values | `hub` (+ `timeline` layers for "5 Years Later") | object cut-outs | HUB__v3_49 |
| FLOW | A → B → C objects with thin arrows and labels | `flow` | object cut-outs | FLOW__v3_19 |
| GREY-FOCUS | world greyscale, Arjun + one object in colour | `scene` with `bg.look:"grey"` + colour layers | plate | GREY-FOCUS__v2_23 |
| VIGNETTE | binocular mask (red) over a scene | `vignette` | plate | VIGNETTE__v2_19 |
| OTS | over-shoulder giant Arjun head holding a phone with a clean UI + small reacting Arjun | `scene` + phone UI text | char gen | OTS__v2_46-47 |
| BUBBLE | cream thought bubble with an icon or a mini memory scene | `scene` + layers | content | BUBBLE__v1_48 |
| STAGES | life stages of a child with Impact red "Baby stage / Age (0-2)" labels | `scene` / `stat` per state | gen | STAGES__v3_4 |
| PAST / MEMORY | sepia version of an earlier frame / greyscale vignette memories around a colour present | `scene` with `look` | plates | PAST__v1_64, MEMORY__v3_53 |
| METAPHOR | a physical stand-in for an idea: see-saw, glass model, banner on a building, chest of gold | `scene` + kit props (see-saw) or gen | often | METAPHOR__v2_51-53 |
| XSECT | camera dives underground into a soil cross-section, white Impact stat | `scene` + gen | yes | XSECT__v2_50 |
| CLOSE | extreme close-up of a face for an emotional beat | `scene` + gen | yes | CLOSE__v3_52 |
| UI / SCREEN | phone or YouTube interface frame; real site walkthroughs are screen captures | `scene` / mark `SCREEN` | — | — |

## Composition constants (from PSD measurements)
- Canvas 1920×1080. Left text margin **139 px**. Chapter title block top ≈ 170–300.
- Timeline: line x = 162–167, dot ⌀ 52 at x 139, year Impact 133–215 px at x 228.
- Characters stand with feet at y ≈ 990–1030; full-height Arjun ≈ 520–580 px tall; three abreast at x ≈ 300 / 800 / 1280.
- Hanging things (tags, boards, tables, article cards) hang from **twine ropes that run off the top edge**.
- Shadows: soft drop to the lower right; cut-outs get a soft contact shadow.

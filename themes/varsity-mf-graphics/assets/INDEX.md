# Asset index (paths relative to assets/)

All taken from the GIFT City PSDs. Grep this file for a word; don't read it all.

| file | size | what / where it is used |
|---|---|---|
| bg/bg_light_grid.jpg | 1920x1080 | cream paper with faint blue grid. Light scenes and tables |
| anchor/anchor_plate_right.jpg | 1920x1080 | **preview only**: anchor still placed right, dark gradient on left. Ribbon / definition frames |
| anchor/anchor_cutout_right.png | 1920x1080 | **preview only**: anchor cut out, drawn above the ribbon so the ribbon tail goes behind her (roto) |
| decor/burst_orange.png | 842x516 | orange spiky burst. Behind a hero object (0.02); small at the bottom edge of dark frames |
| decor/floor_stripes.png | 926x399 | black slanted "floor" stripes under a hero object |
| decor/frame_square_blue.png | 243x244 | tilted blue gradient square frame, corner decor |
| decor/frame_square_green.png | 241x241 | tilted green/white square frame, bottom-left decor |
| decor/frame_square_purple.png | 160x160 | small purple square frame |
| decor/star_blue.png | 107x107 | 8-point blue star, dark frames top-right |
| decor/leaf_green.png | 82x75 | green half-circle leaf, dark frames |
| decor/ribbon_yellow_curve_full.png | 1920x1080 | yellow dashed wave behind the ribbon (full-canvas, already placed) |
| illus/vault_open.png | 612x642 | open steel safe: investing, holdings, "where your money sits" |
| illus/folder_docs.png | 691x548 | orange folder with papers: a fund, a portfolio, a document set |
| illus/notes_coins_stack.png | 265x165 | rupee notes + coin stack (3/4 view): money, investing |
| illus/coins_notes_flat.png | 350x151 | coins + notes lying flat: money, redemption, cash |
| illus/logo_card_apple.png / _microsoft / _nvidia | ~170 | tilted brand cards (example of the logo-card treatment) |
| illus/map_gift_city.png | 1578x1064 | illustrated GIFT City map (topic-specific) |
| illus/map_legend.png | 270x345 | map legend card |
| ui/icon_search.png | 78x78 | white magnifier for the search pill |
| ui/icon_rupee_coin.png | 73x73 | gold rupee coin for the coin pill |
| ui/tile_orange.png / tile_pink.png / tile_green.png | ~400 | grainy gradient tiles with corner handles (SOP numbers, cycle steps) |
| ui/cursor_pixel_3d.png | 103x135 | pixel cursor with 3D shadow (dark frames) |
| ui/cursor_arrow_outline.png | 121x136 | flat pixel cursor (light frames) |
| ui/ribbon_blank_full.png | 1920x1080 | white torn-paper ribbon + coin, full canvas, already placed |
| ui/def_blue_tab.png | 1131x126 | blue capsule tab beside the definition box |
| ui/grain.png | 256x256 | grain overlay tile |

Need something not here (a building, a phone, a calculator)? Draw a flat SVG inside an `html` block (thick dark outline, flat fill, a little grain) or set `"asset": "TODO:<description>"` and list it under "assets for the designer" in the hand-off.

# House style: Varsity Mutual Fund IP

Measured from the GIFT City PSDs (1920×1080). The templates already encode all of this. Read this file only to extend the kit or to hand-write an `html` block.

## Type
- **Inter** only (bundled in `templates/fonts`).
- Keyword pill / ribbon: Inter **Black 900**, ink `#1d1d1d`, grainy texture. Scene pill ≈ 88 px, definition pill ≈ 70 px, ribbon 110–150 px.
- Labels / numbered parts: Inter **Bold 700** ~42 px, near-black `#070708`, number in an outlined circle.
- Definition text: Inter **Medium 500** ~35 px (shrinks to fit), sentence case.
- SOP question boxes: Inter Medium ~52 px, white on `#1b1b1b`, 2 px grey `#8a8a8a` border.
- SOP numbers: Inter SemiBold *italic* ~104 px, white, centred in the tile.
- Tables: header Inter Bold 34–40 px white; body Inter Medium 25–30 px black.

## Colour
| token | hex | use |
|---|---|---|
| ink | #1d1d1d | headline text |
| dark bg | #1b1b1b + grain | SOP, cycle, lists, dark tables |
| dark grid | #3a3a3a lines at x=384/767/1150/1535, y=310/694 | dark frames (tiles snap to these cells) |
| cream bg | bg_light_grid.jpg | light scenes and tables |
| pill purple | #4a44c9 → #5b55e6 → #7b76ee (left→right), text #fff | every keyword pill |
| pill shadow | #0c0c0c, hard offset 14 px | under pills |
| table header | radial: #5ed0ef glow → #2f6fd2 → #1c2fae | all tables |
| tag Active | #e4950b | table tags |
| tag Passive | #3da20c | table tags |
| tag FoF/other | #4238c2 | table tags |
| highlight cell | #fff4c7 | "highlight as per VO" |
| tiles | orange #d9612d→#e49536 · pink #332fa8→#dc5484 · green #8dc759→#6da43f | numbered tiles, cycle steps |
| decor | zigzag #f2b632 · diamond #f39a2b · bars #4f9bf0 / #5b55e6 | confetti |

## Components (template → where it appeared)
- **Search pill** (magnifier + keyword + white knob): the topic of a light scene. Seen at 0.02, 0.10, 3.23-a, 4.00.
- **Coin pill** (rupee coin in a white circle + keyword): term headers over the anchor or on lists. Seen at 1.38, 4.53, 5.21.
- **Definition box**: blue capsule tab on the left edge + light-grey rounded box under the coin pill, all in the left 70 % of the frame. Seen at 1.38, 4.53, 5.21.
- **Ribbon (Roto big text)**: white torn-paper ribbon waving left→right with a coin at its end, a yellow dashed wave beneath, keyword on the ribbon. The anchor is rotoscoped **in front** of the ribbon tail. Seen at 0.24, 6.04.
- **SOP tiles**: grainy gradient squares in grid cells, dashed white edge, black square handles at the corners, question boxes alternating below / above / below. Seen at 0.27, 3.56.
- **Light scene**: cream grid paper, pill at the top, a hero illustration at the centre on black slanted "floor" stripes, an optional orange burst behind it, numbered labels in an arc, confetti at the edges, a pixel cursor pointing at the highlighted item. Seen at 0.02, 0.10.
- **Table**: white table, 3 px dark rules, blue-glow header. Light tables get gradient "stair" blocks top-right (blue) and bottom-left (orange). Dark tables can blur columns that haven't been revealed yet, with a yellow scrub marker. Seen at 0.55, 5.58.
- **Cycle**: donut split into N sectors, number badges on the ring, step tiles in the four corner cells. Seen at 3.23-a.

## Layout rules
- Over-anchor frames: the anchor sits right (face ≈ x 1340–1590, y 110–480). Graphics stay left of x≈1320. Never cover the face.
- Light/dark full frames: keep content inside a 60 px margin, except deliberate bleed (map, tiles at frame edges, decor).
- Confetti stays at the edges and never crosses text.
- One highlight colour per frame (yellow number circle / yellow cell / yellow outline).
- Illustrations are textured "risograph" cut-outs (grain, halftone). Don't mix in glossy 3D, emoji or stock icons.

# THE Zero1 Hindi theme (locked by the team, 2026-11-18)

Reference frames: `assets/theme/theme_01_office_deal.jpg`, `theme_02_exterior_certificate.jpg`,
`theme_03_tv_screencapture.jpg`. **Every new plate must look like it belongs next to these three.** The image
generator sends them as style references with every plate, plus `assets/characters/arjun_canonical_sheet.jpg`
whenever a person is in the shot. Older plates (`plates_index.md`) still work for layout ideas and reuse, but some
of them are clay/cardboard-looking: prefer a new `gen:` plate when the old look would stand out.

## 1. Material: paper first, with judgement
The default for every surface is **matte textured handmade paper**: visible fibres, speckles and fine grain, folded,
cut and layered. Not cardboard. Decide per object, the way a paper-craft model maker would:
| Object | Material |
|---|---|
| walls, floors, furniture, upholstery, curtains, rugs, buildings, plants, clothes | textured paper (charcoal speckled paper on chairs, knitted-paper rug, paper curtains, folded-paper leaves) |
| things that are cardboard in real life: parcel boxes, cartons, packaging, a moving box | kraft card / corrugated board |
| notice and pin boards | cork-like pressed paper |
| the characters' bodies, real wooden props (shelves, desk tops, a wooden map) | light wood with visible grain |
| exterior ground | cracked paper ground with paper rocks and dry-grass tufts; trees are crumpled-paper canopies |
| screens, ₹500 cash bundles | may look real (the only exceptions) |
Nothing glossy, plastic, metallic-shiny or photoreal. When unsure, choose paper.

## 2. Palette: earthy and muted, three accents
- Scene tones: kraft beige `#DFBBA4` / `#E5C09B`, warm tan `#C5997B`, sienna brown `#A5673B`, dark walnut `#704D3C`,
  off-white paper `#DFD8CE`, charcoal/slate speckled paper for furniture, soft sky blue `#9CB1B9` (exteriors only).
- Accents ONLY in the house colours: RED `#A4403B` (Arjun's shirt, numbers, book spines, stamps), BLUE `#447599`,
  YELLOW `#D7A742`. Keep them small; the scene itself stays low-saturation. No bright green, purple, orange or neon.
- The same three colours are the only accents in the kit's typography and shapes (`style_guide.md`).

## 3. Light and camera
- Warm, soft late-morning window daylight; gentle soft shadows; slight haze. No hard sun, no neon.
- A stop-motion film still: shallow depth of field, an out-of-focus foreground prop, a real lens perspective.
- Favourite shots: 3/4 medium two-shot across a desk (theme_01), over-the-shoulder behind Arjun (theme_03), low wide
  exterior with paper ground in front (theme_02). Subject on the thirds, room for text.

## 4. Characters
Every person is a wooden-block toy and **head + neck + torso are ONE continuous block**: no separate neck, no neck
joint, no separate head piece, no seam. Clothes (textured paper) wrap around that block. Arms and legs are separate
small blocks; chunky C-shaped wooden hands; grey-silver metal shoe blocks; tall proportions. See
`character_and_prompts.md` and the canonical sheet.

## 5. Information in the world
- Paper documents and cards are generated BLANK; titles and numbers are kit text layers.
- Screens (TV, monitor, laptop, phone) are generated switched on but EMPTY, evenly lit white, front-facing, so a
  screenshot can be placed on them.
- Money = stacked real ₹500 bundles.

## 6. Layers
Plates with Arjun or other people are split into a clean background and a characters picture when the frames go to
Make Layers, so the characters move on their own layer in the PSD. Keep characters clearly separated from
busy foreground props when you write a prompt (a character half-hidden behind a desk still works, but the desk stays
in the background layer).

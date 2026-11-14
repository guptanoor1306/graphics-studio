# Character bible + image-generation prompts

The PSD layer names show the team generates Arjun plates in **Magnific (Freepik)** and composites them in Photoshop. The kit renders all typography, data, boards and tables itself. Only the **pictures** (dioramas, characters in new poses, objects) need an image model. The build writes ready-to-paste prompts to `out/_image_prompts.md`; this page explains how to write the `gen` entries well.

## The look (applies to every plate)
- **Handcrafted miniature diorama photographed in a studio**: clay, wood, card and fabric miniatures, soft rounded edges, warm golden-hour light, soft shadows, shallow depth of field, stop-motion feel.
- **Authentic regional detail** is non-negotiable (designer note in V1: "Is chapter ki sari chezein will be andhra style… do your research"). Use the right architecture, costume, shop signage style, vehicles (KSRTC bus in Kerala), trees, and decor (jasmine garlands, kolam, Khasi wooden houses).
- **No text inside generated images.** All words are added by the kit, so signboards are generated blank and text goes on as a layer.
- Real landmarks (malls, metro, statues, city sign) may be **real-photo cut-outs** for a city collage (V2), but people never are.

## Arjun and every other person
| Part | Spec |
|---|---|
| Head | tall rectangular **light-wood block** with visible grain |
| Eyes | **two small vertical black ovals**. Not squares, not dots (V3 #52 shipped square eyes, an error) |
| Nose / mouth | none by default. Add a mouth/brows **only** for an expression beat |
| Hair | layered **black cut-paper / cardstock fringe**; women: long black cut-paper hair, bun or braids, flowers for festive |
| Body | blocky; jointed wooden arms with mitten hands; wooden legs (city) or legs under cloth; **grey-silver block shoes** |
| Clothes | real fabric/felt, regionally correct |

**Variants (keep costume fixed for the whole episode):**
- `city`: red short-sleeve tee with a front kangaroo pouch pocket (V2 Noida)
- `kerala`: red half-sleeve shirt + white mundu with thin gold kasavu border (V1, V3)
- `andhra`: white shirt, cream angavastram with gold stripes, white dhoti with gold border (V1)
- `meghalaya`: red-yellow turban, black embroidered Khasi jacket, red dhoti-pants, red bead necklace, yellow sash (V1)
- New state? Follow the same pattern: everyday local men's wear of that state + one signature accessory. Add it to this table.

**Expressions** (`expr`): neutral · worried (raised brows, down-turned small mouth, hand scratching head) · happy (small smile) · thinking (hand on chin) · aged (grey fringe + grey moustache) · crying (glossy drops under eyes + small smile).

**Side characters** (family, jeweller, loan officer, guard, crowd) use the **same wooden-block model**: moustache for older men, saree/mundu/jainsem for women, uniform for a guard. Every past episode slipped here (Lego-minifig guard, smooth-faced loan officer, plastic crowd), so say "same wooden-block figure style as Arjun" in the prompt.

## Writing a `gen` prompt
Describe **what is in the frame and where**, not the style (the build appends style + character bible):
```json
"kirana_empty": {"prompt": "Arjun stands behind the counter of his small kirana store, back shelves half empty, sacks of rice and red chillies in front, Andhra village street visible through the door", "arjun": "andhra", "aspect": "16:9"},
"kirana_full":  {"prompt": "Same kirana store, same camera angle, shelves fully stocked with colourful packets", "arjun": "andhra", "aspect": "16:9"},
"house_cutout": {"prompt": "Traditional Kerala house with sloping clay-tile roof, wooden pillars, front verandah, red-earth yard, hibiscus bushes", "cutout": true}
```
- **Builds need matching plates.** For a before/after on the same set, say "same camera angle" and generate from the first image (image-to-image / reference) so the set doesn't jump.
- **Leave empty space where text will go** ("empty sky in the upper-left third").
- Use `cutout:true` for objects and floating scenes (gold bars, house, NSE building, chest). Remove the background before compositing (the kit applies a soft shadow).
- Use 16:9 for full-bleed plates and 1:1 / 3:4 for cut-outs.
- Never put brand logos or readable text in the prompt. Real brand names (Muthoot, Manappuram, NSE) go on as kit text layers or real logos supplied by the team.

## Kit assets you can use without generating
`assets/characters/`: Arjun city (neutral, worried scratching, worried with phone, happy thumbs-up with clipboard, aged), Kerala (neutral, thinking with gold, close-up holding necklace, aged), Andhra, Meghalaya, plus the Meghalaya family (father, mother, two sisters, Arjun).
`assets/props/`: blank hanging ID tag, price tag, option board, rope, see-saw plank + ground, cloud, jasmine garland, grid patch, 22K necklace, jewellery tray (top-down), thought bubble and phone examples.
Poses not in the kit (e.g. city Arjun thinking, Andhra Arjun worried) → generate with `arjun` + `expr`, `cutout:true`. `*_example.png` props have UI text baked in and are references, not reusable blanks.
`assets/maps/`: wooden India map (AP highlighted), flat India map (NE highlighted). `assets/scenes/`: Meghalaya village strip + house, Kerala house cut-out with Arjun.

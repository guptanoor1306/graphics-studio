# Style guide (locked system)

## Type: two families only
| Role | Font | Size (1920×1080) | Colour |
|---|---|---|---|
| Chapter title | Impact | 139, 2 lines, x 139 | #070707 |
| Chapter kicker "Chapter-N" | Bricolage Grotesque Light, italic | 54 | #070707 |
| Year on timeline | Impact | 133–215 | #1F1F1F |
| Big number / stat | Impact | 110–240 | red #B23636 (gold #E0A422 on dark) |
| Emphasis word / question | Impact | 95–256 | red |
| Pivot word ("Lekin!") | Impact, or Bricolage italic | 300+ | red |
| Label under/over a number | Bricolage Regular | 40–64 | #000 (white on dark) |
| Map labels | Impact 54 (states) / Bricolage Light 27–54 (small) | | #000 |
| Tag/board kicker | Bricolage Regular | 35–40 | #1F1F1F |
| Board / option name | Impact | 52–60 | red |
| Table rows | Bricolage Light / Medium for totals | 38–46 | #111 |
| Article title / body | Bricolage SemiBold / Light | 44–71 / 25–30 | #000 |
| Placards | Bricolage Medium | 33–40 | #000 |

- **Impact has no ₹ glyph** (the cause of the Myriad/RealText fallbacks in shipped files). The kit's Impact stack falls back to Anton, which has ₹. Designers on a Mac with Impact should set the "₹" itself in Bricolage Bold.
- The kit renders the "Impact" role with **Anton** (bundled, open licence, has ₹), and the HTML lists Anton first so the PNG and the HTML look identical everywhere. Designers rebuilding a frame in Photoshop may swap in true Impact (set any ₹ in Bricolage Bold, since Impact lacks it).
- No other fonts. No emoji except ✅/❌ tick marks (rendered as kit marks).

## Colour
| Token | Hex | Use |
|---|---|---|
| red | #B23636 | THE accent: key numbers, emphasis words, alerts, verdict table headers, women dots. **Only red**: don't drift to #A03631/#992E2E |
| ink | #1F1F1F | years, body |
| gold | #E0A422 | numbers/keywords on dark frames, gold-topic accents |
| blue | #447599 | contrast group (men) |
| tblue | #30749B | neutral table header |
| teal | #127FA6 | neutral value box (HUB) |
| navy | #083061 | signboard frames on buildings |
| yellow | #F2C66D | table column sub-header |
| tagbrown | #592D25 | ID-tag field labels |
| olive | #A39E66 | focus state on the wooden map |
| sand | #DAB08D | dirt ground |
| xblue | #9EC3D6 @ 55% | explode-diagram blocks |
| pie set | #C0533F #317E76 #1E404C #F5D8AE #E0A43A #CFE6DE | pie/donut slices only |

## Materials and props language
- Everything is **physical and handmade**: paper, card, twine, wood, clay, fabric. Boards, tags, tables and articles **hang on twine from the top edge**. Placards are planted on wooden stakes. Documents are aged paper with rubber stamps held by a suited hand.
- Arrows are thin, hand-drawn, slightly curved, with small solid heads (ink), or dashed for travel paths.
- Shadows are soft, falling lower-right. Cut-outs get a contact shadow.
- **Grades:** greyscale for focus/past, sepia for history, darkened ~70% for gold reveals, red multiply for crisis.

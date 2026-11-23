# Style guide (locked system)

## Type: two families only
| Role | Font | Size (1920×1080) | Colour |
|---|---|---|---|
| Chapter title | Impact | 139, 2 lines, x 139 | #070707 |
| Chapter kicker "Chapter-N" | Bricolage Grotesque Light, italic | 54 | #070707 |
| Year on timeline | Impact | 133–215 | #1F1F1F |
| Big number / stat | Impact | 110–240 | RED #A4403B (YELLOW #D7A742 on dark) |
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

## Colour: three colours only (team rule, 2026-11-18)
| Token | Hex | Use |
|---|---|---|
| red | **#A4403B** | main accent: key numbers, emphasis words, alerts, stamps, "spent"/negative, verdict headers, highlighted state |
| blue | **#447599** | second accent: neutral table headers, label boxes, info cards, value boxes, contrast group |
| yellow (gold) | **#D7A742** | third accent: tags, stickers, "saving"/positive highlight, numbers/keywords on dark frames |
| ink | #1F1F1F | years, body text (white on dark) |

- Nothing else in type, boxes, bars, charts, stamps or highlights: no green, coral, orange, plum, navy, teal or the old reds (#B23636, #B13535, #CD0000, #911212, #A03631, #992E2E). The spec's older names still work and draw in these colours: `gold`/`yellow`/`olive` → YELLOW, `blue`/`tblue`/`teal`/`navy` → BLUE, `tagbrown` → ink.
- Pies/charts with more than three parts use the three colours, then their pale tints (#C98A86, #8FAEC4, #E8CF8E).
- Natural colours of the diorama world (paper, wood, sky, plants) stay natural and muted; generated props are steered to the three colours ("a red #A4403B stamp", "a mustard #D7A742 tag", "a slate-blue #447599 card").

## Materials and props language
- Everything is **physical and handmade, and the default material is matte textured paper** (see `theme.md` for when card, cork or wood are right instead). Boards, tags, tables and articles **hang on twine from the top edge**. Placards are planted on wooden stakes. Documents are aged paper with rubber stamps held by a suited hand.
- Arrows are thin, hand-drawn, slightly curved, with small solid heads (ink), or dashed for travel paths.
- Shadows are soft, falling lower-right. Cut-outs get a contact shadow.
- **Grades:** greyscale for focus/past, sepia for history, darkened ~70% for gold reveals, red multiply for crisis.

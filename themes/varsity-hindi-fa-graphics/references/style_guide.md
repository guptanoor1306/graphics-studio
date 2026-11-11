# House style: Varsity Hindi, Fundamental Analysis series

Look at `style_at_a_glance.jpg` once. Everything below is what the build already does by default.

## Set
- **FSS**: light sky gradient (near-white top centre, pale blue `#AFD2E7` edges, soft blue glow), white wavy line-art at both edges, **white perspective-tiled floor** from y≈835, Varsity eye capsule top-left (top-right when a header is there), a sparkle, 1–2 floating gold ₹ coins.
- **OSA**: same set with the presenter cut out on the right half. Text and cards sit **left of x≈1000**, vertically centred (y 230–850).
- **osa_center**: presenter centred; two pills/cards either side (Qualitative | Quantitative).

## Type: Inter only
| use | weight |
|---|---|
| giant concept word / big titles | ExtraBold 800, tight tracking |
| section header with coral bar | ExtraBold Italic |
| plain headers | Bold 700 |
| name pills on scenes | Medium Italic |
| list pills, chips, card text | Medium/SemiBold, upright |
| formulas | term ExtraBold in a highlight block; fraction Medium Italic |

## Colour
| | hex | only for |
|---|---|---|
| ink | `#141414` | text |
| coral | `#EF5143` | header bars, underline under one header word, triangle/square bullets, negative bars, SELL |
| blue | `#2F7CF6` | chart lines, connectors, divider, dot bullets, ROE-type bars |
| green | `#86BD65` | positive/profit bars, BUY |
| orange `#E8611A` / yellow `#F6C21C` | bar and pie series |
| highlight yellow | `#F5D36B` | label/value blocks (calc, headers of mini charts) |
| highlight blue | `#8DB6FA` | ratio-name block in a formula |
| white / frosted glass | | every pill, card, badge, box |

Green and coral never fill a pill, card, header or highlight block.

## Components (see `spec_format.md`)
- **Pills**: white, 2 px light border, soft shadow, fully rounded. Scene labels are italic with a hand-drawn curved arrow to the subject; list pills upright; word chips bold; method pills may tilt ±8°.
- **Glass cards**: white ~58 %, white border, 28 px radius, soft blue shadow. Definitions are quoted; formulas use a highlight block + fraction; calculations stack yellow-labelled rows.
- **Headers**: five looks. Coral-bar italic (Ep 2) for section headers over charts/comparisons; giant word with a prop overlapping (Ep 5) for concept scenes; plain bold with a coral underline under one word (Ep 8); coral-bar two-line stack (Ep 8 OSA lists); white box / light-blue label (Ep 9). Pick one look per frame; keep it consistent within a section.
- **Charts**: glass card or standing on a landscape phone lying on the floor. Bars with white circle value bubbles; lines blue with dotted drops to labelled points; pies with labels inside slices and white gaps.
- **Scenes**: buildings and characters on the floor; money as coins on a dashed arc; parts of a whole as blue elbow connectors into round icon badges; a magnifier over the thing being examined; a lamp spotlight over a reveal.
- **Module page**: "Module N" with coral bar; 4 glass cards with big numbers; current card white with a black number and a cursor; done cards faded, upcoming blurred.
- **Key Takeaways**: pink swoosh from a coral megaphone bottom-left; "Key / Takeaways" with coral bar; numbered SemiBold list on the right.

## Characters
The team's six characters (`char` element, c1–c6) plus the seated trio. Heads, faces, bodies, legs are never altered; the build adds arm poses and mouth expressions only. Every scene with people uses several **different** characters with poses that match what each person is doing.


## Drawn scenes (story beats)
Flat illustrated environments (`backdrop`) with flat props outlined in the characters' dark line (3 px #1d1d1d). Sky light blue, fields golden, market buildings pastel. See `drawn_backdrops.png` and `drawn_props.png`. Don't mix these with the glossy 3D buildings in one frame.

## Futures series OSA
Dark frosted card (charcoal ~74 % opacity, light border, 22 px radius), white text, active list item in yellow; header = white box with a blue bar along its bottom. Delivered as transparent overlays.

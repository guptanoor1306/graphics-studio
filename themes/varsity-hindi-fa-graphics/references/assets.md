# Asset library (all cut from the team's final PSDs)

Use with `{"type":"img","src":"<folder>/<name>","cx":…,"by":…,"h":…}`. `cx` = centre x, `by` = bottom y (where it touches the floor), `h` = height on screen. Natural size in brackets; don't scale bitmaps far above it.

## chars6/ + `char` element: the team's six Varsity characters (people)
Head, hair, face, eyes, body, legs and shoes are the team's PSD artwork, untouched; the build draws the stick arms (same stroke, the team's mitten hand) for 12 poses and redraws only the mouth for 6 expressions. See `characters_poses.png`.

| id | look | typical role |
|---|---|---|
| c1 | yellow, curly hair, cheerful | main example person (farmer Rajesh, investor) |
| c2 | blue, short curly hair, sceptical | second person, seller, sceptic |
| c3 | coral, woman, bindi | woman, customer, buyer, family member |
| c4 | yellow, spiky hair, glasses | young trader, seller, analyst |
| c5 | blue, round, hat, moustache | business owner, older person (mill owner, buyer) |
| c6 | yellow, quiff | Varsity explainer, any extra person |

Never recolour or redraw them; only position, size, mirror (`flip`), pose and expression.

## chars/ (seated trio from the FA finals: fixed pose, with armchairs)
`trader_seated`, `investor_seated`, `speculator_seated`: market participants / shareholders / investors seated. Standing people always use `char`.

## buildings/
| name | what | use for |
|---|---|---|
| `office_glass` | blue glass office block with trees (702×698) | "Company", generic business, the balance-sheet company |
| `bank` | 3D bank with BANK sign (892×719) | lender, FD, loans |
| `tower_xyz` | tall blue tower (635×697) | "XYZ Company", Company A/B |
| `showroom_bajaj` | Bajaj two-wheeler showroom (1074×552) | **only when the script is about Bajaj Auto** |
| `pharma` | hospital-style blue campus (808×554) | pharma company, Company C |
| `government` | neoclassical blue building (791×643) | regulator, government body |
| `house` | 3D house (799×589) | home loan, personal asset |

## props/
| name | use |
|---|---|
| `coin` | ₹ coin; money in motion (`coinflow` uses it), deco coins |
| `coin_stack` | growth, invested capital, profit pile |
| `cash_stack`, `cash_bundle` | profit, dividends, loan amount |
| `magnifier` | analysis, "look closely", highlight one item |
| `megaphone` | key takeaways (the template places it) |
| `lamp_yellow`, `lamp_blue` | spotlight over a reveal (title / card set) |
| `phone_landscape` | stage under a chart (`"stand":"phone"` does it) |
| `folder_report` | folder with statement tabs + annual-report page (deep research) |
| `paper_scroll` | trader's plan / notes |
| `factory_machine`, `milk_can`, `sugar_sack`, `carton_box` | production / inventory |
| `credit_card` | short-term borrowing, spending |
| `calendar` | due dates, time passing |
| `balance_scale` | valuation vs price, comparing two quantities. Use the `scale` element, which labels the strips |
| `patent_approved` | approval, regulator decision |
| `motorbike` | auto company product |
| `india_map` | plants/locations (add coral pins with `html` dots if needed) |
| `icon_building`, `icon_conveyor`, `icon_shopping`, `icon_fuel` | round badge icons for `branch` |
| `kite_chevron` | used by `window` |

## plates/ (used by the build automatically)
`lineart_left/right` (edge line-art), `floor` (tiled floor), `anchor_right` (presenter right half, for `mode: osa`), `anchor_center` (`mode: osa_center`), `varsity_eye` (logo capsule), `sparkle`.

## Two style families: never mix in one frame
- **Drawn (flat, dark outline)**: `backdrop` environments + `prop` kinds + characters. Use for stories with people (farm, mandi, shop, deal, scenarios).
- **3D glossy (team AI renders)**: `buildings/*` and the 3D `props/*`. Use for institutions and companies (exchange, bank, regulator, Company A–D) on the light set.
- `buildings/tower_xyz` is flat line art: don't put it next to 3D buildings. No 3D building on a drawn backdrop. The build warns on both.

## logos/
- `logos/listed_logos.json.gz`: ~3,150 NSE/BSE-listed company logo tiles packed in one file (TradingView icon set via the public `shareperks/indian-listed-company-logos` repo), found by ticker (`SBIN`, `BAJAJ_AUTO`) or company name. Rounded-tile look.
- `logos/<name>.svg|png`: institutions that aren't listed (NSE, NCDEX, SEBI, RBI, NSDL, Nifty 50, Sensex, AMFI). Add files here as they arrive; until then the build shows a dashed placeholder and warns.
- A named organisation is shown by its logo (on a card, above a building, as a list icon), never by a generic repeated building.

## Missing a prop or setting?
1. **Story/drawn prop**: compose from `prop` kinds + shapes, or add a function to `scripts/scenes.py` following its style rules (flat fill, 3 px #1d1d1d outline, palette in the file header).
2. **3D object/building**: list it in the storyboard under **New assets needed** with this prompt for the designer (ChatGPT image, the team's existing route):
   > 3D isometric illustration of {OBJECT}, glossy blue-and-white palette (#2F7CF6, #5AA0FF, white), soft studio lighting, smooth rounded shapes, small trees at the base if it is a building, clean white background, no text, no logos, centred, high detail, consistent with a set of blue 3D finance icons.

   Save it as a transparent PNG in `assets/buildings/` or `assets/props/` and use it with `"as"`.
3. Never reuse an asset that shows something else (a biscuit machine as a flour mill, one building for four organisations).

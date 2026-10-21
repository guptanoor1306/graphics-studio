# Varsity graphics: style guide

Everything is 1920×1080 and set in **Inter** (Regular, Medium, SemiBold, Bold, ExtraBold). The kit's CSS (`templates/varsity.css`) implements every component named here. Look at the frames in `references/*_finals/` before designing. They are the ground truth.

## 1. The two screen modes

### OSA / OST: graphic over the anchor shot
- The anchor sits on one side, with the edge of her body around x≈900 (anchor right) or x≈1000 (anchor left).
- **Graphics live only on the empty side.**
  - Anchor right: x 140–880 below the shoulder line (y>330), and up to x 1100 above it for title pills and definition banners.
  - Anchor left: mirror it (x 1040–1780; up to x 820 above the shoulders).
  - Never cover her face. The outer 120px margin is for dressing (wire, paper doodle).
  - A definition banner may run across the top **above her head** when the anchor sits lower or more centred (Overdraft 1:12).
- The empty side is darkened by a black gradient (solid near the edge, fading out before the anchor), so text there is **white**.
- Dressing on that side:
  - a faint grid (Set A);
  - thin blue wire curves ending in small square nodes;
  - 1–2 white paper/speech-note doodles;
  - a stack of gold ₹ coins on the floor line;
  - a doodle character standing on the floor (often holding a green ₹ money bag).
- The floor strip (a grey band, y≈1000–1080) runs across the bottom. Characters and props stand on it.
- The exception is the **roto big-text title** (HUF 0:13): giant letters sit behind the anchor and span the frame.

### FSS: full-screen slide (anchor off screen)
- **Background:** a light "sky" with soft clouds, checkerboard floor perspective at the bottom (y≥985), blue wire curves with square nodes, and paper-note doodles at the edges. Optional props: pendant lamps, a potted plant, an outdoor variant with grass and a fence.
- **Accent per video:**
  - **blue sky** (`fss_sky_blue.png`, accent `#248EF7`);
  - **warm cream** (`fss_sky_warm.png`, accent `#F2B233`; add class `warm` to `<body>`).

  One accent per video, never mixed.
- Text is **ink #171717** on white cards.
- **Heading:** the header tab (`.htab`): a white box with a black outline, a coloured bottom bar and a tiny "– ×" tag. It is centred at the top (y≈40–80), or top-right when a character fills the left.

## 2. Colour tokens

| Token | Hex | Used for |
|---|---|---|
| blue | #248EF7 | chart bars and areas, header-tab bar, blue table headers, icon chips, folders |
| blue-soft | #64B0FC | document section tags |
| amber | #F2B233 | calc-table header row, shortfall bars, title tags, keyword accent, warm-FSS accent |
| green | #A5CC65 | callout bubbles, ₹ map pins, "saved / tax-free" pills, net-saving result pill |
| coral | #F26B5B | giant hero keyword (HUF), red flags, "taxable" verdicts, loss values |
| ink | #171717 | text on light |
| white | #FFFFFF | text on dark, cards, rows |

Values: gains in green, losses and shortfalls in red/coral, totals in bold.

## 3. Type scale (px at 1920×1080)

| Element | Size / weight |
|---|---|
| Title lead/tail line over the anchor | 71 Regular (or 56 Bold for the bold-lead variant) |
| Hero keyword | 134 Bold with a 4px black hard shadow; **giant** 250 ExtraBold coral, no shadow |
| Header tab | 40 Bold (30 for sub-point tabs) |
| Title pill | 40 Bold |
| Numbered sub-heading | 45 Regular |
| Big value labels ("Cost to exercise ₹10,00,000") | 51–58 Regular, amount Bold |
| Glass table over the anchor | 22–24 |
| FSS calc table | 22 (header 22 Bold); blue-header table 26 |
| Callout bubble | 33 SemiBold |
| Name pill | 22 Bold (35 for the dark pill) |
| Card label / sub-label | 27 SemiBold / 19 grey |
| Definition body | 30–36 Regular |

## 4. Component catalogue (CSS class → when to use)

| Component | Class | Use when the script… |
|---|---|---|
| Title stack | `.t-line` + `.t-key` (`.xl.coral` for giant) | opens a section or asks the hook question. Small connecting words around one huge keyword |
| Title pill | `.pill-title` | names the section, short form ("How can an HUF help save taxes?"). Dark glass over the anchor, white on FSS |
| Header tab | `.htab` (`.sm`, `.green`, `.amber`) | heads any FSS frame; also the **sub-point tab** revealed under a title pill ("Rental Income", "Gifts") |
| Numbered sub-heading | `.num` | is item n of a list and the frame is about that item |
| Icon chip | `.chip` | sits next to a title as a mascot icon (person, family) |
| Glass table (dark) | `.glass` + `.gt` | shows ≤5 rows of numbers over the anchor; `tr.result` inverts the answer row |
| Calc table (FSS) | `.card` + `.ct` (`.blue`) | shows a full computation; `tr.less` (grey italic) for deductions, `tr.total` for the bottom line, `tr.hl` for the row the VO is reading |
| Result pill | `.result-pill` | states the final saving under a table |
| Name pill | `.name` / `.name.dark` | labels a person, company or amount |
| Black label chip | `.chip-label` | labels a bar or stack ("Interest", "Principal") |
| Speech callout | `.callout` (`.white`) | pulls one key sentence out of a document, or speaks for a character |
| Definition banner | `.def` | defines a term over the anchor: amber title tag + translucent strip |
| Definition card | `.defcard` | defines a term as a stacked title ("Tax / **Scrutiny** / Notice") + text |
| Pop-up window card | `.popup` + `.popup-base` | says a sum or total aloud over the anchor |
| Highlight pill | `.hpill` | needs one figure called out from a table the VO is reading (pops over the table) |
| Verdict pills | `.verdict.good/.bad` | needs a taxable / tax-free style verdict |
| Blurred list in folder | `.folder` + `li.off` | introduces a list of pointers that will be revealed one by one |
| Numbered glass list | `.nlist` + `li.off` | gives the FSS "Things to remember / Should you…?" list; the current point is solid, the rest faded |
| Drum list | `.drum` | lists ≥6 short options (ways to e-verify) |
| Icon cards row | `.icard` | lists 4–6 sources, entities or types, each with an object |
| Chart card | `.chartcard` + `.axisbox` + inline SVG | gives growth or comparison numbers (bars vs a dashed target line, an area curve, a stacked bar) |
| Document mock | `.doc` (+ `.blurred`, `.hl-mark`) | mentions a letter, certificate, notice, Form 16 or slip |

## 5. Characters and props

- **Doodle people:** a big round head (≈⅓ of the height) with a black outline, dot eyes in white circles, a solid triangle "dress" with a darker fold on one side, stick legs, white shoes. Colours: yellow #F2B233, blue #248EF7, green #A5CC65, coral #F26B5B.
  - Draw them with `V.person({color, hair:'spiky'|'long'|'none', hat, moustache, bindi, name})`.
  - Or use the PSD-extracted PNGs in `assets/setA` and `assets/setB`: Rahul yellow, money-bag pose, pointing pose, the man in the red dress with a moustache, the retired man in a beach chair.
- **Personas:** each script example person (Rahul, Arjun, Anjali, Mr/Mrs Kapoor) gets one consistent figure and colour for the whole video, labelled with a name pill. A family = 4 figures of different colours side by side.
- **Topic prop:** one recurring prop in a bottom corner of most frames, chosen from the topic:
  - coins (equity, ESOP);
  - TAX doc + pencil + calculator + coins (tax);
  - glass jar of cash (retirement);
  - house (home loan);
  - BANK building (banking).
- **3D objects** (buildings, bank, calendar, cards) come from `assets/`. If an object isn't in the kit, draw a clean **flat** SVG in the same palette with a black outline. Never fake 3D badly, and never use emoji as artwork (emoji only as a stand-in inside `.chip`).
- **Cursor arrow** (`assets/setB/cursor_arrow.png`) and **magnifier** (`assets/setA/magnifying_glass.png`) mark "highlight as per VO" on tables, lists and documents.

## 6. Layout rules

- Max ~40 words of body text per frame; tables excepted.
- One idea per frame. If the VO keeps going on the same idea, the frame stays and only the highlight moves.
- Align to a 40px grid. Cards get 14–24px radius; tables get 6–8px row radius.
- Number format: Indian grouping (₹12,50,000; ₹1.25 lakh; ₹11.2 crore). Copy numbers from the script exactly; never round unless the storyboard does.
- Spell-check every heading. A typo ("ITR Filling") shipped once; it must not happen again.

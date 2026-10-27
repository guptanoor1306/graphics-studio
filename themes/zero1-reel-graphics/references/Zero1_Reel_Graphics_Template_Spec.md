# Zero1 Reel Graphics: Format Library & Template Spec (v1)

Source: 4 reels (Ranking Dark Patterns, Wedding Insurance, Standard Deviation, Axis EV Sector), their storyboards and the moodboard.
Scope: **static graphics only**. Animation comes in part two; motion notes here only say what the end state of each graphic looks like.

> **Canvas:** 1080 × 1920 px (9:16). The source reels were exported at 720 × 1280, so every measurement below has been scaled ×1.5.
> **Open items** are marked ⚠️. They need your confirmation before generation is fully locked (see §7).

---

## 1. Format identification

| # | Reel | Format | Name | Tag | One-line definition |
|---|------|--------|------|-----|---------------------|
| 1 | Ranking Dark Patterns | Ranking | **Tier Board** | `TIER` | Presenter rates N items one by one. Each item drops into a persistent A–F tier board. |
| 2 | Standard Deviation | Versus | **Metric Face-off** | `VS` | Two options look identical on one metric but differ on a second. The reel reveals the second metric, explains it, then widens to N options. |
| 3 | Wedding Insurance | Explainer | **Story Explainer** | `EXPL` | One product/idea told as a story: scenario → what it covers → what it doesn't → verdict. Heavy on full-screen illustration and kinetic type. |
| 4 | Axis EV Sector | Multi-company breakdown | **Sector Breakdown** | `BRK` | A sector split into numbered chapters (parts → risks → opportunities → should you invest?). Companies appear as logo chips in the hook and the portfolio-overlap Venn. |

Notes
- `VS` is a hybrid: Versus in the hook, Explainer in the body. I've kept it as Versus because the A-vs-B setup drives the hook and every comparison graphic.
- The `BRK` reel closes with a mini A-vs-B teaser ("WHO WINS? ICE vs EV"). That's a component (O10), not a separate format.

---

## 2. Reading a storyboard (applies to every format)

The storyboard PDF has 3 columns: **LINES | ASSETS | INSTRUCTIONS**.

| Signal in storyboard | Meaning | What I generate |
|---|---|---|
| `{m:ss – m:ss}` in **green** before a line | Kept segment, with timecode | Graphic(s) for that span |
| `{m:ss – m:ss}` in **red** + struck-through text | Cut segment | Nothing (ignore) |
| Line with no instruction | Plain presenter shot | Subtitle only (G2) |
| ASSETS thumbnail tagged with a timecode | Visual reference for that span | Match its layout using our components |
| ASSETS link (YouTube, PIB, IEEFA…) | Source to screenshot/cite | Doc highlight (F11) / thumbnail (O7) / source line |
| **Header copy: …** | Hook title | H1 (variant by format) |
| **SOP** ⚠️ | Section opener ("What goes in the EV? / 1. Battery") | S1 |
| **OST** | On-Screen Text over presenter | O1 / O2 / O3 |
| **OSA** | On-Screen Asset (icon/object/logo overlaid on presenter) | O4 / O5 / F15 badges |
| **FSS** | Full-Screen Still (graphic replaces presenter) | F-series |
| **FSA** | Full-Screen Animation | F-series still now, animated in part two |
| **PS** | Presenter Shot | No graphic (maybe framed PS) |
| "slow zoom on PS" / "only subtitle" | No graphic | Subtitle only |
| "highlight as per VO" | Mark the words the VO says | Marker highlight on doc/table/number |
| "thumbnail of video link" | CTA | O7 |
| "Zero1 IG bio ss" | Follow CTA | O8 |
| "instead of X write Y" | Copy swap in a referenced layout | Same component, new copy |

**General mapping rule:** every number spoken in VO that the storyboard flags ("highlight number", "show 5000 → 50,000") becomes a stat graphic. A list of 2–4 named things becomes icons/badges. A named source becomes a doc highlight with a `Source:` line. The hook line becomes H1. Any "First / Second / Risk one / Advantages" structure becomes S1 openers.

---

## 3. Global design system (fixed in every reel)

### 3.1 Colour tokens
| Token | Hex | Used for |
|---|---|---|
| `cream` | `#FBF6DA` | FSS / split-panel background (EXPL, VS) |
| `cream-2` ⚠️ | `#FCF8EE` | FSS background in BRK (slightly whiter) |
| `ink` | `#0C0C0C` | Primary text on cream; tier board panel |
| `white` | `#FFFFFF` | Text on presenter |
| `zero1-yellow` | `#F6F66C` | Hook pill, CTA keyword ("Electric", "Zero1") |
| `alert-red` | `#EA001E` (serif) / `#FC363C` (caps OST) | Ranking punch word, "Risks", "SIGNIFICANT RISKS" |
| `marker-orange` | `#E46C24` | Doc highlight (policy/gov source), checklist item 1, Venn bottom stroke |
| `marker-green` | `#00D890` | Doc highlight (research/data source) |
| `mint` | `#48DEA8` / table `#A2EAC6` | Venn top fill, data-table cells, "opportunity" accents |
| `deep-green` | `#06AE78` | Checklist item 2, positive accents |
| `peach` | `#EA9660` | Venn bottom fill |
| `salmon-tile` | `#DE7E5A` | Rounded tile behind hero objects (EXPL) |
| `purple` | `#6C60DE` | VS tag pills, % values on option cards |
| `purple-row` | `#483678` @ ~85% | Highlighted row on dark table (VS) |
| `hl-orange` | `#D85430` | Winner highlight box behind a number (VS) |
| `chart-red` | `#D25A4E` | Line chart stroke |
| `beige-icon` | `#D2C09C` | Icon circle fill (F5) |
| `bms-orange` | `#C65436` | Full-form / sub-label under a concept word |

### 3.2 Typography ⚠️ (closest matches; please send the actual font names/files)
| Role | Looks like | Weight | Seen in |
|---|---|---|---|
| **Display Grotesk** (D) | Clash Display / Gilroy-style wide grotesk, tight tracking (−3 %) | Bold/Black | "EV Sector", "Which mutual fund…", "18.80", "BREAK IT DOWN", "WHO WINS?", "What goes in the EV?" |
| **UI Sans** (U) | Manrope / Inter-style | Light–SemiBold | Sub-headers, labels, table text, subtitles, "1. Battery" |
| **Editorial Serif** (S) | Instrument Serif-style condensed | Regular & Italic | "FOOL YOU", "Getting married", "₹2 lakh" |
| **Bold Serif** (SB) | Tiempos/Gloock-style heavy serif | Bold & Bold Italic | "material damage", "*Indigenous* BMS" |

Casing rules: D is used in Title Case for headers and in ALL CAPS for pivot OST lines. U is sentence case. S/SB are lowercase or Title Case and never all caps, except the Ranking punch line ("FOOL YOU").

### 3.3 Fixed chrome
- **Logo bug (G1):** ZERO1⚡ "by ZERODHA", top-right, box ≈ x 819–1032, y 96–138 (≈ 213 × 42), right margin ≈ 48. Black version on cream, white version on presenter. Present in RANK / EXPL / VS. ⚠️ Absent from the EV (Axis) reel.
- **Safe area:** side margins ≥ 90 px. Keep text out of the bottom 22 % (IG UI). Headers start at y ≈ 220–240.
- **Subtitles (G2):** U SemiBold ≈ 45 px, white, soft drop shadow (0 2 8 @ 40 %), centred, 1–4 words per card. Default baseline y ≈ 900–1130 (chest height), moved up/down to avoid graphics. CTA subtitles go to 2 lines with the keyword in `zero1-yellow` + italic.
- **Framed PS card:** presenter video in a rounded rect x 192–887 (w ≈ 695), y 255–1643 (h ≈ 1388), radius ≈ 45, on cream. Used by S1, F15 and the coins/stamps scenes.
- **Split screen:** top graphic panel on cream, presenter below. Panel height = **960** (VS charts/tables) or **≈ 860** (BRK doc/table/concept). In BRK the presenter panel has 24 px rounded top corners.

---

## 4. Component library

IDs are referenced by the format recipes in §5. Sizes are font-size in px @1080.

### Hooks (H1)
| ID | Layout | Specs |
|---|---|---|
| **H1-A Ranking** | Over PS, centred top. Line 1 small setup + line 2 huge punch. | L1: U SemiBold 54 white, y≈240–300. L2: S Regular ALL CAPS ~186, `alert-red`, y≈333–465, width ≈ 74 %. Stays on screen the **whole reel**. |
| **H1-B Explainer** | Over PS. Serif italic line + bold line + yellow pill with cursor. | L1: S Italic ~144 white. L2: D Bold ~80 white. Pill: `zero1-yellow`, radius 12, U Medium 40 ink, ~50 px pad; black/white cursor arrow on the pill's right end. Block y≈240–560. |
| **H1-C Breakdown** | Over PS. Display title + light subtitle. Logo chips (O4) float around the presenter. | Title: D Bold ~150 white, y≈222–330. Sub: U Light ~66 white, y≈382–450. |
| **H1-D Versus** | Over PS. 2-line display question + 2 option cards (O5) underneath. | D Black ~72, leading 1.15, white, y≈300–450, width ≈ 80 %. |

### Overlays on presenter (O)
| ID | Name | Specs |
|---|---|---|
| **O1** | Pivot OST | L1 U Medium ~48 white @90 % + L2 D Black ALL CAPS ~66, centred, y≈225–330. L2 colour encodes tone: white (neutral: "BREAK IT DOWN", "CARS : CHARGERS"), `alert-red` (risks), mint/`marker-green` (opportunities). Light 30 % dark gradient behind the top band if the background is bright. |
| **O2** | Stat OST | Number D Black ~150 white + label U Regular ~48 white + optional source U 18 white @70 % right-aligned under the label. y≈200–360. |
| **O3** | Serif section OST | Small U Regular ~54 white + big SB Bold ~120 white directly underneath (tight, overlapping leading). Left-aligned at x≈120. ("Then there is / material damage") |
| **O4** | Logo chips | White rounded rects (radius 16, ~310 × 110), brand logo centred, drop shadow 0 6 20 @20 %. 3–5 chips staggered left/right around the presenter's head and torso, partly overlapping him. |
| **O5** | Option cards | 2 cards ~170 × 180, white `#FCF6EA`, radius 30, gap 24, centred under H1-D. Inside: name U Medium 36 ink, value D Bold 42 `purple`, caption U 18 ink ("(5Y Returns)"). |
| **O6** | Number duel | Two numbers D Black ~117 white, separated by a 2 px white vertical rule (h≈130). Under each, a `purple` tag pill (U Medium 33 white). Winner = `hl-orange` box behind the number. y≈200–350. |
| **O7** | Thumbnail CTA | Long-form thumbnail, rounded 16, ~520 × 290, centred top (y≈150–445), drop shadow. Optional caption below: U Bold 48 white "Comment “**KEYWORD**” to get the full video link", keyword in `zero1-yellow`. |
| **O8** | IG bio card | Dark rounded card (`#0F1115`, radius 24, ~570 × 290) holding the Zero1 IG profile screenshot. Centred lower-middle (y≈800–1095). |
| **O9** | Dark table on PS | 2-column table, no bg. Header D Bold 60 white. Rows U Regular 48 white. 2 px white vertical divider. Highlighted row = `purple-row` bar full width. Top area y≈160–400. |
| **O10** | A-vs-B teaser | "WHO WINS?" D Black ~110 white top + "ICE (red) [vs yellow circle] EV (green)" D Black ~90 + two objects facing each other + per-side price U Medium 45 white. |

### Section structure (S)
| ID | Name | Specs |
|---|---|---|
| **S1** | Section opener (SOP) | Cream bg. L1 D Black ~66 ink ("What goes in the EV?"). L2 U Regular ~57 ink ("1. Battery"). Centred, y≈245–372. Framed PS card below. **Variants:** L1 = "Risks" in `alert-red` D Black ~72. L1 = "Advantages" in `deep-green`. Numbering restarts per group (1., 2., 3.). |
| **S2** | Title card with side rules | Cream bg. Centred 2-line U Regular ~66 ink ("Wedding Insurance / in 2026?"), with a 10 px black horizontal rule from each screen edge to the text block, at the vertical centre of line 1. y≈225–330. |

### Full-screen stills (F) on cream unless noted
| ID | Name | Specs |
|---|---|---|
| **F1** | Kinetic type line | Small lead-in U Medium ~36 ink, then the key word U/D Bold ~96 ink, centred at y≈960. One letter of the key word is replaced by a small object (💸 note for "money", life-ring for "compensate"). Trailing words U ~36 ink, right-aligned under it. |
| **F2** | Object + price | Label U Regular ~66 + price S Regular ~110 ink, top-centre right (x≈780 centre). Hero object on a `salmon-tile` rounded rect (radius 30) below. Character illustration bottom-left, walking or reacting. |
| **F3** | Illustration + word | Large cut-out illustration (hospital bed etc.) + one word in D Black ~72 with a small connector word U ~33 ("gets **ill** or"). |
| **F4** | Big number + image | Label U Regular ~66 ink + number D Black ~105 ink (left-aligned at x≈235, y≈380–510). Product image below, with a coloured fill covering the share being described (car tinted mint for 30–40 %). Thin arrow from number to image, plus a secondary label U Light ~42 grey ("Largest Cost"). |
| **F5** | Icon zigzag list | 2–6 items, alternating left/right, stepping down. Each item: beige circle (≈180 Ø, `beige-icon`, 2 px ink stroke) with a line icon, plus a label U Regular ~36 ink above it. |
| **F6** | Map / region stat | 3D beige map image top-left, curved arrow to a stat block: label U Regular ~45 ink + value D Black ~66 ink + unit U ~42. Second stat bottom-left with its own object image. Source line U ~18 top-right. |
| **F7** | Growth compare | Two versions of the same object, small (left, old year) and big (right, new year), on a baseline rule. Each has year U ~36 + value D Black ~90/105 + unit U ~42. Source line centred under the baseline. |
| **F8** | Pictogram ratio | Rows: "1 EV Charger" label + charger image (left) vs a grid of N car icons (right) with header D Black ~60 ("India 190"). Second row = benchmark. Source line bottom. |
| **F9** | Checklist | Header D Black ~66 ink, centred top ("Basics of Personal Finance"). Items U Regular ~66, each rotated −4° to +4° and coloured in turn: `marker-orange`, `deep-green`, ink. |
| **F10** | Venn overlap | Two circles stacked vertically (Ø≈500), top `mint`, bottom `peach`, overlap blended, thin dark stroke. Logo chips (O4 small) inside each. Handwritten-style label "Your Portfolio" (U Light ~66) with a curved arrow into the top circle. |
| **F11** | Doc highlight (split) | Top panel (cream, h≈860): source masthead/logo + date line, 2 px rule, then the article text U Regular ~42 ink (headline D Bold ~54 caps if present). Highlight = marker rectangle behind the exact VO words (`marker-orange` for govt/policy, `marker-green` for research ⚠️). PS below, with `Source: url` U 18 white in its top-left. |
| **F12** | Line chart (split) | Top panel h≈960. Option pill (`purple`, U Medium 33 white) top-centre. Axes in ink 2 px, axis labels U 18. Line `chart-red` 3 px. Average = dashed ink line + value pill ("16.7% (average returns)"). One chart per option, same scale. |
| **F13** | Data table (split) | Title U Medium ~60 ink (optional). Column header cells ink bg + white U Medium 36. Body: row labels U Regular 42 ink, value cells `mint` (BRK) or plain with 2 px rules (VS). Winner row = `purple` @40 % band. Source line on the PS panel. |
| **F14** | Concept card (split) | Panel h≈860, centred: icon (battery etc.) ~240 w, kicker U Regular ~36 ink ("The battery's brain"), term D Black ~78 ink ("BMS"), full-form U SemiBold ~30 `bms-orange`. Variant: SB Bold Italic word + D Black word ("*Indigenous* BMS") with a coloured sub-line. |
| **F15** | Framed PS + badges | Framed PS card + 3–4 round or postage-stamp badges overlapping its edges at the corners. Coins: gold embossed words. Elements: periodic-tile style. Stamps: perforated cream card, number "01" U 30 top-left, object, label U Medium 36. |
| **F16** | Big number card (split) | Panel h≈960, centred: label D Bold ~45 ink + number D Black ~150 ink + tag pill `purple` U 45 white. |

### Ranking-only (R)
| ID | Name | Specs |
|---|---|---|
| **R1** | Tier board | Panel x 210–899 (w 689), y 980–1754, `ink` bg, radius 12, 6 equal rows (~129 h, 3 px gaps). Each row: letter tile 123 w on the left, radius 10, letter D Black ~84 ink + sub-label U 18 ink. Colours: A `#F0485A` (best), B `#F6A86C` (great), C `#F6D86C` (average), D `#72F072` (bad), E `#6CB4D8` (very bad), F `#4EBAAE` (worst). |
| **R1-card** | Item reveal card | `#EAFCC0` lime-cream rounded square ~375 × 375, radius 36, centred over the board's right area. Contains a mini UI mock or icon + item name U Regular ~45 ink at the bottom. While a card is shown, the other rows dim to 40 %. |
| **R1-row** | Placed item | Thumbnail (mini R1-card) ~117 × 117 in the tier row + label U Medium ALL CAPS ~27 white to its right. A second item in the same row sits to the right. |

---

## 5. Format recipes

Time % = share of reel duration (rough). "Map" = which script part produces it.

### 5.1 `TIER`: Tier Board (≈ 60 s)
| Scene | % | Component | Map from script | Fixed | Variable |
|---|---|---|---|---|---|
| Hook | 0–2 | H1-A + R1 (empty) | Reel title / storyboard header → L1 setup + L2 punch | Position, colours, H1 stays all reel | Copy |
| Item n reveal | ~15 each | R1-card (large) | "<Item name>. That's a <X> tier." → card | Card size/colour | Item name, mini mock/icon |
| Item n placed | — | R1-row | Tier letter in VO → row; name → caps label | Row geometry | Row, thumbnail, label |
| Final board | 90–95 | R1 full | — | — | — |
| CTA | 95–100 | none (PS + G2) | Last line | — | — |

Rules: one item per VO segment, in VO order. Two items in the same tier sit side by side. The board is visible from the first item to the last, and is removed for the closing line.

### 5.2 `VS`: Metric Face-off (≈ 85 s)
| Scene | % | Component | Map | Fixed | Variable |
|---|---|---|---|---|---|
| Hook | 0–8 | H1-D + O5 ×2 | Question line → H1. "same return X%" → cards | Layout | Question, option names, shared metric + value, caption |
| Number duel | 10–18 | O6 → O6 + `hl-orange` on winner | "if I see 18.8 and 12.88, you pick the lower" | Layout | Values, labels, winner |
| Term reveal | 18–20 | O1 variant (U ~45 + D ~120 white, left-aligned) | "It's called <term>" | — | Term |
| Explain per option | 28–45 | F12 ×N (split) | "Fund A went up and down…" | Chart style | Option label, curve shape (volatile/smooth), average value |
| Key number | 45–48 | F16 | Winning value | — | Label, value, tag |
| Recap table | 55–60 | O9 | "this one has the lower…" | — | Rows, highlight |
| Widen to N | 62–75 | F13 (split) | "compare all funds… 9.9, 14.65, 13, 15.32" | — | Rows, values, highlighted best |
| CTA | 85–100 | O7 (+ G2 with yellow keyword) | "Type zero one…" | — | Thumbnail, keyword |

Rules: real fund names are anonymised to "Fund-A/Fund-B" when the storyboard says so. The winner is always marked with `hl-orange` (on PS) or a purple row (on tables).

### 5.3 `EXPL`: Story Explainer (≈ 80 s)
| Scene | % | Component | Map | Fixed | Variable |
|---|---|---|---|---|---|
| Hook | 0–5 | H1-B | "Header copy" in instructions | Layout, yellow pill, cursor | Serif line, bold line, pill text |
| Title | 5–8 | S2 + illustration scene | "This is just a header not a SOP" | Side rules | Title, scene objects/character |
| Scenario costs | 8–20 | F15 (framed PS + coins/icons) | List of costs in VO (food, location, outfits…) | Badge style | Badge words/icons |
| Key line | 25–32 | F1 ×1–3 | Punchy VO line ("lose money", "compensate") | Layout | Words, letter-swap object |
| Coverage points | 32–50 | O3 → F2 / F3 | "Then there is material damage", "ill or hospitalised" | — | Category word, object, price |
| Exclusions | 60–68 | F15 stamp cards | "does not cover wear and tear…" list | Stamp style | Items 01..n, damaged variants |
| Verdict | 68–90 | PS + G2 (slow zoom) | Emotional close | — | — |
| CTA | 90–100 | O7 → O8 | "Type zero one…", "follow for more" | — | Thumbnail |

### 5.4 `BRK`: Sector Breakdown (≈ 165 s)
| Scene | % | Component | Map | Fixed | Variable |
|---|---|---|---|---|---|
| Hook | 0–4 | H1-C + O4 | "Header copy" + "look at all these companies" | Layout | Sector, sub, logos |
| Pivot | 4–6 | O1 | "Let me break it down" | — | Copy |
| Chapter opener ×n | per chapter | S1 | "First is the battery", "the next part is…" | Header line | "1. X", "2. Y"… |
| Chapter body | — | F4 / F5 / F11 / F6 / O2 / F14 | Numbers → F4/O2. Sub-parts list → F5. Cited source → F11. Region stat → F6. New term + full form → F14 | Styles | Data |
| Risks pivot | 40–42 | O1 (red) | "But there are significant risks" | — | — |
| Risk ×n | — | S1 (Risks variant) + F11/F15/F13/F7/F8 | "Risk one…", data mentioned | — | Data |
| Opportunities pivot | 73–75 | O1 (green) + O2 | "There are some growth opportunities" | — | — |
| Decision | 80–90 | O1 + F9 + F10 | "Should you invest? First… second overlap… third…" | — | Checklist copy, logos |
| Where to invest | 90–94 | F13 / screen-recording split | "see all the funds" | — | Fund list |
| Teaser + CTA | 94–100 | O10 → O7 | "who wins ICE vs EV… type electric" | — | Teaser, thumbnail, keyword |

---

## 6. Fixed vs variable (summary)

**Always fixed:** canvas, safe margins, colour tokens, fonts and their roles, logo position, subtitle style, framed-PS geometry, split-panel heights, tier colours/labels, CTA structure (thumbnail + "Comment “X”" with yellow keyword).

**Always variable (from script):** header copy, item/option names, numbers, tier/winner assignments, list items, sources and highlighted phrases, CTA keyword, thumbnail, objects/illustrations.

**Generation procedure (what I'll do when you send a script/storyboard):**
1. Parse the storyboard. Drop red/struck segments. Build a timeline of kept lines with their instructions and asset refs.
2. Detect the format: tier words → TIER, two options + metric → VS, numbered parts/risks → BRK, single concept story → EXPL. Confirm with you if unsure.
3. Assign a component to each timecode from §2 and §5. Lines with no instruction get subtitles only.
4. Render each graphic at 1080 × 1920 and name it `<reel>_<mm-ss>_<componentID>.png`. Deliver a contact sheet + shot list (timecode → file → copy).

---

## 7. Open items ⚠️ (need your answer)
1. **Fonts:** exact family names and files for Display Grotesk, UI Sans, Editorial Serif and Bold Serif.
2. **Deliverable format:** transparent PNG overlays (presenter areas left empty) vs full-frame mockups with a presenter placeholder. Also: layered SVG/PSD needed?
3. **Logo:** the EV reel has no Zero1 bug. Is that a sponsored-reel rule (drop the logo / add a partner logo)?
4. **Cream:** `#FBF6DA` vs `#FCF8EE`. One canonical, or keep per format?
5. **Abbreviations:** confirm SOP = section opener, OSA = on-screen asset, FSS = full-screen still.
6. **Tier scale:** always A–F, or can it be S–D (moodboard)?
7. **Images:** 3D objects, maps, characters and coins are custom renders. Do you have an asset library I should pull from, or should I leave labelled placeholders?
8. **Highlight colour rule:** orange for govt/policy and green for research sources is what I observed. Is that intended?

---

## 8. Additions (2026-10-23, Inflation_2 reel)

### New format: `FRAME` (Bucket/Framework Explainer), category **Explainer**
A single method taught as N numbered parts revealed one at a time, then the common mistake and the payoff.
Backbone: hook header → problem visual (e.g. salary draining) → step opener with all N parts hidden → each part revealed as the VO reaches it (active part enlarged; later parts blurred) → per-part detail graphics (data bars, table, typography) → mistake/payoff (subtitles) → CTA.
Detection signals: "think in terms of these N buckets/rules/steps", "The first… the second… the third…".

### Theme 2 (Light Pop): EXCLUDED by the team (2026-10-23). Its tokens and measurements were removed. Don't use it.

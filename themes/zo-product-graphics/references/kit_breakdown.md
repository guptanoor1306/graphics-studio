# Product IP · kit breakdown (Graphics Studio)

Studio renders **FSS + anchor** (`mode: fss | osa | ost | tos`, `items[]` from `spec_format.md`). Screen / footage / repeat stay **storyboard-only**.

**Studio creativity:** use kit_breakdown + video_breakdowns as **grammar** (~90%), not a template to copy. Each new script gets fresh copy, INDEX picks, and layout choices (~10%) — never paste unrelated frames from `example_spec.json`.

## Beat labels (one per script beat)

| Label | In `spec.frames`? | Storyboard line format |
|---|---|---|
| **FSS** | Yes — `mode: "fss"` | `~0:42 – FSS – heading + compare … → 6a` |
| **OSA / OST / TOS** | Yes — `mode: "osa"` / `"ost"` / `"tos"` + anchor items (`lower`, `punch`, …); TOS needs `title` | `~0:08 – OST – pop-up callout … → 2` |
| **Screen capture** | No | `Screen – Kite option chain / Coin dashboard …` |
| **Footage** | No | `Footage – motivation / section question / CTA` |
| **Repeat** | No (reuse prior id) | `Repeat – continue animation on 4` |

## FSS component pick (when a beat earns a designed frame)

| Beat need | `t` | Seen in |
|---|---|---|
| Positions / account surprise | `positions` | V1 #2, #7 |
| Above/below strike rule | `chart` | V1 #6 |
| Worked example (numbers) | `chart` + `positions` or `compare` | V1 #7, V2 6a–c |
| Two things side by side | `compare` | V2 1B, 2a, 10A, 16a |
| Size comparison | `bars` | V2 10b |
| Named formula | `formula` | V2 8 |
| Two-type classification | `hub2` | V1 #13, V3 8a |
| 4–6 factors around one hub | `hub_fan` (`fan` / `mind`) | V3 4a, V2 21 |
| Icon cards + bullets | `cards` | V3 #10 |
| Two objects → result | `row` + `cards` | V1 #10 |
| Alerts / checks / forms | `phone`, `status`, `cards` | V1 #17–20 |
| Trading days / counterparty | `week`, `exchange` | V3 8b–c |
| One object + changing number | `objstat`, `calendar` | V3 13–14 |
| Broker rule / caveat | `note` | V1 #14, V3 #11 |
| Question list | `notepad` | V2 18 |
| Live watchlist | `kite_watchlist` | V4 #1, #9 |
| Order book / depth | `kite_depth` | V4 #4 |
| Auction / match | `auction` | V4 #3 |
| Tick chart | `kite_chart` | V4 #10 |

Illustrations: `grep -i keyword assets/INDEX.md` — bare names in spec (`"img":"vault_blue"`).

## Density (FSS frames including a/b/c states)

- Product mechanics: ~**1 FSS per 90–180 spoken words** (V1: 9 / ~1,100w; V3: 15 / ~1,000w; V4: 4 new + 2 repeats / ~900w).
- Concept + analogies: up to **1 per 40–60 words** (V2: 26 / ~1,050w).
- Script `[SHOW: …]` cues are **mandatory FSS**.
- Over target: drop build states first, merge same-subject FSS, move word-only beats to Anchor.

## Team storyboard (SB doc) — when attached

- Keep SB numbers as frame `id`. FSS rows → `mode: fss`; OST/OSA/TOS rows → matching anchor mode + on-screen copy in spec.
- Ref img / sketch → layout only; rebuild as vector UI (`kite_*`, `compare`, …), generic tickers unless script names one; **script numbers win**.
- **Repeat** → no new frame; `reuse N` in storyboard.
- Two SB rows may merge into one frame (V4: order table + depth screenshot → one `kite_depth`).

## Cross-video snapshot

| Video | FSS | Anchor / OST (editor) | FSS flavour |
|---|---|---|---|
| V1 Devolvement | 9 | 13 | Kite UI mocks, charts, diagrams |
| V2 Share price | 26 | 8 | Metaphors (pizza, puzzle, buildings) |
| V3 SIFs on Coin | 15 | 5 | Hubs, cards, vault, calendar |
| V4 Stock ticks | 4 (+2 repeat) | 6 | `kite_watchlist`, `auction`, `kite_depth`, `kite_chart` |

Continuity: same hero objects and colours across states (A blue / B green; call green / put orange). Indian digit grouping on all ₹ amounts.

Full beat-by-beat scripts → `references/deep/video_breakdowns.md`.

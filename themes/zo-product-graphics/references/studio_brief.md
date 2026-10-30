# Graphics Studio (Zerodha Online · Product IP)

Web app renders **FSS + anchor** frames from `spec.json` via `scripts/build.py` (`frame_html`). Canvas **1920×1080**.

- **Storyboard** may include Screen capture, Footage, Repeat — those beats are **not** in `spec.frames`.
- **spec.frames** = designed graphics: `mode: "fss"` (full-screen `items[]`) and `mode: "osa" | "ost" | "tos"` (anchor-side `items[]` — `lower`, `punch`, `bignum`, `scroll_list`, …). TOS frames also need `title`.
- Default **`look.plate`**: `m1_wide_centre` (see `references/anchor_plates.md` + `assets/plates/`). Per-frame `plate` overrides for side panels / TOS.
- Use `scenes/example_spec.json` as the FSS quality bar. Anchor patterns: `references/spec_format.md` § Anchor.

When generating via the app: return storyboard + spec through `submit_storyboard`; ignore zip delivery and local CLI-only steps.

**Kit mapping:** `references/kit_breakdown.md`. Beat examples: `references/deep/video_breakdowns.md`.

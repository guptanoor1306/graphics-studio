# spec.json format (Zero1 reel · 1080×1920)

```json
{ "title": "…", "look": "Theme A · Cream Editorial · Manrope body + Behind The Nineties headlines", "frames": [ … ] }
```

- `id`: file order `01`, `02`, … or storyboard row key; must be unique.
- `vo` / `why`: optional; ignored by renderer, kept for the app storyboard.
- Types `footage`, `screen`, `repeat` are **storyboard-only** (not in spec.frames for studio preview).
- Canvas is always **1080×1920**. Centre content per SKILL safe zone (x 120–960 above y 720; x 200–880 below).
- Asset paths relative to `assets/`. Missing assets: `"TODO:<description>"` (placeholder box in html if you render one).

## Renderable types

### `fss` — full-screen still (most graphics)
```json
{"id":"01","type":"fss","bg":"cream","html":"<div class='abs' style='left:50%;top:320px;transform:translateX(-50%);width:840px;text-align:center;font:700 72px Manrope'>Headline</div>","vo":"…"}
```
`bg`: `cream` | `dark` | `green` (optional if html fills the frame).

### `html` — same as `fss` (escape hatch)
Use self-contained HTML with `.abs` positioning in px on the 1080×1920 stage. Prefer `data-mf-path="headline"` on editable blocks for studio layer list.

### `ost` — on-screen text over presenter
Same fields as `fss`; also produces `<id>_overlay.png` (transparent) for the editor.

### `anchor` — graphic over presenter (split or popup)
Optional `plate` (path under assets/) for the presenter frame grab. Produces overlay PNG.

### Optional on all types
- `subtitle`: short centred subtitle line (body font, white + shadow).
- `plate`: full-frame background image path.

## Storyboard string (app)
Tag beats like the skill: `01 → fss · hook header`, `02 → footage · …`. Footage/PS lines have **no** `→ frame id`.

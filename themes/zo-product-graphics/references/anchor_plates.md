# Anchor plates (studio default)

Set **`spec.look.plate`** to one of these keys (see `assets/plates/plates.json`). Studio defaults to **`m1_wide_centre`** when unset or `"default"`.

| Plate key | Use when |
|---|---|
| `m1_wide_centre` | Lower third, centred anchor (V1 male) — default OST / short OSA |
| `m1_mid_centre` | Punch-in centre, lower third |
| `m1_close_left` | Side panel: `scroll_list`, `side_list`, `ladder`, `mini_table`, `ticket` |
| `m1_tos` | **TOS only** — giant title behind anchor (`title` + optional lower line) |
| `f1_left_circle` | Female anchor (V2), text on the right |
| `f1_centre_circle` | Female centre, lower third |
| `f1_close_right` | Female side close-up, text on the left |
| `m2_centre` / `m2_centre_dark` | V3 male; dark for `objcards` / flanking cards |
| `m2_left` / `m2_right` | Side panel with anchor on one side |

**Rules:** One anchor item type per zone when possible (one `lower` OR one `punch`, not three stacked punchlines). Side lists go on **`m1_close_left`** (or `m2_left`), not wide-centre. TOS uses **`m1_tos`** only. Per-frame override: `"plate": "m1_close_left"` on the frame object.

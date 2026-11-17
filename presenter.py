"""The presenter shot behind anchor frames, changed once for a whole project.

Every kit with anchor frames draws a stock photo of a presenter behind them (a "plate"). A project can replace
that photo per camera position ("slot") with a still from its own video: look.presenter = {slot: "gen/<file>"}.
The kit renderers read look.presenter themselves; this module only says which frames use which slot (so the
editor can show "Presenter on the right · 6 frames") and what the stock photo is.

On-screen-text frames (OST) that sit over the presenter also show the photo, but there it is only the preview
behind the text (the graphic goes over the real footage), so they are counted separately.
"""
from __future__ import annotations

SLOTS: dict[str, dict[str, tuple[str, str]]] = {   # theme -> slot -> (label, stock photo under assets/)
    "varsity-english": {
        "right": ("Presenter on the right", "plates/anchor_right_setA_clean.png"),
        "left": ("Presenter on the left", "plates/anchor_left_setB.png"),
    },
    "varsity-hindi-graphics": {
        "main": ("Main camera", "plates/maincam.jpg"),
        "side": ("Side camera", "plates/sidecam.jpg"),
    },
    "varsity-hindi-fa-graphics": {
        "right": ("Presenter on the right", "plates/anchor_right.png"),
        "centre": ("Presenter in the centre", "plates/anchor_center.png"),
    },
    "zo-product-graphics": {
        "right": ("Presenter on the right", "plates/m2_right.jpg"),
        "left": ("Presenter on the left", "plates/m2_left.jpg"),
        "centre": ("Presenter in the centre", "plates/m2_centre.jpg"),
    },
}


def has_slots(theme: str) -> bool:
    return theme in SLOTS


def side_of_plate_key(key: str) -> str:
    """ZO plate keys name where the presenter sits: m2_right, m1_close_left, f1_centre_circle..."""
    k = (key or "").lower()
    return "left" if "left" in k else "right" if "right" in k else "centre"


def slot_of(theme: str, f: dict, look: dict | None = None) -> str | None:
    """Which presenter slot this frame shows, or None (full screen, or a special plate such as a scene)."""
    look = look or {}
    mode = str(f.get("mode") or "")
    plate = str(f.get("plate") or "")
    if theme == "varsity-english":
        if mode == "fss":
            return None
        if plate and not plate.startswith("anchor_"):
            return None
        side = f.get("anchor") or look.get("anchor") or "right"
        if plate.startswith("anchor_"):
            side = "left" if "left" in plate else "right"
        return "left" if side == "left" else "right"
    if theme == "varsity-hindi-graphics":
        if plate and plate.split(".")[0] not in ("maincam", "sidecam"):
            return None
        if plate:
            return "side" if plate.startswith("sidecam") else "main"
        return {"main": "main", "blur": "main", "side": "side"}.get(mode)
    if theme == "varsity-hindi-fa-graphics":
        return {"osa": "right", "osa_center": "centre"}.get(mode)
    if theme == "zo-product-graphics":
        if mode in ("", "fss") and not f.get("html"):
            return None
        if mode == "fss":
            return None
        try:   # the kit's own choice of plate for this frame
            import mf_studio
            key = plate or mf_studio.zo_plate_for_frame(f, look.get("plate"))
        except Exception:
            key = plate or "m2_right"
        return side_of_plate_key(key)
    return None


def is_ost(theme: str, f: dict) -> bool:
    return str(f.get("mode") or "").lower() == "ost"


def summary(theme: str, spec: dict | None, look: dict | None) -> list[dict]:
    """[{slot, label, count, ost, custom, src}] for the slots this project's frames use."""
    if theme not in SLOTS:
        return []
    look = look or {}
    custom = look.get("presenter") if isinstance(look.get("presenter"), dict) else {}
    counts: dict[str, list[int]] = {}
    for f in (spec or {}).get("frames") or []:
        if not isinstance(f, dict):
            continue
        s = slot_of(theme, f, look)
        if s:
            c = counts.setdefault(s, [0, 0])
            c[0] += 1
            c[1] += 1 if is_ost(theme, f) else 0
    out = []
    for slot, (label, stock) in SLOTS[theme].items():
        if slot not in counts and slot not in custom:
            continue
        rel = custom.get(slot) or stock
        out.append({"slot": slot, "label": label, "count": counts.get(slot, [0, 0])[0],
                    "ost": counts.get(slot, [0, 0])[1], "custom": bool(custom.get(slot)),
                    "src": f"/themes/{theme}/assets/{rel}"})
    return out

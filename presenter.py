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
        if slot not in counts and slot not in custom and not (theme == "varsity-english" and counts):
            continue   # Varsity English always shows both sides: the other side is the second camera
        rel = custom.get(slot) or stock
        out.append({"slot": slot, "label": label, "count": counts.get(slot, [0, 0])[0],
                    "ost": counts.get(slot, [0, 0])[1], "custom": bool(custom.get(slot)),
                    "src": f"/themes/{theme}/assets/{rel}"})
    return out


# ---- fitting an uploaded still to a slot ----
# Where the presenter's face should sit across the frame for each slot; content goes on the other side.
# Varsity Hindi cameras keep their own framing (main/side are the real camera angles).
_FACE_X = {"right": 0.70, "left": 0.30, "centre": 0.50}
_REFRAME = {"varsity-english", "varsity-hindi-fa-graphics", "zo-product-graphics"}


def _face_center(im):
    """(x, y) of the largest face in pixels, or None. Uses OpenCV when installed."""
    try:
        import cv2, numpy as np
    except Exception:
        return None
    small = im.copy(); small.thumbnail((960, 960))
    k = im.width / small.width
    gray = cv2.cvtColor(np.asarray(small.convert("RGB")), cv2.COLOR_RGB2GRAY)
    try:
        det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        if det.empty():
            return None
        faces = det.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
    except Exception:
        return None
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return ((x + w / 2) * k, (y + h / 2) * k)


def fit_to_slot(im, theme: str, slot: str, cw: int, ch: int):
    """Crop (and zoom a little if needed) so the presenter sits on the slot's side, then size to the canvas.
    A centred front shot uploaded for "right" ends up with the presenter on the right half, clear of the content."""
    from PIL import Image
    W, H = im.size
    ar = cw / ch
    wc = min(W, H * ar)
    target = _FACE_X.get(slot) if theme in _REFRAME else None
    if target is not None:
        face = _face_center(im)
        fx, fy = face if face else (W / 2, H * 0.35)
        need = None
        if target > 0.5:                      # window starts at the left edge: face lands at fx / wc
            need = fx / target
        elif target < 0.5:                    # window ends at the right edge
            need = (W - fx) / (1 - target)
        if need:
            wc = max(min(wc, need), min(W, H * ar) * 0.62)   # zoom in at most ~1.6x
        x0 = min(max(fx - target * wc, 0), W - wc)
        hc = wc / ar
        y0 = min(max(fy - 0.33 * hc, 0), H - hc)
    else:
        hc = wc / ar
        x0, y0 = (W - wc) / 2, (H - hc) / 2
    out = im.crop((round(x0), round(y0), round(x0 + wc), round(y0 + wc / ar))).resize((cw, ch), Image.LANCZOS)
    if theme == "varsity-english" and slot in ("left", "right"):
        out = _fade(out, slot)                # like the kit's own plates: the content side fades to dark
    return out


def _fade(im, slot: str, strength: float = 0.72):
    from PIL import Image
    w, h = im.size
    mask = Image.new("L", (w, 1))
    for x in range(w):
        f = x / w if slot == "left" else 1 - x / w        # 1 at the content edge
        a = max(0.0, (f - 0.45) / 0.55)                  # fade over the content half only
        mask.putpixel((x, 0), int(255 * strength * a ** 1.4))
    mask = mask.resize((w, h))
    return Image.composite(Image.new("RGB", (w, h), (8, 8, 10)), im, mask)

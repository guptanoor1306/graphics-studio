"""Zero1 Hindi: split a generated scene plate into BACKGROUND + CHARACTERS, so Make Layers gives Arjun (and the
other wooden-block people) their own layer and a clean background behind them, like the team's Photoshop step
(Select Subject + Generative Fill).

Two image-model edits per plate, made only when a frame goes to Layers (and kept for next time):
  1. mask: the same picture with everything that is not a character painted flat green -> the character outline.
     The character layer is the ORIGINAL pixels inside that outline (nothing redrawn).
  2. clean plate: the same picture with the characters removed and the space behind them filled. Only the area
     around the characters is taken from it; everything else stays the original picture.
A split that doesn't line up (outline too small/large, or the model moved things) is not used: the plate stays one
picture, exactly as before.
"""
from __future__ import annotations

import io
import os

import numpy as np
from PIL import Image, ImageFilter

import asset_gen
import z1_plates

THEME = z1_plates.THEME
W, H = 1920, 1080

MASK_PROMPT = (
    "This is a frame from a stop-motion paper-craft film. Return the SAME picture, same framing and size, with ONE "
    "change: paint every pixel that is NOT part of a toy character flat pure green #00FF00. A toy character = a "
    "wooden-block person (Arjun or anyone else) including their clothes, hair, hands, shoes and anything they hold in "
    "their hands. Keep every character exactly where it is, unchanged, same size and pose. Furniture they sit on, the "
    "floor, their shadows and everything else becomes flat green. No new objects.")
CLEAN_PROMPT = (
    "This is a frame from a stop-motion paper-craft film. Return the SAME picture, same framing, size, light and paper "
    "textures, with ONE change: remove every toy character (the wooden-block people and whatever they hold) and fill "
    "in what was behind them so the set looks complete and natural (chairs, desks, walls, floor continue). Do not move, "
    "add or restyle anything else. No people at all.")


def wanted(entry: dict) -> bool:
    """A full-frame scene plate with a character in it (Arjun or other people)."""
    if not isinstance(entry, dict) or entry.get("cutout") or not entry.get("file"):
        return False
    if (entry.get("aspect") or "16:9") != "16:9":
        return False
    return entry.get("arjun") is not None or bool(entry.get("people"))


SPLIT_V = 2   # a plate that could not be split by an older version is tried again


def done(entry: dict) -> bool:
    s = (entry or {}).get("split") or {}
    if s.get("none"):
        return s.get("of") == entry.get("file") and s.get("v") == SPLIT_V
    return s.get("of") == entry.get("file") and all((z1_plates.KIT / "assets" / s.get(k, "")).is_file() for k in ("bg", "char"))


def _edit(path, prompt: str) -> Image.Image:
    name, fn, key = z1_plates._provider()
    if not fn:
        raise RuntimeError("no image API key")
    gi = z1_plates._gen_images()
    raw = fn({"refs": [str(path)], "prompt": prompt, "aspect": "16:9", "cutout": False}, key)
    return gi.cover(Image.open(io.BytesIO(raw)).convert("RGB"), W, H)


def mask_from_green(img: Image.Image) -> np.ndarray:
    """0..255 character mask from the green picture: not-green = character; specks dropped, holes filled."""
    import cv2
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g > 120) & (g - np.maximum(r, b) > 50)
    m = (~green).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n <= 1:
        return np.zeros_like(m)
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep = [i + 1 for i, s in enumerate(areas) if s >= max(1500, 0.03 * areas.max())]
    m = np.isin(lab, keep).astype(np.uint8) * 255
    # fill holes (gaps between an arm and the body stay open only if they touch the outside)
    inv = 255 - m
    n2, lab2, stats2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    for i in range(1, n2):
        x, y, w, h, s = stats2[i]
        if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0] and s < 0.002 * m.size:
            m[lab2 == i] = 255
    return m


def compose(orig: Image.Image, mask: np.ndarray, clean: Image.Image) -> tuple[Image.Image, Image.Image, str]:
    """(background, character layer, '' or why the split is not usable)."""
    import cv2
    frac = (mask > 127).mean()
    if frac < 0.004:
        return orig, orig, "no character found"
    if frac > 0.55:
        return orig, orig, "outline covers most of the picture"
    o = np.asarray(orig.convert("RGB")).astype(np.float32)
    c = np.asarray(clean.convert("RGB")).astype(np.float32) if clean is not None else None
    ring = cv2.dilate(mask, np.ones((61, 61), np.uint8)) & ~cv2.dilate(mask, np.ones((25, 25), np.uint8))
    # does the model's cleaned picture line up with the original around the characters? Compared blurred: a detailed
    # paper/wood texture redrawn a pixel off differs everywhere sharp, but its colours and shapes match.
    if c is not None and ring.any():
        ob, cb = cv2.GaussianBlur(o, (0, 0), 6), cv2.GaussianBlur(c, (0, 0), 6)
        if np.abs(ob - cb)[ring > 0].mean() > 40:
            c = None
    if c is None:   # no usable cleaned picture: fill the space behind them from its surroundings (hidden unless moved)
        hole = cv2.dilate(mask, np.ones((15, 15), np.uint8))
        small = cv2.resize(o.astype(np.uint8), (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        hs = cv2.resize(hole, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST)
        c = cv2.resize(cv2.inpaint(small, hs, 9, cv2.INPAINT_TELEA), (o.shape[1], o.shape[0]), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    soft = cv2.GaussianBlur(cv2.dilate(mask, np.ones((3, 3), np.uint8)), (0, 0), 1.0)
    char = np.dstack([o.astype(np.uint8), soft.astype(np.uint8)])
    take = cv2.GaussianBlur(cv2.dilate(mask, np.ones((21, 21), np.uint8)), (0, 0), 6).astype(np.float32)[..., None] / 255
    bg = (o * (1 - take) + c * take).clip(0, 255).astype(np.uint8)
    return Image.fromarray(bg, "RGB"), Image.fromarray(char, "RGBA"), ""


def _png(im: Image.Image) -> bytes:
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


def split_one(entry: dict) -> dict:
    """The split record for one plate: {"of", "bg", "char"} or {"of", "none": why}. Raises on API errors."""
    rel = entry["file"]
    src = z1_plates.KIT / "assets" / rel
    d_bg, d_char = f"split-bg || {rel}", f"split-char || {rel}"
    hb, hc = asset_gen.lookup(THEME, d_bg), asset_gen.lookup(THEME, d_char)
    if hb and hc:
        return {"of": rel, "bg": hb, "char": hc}
    orig = Image.open(src).convert("RGB")
    if orig.size != (W, H):
        orig = z1_plates._gen_images().cover(orig, W, H)
    green = _edit(src, MASK_PROMPT)
    mask = mask_from_green(green)
    if (mask > 127).mean() > 0.004:   # the outline must sit on the characters: same picture there (blurred), else it moved
        import cv2
        ob = cv2.GaussianBlur(np.asarray(orig).astype(np.float32), (0, 0), 4)
        gb = cv2.GaussianBlur(np.asarray(green.convert("RGB")).astype(np.float32), (0, 0), 4)
        core = cv2.erode(mask, np.ones((9, 9), np.uint8))
        if core.any() and np.abs(ob - gb)[core > 0].mean() > 45:
            return {"of": rel, "none": "the characters' outline did not line up with the picture", "v": SPLIT_V}
    try:
        clean = _edit(src, CLEAN_PROMPT)
    except Exception as e:   # the outline is what matters; the space behind can be filled without the model
        print(f"z1_split: cleaned background failed for {rel} ({e}); filling it from the surroundings", flush=True)
        clean = None
    bg, char, why = compose(orig, mask, clean)
    if why:
        return {"of": rel, "none": why, "v": SPLIT_V}
    return {"of": rel, "bg": asset_gen.store(THEME, d_bg, _png(bg), "png", "split"),
            "char": asset_gen.store(THEME, d_char, _png(char), "png", "split")}


def split_frames(spec: dict, ids: set[str], log=print) -> tuple[dict, dict]:
    """Split every character plate the given frames use. Returns (spec with gen[k]["split"], report). Never raises."""
    import concurrent.futures as cf
    gen = dict((spec or {}).get("gen") or {})
    frames = [f for f in (spec or {}).get("frames") or [] if isinstance(f, dict) and str(f.get("id")) in ids]
    keys = sorted({k for f in frames for k in z1_plates.GEN_RE.findall(__import__("json").dumps(f, ensure_ascii=False))})
    todo = [k for k in keys if wanted(gen.get(k)) and not done(gen[k])]
    rep = {"split": [], "kept": {}, "failed": {}, "already": sum(1 for k in keys if wanted(gen.get(k)) and done(gen[k]))}
    if not todo or not z1_plates.available():
        if todo:
            rep["failed"] = {k: "no image API key" for k in todo}
        return spec, rep
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get("STUDIO_SPLIT_WORKERS", "3"))) as ex:
        futs = {ex.submit(split_one, gen[k]): k for k in todo}
        for fu in cf.as_completed(futs):
            k = futs[fu]
            try:
                s = fu.result()
                gen[k] = {**gen[k], "split": s}
                (rep["kept"].__setitem__(k, s["none"]) if s.get("none") else rep["split"].append(k))
            except Exception as e:
                rep["failed"][k] = str(e)[:200]
                log(f"z1_split: {k} failed ({e})")
    return {**spec, "gen": gen}, rep

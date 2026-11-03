"""Character PNG resolution and non-distorting layout opts for Varsity English."""
from __future__ import annotations

import os

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(KIT, "assets")


def asset_path(rel: str) -> str:
    return os.path.join(ASSETS, rel.replace("\\", "/"))


def resolve_asset_src(src: str) -> str:
    """Use standard PNG when present; fall back to *_legacy.png if refresh not deployed."""
    src = (src or "").replace("\\", "/").lstrip("/")
    if os.path.isfile(asset_path(src)):
        return src
    if src.endswith(".png"):
        leg = src[:-4] + "_legacy.png"
        if os.path.isfile(asset_path(leg)):
            return leg
    return src


def is_character_asset(src: str) -> bool:
    s = (src or "").lower()
    return "character" in s or "/rahul_" in s


def _norm_color(color: str | None) -> str:
    c = (color or "").strip().upper().lstrip("#")
    return c[:6] if len(c) >= 6 else c


def person_kit_src(item: dict) -> str | None:
    """Map spec `person` items to transparent kit PNGs (full limbs from PSD refresh)."""
    if item.get("doodle") is True:
        return None
    if item.get("src"):
        return item["src"].replace("\\", "/").lstrip("/")
    name = (item.get("name") or "").lower()
    col = _norm_color(item.get("color"))
    if item.get("small"):
        return "setC/character_small_on_box.png"
    if "point" in name or item.get("pose") == "pointing":
        return "setA/character_rahul_pointing.png"
    if item.get("moustache") or (item.get("hat") and col in {"248EF7", "64B0FC", "2480F7"}):
        return "setB/character_mustache_garland.png"
    if col in {"248EF7", "64B0FC", "2480F7", "1E90FF"}:
        return "setC/character_friend_blue.png"
    if col in {"F26B5B", "E85D5D", "FF6B6B", "D33"}:
        return "setA/character_rahul_standing.png"
    if col in {"A5CC65", "7CB342"}:
        return "setC/character_friend_blue.png"
    # default yellow persona + any unknown colour
    return "setC/character_friend_yellow.png"


def person_kit_available(item: dict) -> str | None:
    rel = person_kit_src(item)
    if not rel:
        return None
    resolved = resolve_asset_src(rel)
    return resolved if os.path.isfile(asset_path(resolved)) else None


def person_display_height(item: dict) -> int:
    h = item.get("h") or 315
    try:
        h = int(h)
    except (TypeError, ValueError):
        h = 315
    return max(h, 280)


def normalize_asset_opts(o: dict, src: str, visible_box_fn) -> dict:
    """Drop conflicting w+h so <img> keeps PNG aspect ratio (fixes stretched characters)."""
    o = dict(o)
    rel = resolve_asset_src(src)
    try:
        (iw, ih), _ = visible_box_fn(rel)
    except OSError:
        return o
    w, h = o.get("w"), o.get("h")
    if w and h and iw and ih:
        expected = iw / ih
        actual = w / h
        if abs(actual - expected) / expected > 0.015:
            if is_character_asset(src):
                del o["w"]
            else:
                del o["h"]
    elif w and h:
        del o["w"]
    return o

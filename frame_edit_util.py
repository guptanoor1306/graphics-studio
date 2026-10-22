"""Post-process frame edits (reference replace, dedupe assets)."""
from __future__ import annotations

import re

_SCENE = frozenset({"asset", "person"})


def wants_replace(ask: str, replace_flag: bool) -> bool:
    if replace_flag:
        return True
    return bool(re.search(r"\breplace\b|\binstead of\b|\bswap\b|\bremove\b.*\b(add|with)\b", ask or "", re.I))


def _scene_key(it: dict) -> tuple:
    if it.get("t") == "person":
        return ("person", it.get("name"), it.get("color"))
    if it.get("t") == "asset":
        return ("asset", it.get("src"))
    return (it.get("t"),)


def strip_upload_assets(frame: dict, ref_src: str | None = None) -> dict:
    """Remove flat pasted upload PNGs (smart mode uses INDEX kit paths only)."""
    items = []
    for it in frame.get("items") or []:
        if not isinstance(it, dict) or it.get("t") != "asset":
            items.append(it)
            continue
        src = it.get("src") or ""
        if "uploads/ref_" in src or (ref_src and ref_src in src):
            continue
        items.append(it)
    return {**frame, "items": items}


def limit_scene_items(scene: list[dict], *, max_assets: int = 2, max_person: int = 1) -> list[dict]:
    assets = [it for it in scene if it.get("t") == "asset"]
    persons = [it for it in scene if it.get("t") == "person"]
    return assets[-max_assets:] + persons[-max_person:]


def finalize_reference_edit(
    before: dict,
    after: dict,
    *,
    replace: bool,
    ref_src: str | None,
    smart: bool,
) -> dict:
    """Prevent stacked illustrations after Apply (model often appends instead of replacing)."""
    if smart and ref_src:
        after = strip_upload_assets(after, ref_src)

    items = list(after.get("items") or [])
    non_scene = [it for it in items if isinstance(it, dict) and it.get("t") not in _SCENE]
    scene = [it for it in items if isinstance(it, dict) and it.get("t") in _SCENE]

    if not replace:
        if len(scene) > 3:
            after = {**after, "items": non_scene + limit_scene_items(scene)}
        return after

    before_keys = {_scene_key(it) for it in before.get("items") or [] if isinstance(it, dict) and it.get("t") in _SCENE}
    novel = [it for it in scene if _scene_key(it) not in before_keys]
    if novel:
        scene_out = limit_scene_items(novel)
    elif scene:
        scene_out = limit_scene_items(scene)
    else:
        scene_out = []

    return {**after, "items": non_scene + scene_out, "prop": False}


def apply_flat_paste_replace(frame: dict, ref_src: str, ask: str, replace_flag: bool = False) -> dict:
    """Flat paste: one upload PNG as the only illustration."""
    if not ref_src or not wants_replace(ask, replace_flag):
        return frame
    items = [it for it in frame.get("items") or [] if isinstance(it, dict) and it.get("t") not in _SCENE]
    h = 400 if frame.get("mode") == "fss" else 480
    items.append({"t": "asset", "src": ref_src, "x": 90, "h": h})
    return {**frame, "items": items, "prop": False}


def remove_scene_illustrations(frame: dict) -> dict:
    items = [it for it in frame.get("items") or [] if isinstance(it, dict) and it.get("t") not in _SCENE]
    return {**frame, "items": items, "prop": False}

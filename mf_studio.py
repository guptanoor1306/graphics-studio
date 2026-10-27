"""MF theme helpers for Graphics Studio (spec vs storyboard-only beats)."""
from __future__ import annotations

MF_STORYBOARD_ONLY = frozenset({"footage", "screen", "repeat", None, ""})


def is_mf_renderable(frame: dict) -> bool:
    return (frame.get("type") or "") not in MF_STORYBOARD_ONLY


_ZO_STORYBOARD_ONLY = frozenset(
    {"footage", "screen", "repeat", "screen capture", "screencapture", "anchor"}
)
ZO_RENDER_MODES = frozenset({"fss", "osa", "ost", "tos"})


def is_zo_renderable(frame: dict) -> bool:
    mode = str(frame.get("mode") or "fss").strip().lower()
    if mode in _ZO_STORYBOARD_ONLY:
        return False
    return mode in ZO_RENDER_MODES


def compact_zo_spec_for_studio(spec: dict) -> dict:
    """Keep FSS + anchor (osa/ost/tos) frames; footage/screen/repeat stay in storyboard only."""
    if not spec or not isinstance(spec.get("frames"), list):
        return spec
    kept: list[dict] = []
    for f in spec["frames"]:
        if not isinstance(f, dict):
            continue
        mode = str(f.get("mode") or "fss").strip().lower()
        if mode in _ZO_STORYBOARD_ONLY or mode not in ZO_RENDER_MODES:
            continue
        items = [it for it in (f.get("items") or []) if isinstance(it, dict) and it.get("t")]
        if mode == "tos":
            if not f.get("title") and not items:
                continue
            kept.append({**f, "mode": mode, "items": items})
            continue
        if not items:
            continue
        kept.append({**f, "mode": mode if mode != "fss" else "fss", "items": items})
    return {**spec, "frames": kept}


def compact_mf_spec_for_studio(spec: dict) -> dict:
    """Keep only PNG-renderable frames in spec.frames; footage beats stay in storyboard text only."""
    if not spec or not isinstance(spec.get("frames"), list):
        return spec
    if not spec["frames"]:
        return spec
    first = spec["frames"][0]
    if not isinstance(first, dict) or "type" not in first or "mode" in first:
        return spec
    spec = {**spec, "frames": [f for f in spec["frames"] if is_mf_renderable(f)]}
    return spec

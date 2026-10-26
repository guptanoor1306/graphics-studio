"""MF theme helpers for Graphics Studio (spec vs storyboard-only beats)."""
from __future__ import annotations

MF_STORYBOARD_ONLY = frozenset({"footage", "screen", "repeat", None, ""})


def is_mf_renderable(frame: dict) -> bool:
    return (frame.get("type") or "") not in MF_STORYBOARD_ONLY


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

"""MF theme helpers for Graphics Studio (spec vs storyboard-only beats)."""
from __future__ import annotations

MF_STORYBOARD_ONLY = frozenset({"footage", "screen", "repeat", None, ""})


def is_mf_renderable(frame: dict) -> bool:
    return (frame.get("type") or "") not in MF_STORYBOARD_ONLY


_ZO_STORYBOARD_ONLY = frozenset(
    {"footage", "screen", "repeat", "screen capture", "screencapture", "anchor"}
)
ZO_RENDER_MODES = frozenset({"fss", "osa", "ost", "tos"})
ZO_PLATE_KEYS = frozenset({
    "m1_wide_centre", "m1_mid_centre", "m1_close_left", "m1_tos",
    "f1_left_circle", "f1_centre_circle", "f1_centre", "f1_close_right",
    "m2_centre", "m2_centre_dark", "m2_left", "m2_right",
})
ZO_DEFAULT_PLATE = "m1_wide_centre"
_ZO_SIDE_PANEL_TYPES = frozenset({"side_list", "scroll_list", "ladder", "mini_table", "ticket"})


def zo_plate_for_frame(frame: dict, look_plate: str | None = None) -> str:
    """Pick a kit plate key for anchor frames (see assets/plates/plates.json)."""
    mode = str(frame.get("mode") or "fss").strip().lower()
    if mode == "fss":
        return ""
    raw = frame.get("plate") or look_plate or ZO_DEFAULT_PLATE
    if raw in ("", "default", None):
        raw = ZO_DEFAULT_PLATE
    if mode == "tos":
        return "m1_tos"
    types = {it.get("t") for it in (frame.get("items") or []) if isinstance(it, dict)}
    if types & _ZO_SIDE_PANEL_TYPES:
        return "m1_close_left"
    if "objcards" in types:
        return "m2_centre_dark"
    if raw in ZO_PLATE_KEYS:
        return str(raw)
    return ZO_DEFAULT_PLATE


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
    look = spec.get("look") if isinstance(spec.get("look"), dict) else {}
    look = dict(look)
    lp = look.get("plate")
    if not lp or lp == "default":
        look["plate"] = ZO_DEFAULT_PLATE
    for f in kept:
        if f.get("mode") in ZO_RENDER_MODES - {"fss"}:
            f["plate"] = zo_plate_for_frame(f, look.get("plate"))
            if len(f.get("items") or []) > 2 and not (
                {it.get("t") for it in f["items"]} & _ZO_SIDE_PANEL_TYPES
            ):
                f["gap"] = f.get("gap", 24)
                f["fit"] = f.get("fit", 0.95)
    return {**spec, "look": look, "frames": kept}


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

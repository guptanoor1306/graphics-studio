"""Post-process frame edits (reference replace, dedupe assets)."""
from __future__ import annotations

import re

_SCENE = frozenset({"asset", "person"})


def wants_replace(ask: str, replace_flag: bool) -> bool:
    if replace_flag:
        return True
    return bool(re.search(r"\breplace\b|\binstead of\b|\bswap\b|\bremove\b.*\b(add|with)\b", ask or "", re.I))


def apply_reference_replace(frame: dict, ref_src: str, ask: str, replace_flag: bool = False) -> dict:
    """When replacing: one illustration from upload, not stacked kit + reference."""
    if not ref_src or not wants_replace(ask, replace_flag):
        return frame
    items = [it for it in frame.get("items") or [] if isinstance(it, dict) and it.get("t") not in _SCENE]
    h = 400 if frame.get("mode") == "fss" else 480
    existing = next(
        (it for it in frame.get("items") or [] if it.get("t") == "asset" and ref_src in (it.get("src") or "")),
        None,
    )
    if existing:
        o = {k: v for k, v in existing.items() if k != "t"}
        o.setdefault("src", ref_src)
        o.setdefault("x", 90)
        o.setdefault("h", h)
        items.append({"t": "asset", **o})
    else:
        items.append({"t": "asset", "src": ref_src, "x": 90, "h": h})
    frame = {**frame, "items": items, "prop": False}
    return frame

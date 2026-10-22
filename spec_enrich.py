"""Deterministic kit visuals when Claude returns text-only OST frames (common for broker/RMS scripts)."""
from __future__ import annotations

import re

_SCENE_TYPES = frozenset({"asset", "person"})
_CONTENT_TYPES = frozenset({"htab", "points", "text", "glass_table", "calc_table", "popup"})

# (regex on frame + storyboard text, items to append)
_OSA_PRESETS: list[tuple[re.Pattern[str], list[dict]]] = [
    (
        re.compile(
            r"broker|rms|risk management|square\s*off|intraday|margin|position|trader|leverage|cut-off|cutoff",
            re.I,
        ),
        [
            {"t": "asset", "src": "setA/building_company_3d.png", "x": 90, "h": 520},
            {"t": "person", "color": "#248EF7", "name": "Broker", "x": 560, "h": 315},
        ],
    ),
    (
        re.compile(r"bank|savings|deposit|account|loan|emi", re.I),
        [
            {"t": "asset", "src": "setB/bank_building.png", "x": 90, "h": 480},
            {"t": "person", "color": "#64B0FC", "name": "Customer", "x": 560, "h": 300},
        ],
    ),
    (
        re.compile(r"tax|itr|income tax|notice|scrutiny", re.I),
        [
            {"t": "asset", "src": "setA/document_clipped_note_rule.png", "x": 100, "h": 420},
            {"t": "person", "color": "#F2B233", "name": "Taxpayer", "x": 580, "h": 300},
        ],
    ),
]

def _frame_text(f: dict) -> str:
    chunks: list[str] = []
    for it in f.get("items") or []:
        if not isinstance(it, dict):
            continue
        if it.get("text"):
            chunks.append(str(it["text"]))
        if it.get("title"):
            chunks.append(str(it["title"]))
        for sub in it.get("items") or []:
            chunks.append(str(sub))
        for row in it.get("rows") or []:
            if isinstance(row, (list, tuple)):
                chunks.extend(str(c) for c in row)
            else:
                chunks.append(str(row))
    return " ".join(chunks)


def _has_scene(f: dict) -> bool:
    return any(isinstance(it, dict) and it.get("t") in _SCENE_TYPES for it in f.get("items") or [])


def _item_types(f: dict) -> set[str]:
    return {it.get("t") for it in f.get("items") or [] if isinstance(it, dict) and it.get("t")}


def _storyboard_line_for_id(storyboard: str, fid: str) -> str:
    for line in (storyboard or "").splitlines():
        if fid in line or line.rstrip().endswith(f"→ {fid}") or f"→ {fid}" in line:
            return line
    return ""


def _apply_fss_from_storyboard(f: dict, storyboard: str) -> None:
    fid = f.get("id") or ""
    line = _storyboard_line_for_id(storyboard, fid)
    if not line:
        return
    if re.search(r"\bFSS\b", line, re.I):
        f["mode"] = "fss"


def _maybe_promote_long_list(f: dict) -> None:
    if f.get("mode") == "fss":
        return
    for i, it in enumerate(f.get("items") or []):
        if not isinstance(it, dict) or it.get("t") != "points":
            continue
        pts = it.get("items") or []
        if len(pts) >= 4:
            f["mode"] = "fss"
            f["items"][i] = {"t": "nlist", "active": 0, "items": list(pts)}
            return


def enrich_spec(spec: dict, storyboard: str = "") -> dict:
    if not spec:
        return spec
    frames = spec.get("frames")
    if not isinstance(frames, list):
        return spec

    sb_blob = storyboard if isinstance(storyboard, str) else ""
    look = spec.get("look") if isinstance(spec.get("look"), dict) else {}
    skip_osa_presets = look.get("storyboard_style") == "reference_designs"
    for f in frames:
        if not isinstance(f, dict):
            continue
        _apply_fss_from_storyboard(f, sb_blob)
        _maybe_promote_long_list(f)

        if f.get("mode") == "fss":
            continue
        if _has_scene(f):
            continue
        types = _item_types(f)
        if "title" in types and not (types & _CONTENT_TYPES - {"title"}):
            continue
        if not (types & _CONTENT_TYPES):
            continue

        line = _storyboard_line_for_id(sb_blob, f.get("id") or "")
        if re.search(r"\bTitle\b|\bOST\b.*[Tt]itle", line) and types <= {"title"}:
            continue
        if line and not re.search(r"\b(OSA|FSS)\b", line, re.I):
            if types <= {"title"} or "title" in types:
                continue
        if skip_osa_presets:
            continue
        blob = _frame_text(f) + " " + line
        for pat, items in _OSA_PRESETS:
            if pat.search(blob):
                f.setdefault("items", []).extend(items)
                break

    return spec

"""Per-video persona kit + layout (avoid same PNG and same x on every frame)."""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
from character_assets import asset_path, person_display_height, resolve_asset_src

# Common Claude / enrich defaults — safe to re-layout
_BORING_X = frozenset({110, 560, 580, 600, 1500})

_POOL = [
    "setC/character_friend_yellow.png",
    "setA/character_rahul_pointing.png",
    "setA/character_rahul_standing.png",
    "setC/character_friend_blue.png",
    "setC/character_small_on_box.png",
    "setA/character_with_moneybag.png",
    "setB/character_mustache_garland.png",
]

_KEYWORD_KITS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"salary|invest|step up|glass table|10\s*%", re.I), "setA/character_rahul_pointing.png"),
    (re.compile(r"limit|decision\s*\d|small step|routine task", re.I), "setC/character_small_on_box.png"),
    (re.compile(r"not autom|big call|your hand|keep the", re.I), "setB/character_mustache_garland.png"),
    (re.compile(r"retire|beach|relax|pension", re.I), "setB/character_beach_chair_retired.png"),
    (re.compile(r"friend|together|two people|couple", re.I), "setC/character_friend_blue.png"),
    (re.compile(r"\bmoney\b|save|rupee|coin|wallet|budget|emi|\bspend\b", re.I), "setA/character_with_moneybag.png"),
    (re.compile(r"tax|itr|notice", re.I), "setA/character_rahul_standing.png"),
    (re.compile(r"bank|loan|home", re.I), "setC/character_friend_blue.png"),
]

_NAME_KITS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"kapoor|mustache|broker|agent", re.I), "setB/character_mustache_garland.png"),
    (re.compile(r"rahul|arjun|rohan", re.I), "setA/character_rahul_standing.png"),
    (re.compile(r"anjali|priya|mrs|ms\.|woman|she\b", re.I), "setA/character_rahul_standing.png"),
    (re.compile(r"point|present|explain", re.I), "setA/character_rahul_pointing.png"),
]

_COLOR_KITS = {
    "248EF7": "setC/character_friend_blue.png",
    "64B0FC": "setC/character_friend_blue.png",
    "F26B5B": "setA/character_rahul_standing.png",
    "A5CC65": "setC/character_friend_blue.png",
    "F2B233": "setC/character_friend_yellow.png",
}


def _norm_color(color: str | None) -> str:
    c = (color or "").strip().upper().lstrip("#")
    return c[:6] if len(c) >= 6 else c


def _frame_blob(frame: dict) -> str:
    chunks: list[str] = [str(frame.get("id") or "")]
    for it in frame.get("items") or []:
        if not isinstance(it, dict):
            continue
        for k in ("text", "title", "key", "name"):
            if it.get(k):
                chunks.append(str(it[k]))
        for sub in it.get("items") or []:
            chunks.append(str(sub))
        for row in it.get("rows") or []:
            if isinstance(row, (list, tuple)):
                chunks.extend(str(c) for c in row)
    return " ".join(chunks)


def _kit_exists(rel: str) -> bool:
    return os.path.isfile(asset_path(resolve_asset_src(rel)))


def _pick_from_pool(frame_i: int, recent: list[str]) -> str:
    for off in range(len(_POOL)):
        cand = _POOL[(frame_i + off) % len(_POOL)]
        if _kit_exists(cand) and cand not in recent[-2:]:
            return cand
    for cand in _POOL:
        if _kit_exists(cand):
            return cand
    return "setC/character_friend_yellow.png"


def _pick_kit(frame_i: int, item: dict, blob: str, recent: list[str], names: dict[str, str]) -> str:
    if item.get("doodle") is True:
        return ""
    if item.get("src"):
        return resolve_asset_src(str(item["src"]).replace("\\", "/").lstrip("/"))
    name = (item.get("name") or "").strip()
    name_key = name.lower()
    if name_key and name_key in names:
        return names[name_key]
    for pat, kit in _NAME_KITS:
        if name and pat.search(name):
            if _kit_exists(kit):
                if name_key:
                    names[name_key] = kit
                return kit
    for pat, kit in _KEYWORD_KITS:
        if pat.search(blob):
            if _kit_exists(kit):
                return kit
    col = _norm_color(item.get("color"))
    if col in _COLOR_KITS and _kit_exists(_COLOR_KITS[col]):
        kit = _COLOR_KITS[col]
        if kit not in recent[-1:] or len(recent) < 2:
            return kit
    kit = _pick_from_pool(frame_i, recent)
    if name_key:
        names[name_key] = kit
    return kit


def _asset_xs(frame: dict) -> list[int]:
    xs = []
    for it in frame.get("items") or []:
        if isinstance(it, dict) and it.get("t") == "asset" and it.get("x") is not None:
            try:
                xs.append(int(it["x"]))
            except (TypeError, ValueError):
                pass
    return xs


def _layout_x(frame_i: int, frame: dict, side: str, kit: str) -> int:
    fss = frame.get("mode") == "fss"
    person_left = bool(frame.get("person_left"))
    assets = _asset_xs(frame)
    has_left_asset = any(x < 350 for x in assets)

    if fss and person_left:
        return (88, 128, 168)[frame_i % 3]
    if fss:
        return (760, 880, 1000)[frame_i % 3]
    if side == "right":
        slots = (460, 540, 620, 700, 580, 500) if has_left_asset else (400, 480, 560, 640, 520)
        return slots[frame_i % len(slots)]
    return (1240, 1340, 1140, 1440)[frame_i % 4]


def _layout_h(kit: str, item: dict) -> int:
    if item.get("h") is not None and item.get("h") not in (300, 315):
        return person_display_height(item)
    if "small_on_box" in kit:
        return 260
    if "beach_chair" in kit:
        return 400
    if "moneybag" in kit:
        return 340
    if "mustache" in kit or "garland" in kit:
        return 330
    return 315


def should_relayout_x(item: dict) -> bool:
    if "y" in item:
        return False
    if item.get("x") is None:
        return True
    try:
        return int(item["x"]) in _BORING_X
    except (TypeError, ValueError):
        return True


@dataclass(frozen=True)
class PersonPlan:
    kit: str
    x: int
    h: int
    flip: bool = False


class PersonVideoPlan:
    def __init__(self, plans: dict[tuple[str, int], PersonPlan]):
        self._plans = plans

    @classmethod
    def from_frames(cls, frames: list[dict], *, side: str = "right") -> PersonVideoPlan:
        plans: dict[tuple[str, int], PersonPlan] = {}
        recent: list[str] = []
        names: dict[str, str] = {}
        frame_i = 0
        for f in frames or []:
            if not isinstance(f, dict):
                continue
            fid = str(f.get("id") or frame_i)
            blob = _frame_blob(f)
            side_f = f.get("anchor") or side
            for ii, it in enumerate(f.get("items") or []):
                if not isinstance(it, dict) or it.get("t") != "person":
                    continue
                kit = _pick_kit(frame_i, it, blob, recent, names)
                if not kit:
                    continue
                x = int(it["x"]) if not should_relayout_x(it) and it.get("x") is not None else _layout_x(frame_i, f, side_f, kit)
                h = _layout_h(kit, it)
                flip = it.get("facing") == "left"
                if "moneybag_left" in kit:
                    flip = False
                elif "moneybag" in kit and side_f == "left":
                    kit = "setA/character_with_moneybag_left.png" if _kit_exists("setA/character_with_moneybag_left.png") else kit
                plans[(fid, ii)] = PersonPlan(kit=kit, x=x, h=h, flip=flip)
                recent.append(kit)
            frame_i += 1
        return cls(plans)

    def get(self, frame_id: str, item_index: int, item: dict, frame: dict, *, side: str = "right") -> PersonPlan | None:
        key = (str(frame_id), item_index)
        if key in self._plans:
            return self._plans[key]
        # single-frame fallback
        one = PersonVideoPlan.from_frames([frame], side=side)
        return one._plans.get((str(frame_id), item_index))


def apply_person_plans_to_spec(spec: dict, *, side: str = "right") -> dict:
    frames = spec.get("frames") if isinstance(spec, dict) else None
    if not isinstance(frames, list):
        return spec
    look = spec.get("look") or {}
    side = look.get("anchor") or side
    plan = PersonVideoPlan.from_frames(frames, side=side)
    for f in frames:
        if not isinstance(f, dict):
            continue
        fid = str(f.get("id") or "")
        for ii, it in enumerate(f.get("items") or []):
            if not isinstance(it, dict) or it.get("t") != "person":
                continue
            p = plan.get(fid, ii, it, f, side=side)
            if not p:
                continue
            if not it.get("src") and not it.get("doodle"):
                it["src"] = p.kit
            if should_relayout_x(it):
                it["x"] = p.x
            if it.get("h") in (None, 300, 315):
                it["h"] = p.h
    return spec

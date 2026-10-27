"""Per-theme stage size and kit detection (templates/render.js)."""
from __future__ import annotations

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
THEMES = ROOT / "themes"
_cache: dict[str, tuple[int, int]] = {}


def is_kit_theme(theme: str) -> bool:
    return (THEMES / theme / "templates" / "render.js").is_file()


def canvas_for_theme(theme: str) -> tuple[int, int]:
    if theme in _cache:
        return _cache[theme]
    default = (1920, 1080)
    p = THEMES / theme / "scripts" / "build.py"
    if not p.is_file():
        _cache[theme] = default
        return default
    spec = importlib.util.spec_from_file_location(f"build_meta_{theme}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    w = getattr(mod, "CANVAS_W", None)
    h = getattr(mod, "CANVAS_H", None)
    if w is None or h is None:
        c = getattr(mod, "CANVAS", default)
        w, h = c[0], c[1]
    _cache[theme] = (int(w), int(h))
    return _cache[theme]


def theme_meta_map() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not THEMES.is_dir():
        return out
    for p in THEMES.iterdir():
        if not (p / "SKILL.md").is_file():
            continue
        w, h = canvas_for_theme(p.name)
        out[p.name] = {"w": w, "h": h, "kit": is_kit_theme(p.name)}
    return out

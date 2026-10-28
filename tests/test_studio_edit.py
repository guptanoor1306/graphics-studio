"""Studio edit contracts: layer tags, resize modes, reference replace (no browser)."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from frame_edit_util import apply_layer_reference_replace  # noqa: E402
from theme_canvas import theme_meta_map  # noqa: E402

THEMES = ROOT / "themes"


def load_build(theme: str):
    p = THEMES / theme / "scripts" / "build.py"
    spec = importlib.util.spec_from_file_location(f"build_{theme}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SKIP_BEAT = frozenset({"footage", "screen", "repeat"})


def example_frame(theme: str) -> dict | None:
    is_kit = (THEMES / theme / "templates" / "render.js").is_file()
    for name in ("example_spec.json", "gift_city_spec.json"):
        p = THEMES / theme / "scenes" / name
        if not p.is_file():
            continue
        data = json.loads(p.read_text())
        frames = data.get("frames") or []
        for fr in frames:
            if is_kit and fr.get("type") in SKIP_BEAT:
                continue
            return fr
        if frames and not is_kit:
            return frames[0]
    return None


def test_layer_reference_replace_title_to_asset():
    fr = {
        "id": "G01",
        "mode": "anchor",
        "items": [{"t": "title", "lead": "What", "key": "Automate", "tail": "?"}],
    }
    out = apply_layer_reference_replace(fr, 0, "uploads/ref_1_G01.png")
    assert out["items"][0]["t"] == "asset"
    assert out["items"][0]["src"] == "uploads/ref_1_G01.png"


def test_varsity_english_title_resize_tag():
    build = load_build("varsity-english")
    look = {"anchor": "right", "fss": "blue", "prop": "tax"}
    fr = {"id": "0.13", "mode": "anchor", "items": [{"t": "title", "key": "HUF", "color": "coral", "size": "xl"}]}
    html = build.frame_html(fr, look, edit=True)
    assert 'data-layer-type="title"' in html
    assert 'data-resize="font"' in html
    assert "studio-editable" in html


def test_varsity_english_title_numeric_size_render():
    build = load_build("varsity-english")
    look = {"anchor": "right", "fss": "blue", "prop": "none"}
    fr = {"id": "t", "mode": "anchor", "items": [{"t": "title", "key": "X", "size": 120}]}
    html = build.frame_html(fr, look, edit=False)
    assert 'style="font-size:120px"' in html


def test_all_kits_edit_html_has_layers():
    """Every skill kit should enable studio edit (static tags or client-side tagMfStudioLayers)."""
    meta = theme_meta_map()
    missing = []
    for theme in sorted(meta):
        fr = example_frame(theme)
        if not fr:
            missing.append(f"{theme}: no example frame")
            continue
        try:
            build = load_build(theme)
            look = fr.get("look") or {"anchor": "right", "fss": "blue"}
            if isinstance(look, str):
                look = {"look_line": look}
            html = build.frame_html(fr, look, edit=True)
        except Exception as e:
            missing.append(f"{theme}: render failed ({e})")
            continue
        static_layers = 'data-spec-idx' in html or "studio-editable" in html
        client_layers = "studioEdit" in html and "render.js" in html
        if not static_layers and not client_layers:
            missing.append(f"{theme}: no studio edit surface in preview HTML")
    assert not missing, "\n".join(missing)


def test_resize_attrs_on_common_english_types():
    build = load_build("varsity-english")
    look = {"anchor": "right", "fss": "blue", "prop": "none"}
    cases = [
        ({"t": "htab", "text": "Head"}, "font"),
        ({"t": "person", "name": "Rahul", "x": 600, "h": 315}, None),
        ({"t": "text", "text": "Body"}, "font"),
        ({"t": "glass_table", "head": ["A"], "rows": [["1"]]}, "w"),
    ]
    for item, want_resize in cases:
        fr = {"id": "x", "mode": "anchor", "items": [item]}
        html = build.frame_html(fr, look, edit=True)
        if want_resize:
            assert f'data-resize="{want_resize}"' in html, item
        tagged = "data-spec-idx" in html or "specIdx" in html
        assert tagged, item


def test_mf_render_includes_studio_boot():
    build = load_build("varsity-mf-graphics")
    spec_path = THEMES / "varsity-mf-graphics" / "scenes" / "gift_city_spec.json"
    data = json.loads(spec_path.read_text())
    fr = next(f for f in data["frames"] if f.get("type") == "sop")
    html = build.frame_html(fr, data.get("look") or {}, edit=True)
    assert "RENDER" in html or "render.js" in html
    assert "studio-edit-mode" in html or "in-studio-iframe" in html or "studioEdit" in html

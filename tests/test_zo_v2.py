"""ZO v2 kit: every new component renders without layout warnings, and the Bulletin export is well formed."""
import io
import json
import pathlib
import sys
import zipfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
pytest.importorskip("playwright")

THEME = "zo-product-graphics"
V2_IDS = [f"v2_{x}" for x in ("s02", "s09", "s10", "s11", "s12", "s15", "s16", "s19", "a02", "a04")]


def _spec():
    return json.loads((ROOT / "themes" / THEME / "scenes" / "example_spec.json").read_text())


def test_every_component_is_registered():
    import app
    m = app.builder(THEME)
    for t in ("acronym", "qtitle", "steps", "slab_table", "split_bar", "cost_compare", "updown", "donut", "pie", "fbox",
              "people", "catgrid", "checklist", "options", "buildlist", "recap", "pills", "timeline", "bigphrase",
              "ov_title", "ybox", "bubble", "caption", "pill_rail", "relation"):
        assert t in m.R, t


def test_v2_example_frames_render_clean():
    import app, critique
    spec = _spec(); p = {"theme": THEME, "look": spec.get("look", {}), "spec": spec}
    base = (app.THEMES / THEME / "scenes").as_uri() + "/"
    frames = [f for f in spec["frames"] if f["id"] in V2_IDS]
    assert len(frames) == len(V2_IDS)
    pages = [(f["id"], app.frame_page(THEME, app.frame_for_render(p, f), app.effective_look(p), base_href=base,
                                       all_frames=spec["frames"], spec=spec), None) for f in frames]
    out = critique.render_frames(pages, app.builder(THEME).CHECK_JS, (1920, 1080))
    for fid, (png, warns) in out.items():
        assert png, fid
        assert not warns, (fid, warns)


def test_decor_is_stable_between_runs():
    import app
    m = app.builder(THEME)
    f = {"id": "7a", "mode": "fss", "items": []}
    assert m.fss_decor(m._seed("7a"), f) == m.fss_decor(m._seed("7a"), f)


def test_bulletin_export_structure(tmp_path):
    import app
    spec = _spec()
    p = {"id": 0, "name": "MTF test", "theme": THEME, "look": spec.get("look", {}), "spec": spec,
         "storyboard": "~0:40 – Screen capture – Console charges page"}
    dest = tmp_path / "x.zip"
    fn = app._export_bulletin(p, "v2_s11,v2_a02", dest)
    assert fn.endswith("_layers.zip")
    z = zipfile.ZipFile(dest); names = z.namelist()
    root = names[0].split("/")[0]
    assert root == "MTF_test_layers"
    for part in ("html/", "png/", "layers/"):
        assert sum(n.startswith(f"{root}/{part}") for n in names) == 2, part
    for f in ("LAYERS.txt", "README.txt", "spec.json"):
        assert f"{root}/{f}" in names
    s = json.loads(z.read(f"{root}/spec.json"))
    assert [f["mode"] for f in s["frames"]] == ["FSS", "Over presenter"]
    assert s["skipped"] and "stand-in" in s["notes"][0]
    html = z.read(next(n for n in names if n.startswith(f"{root}/html/") and "s11" in n)).decode()
    assert "<script" not in html and "class=" not in html and "@font-face" in html
    assert "Split bar" in z.read(f"{root}/LAYERS.txt").decode()
    assert "Check after flattening" not in z.read(f"{root}/README.txt").decode()


def test_bulletin_diff_catches_a_missing_shape():
    import bulletin
    from PIL import Image, ImageDraw
    a = Image.new("RGB", (1920, 1080), "white"); ImageDraw.Draw(a).rounded_rectangle([600, 400, 1200, 600], 30, fill="#387FD1")
    b = Image.new("RGB", (1920, 1080), "white")
    buf_a, buf_b = io.BytesIO(), io.BytesIO(); a.save(buf_a, "PNG"); b.save(buf_b, "PNG")
    assert bulletin._diff(buf_a.getvalue(), buf_b.getvalue()) > 600
    assert bulletin._diff(buf_a.getvalue(), buf_a.getvalue()) == 0

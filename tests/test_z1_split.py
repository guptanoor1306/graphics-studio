import json

import numpy as np
from PIL import Image

import z1_plates
import z1_split


def _plate():
    a = np.zeros((1080, 1920, 3), np.uint8)
    a[:] = (200, 180, 150)
    a[500:900, 800:1000] = (164, 64, 59)      # the "character"
    return Image.fromarray(a)


def test_mask_and_compose_keep_original_pixels():
    orig = _plate()
    g = np.zeros((1080, 1920, 3), np.uint8); g[:] = (0, 255, 0); g[500:900, 800:1000] = (164, 64, 59)
    m = z1_split.mask_from_green(Image.fromarray(g))
    assert 0.03 < (m > 127).mean() < 0.05
    clean = np.zeros((1080, 1920, 3), np.uint8); clean[:] = (200, 180, 150)
    bg, char, why = z1_split.compose(orig, m, Image.fromarray(clean))
    assert why == ""
    c = np.asarray(char)
    assert c[700, 900, 3] == 255 and tuple(c[700, 900, :3]) == (164, 64, 59) and c[100, 100, 3] == 0
    assert tuple(np.asarray(bg)[700, 900]) == (200, 180, 150) and tuple(np.asarray(bg)[100, 100]) == (200, 180, 150)


def test_compose_refuses_a_moved_background():
    orig = _plate()
    g = np.zeros((1080, 1920, 3), np.uint8); g[:] = (0, 255, 0); g[500:900, 800:1000] = 50
    m = z1_split.mask_from_green(Image.fromarray(g))
    moved = np.zeros((1080, 1920, 3), np.uint8); moved[:] = (40, 90, 200)
    assert z1_split.compose(orig, m, Image.fromarray(moved))[2]


def test_split_used_only_for_layers(tmp_path):
    spec = {"gen": {"room": {"prompt": "x", "arjun": "", "file": "gen/a.png", "split": {"of": "gen/a.png", "bg": "gen/b.png", "char": "gen/c.png"}}},
            "frames": [{"id": "1", "type": "scene", "bg": "gen:room"}]}
    f = spec["frames"][0]
    assert "split" not in z1_plates.attach(spec, f)["_gen"]["room"]
    assert z1_plates.attach(spec, f, layers=True)["_gen"]["room"]["split"]["char"] == "gen/c.png"
    spec["gen"]["room"]["file"] = "gen/new.png"      # remade plate: the old split no longer applies
    assert "split" not in z1_plates.attach(spec, f, layers=True)["_gen"]["room"]


def test_frame_html_draws_background_and_characters(tmp_path):
    import importlib.util, sys
    kit = z1_plates.KIT
    sys.path.insert(0, str(kit / "scripts"))
    spec_ = importlib.util.spec_from_file_location("z1build_t", kit / "scripts" / "build.py")
    b = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(b)
    gd = kit / "assets" / "gen"; gd.mkdir(parents=True, exist_ok=True)
    names = []
    for n in ("_t_plate.png", "_t_bg.png", "_t_char.png"):
        Image.new("RGB", (1920, 1080)).save(gd / n); names.append(n)
    try:
        g = {"room": {"file": "gen/_t_plate.png", "split": {"of": "gen/_t_plate.png", "bg": "gen/_t_bg.png", "char": "gen/_t_char.png"}}}
        html = b.frame_html({"id": "1", "type": "scene", "bg": "gen:room", "_gen": g})
        assert 'aria-label="Background"' in html and 'aria-label="Characters"' in html and "_t_char.png" in html
        g2 = {"room": {"file": "gen/_t_plate.png"}}
        assert "Characters" not in b.frame_html({"id": "1", "type": "scene", "bg": "gen:room", "_gen": g2})
    finally:
        for n in names:
            (gd / n).unlink(missing_ok=True)


def test_wanted():
    assert z1_split.wanted({"file": "gen/a.png", "arjun": ""})
    assert z1_split.wanted({"file": "gen/a.png", "people": True})
    assert not z1_split.wanted({"file": "gen/a.png"})
    assert not z1_split.wanted({"file": "gen/a.png", "arjun": "", "cutout": True})

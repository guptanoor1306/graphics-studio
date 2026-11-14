"""Zero1 Hindi kit inside the studio: renders, gen: plates (image API mocked), checks and export files."""
import io
import json
import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
pytest.importorskip("playwright")

import db_store  # noqa: E402

THEME = "zero1-hindi-graphics"
KIT = ROOT / "themes" / THEME


def _spec():
    return json.loads((KIT / "examples" / "example_spec.json").read_text())


@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_store, "SQLITE_PATH", tmp_path / "studio.db")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import z1_plates
    monkeypatch.setattr(z1_plates, "_provider", z1_plates._provider)  # tests swap it; restored after each
    gen = KIT / "assets" / "gen"
    existed = gen.exists()
    yield
    if not existed:
        shutil.rmtree(gen, ignore_errors=True)


def _png(size=(1344, 768), white=False):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", size, "white" if white else (180, 140, 100))
    ImageDraw.Draw(im).ellipse((200, 200, 600, 600), fill=(200, 60, 60))
    b = io.BytesIO(); im.save(b, "PNG")
    return b.getvalue()


def test_kit_is_listed_and_rules_carry_the_method():
    import app, claude_client
    assert THEME in app.themes()
    rules = claude_client.theme_rules(KIT)
    for part in ("storyboarding_method.md", "gold/v2_corpus.md", "plates_index.md", "example_spec.json"):
        assert part in rules
    assert claude_client._system(KIT)[0]["text"].startswith("You are the Zero1 Hindi IP")


def test_every_example_frame_renders_without_layout_warnings():
    import app, critique
    spec = _spec(); p = {"theme": THEME, "look": {}, "spec": spec}
    base = (KIT / "scenes").as_uri() + "/"
    pages = [(f["id"], app.frame_page(THEME, app.frame_for_render(p, f), app.effective_look(p), base_href=base,
                                       all_frames=spec["frames"], spec=spec), None) for f in spec["frames"]]
    out = critique.render_frames(pages, app.builder(THEME).CHECK_JS, (1920, 1080))
    assert len(out) == len(spec["frames"])
    for fid, (png, warns) in out.items():
        assert png and not warns, (fid, warns)


def test_gen_plate_is_placeholder_until_made_then_the_image():
    import app, z1_plates
    spec = {"arjun": "city", "gen": {"flat": {"prompt": "Arjun in a small Mumbai flat", "arjun": ""}},
            "frames": [{"id": "0.00", "type": "scene", "bg": "gen:flat"}]}
    p = {"theme": THEME, "look": {}, "spec": spec}
    html = app.frame_page(THEME, app.frame_for_render(p, spec["frames"][0]), {})
    assert 'class="ph"' in html and "GEN: flat" in html
    z1_plates._provider = lambda: ("gemini", lambda req, key: _png(), "k")
    spec2, rep = z1_plates.fill(spec)
    assert rep["filled"] and not rep["failed"]
    f = spec2["gen"]["flat"]["file"]
    assert f.startswith("gen/") and (KIT / "assets" / f).is_file()
    from PIL import Image
    assert Image.open(KIT / "assets" / f).size == (1920, 1080)
    p2 = {**p, "spec": spec2}
    html2 = app.frame_page(THEME, app.frame_for_render(p2, spec2["frames"][0]), {})
    assert 'class="ph"' not in html2 and f"../assets/{f}" in html2
    # same prompt again comes from the library, no API call
    z1_plates._provider = lambda: (_ for _ in ()).throw(AssertionError("API called"))
    _, rep2 = z1_plates.fill(spec)
    assert list(rep2["filled"].values())[0]["source"] == "library"
    assert z1_plates.pending(spec2) == [] and z1_plates.pending(spec) == ["flat"]


def test_cutout_comes_back_transparent():
    import z1_plates
    spec = {"gen": {"bars": {"prompt": "gold bars", "cutout": True, "aspect": "1:1"}},
            "frames": [{"id": "1", "type": "scene", "layers": [{"img": "gen:bars", "x": 0, "y": 0, "w": 300}]}]}
    z1_plates._provider = lambda: ("gemini", lambda req, key: _png((1024, 1024), white=True), "k")
    spec2, _ = z1_plates.fill(spec)
    from PIL import Image
    im = Image.open(KIT / "assets" / spec2["gen"]["bars"]["file"])
    assert im.mode == "RGBA" and im.getpixel((5, 5))[3] == 0


def test_no_key_keeps_placeholders():
    import z1_plates
    spec = {"gen": {"x": {"prompt": "a lane"}}, "frames": [{"id": "1", "type": "scene", "bg": "gen:x"}]}
    z1_plates._provider = lambda: (None, None, None)
    spec2, rep = z1_plates.fill(spec)
    assert "gen:x" in rep["failed"] and "file" not in spec2["gen"]["x"]


def test_quality_gate_catches_missing_prompts_types_and_devanagari():
    import claude_client
    spec = {"gen": {}, "frames": [
        {"id": "1", "type": "scene", "bg": "gen:nope"},
        {"id": "2", "type": "slide"},
        {"id": "3", "type": "word", "text": "लेकिन"},
    ]}
    issues = " | ".join(claude_client.spec_quality_issues(spec, theme=THEME))
    assert "gen:nope has no prompt" in issues and 'unknown type "slide"' in issues and "Devanagari" in issues
    assert claude_client.spec_quality_issues(_spec(), theme=THEME) == []


def test_export_html_inlines_background_plate_and_adds_prompts():
    import app, exporter, z1_plates
    spec = _spec(); p = {"theme": THEME, "look": {}, "spec": spec, "storyboard": "#1 ~0:00 VO: Miliye Arjun se."}
    f = next(fr for fr in spec["frames"] if fr.get("type") == "table")
    html = app.frame_page(THEME, app.frame_for_render(p, f), {})
    out = exporter.inline_assets(html, KIT)
    assert "url('../assets" not in out and "data:image/jpeg;base64" in out and "<link" not in out
    files = z1_plates.export_files(p)
    assert "storyboard.md" in files and "## kirana" in files["image_prompts.md"] and "wooden toy" in files["image_prompts.md"]

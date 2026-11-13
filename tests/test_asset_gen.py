"""Asset placeholders → generated images (Gemini and Claude mocked, temp SQLite)."""
import base64
import io
import json
import pathlib
import shutil
import sys
from types import SimpleNamespace

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asset_gen  # noqa: E402
import db_store  # noqa: E402

THEME = "varsity-mf-graphics"


def _green_png(obj=(200, 40, 40), size=400):
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (size, size), (0, 255, 0))
    ImageDraw.Draw(im).ellipse([100, 120, 300, 280], fill=obj, outline=(20, 20, 20), width=8)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_store, "SQLITE_PATH", tmp_path / "studio.db")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("STUDIO_ASSET_QA", "0")
    gen = ROOT / "themes" / THEME / "assets" / "gen"
    existed = gen.exists()
    yield
    if not existed:
        shutil.rmtree(gen, ignore_errors=True)


def test_cut_out_makes_background_transparent_and_crops():
    from PIL import Image

    out = Image.open(io.BytesIO(asset_gen.cut_out(_green_png())))
    assert out.mode == "RGBA"
    assert out.size[0] < 260 and out.size[1] < 200  # cropped to the ellipse
    px = out.getpixel((out.size[0] // 2, out.size[1] // 2))
    assert px[3] == 255 and px[0] > 150 and px[1] < 80  # opaque red centre, no green spill
    assert out.getpixel((0, 0))[3] < 30  # corner is transparent


def test_sanitize_svg_strips_scripts_and_handlers():
    s = asset_gen.sanitize_svg('x <svg viewBox="0 0 10 10" onload="evil()"><script>evil()</script>'
                               '<a href="javascript:x"><rect width="5" height="5"/></a></svg> y')
    assert "script" not in s and "onload" not in s and "javascript" not in s
    assert s.startswith("<svg") and 'xmlns="http://www.w3.org/2000/svg"' in s


SPEC = {"look": "x", "frames": [
    {"id": "0.59", "type": "scene", "hero": {"asset": "TODO:gold bar", "x": 700, "y": 400, "w": 400},
     "props": [{"asset": "TODO: silver nugget ", "x": 100, "y": 100, "w": 200},
               {"asset": "illus/vault_open.png", "x": 1, "y": 1, "w": 1}]},
    {"id": "1.10", "type": "scene", "hero": {"asset": "TODO:gold bar", "x": 1, "y": 1, "w": 300}},
]}


def test_fill_spec_uses_gemini_then_library(monkeypatch):
    calls = []
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr(asset_gen, "gemini_image", lambda t, d, fb="": calls.append(d) or asset_gen.cut_out(_green_png()))
    spec, rep = asset_gen.fill_spec(THEME, json.loads(json.dumps(SPEC)))
    assert sorted(calls) == ["gold bar", "silver nugget"]  # deduped
    hero = spec["frames"][0]["hero"]["asset"]
    assert hero.startswith("gen/gold-bar-") and hero.endswith(".png")
    assert spec["frames"][1]["hero"]["asset"] == hero
    assert spec["frames"][0]["props"][1]["asset"] == "illus/vault_open.png"
    assert (ROOT / "themes" / THEME / "assets" / hero).is_file()
    assert asset_gen.todo_descriptions(spec) == []

    # second run: same descriptions come from the library, even after the disk is wiped
    shutil.rmtree(ROOT / "themes" / THEME / "assets" / "gen")
    calls.clear()
    spec2, rep2 = asset_gen.fill_spec(THEME, json.loads(json.dumps(SPEC)))
    assert calls == [] and {v["source"] for v in rep2["filled"].values()} == {"library"}
    assert (ROOT / "themes" / THEME / "assets" / hero).is_file()


def test_falls_back_to_claude_svg(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    import claude_client
    monkeypatch.setattr(claude_client, "draw_asset_svg",
                        lambda td, d: '<svg viewBox="0 0 800 800"><rect width="400" height="300"/></svg>')
    spec, rep = asset_gen.fill_spec(THEME, {"frames": [{"id": "a", "hero": {"asset": "TODO:bond certificate"}}]})
    assert spec["frames"][0]["hero"]["asset"].endswith(".svg")
    assert rep["filled"]["bond certificate"]["source"] == "claude-svg"


def test_failure_keeps_placeholder(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr(asset_gen, "gemini_image", lambda t, d, fb="": (_ for _ in ()).throw(RuntimeError("quota")))
    monkeypatch.setattr(asset_gen, "claude_svg", lambda t, d: (_ for _ in ()).throw(RuntimeError("down")))
    spec, rep = asset_gen.fill_spec(THEME, {"frames": [{"id": "a", "hero": {"asset": "TODO:phone"}}]})
    assert spec["frames"][0]["hero"]["asset"] == "TODO:phone"
    assert "quota" in rep["failed"]["phone"] and "down" in rep["failed"]["phone"]


def test_gemini_request_shape_and_model_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret")
    monkeypatch.setenv("STUDIO_GEMINI_IMAGE_MODEL", "made-up-model")
    seen = []

    def fake_post(url, body, headers, timeout):
        seen.append((url, body, headers))
        if "made-up-model" in url:
            return 404, "models/made-up-model is not found"
        data = base64.b64encode(_green_png()).decode()
        return 200, json.dumps({
            "candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": data}}]}}]})

    monkeypatch.setattr(asset_gen, "_http_post", fake_post)
    png = asset_gen.gemini_image(THEME, "gold bar")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(seen) == 2 and "made-up-model" in seen[0][0] and "gemini-3-pro-image-preview" in seen[1][0]
    url, body, headers = seen[1]
    assert headers["x-goog-api-key"] == "secret" and "key=" not in url
    parts = body["contents"][0]["parts"]
    text = parts[0]["text"]
    assert "gold bar" in text and "risograph" in text.lower()  # kit style text (asset_style.md)
    assert "glossy" in text and "podium" in text  # negatives
    refs = [p["inline_data"] for p in parts if "inline_data" in p]
    assert len(refs) >= 3 and all(r["mime_type"] == "image/jpeg" for r in refs)  # cut-outs on cream, not PNG alpha
    assert body["generationConfig"]["responseModalities"] == ["IMAGE"]


def test_generated_asset_renders_as_image_not_placeholder(monkeypatch):
    pytest.importorskip("playwright")
    import app, critique

    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr(asset_gen, "gemini_image", lambda t, d, fb="": asset_gen.cut_out(_green_png()))
    spec = json.loads((app.THEMES / THEME / "scenes/gift_city_spec.json").read_text())
    f = next(fr for fr in spec["frames"] if isinstance(fr.get("hero"), dict))
    f["hero"]["asset"] = "TODO:gold bar"
    spec, _ = asset_gen.fill_spec(THEME, spec)
    f = next(fr for fr in spec["frames"] if fr["id"] == f["id"])
    assert f["hero"]["asset"].startswith("gen/")
    p = {"theme": THEME, "look": {}, "spec": spec}
    base = (app.THEMES / THEME / "scenes").as_uri() + "/"
    html = app.frame_page(THEME, app.frame_for_render(p, f), app.effective_look(p),
                          base_href=base, all_frames=spec["frames"], spec=spec)
    probe = ("() => [document.body.innerText.includes('ASSET NEEDED') ? 'PLACEHOLDER' : 'no-placeholder', "
             "[...document.images].some(i => i.src.includes('/gen/') && i.naturalWidth > 0) ? 'GEN-IMG' : 'no-img']")
    png, res = critique.render_frames([(f["id"], html, None)], probe, (1920, 1080))[f["id"]]
    assert png
    assert "GEN-IMG" in res and "PLACEHOLDER" not in res, res


def _magenta_with_base():
    """Object (green rupee note + gold coin) on magenta, with a lighter pink 'podium' under it."""
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (512, 512), (255, 0, 255))
    d = ImageDraw.Draw(im)
    d.ellipse([110, 330, 400, 430], fill=(235, 60, 220))  # podium in a different magenta shade
    d.rectangle([140, 200, 370, 340], fill=(60, 170, 80))  # green note
    d.ellipse([300, 260, 380, 340], fill=(220, 170, 40))  # gold coin
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def test_cut_out_removes_tinted_base_and_keeps_green_notes():
    from PIL import Image

    png = asset_gen.cut_out(_magenta_with_base(), (255, 0, 255))
    out = Image.open(io.BytesIO(png))
    assert asset_gen.leftover_key(png) < 0.01
    w, h = out.size
    px = out.getpixel((w // 3, h // 2))
    assert px[3] == 255 and px[1] > 120  # the green note survives
    assert w < 260  # cropped to note + coin, not the wider podium


def test_style_check_rejects_then_retries_with_feedback(monkeypatch):
    import claude_client

    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("STUDIO_ASSET_QA", "1")
    feedbacks = []
    monkeypatch.setattr(asset_gen, "gemini_image",
                        lambda t, d, fb="": feedbacks.append(fb) or asset_gen.cut_out(_green_png()))
    verdicts = iter([{"ok": False, "problems": "too glossy, make it matte and grainy"}, {"ok": True, "problems": ""}])
    seen = {}

    def fake_review(theme_dir, desc, cand, refs, style):
        seen.update(refs=len(refs), style=style)
        return next(verdicts)
    monkeypatch.setattr(claude_client, "review_asset", fake_review)
    spec, rep = asset_gen.fill_spec(THEME, {"frames": [{"id": "a", "hero": {"asset": "TODO:gold bar"}}]})
    assert feedbacks == ["", "too glossy, make it matte and grainy"]
    assert rep["filled"]["gold bar"]["source"] == "gemini" and "note" not in rep["filled"]["gold bar"]
    assert seen["refs"] >= 3 and "risograph" in seen["style"].lower()


def test_redo_regenerates_existing_generated_assets(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    n = {"calls": 0}
    monkeypatch.setattr(asset_gen, "gemini_image",
                        lambda t, d, fb="": n.__setitem__("calls", n["calls"] + 1) or asset_gen.cut_out(_green_png()))
    spec, _ = asset_gen.fill_spec(THEME, {"frames": [{"id": "a", "hero": {"asset": "TODO:gold bar"}}]})
    first = spec["frames"][0]["hero"]["asset"]
    monkeypatch.setattr(asset_gen, "STYLE_VERSION", "test-next")
    spec2, rep = asset_gen.fill_spec(THEME, spec, redo=True)
    assert n["calls"] == 2
    new = spec2["frames"][0]["hero"]["asset"]
    assert new != first and new.startswith("gen/gold-bar-")

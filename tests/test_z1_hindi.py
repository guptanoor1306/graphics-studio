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


def _new_project(app, name="live"):
    with app.connect() as c:
        c.execute("insert into projects(name,theme,script,look,storyboard,spec,updated_by,updated_at) values(?,?,?,?,?,?,?,?)",
                  (name, THEME, "", "{}", "", None, "t", 0)); c.commit()
        return c.execute("select max(id) as id from projects").fetchone()["id"]


def test_live_preview_shows_frames_while_written_and_keeps_the_same_result(monkeypatch):
    import asyncio, time as _t
    import app, claude_client, critique, z1_plates
    final = {"arjun": "city", "gen": {"a": {"prompt": "a Mumbai lane", "arjun": ""}},
             "frames": [{"id": "0.00", "type": "scene", "bg": "gen:a"}, {"id": "0.05", "type": "word", "text": "Lekin!"},
                        {"id": "0.10", "type": "word", "text": "Sirf"}]}
    seen = []

    def fake_storyboard(tdir, script, look, notes="", episode_transcript=None):
        hook = claude_client._PARTIAL.fn
        assert hook, "the storyboard call must get the preview hook"
        hook({"storyboard": "#1 ~0:00\n#2 ~0:05"})                                  # still writing beats
        hook({"storyboard": "#1\n#2", "spec": {"gen": final["gen"], "frames": final["frames"][:2]}})   # 1 complete
        seen.append([f["id"] for f in app.load(pid)["spec"]["frames"]])
        hook({"storyboard": "#1\n#2", "spec": {"gen": final["gen"], "frames": final["frames"]}})       # 2 complete
        seen.append([f["id"] for f in app.load(pid)["spec"]["frames"]])
        return {"storyboard": "#1 ~0:00\n#2 ~0:05", "spec": json.loads(json.dumps(final))}
    monkeypatch.setattr(claude_client, "storyboard", fake_storyboard)
    monkeypatch.setattr(z1_plates, "_provider", lambda: ("gemini", lambda req, key: (_t.sleep(0.2), _png())[1], "k"))
    monkeypatch.setattr(app, "_critique_spec", lambda p, sp, sb, sc, fin, only_ids=None: (sp, {}))
    pid = _new_project(app)

    async def go():
        out = await app._make_storyboard(pid, {"script": "x", "look": {}}, "t")
        assert out["background"]
        for _ in range(100):
            s = app.project_progress(pid)
            if s.get("state") in ("done", "error"):
                return s
            await asyncio.sleep(0.05)
    s = asyncio.run(go())
    assert s["state"] == "done", s
    assert seen == [["0.00"], ["0.00", "0.05"]]           # frames appeared one by one, last one only when complete
    sp = app.load(pid)["spec"]
    assert [f["id"] for f in sp["frames"]] == ["0.00", "0.05", "0.10"] and sp["gen"]["a"]["file"]
    with app.connect() as c:
        notes = [r["note"] for r in c.execute("select note from versions where project_id=? order by id", (pid,)).fetchall()]
    assert notes == ["generated storyboard (generated 1 asset(s))"]   # previews add no Undo steps


def test_failed_storyboard_puts_the_old_frames_back(monkeypatch):
    import asyncio
    import app, claude_client
    pid = _new_project(app, "fail")
    old = {"frames": [{"id": "9", "type": "word", "text": "Old"}]}
    app.save(pid, "t", "seed", spec=old, storyboard="old sb")

    def boom(*a, **k):
        claude_client._PARTIAL.fn({"storyboard": "#1", "spec": {"frames": [{"id": "1", "type": "word"}, {"id": "2"}]}})
        raise RuntimeError("overloaded")
    monkeypatch.setattr(claude_client, "storyboard", boom)

    async def go():
        await app._make_storyboard(pid, {"script": "x", "look": {}}, "t")
        for _ in range(50):
            s = app.project_progress(pid)
            if s.get("state") in ("done", "error"):
                return s
            await asyncio.sleep(0.05)
    s = asyncio.run(go())
    assert s["state"] == "error" and "overloaded" in s["msg"]
    p = app.load(pid)
    assert p["spec"] == old and p["storyboard"] == "old sb"


def test_stream_hands_partial_tool_input_to_the_hook(monkeypatch):
    import claude_client

    class Ev:
        def __init__(self, snap): self.type, self.snapshot = "input_json", snap

    class S:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def __iter__(self):
            yield Ev({"storyboard": "#1"})
        def get_final_message(self): return "FINAL"

    class C:
        class messages:
            @staticmethod
            def stream(**kw): return S()
    monkeypatch.setattr(claude_client, "_client", lambda: C())
    got = []
    assert claude_client._messages_create(on_partial=got.append, max_tokens=100, messages=[]) == "FINAL"
    assert got == [{"storyboard": "#1"}]


def test_script_mode_is_told_to_stay_inside_the_given_lines(monkeypatch):
    import claude_client
    msgs = []
    monkeypatch.setattr(claude_client, "_call_storyboard", lambda tdir, msg, **k: msgs.append(msg) or {"spec": {"frames": []}})
    monkeypatch.setattr(claude_client, "patch_until_clean", lambda tdir, out, *a, **k: out)
    claude_client.storyboard(KIT, "Line one.\nLine two.", {}, "")
    assert "SCOPE" in msgs[0] and "Do not invent sections it does not contain" in msgs[0]
    assert "follow the skill fully" in msgs[0] and "more than one frame only" not in msgs[0]


def test_pdf_styleframe_becomes_the_main_reference_and_text_is_dropped(tmp_path, monkeypatch):
    import fitz
    import z1_plates
    pic = tmp_path / "shot.png"
    from PIL import Image
    Image.new("RGB", (800, 450), (40, 90, 160)).save(pic)
    pdf = tmp_path / "sb.pdf"
    doc = fitz.open(); doc.new_page(); pg = doc.new_page()
    pg.insert_image(fitz.Rect(50, 50, 450, 275), filename=str(pic)); doc.save(str(pdf))
    monkeypatch.setattr(z1_plates, "PDF_REF_DIR", tmp_path / "refs")
    imgs = z1_plates.pdf_page_images(pdf, 2, "p1")
    assert len(imgs) == 1 and z1_plates.pdf_page_images(pdf, 1, "p1") == []
    sent = {}
    monkeypatch.setattr(z1_plates, "_provider", lambda: ("gemini", lambda req, key: (sent.update(req), _png())[1], "k"))
    entry = {"prompt": 'Big paper-cut "₹1,00,000" numerals over the Mumbai skyline, ₹4,000 balance', "pdf_page": 2}
    z1_plates.make_one("sky", entry, {"arjun": "city"}, True, {"path": str(pdf), "key": "p1"})
    assert sent["refs"][0] == imgs[0] and "approved styleframe" in sent["prompt"]
    assert "1,00,000" not in sent["prompt"] and "4,000" not in sent["prompt"] and "Mumbai skyline" in sent["prompt"]

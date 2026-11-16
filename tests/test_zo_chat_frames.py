"""ZO Product chat-skill mode: hand-written html frames render, pass/flag the checks, export to Bulletin."""
import io
import json
import zipfile

import pytest

FSS = {"id": "04", "mode": "fss", "name": "04_Exit-load", "section": "Intro",
       "html": ('<div class="center" data-name="Heading" style="top:120px;text-align:center"><div class="h" data-name="Heading text">'
                '<span>Exit load </span><span class="o">reduces</span><span> over time</span></div>'
                '<div class="bar" data-name="Yellow underline"></div></div>'
                '<div class="card abs" data-name="Card / Table" style="left:410px;top:330px;width:1100px;padding:70px 40px 30px">'
                '<div class="dots" data-name="Window dots"><div data-name="Dot"></div><div data-name="Dot"></div><div data-name="Dot"></div></div>'
                '<table class="zt left" style="font-size:44px"><tr><th>Exit period</th><th>Exit load</th></tr>'
                '<tr><td>Within 1 year</td><td>3%</td></tr><tr class="hl"><td>After 1 year</td><td>Nil</td></tr></table></div>'),
       "decor": {"doodleAt": {"left": "200px", "top": "140px"}, "tri1": {"right": "150px", "top": "170px"},
                 "tri2": {"left": "170px", "bottom": "110px"}, "starAt": {"right": "130px", "bottom": "90px"},
                 "dash1": {"left": "100px", "top": "60%"}, "dash2": {"right": "100px", "top": "45%"}}}
OST = {"id": "05", "mode": "ost", "plate": "m2_right", "name": "05_TOS_No-lock-in",
       "html": ('<div class="abs ov" data-name="Title" style="left:160px;top:420px"><div class="ov-title" data-name="Title text">'
                '<span>No </span><span class="y">lock-in</span></div><div class="ov-line" data-name="Underline"></div></div>'),
       "decor": {"doodleAt": {"left": "160px", "top": "280px"}, "tri1": {"left": "160px", "top": "720px"},
                 "tri2": {"left": "700px", "top": "760px"}}}


def _render(html_pages):
    import critique
    import theme_canvas
    from app import builder
    b = builder("zo-product-graphics")
    return critique.render_frames(html_pages, b.CHECK_JS, theme_canvas.canvas_for_theme("zo-product-graphics"))


def test_html_frames_render_with_the_chat_kit_and_its_checks():
    import app
    base = (app.THEMES / "zo-product-graphics" / "scenes").as_uri() + "/"
    spec = {"look": {}, "frames": [FSS, OST]}
    pages = [(f["id"], app.frame_page("zo-product-graphics", f, {}, base_href=base, all_frames=spec["frames"], spec=spec), None)
             for f in spec["frames"]]
    assert "templates/chat/zo.css" in pages[0][1] and "m2_right.jpg" in pages[1][1]
    out = _render(pages)
    for fid, (png, warns) in out.items():
        assert png, fid
        assert not [w for w in warns if "never finished" in w or "page error" in w], (fid, warns)
    # a decor piece on top of the heading is reported
    bad = {**FSS, "decor": {**FSS["decor"], "tri1": {"left": "900px", "top": "130px"}}}
    out = _render([("x", app.frame_page("zo-product-graphics", bad, {}, base_href=base, all_frames=[bad], spec={"frames": [bad]}), None)])
    assert any("decor Triangle touches" in w for w in out["x"][1])


def test_compact_keeps_html_frames_and_their_plates():
    from mf_studio import compact_zo_spec_for_studio
    sp = compact_zo_spec_for_studio({"look": {}, "frames": [FSS, {**OST, "plate": None}, {"id": "06", "mode": "screen"}]})
    assert [f["id"] for f in sp["frames"]] == ["04", "05"]
    assert sp["frames"][1]["plate"] == "m2_right" and sp["frames"][0]["html"] == FSS["html"]


def test_html_frames_export_to_bulletin(tmp_path):
    import app
    p = {"name": "Exit load demo", "theme": "zo-product-graphics", "spec": {"look": {}, "frames": [FSS, OST]}, "storyboard": ""}
    dest = tmp_path / "b.zip"
    app._export_bulletin(p, "", dest)
    z = zipfile.ZipFile(dest)
    names = z.namelist()
    assert any(n.endswith(".html") and "/html/" in n for n in names) and any("/png/" in n for n in names)
    layers = [json.loads(z.read(n)) for n in names if "/layers/" in n and n.endswith(".json")]
    flat = json.dumps(layers)
    assert "Heading text" in flat and "Presenter plate" in flat


def test_pdf_batch_cut_off_reply_retries_with_fewer_frames(monkeypatch):
    import pathlib
    import claude_client as c
    calls = []

    def fake_call(theme_dir, msg, pdf_bytes, *, page_images=None, max_tokens=0, sb_tool=None):
        calls.append((msg, max_tokens))
        if len(calls) == 1:
            raise c.ReplyCutOff("cut")
        return {"storyboard": "SB", "frames": [{"id": "01", "mode": "fss", "html": "<div class=abs>x</div>"},
                                                {"id": "02", "mode": "fss", "html": "<div class=abs>y</div>"}]}

    monkeypatch.setattr(c, "_call_with_pdf", fake_call)
    out = c._storyboard_pdf_batch_once(pathlib.Path("themes/zo-product-graphics"), b"%PDF", "", {}, "",
                                       batch_size=5, page_images=[])
    assert len(calls) == 2 and calls[0][1] == c.PDF_BATCH_MAX_TOKENS
    assert "at most 3 frames" in calls[1][0] and out["frames_added"] == 2


def test_all_remaining_ends_cleanly_when_claude_says_nothing_is_left(monkeypatch):
    import pathlib
    import claude_client as c
    calls = []

    def fake_call(theme_dir, msg, pdf_bytes, *, page_images=None, max_tokens=0, sb_tool=None):
        calls.append(msg)
        if len(calls) == 1:
            return {"frames": [{"id": "08", "mode": "fss", "html": "<div class=abs>x</div>"}]}
        raise c.NoToolCall("Claude did not call submit_graphic_batch (stop_reason=end_turn). Try again.")

    monkeypatch.setattr(c, "_call_with_pdf", fake_call)
    out = c._storyboard_pdf_finish_all(pathlib.Path("themes/zo-product-graphics"), b"%PDF", "", {}, "", batch_size=5,
                                       existing_spec={"frames": [{"id": "01", "mode": "fss", "html": "<i>a</i>"}]},
                                       existing_storyboard="SB", episode_transcript=None, page_images=[])
    assert out["frames_added"] == 1 and [f["id"] for f in out["frames"]] == ["08"]

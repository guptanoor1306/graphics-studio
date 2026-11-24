import toolkit


def test_marked_script_and_merge_rest_order():
    lines = ["Intro line one", "MTF lets you buy more", "", "Interest is 0.04% a day", "Risks of margin", "Wrap up now"]
    tk = {"id": "tk1", "tk_from": "t1", "lines": [3, 3], "vo": "Interest is 0.04% a day"}
    m = toolkit.marked_script(lines, {3})
    assert "[[ALREADY A FRAME: Interest is 0.04% a day]]" in m and "Intro line one" in m
    new = [{"id": "1", "vo": "Intro line one. MTF lets you buy more"}, {"id": "2", "vo": "Interest is 0.04% a day"},
           {"id": "3", "vo": "Risks of margin"}, {"id": "4", "vo": "Wrap up now"}]
    out = toolkit.merge_rest([tk], new, lines, "script")
    assert [f["id"] for f in out] == ["1", "tk1", "3", "4"]          # frame 2 duplicated a toolkit line: dropped
    assert out[0]["lines"] == [0, 2] and out[2]["lines"] == [4, 4] and out[3]["lines"] == [5, 5]


def test_place_inserts_by_line_and_carries_template_photo():
    proj = {"theme": "zo-product-graphics", "spec": {"frames": [
        {"id": "1", "mode": "osa", "html": "<p>a</p>", "lines": [0, 1]}, {"id": "2", "mode": "fss", "html": "<p>b</p>", "lines": [5, 6]}]}}
    tpl = {"id": "t3", "name": "Anchor right", "mode": "osa", "plate": "m2_right", "html": "<p>Heading</p>"}
    spec, fid = toolkit.place(proj, tpl, {"presenter": {"right": "gen/photo.jpg"}}, [2, 3], "Some words", "script")
    assert fid == "tk1" and [f["id"] for f in spec["frames"]] == ["1", "tk1", "2"]
    f = spec["frames"][1]
    assert f["tk_from"] == "t3" and f["lines"] == [2, 3] and f["vo"] == "Some words" and f["plate_img"] == "gen/photo.jpg"


def test_from_frame_takes_the_videos_presenter_shot():
    src = {"theme": "zo-product-graphics", "look": {"presenter": {"left": "gen/me.jpg"}}}
    fr = {"id": "7", "mode": "osa", "plate": "m2_left", "html": "<p>x</p>", "vo": "words", "lines": [1, 2]}
    t = toolkit.from_frame(src, fr, "Left list", [])
    assert t["id"] == "t1" and t["name"] == "Left list" and t["plate_img"] == "gen/me.jpg" and "vo" not in t and "lines" not in t


def test_blank_templates():
    a = toolkit.blank("m2_left", [])
    assert a["mode"] == "osa" and a["plate"] == "m2_left" and "left:1010px" in a["html"]
    b = toolkit.blank("fss", [a])
    assert b["mode"] == "fss" and "plate" not in b and b["id"] == "t2"


def test_pdf_lines_drop_repeated_headers():
    import fitz
    d = fitz.open()
    for i in range(4):
        pg = d.new_page()
        pg.insert_text((50, 40), "MTF storyboard v2")          # header on every page
        pg.insert_text((50, 100), f"Scene {i + 1}: interest is 0.0{i}% a day")
        pg.insert_text((50, 130), "0:12")
    lines = toolkit.pdf_lines(d.tobytes())
    assert lines == [f"Scene {i + 1}: interest is 0.0{i}% a day" for i in range(4)]

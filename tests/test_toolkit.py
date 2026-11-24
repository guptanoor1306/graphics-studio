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


def test_skip_lines_are_left_out():
    lines = ["intro", "toolkit line", "no graphic here", "fourth", "fifth"]
    s = toolkit.marked_script(lines, {1}, {2})
    assert "[[ALREADY A FRAME: toolkit line]]" in s and "[[NO FRAME: no graphic here]]" in s
    kept = [{"id": "tk1", "tk_from": "t1", "lines": [1, 1]}]
    new = [{"id": "1", "vo": "intro"}, {"id": "2", "vo": "no graphic here"}, {"id": "3", "vo": "fourth"}]
    out = toolkit.merge_rest(kept, new, lines, "script", {2})
    assert [f["id"] for f in out] == ["1", "tk1", "3"]
    assert out[2]["lines"] == [3, 4]


def test_carry_keeps_skip_marks():
    new = {"frames": []}
    toolkit.carry({"tk_skip": [2, 3], "tk_skip_src": "pdf"}, new)
    assert new["tk_skip"] == [2, 3] and new["tk_skip_src"] == "pdf"


def test_ipo_kit_reuses_zo_product():
    import theme_alias, presenter
    assert theme_alias.base("zo-ipo-graphics") == "zo-product-graphics"
    assert toolkit.enabled("zo-ipo-graphics")
    assert presenter.has_slots("zo-ipo-graphics")
    assert presenter.slot_of("zo-ipo-graphics", {"mode": "osa", "plate": "m2_left", "html": "<div></div>"}) == "left"


def test_paraphrased_frame_lands_on_its_free_line():
    lines = ["Jio is launching its IPO this month.", "The IPO opens on October 21 and closes on October 23.",
             "In this video we'll look at how Jio makes money.",
             "To understand how Jio makes money, think of the nationwide network it has built as a digital highway. Every time you recharge you pay a toll.",
             "Today Jio's business extends beyond mobile connectivity."]
    kept = [{"id": f"tk{i}", "tk_from": "t", "lines": [i, i]} for i in (0, 1, 2, 4)]
    new = [{"id": "5", "vo": "Jio's network: a digital highway, recharge = toll"}]
    out = toolkit.merge_rest(kept, new, lines, "script")
    assert [f["id"] for f in out] == ["tk0", "tk1", "tk2", "5", "tk4"]
    assert out[3]["lines"] == [3, 3]
    # nothing in common: still the free line, never a toolkit line
    out = toolkit.merge_rest(kept, [{"id": "6", "vo": "zzz qqq"}], lines, "script")
    assert next(f for f in out if f["id"] == "6")["lines"] == [3, 3]

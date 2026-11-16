"""Make Layers sends smaller frames: the fonts a kit uses can be listed, and a frame's HTML can leave out the fonts
LA Studio already has installed (export.html?skip=Family:weight[i],...). Without skip the HTML is exactly as before."""
import json
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import db_store  # noqa: E402
import exporter  # noqa: E402

PAGE = """<html><head><style>
@font-face{font-family:Inter;font-weight:300;src:url(data:font/ttf;base64,AAA)}
@font-face{font-family:"Inter";font-weight:700;font-style:italic;src:url(data:font/ttf;base64,BBB)}
@font-face{font-family:'Bricolage';src:url(data:font/woff2;base64,CCC) format("woff2");font-weight:200}
@font-face{font-family:Anton;src:url(data:font/woff2;base64,DDD)}
body{font-family:Inter}
</style></head><body>Hi</body></html>"""


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(db_store, "SQLITE_PATH", tmp_path / "studio.db")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from fastapi.testclient import TestClient
    import app
    return TestClient(app.app)


def faces(html):
    return {(f["family"], f["weight"], f["italic"]) for f in exporter.font_faces(html)}


def test_font_faces_reads_family_weight_and_style():
    assert faces(PAGE) == {("Inter", 300, False), ("Inter", 700, True), ("Bricolage", 200, False), ("Anton", 400, False)}


def test_parse_skip_reads_family_weight_and_italic():
    assert exporter.parse_skip("Inter:300,Inter:700i, Bricolage Grotesque:400") == {
        ("inter", 300, False), ("inter", 700, True), ("bricolage grotesque", 400, False)}


def test_parse_skip_ignores_bad_values():
    assert exporter.parse_skip("") == set()
    assert exporter.parse_skip(None) == set()
    assert exporter.parse_skip("<script>,::,Inter:abc,Inter:9000,:400,Inter") == set()
    assert len(exporter.parse_skip(",".join(f"F{i}:400" for i in range(500)))) <= exporter.MAX_SKIP


def test_drop_faces_points_the_named_fonts_at_the_installed_ones():
    out = exporter.drop_faces(PAGE, {("inter", 300, False), ("inter", 700, True)})
    assert "AAA" not in out and "BBB" not in out and "CCC" in out and "DDD" in out
    assert faces(out) == faces(PAGE)                                         # the same fonts, so the page picks the same weights
    assert 'local("Inter Light")' in out and 'local("Inter-Light")' in out
    assert 'local("Inter Bold Italic")' in out and 'local("Inter-BoldItalic")' in out
    assert "body{font-family:Inter}" in out


def test_drop_faces_names_regular_and_italic_the_usual_way():
    page = "@font-face{font-family:Inter;src:url(data:x)}@font-face{font-family:Inter;font-style:italic;src:url(data:y)}"
    out = exporter.drop_faces(page, {("inter", 400, False), ("inter", 400, True)})
    assert 'local("Inter Regular")' in out and 'local("Inter-Regular")' in out
    assert 'local("Inter Italic")' in out and 'local("Inter-Italic")' in out and "data:" not in out


def test_drop_faces_with_nothing_to_skip_changes_nothing():
    assert exporter.drop_faces(PAGE, set()) == PAGE
    assert exporter.drop_faces(PAGE, {("inter", 400, False)}) == PAGE          # a weight the page doesn't have


def test_kit_font_faces_route_lists_the_fonts_of_the_project_kit(client):
    p = client.post("/api/projects", json={"name": "Fonts", "theme": "zo-product-graphics"}).json()
    got = client.get(f"/api/projects/{p['id']}/font-faces").json()["faces"]
    assert {(f["family"], f["weight"], f["italic"]) for f in got} == {("Inter", w, False) for w in (300, 400, 500, 600, 700)}


def test_kit_font_faces_route_404_for_a_missing_project(client):
    assert client.get("/api/projects/999999/font-faces").status_code == 404


def test_export_skip_leaves_installed_fonts_out_and_keeps_the_rest(client):
    pytest.importorskip("playwright")
    p = client.post("/api/projects", json={"name": "Skip", "theme": "zero1-hindi-graphics"}).json()
    spec = json.loads((ROOT / "themes/zero1-hindi-graphics/examples/example_spec.json").read_text())
    client.put(f"/api/projects/{p['id']}", json={"spec": spec})
    fid = spec["frames"][0]["id"]
    url = f"/api/projects/{p['id']}/frames/{fid}/export.html"
    full = client.get(url).text
    same = client.get(url + "?skip=" + "<bad>,::").text
    assert same == full                                                       # a bad skip changes nothing
    kept = faces(full)
    some = {f for f in kept if f[0] == "Bricolage"}
    assert some, "this kit embeds Bricolage"
    skip = ",".join(f"{f}:{w}{'i' if i else ''}" for f, w, i in some)
    lean = client.get(url + "?skip=" + skip).text
    assert faces(lean) == kept                                               # same fonts, now from this computer
    assert 'local("Bricolage' in lean
    assert len(lean) < len(full)
    assert re.search(r"data:image", lean), "pictures are still inlined"


def test_parse_skip_is_quick_on_a_long_value():
    import time
    t = time.perf_counter()
    assert exporter.parse_skip(" " * 20000) == set()
    assert exporter.parse_skip("a" * 20000 + ":400") == set()
    assert exporter.parse_skip(("Inter " * 3000) + ":400") == set()
    assert time.perf_counter() - t < 0.2


def test_drop_faces_is_quick_on_unclosed_brackets():
    import time
    page = "@font-face{font-family:Inter;font-weight:300;" + "src:(" * 40000 + "}"
    t = time.perf_counter()
    exporter.drop_faces(page, {("inter", 300, False)})
    assert time.perf_counter() - t < 0.5


def test_a_huge_weight_number_is_read_as_normal():
    page = "@font-face{font-family:Inter;font-weight:" + "9" * 5000 + ";src:url(data:x)}"
    assert faces(page) == {("Inter", 400, False)}

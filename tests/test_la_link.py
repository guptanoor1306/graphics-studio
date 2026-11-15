"""LA Studio link: hierarchy, linking a project, frame counts, self-contained frame HTML, CORS for the local app."""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import db_store  # noqa: E402


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(db_store, "SQLITE_PATH", tmp_path / "studio.db")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from fastapi.testclient import TestClient
    import app
    return TestClient(app.app)


def test_hierarchy_lists_channels_with_their_kits(client):
    h = client.get("/api/hierarchy").json()["channels"]
    ids = {c["id"]: c for c in h}
    assert {"zo", "varsity", "zero1"} <= set(ids)
    assert any(k["theme"] == "zero1-reel-graphics" and k["form"] == "sf" for k in ids["zero1"]["kits"])
    assert all(k["form"] in ("lf", "sf") for c in h for k in c["kits"])


def test_link_creates_and_finds_the_project_then_delete_unlinks(client):
    p = client.post("/api/la/link", json={"la_project": "prj18f00abcd", "la_name": "1 Lakh Mumbai",
                                          "name": "1 Lakh Mumbai", "theme": "zero1-hindi-graphics"}).json()
    assert p["theme"] == "zero1-hindi-graphics" and p["name"] == "1 Lakh Mumbai"
    assert client.get("/api/la/project/prj18f00abcd").json()["project_id"] == p["id"]
    spec = json.loads((ROOT / "themes/zero1-hindi-graphics/examples/example_spec.json").read_text())
    client.put(f"/api/projects/{p['id']}", json={"spec": spec})
    links = client.get("/api/la/links").json()["links"]
    assert links == [{"la_project": "prj18f00abcd", "project_id": p["id"], "la_name": "1 Lakh Mumbai", "name": "1 Lakh Mumbai",
                      "theme": "zero1-hindi-graphics", "updated_at": links[0]["updated_at"], "frames": len(spec["frames"]),
                      "channel": "zero1"}]
    client.delete(f"/api/projects/{p['id']}")
    assert client.get("/api/la/links").json()["links"] == []


def test_relinking_moves_the_link(client):
    a = client.post("/api/la/link", json={"la_project": "prjA", "name": "A", "theme": "zo-product-graphics"}).json()
    client.post("/api/la/link", json={"la_project": "prjB", "project_id": a["id"]})
    assert client.get("/api/la/project/prjA").json()["project_id"] is None
    assert client.get("/api/la/project/prjB").json()["project_id"] == a["id"]


def test_bad_requests_are_refused(client):
    assert client.post("/api/la/link", json={"la_project": "../x", "theme": "zo-product-graphics"}).status_code == 400
    assert client.post("/api/la/link", json={"la_project": "prjC", "theme": "nope"}).status_code == 400


def test_frame_html_is_self_contained(client):
    pytest.importorskip("playwright")
    p = client.post("/api/la/link", json={"la_project": "prjD", "name": "D", "theme": "zero1-hindi-graphics"}).json()
    spec = json.loads((ROOT / "themes/zero1-hindi-graphics/examples/example_spec.json").read_text())
    client.put(f"/api/projects/{p['id']}", json={"spec": spec})
    fid = spec["frames"][0]["id"]
    r = client.get(f"/api/projects/{p['id']}/frames/{fid}/export.html")
    assert r.status_code == 200 and "data:image" in r.text and "<base " not in r.text
    import re
    assert not re.findall(r"url\(\s*['\"]?(?!data:|#)[^)'\"]+", r.text), "every picture inlined"
    assert client.get(f"/api/projects/{p['id']}/frames/nope/export.html").status_code == 404


def test_local_la_studio_may_read_the_api(client):
    r = client.get("/api/hierarchy", headers={"Origin": "http://127.0.0.1:8770"})
    assert r.headers.get("access-control-allow-origin") == "http://127.0.0.1:8770"
    r = client.get("/api/hierarchy", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers

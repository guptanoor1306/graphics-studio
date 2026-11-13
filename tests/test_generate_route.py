"""Generate route end to end with a fake Claude: storyboard → quality gate → render review → save.
Needs Playwright Chromium (set CHROMIUM_PATH if needed)."""
import copy
import json
import pathlib
import sys
from types import SimpleNamespace

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

pytest.importorskip("playwright")


def _tool(name, inp):
    return SimpleNamespace(stop_reason="tool_use", content=[SimpleNamespace(type="tool_use", name=name, input=inp)])


class FakeMessages:
    def __init__(self, spec, good, fail=False):
        self.spec, self.good, self.fail = spec, good, fail

    def create(self, **kw):
        return self._reply(kw)

    def stream(self, **kw):
        outer = self

        class S:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def get_final_message(self):
                return outer._reply(kw)
        return S()

    def _reply(self, kw):
        if self.fail:
            raise RuntimeError("Claude did not call submit_storyboard")
        name = kw["tools"][0]["name"]
        if name == "submit_storyboard":
            return _tool(name, {"storyboard": "SB\n~1:12 – OSA – building → 1.12", "spec": copy.deepcopy(self.spec)})
        text = kw["messages"][0]["content"][-1]["text"]
        if "Contact sheet" in json.dumps(kw["messages"][0]["content"]) and "1.12: " in text and "off-canvas" in text:
            return _tool(name, {"fixes": [{"id": "1.12", "why": "moved building on frame", "frame": self.good}]})
        return _tool(name, {"fixes": []})


@pytest.fixture
def client(monkeypatch, tmp_path):
    import app
    from fastapi.testclient import TestClient
    return app, TestClient(app.app)


def _setup(app, monkeypatch, fail=False):
    import claude_client
    spec = json.loads((app.THEMES / "varsity-english/scenes/example_spec.json").read_text())
    good = copy.deepcopy(next(f for f in spec["frames"] if f["id"] == "1.12"))
    for it in next(f for f in spec["frames"] if f["id"] == "1.12")["items"]:
        if it["t"] == "asset":
            it["x"] = 1700
    monkeypatch.setattr(claude_client, "_client", lambda: SimpleNamespace(messages=FakeMessages(spec, good, fail)))
    monkeypatch.setattr(claude_client, "MODEL", "claude-opus-5-5")


def test_generate_reviews_and_saves(client, monkeypatch):
    app, c = client
    _setup(app, monkeypatch)
    pid = c.post("/api/projects", json={"name": "route test", "theme": "varsity-english"}).json()["id"]
    try:
        r = c.post(f"/api/projects/{pid}/storyboard", json={"script": "s", "look": {"anchor": "right"}})
        assert r.status_code == 200
        d = json.loads(r.text)  # streamed body may start with keep-alive spaces
        assert "1.12" in d["critique"]["changed"]
        saved = next(f for f in d["spec"]["frames"] if f["id"] == "1.12")
        assert [it["x"] for it in saved["items"] if it["t"] == "asset"] != [1700]
        assert "auto-fixed 1 frame" in c.get(f"/api/projects/{pid}/history").json()[0]["note"]
    finally:
        c.delete(f"/api/projects/{pid}")


def test_generate_error_comes_back_in_body(client, monkeypatch):
    app, c = client
    _setup(app, monkeypatch, fail=True)
    pid = c.post("/api/projects", json={"name": "route err", "theme": "varsity-english"}).json()["id"]
    try:
        d = json.loads(c.post(f"/api/projects/{pid}/storyboard", json={"script": "s"}).text)
        assert d["status"] == 502 and "submit_storyboard" in d["__stream_error"]
    finally:
        c.delete(f"/api/projects/{pid}")


def test_generate_404_before_streaming(client):
    app, c = client
    assert c.post("/api/projects/99999999/storyboard", json={"script": "s"}).status_code == 404

"""Cost record and the two-pass storyboard (Opus plans, Sonnet draws), with Claude stubbed out."""
import json
import pathlib
import types

import claude_client as c


def _resp(tool, inp, inp_tokens=1000, out_tokens=500):
    return types.SimpleNamespace(content=[types.SimpleNamespace(type="tool_use", name=tool, input=inp)], stop_reason="tool_use",
                                 usage=types.SimpleNamespace(input_tokens=inp_tokens, output_tokens=out_tokens,
                                                             cache_read_input_tokens=0, cache_creation_input_tokens=0))


def test_cost_usd_prices():
    assert abs(c.cost_usd("claude-opus-5-5", {"input": 1_000_000, "output": 1_000_000}) - 24.0) < 1e-6
    assert abs(c.cost_usd("claude-sonnet-5-5", {"input": 1_000_000, "output": 1_000_000}) - 12.0) < 1e-6
    assert abs(c.cost_usd("claude-opus-5-5", {"cache_read": 1_000_000}) - 0.2) < 1e-6


def test_split_plans_with_opus_and_draws_with_sonnet(monkeypatch):
    calls = []

    def fake(**kw):
        calls.append((kw.get("label"), kw.get("model")))
        tool = kw["tools"][0]["name"]
        if tool == "submit_plan":
            return _resp(tool, {"storyboard": "SB text", "spec_extra": {"look": {"anchor": "right"}},
                                "frames": [{"id": f"0.{i:02d}", "brief": f"frame {i}"} for i in range(1, 9)]})
        ask = kw["messages"][0]["content"][-1]["text"]
        ids = [ln.split(":")[0][2:] for ln in ask.splitlines() if ln.startswith("- ")]
        return _resp(tool, {"frames": [{"id": i, "mode": "fss", "items": [{"t": "title", "text": i}]} for i in ids]})

    monkeypatch.setattr(c, "_messages_create", fake)
    monkeypatch.setattr(c, "SETTING", lambda k: "on" if k == "sb_split" else None)
    seen = []
    with c.partial_hook(lambda snap: seen.append(len(snap["spec"]["frames"]))):
        out = c._call_storyboard(pathlib.Path("themes/varsity-english"), "SCRIPT: hello")
    assert out["storyboard"] == "SB text"
    assert out["spec"]["look"] == {"anchor": "right"}
    assert [f["id"] for f in out["spec"]["frames"]] == [f"0.{i:02d}" for i in range(1, 9)]
    assert calls[0] == ("storyboard-plan", None)                       # Opus (the default model) plans
    assert all(l == "storyboard-frames" and m == c.LIGHT_MODEL for l, m in calls[1:])
    assert len(calls) == 1 + 2 and seen and seen[-1] == 8


def test_split_off_keeps_one_call(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "_messages_create", lambda **kw: calls.append(kw["label"]) or _resp(kw["tools"][0]["name"], {"storyboard": "x", "spec": {"look": {}, "frames": [{"id": "1", "mode": "fss", "items": [{"t": "title"}]}]}}))
    monkeypatch.setattr(c, "SETTING", lambda k: "off")
    out = c._call_storyboard(pathlib.Path("themes/varsity-english"), "SCRIPT: hello")
    assert calls == ["storyboard"] and out["spec"]["frames"][0]["id"] == "1"


def test_split_falls_back_when_a_frame_is_missing(monkeypatch):
    calls = []

    def fake(**kw):
        calls.append(kw["label"])
        tool = kw["tools"][0]["name"]
        if tool == "submit_plan":
            return _resp(tool, {"storyboard": "s", "spec_extra": {}, "frames": [{"id": "a", "brief": "b"}]})
        if tool == "submit_frames":
            return _resp(tool, {"frames": []})
        return _resp(tool, {"storyboard": "one call", "spec": {"look": {}, "frames": [{"id": "a", "mode": "fss", "items": [{"t": "x"}]}]}})

    monkeypatch.setattr(c, "_messages_create", fake)
    monkeypatch.setattr(c, "SETTING", lambda k: "on")
    out = c._call_storyboard(pathlib.Path("themes/varsity-english"), "SCRIPT")
    assert out["storyboard"] == "one call" and calls[-1] == "storyboard"


def test_usage_record_and_endpoint(monkeypatch):
    from fastapi.testclient import TestClient
    import app as A
    cl = TestClient(A.app)
    before = cl.get("/api/usage?days=1").json()["calls"]
    c._log_usage("storyboard-plan", "claude-opus-5-5", _resp("x", {}, 2000, 1000))
    j = cl.get("/api/usage?days=1").json()
    assert j["calls"] == before + 1
    job = next(x for x in j["jobs"] if x["label"] == "storyboard-plan")
    assert job["cost"] > 0
    assert cl.put("/api/settings", json={"key": "sb_split", "value": "on"}).status_code == 200
    assert cl.get("/api/usage?days=1").json()["settings"]["sb_split"] == "on"
    assert c.sb_split_on()
    cl.put("/api/settings", json={"key": "sb_split", "value": "off"})
    assert cl.put("/api/settings", json={"key": "nope", "value": "on"}).status_code == 400

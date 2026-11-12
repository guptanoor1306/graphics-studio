"""Request shape of the Claude calls (fake Anthropic client, no network)."""
import pathlib
import sys
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import claude_client  # noqa: E402

THEME = ROOT / "themes" / "varsity-english"


class FakeMessages:
    def __init__(self, replies, reject_thinking=False):
        self.replies, self.calls, self.reject = list(replies), [], reject_thinking

    def _reply(self, kw):
        self.calls.append(kw)
        if self.reject and "thinking" in kw:
            raise RuntimeError("thinking: unsupported for this model")
        name, inp = self.replies.pop(0)
        return SimpleNamespace(stop_reason="tool_use", content=[
            SimpleNamespace(type="thinking"),
            SimpleNamespace(type="tool_use", name=name, input=inp),
        ])

    def create(self, **kw):
        kw["_streamed"] = False
        return self._reply(kw)

    def stream(self, **kw):
        kw["_streamed"] = True
        outer = self

        class S:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def get_final_message(self):
                return outer._reply(kw)
        return S()


def _fake(monkeypatch, replies, **kw):
    msgs = FakeMessages(replies, **kw)
    monkeypatch.setattr(claude_client, "_client", lambda: SimpleNamespace(messages=msgs))
    monkeypatch.setattr(claude_client, "MODEL", "claude-opus-5-5")
    return msgs


GOOD = {"look": {}, "frames": [
    {"id": "0.13", "mode": "anchor", "items": [{"t": "title", "lines": [{"text": "X"}]}]},
    {"id": "1.00", "mode": "fss", "items": [{"t": "htab", "text": "T"}, {"t": "bars", "bars": []}]},
    {"id": "2.00", "mode": "fss", "items": [{"t": "htab", "text": "T"}, {"t": "calc_table", "rows": []}]},
]}


def test_storyboard_call_streams_with_thinking_and_style_image(monkeypatch):
    msgs = _fake(monkeypatch, [("submit_storyboard", {"storyboard": "SB", "spec": GOOD})])
    out = claude_client.storyboard(THEME, "script", {"anchor": "right"})
    kw = msgs.calls[0]
    assert kw["_streamed"] and kw["max_tokens"] > 16384
    assert kw["thinking"] == {"type": "adaptive"}
    blocks = kw["messages"][0]["content"]
    assert blocks[0]["type"] == "image" and blocks[0]["cache_control"]["type"] == "ephemeral"
    assert out["spec"]["frames"]


def test_quality_retry_patches_only_failing_frame(monkeypatch):
    bad = {"look": {}, "frames": [dict(f) for f in GOOD["frames"]]}
    bad["frames"][1] = {"id": "1.00", "mode": "fss", "items": [{"t": "htab", "text": "only text"}]}
    fixed = GOOD["frames"][1]
    msgs = _fake(monkeypatch, [
        ("submit_storyboard", {"storyboard": "SB", "spec": bad}),
        ("submit_frame_fixes", {"fixes": [{"id": "1.00", "frame": fixed, "why": "add bars"}]}),
    ])
    out = claude_client.storyboard(THEME, "script", {})
    assert len(msgs.calls) == 2
    assert msgs.calls[1]["tools"][0]["name"] == "submit_frame_fixes"  # not a full regeneration
    ids = [f["id"] for f in out["spec"]["frames"]]
    assert ids == ["0.13", "1.00", "2.00"]
    assert any(it["t"] == "bars" for it in out["spec"]["frames"][1]["items"])


def test_thinking_falls_back_when_rejected(monkeypatch):
    msgs = _fake(monkeypatch, [("submit_storyboard", {"storyboard": "SB", "spec": GOOD})], reject_thinking=True)
    claude_client.storyboard(THEME, "script", {})
    assert "thinking" in msgs.calls[0] and "thinking" not in msgs.calls[1]


def test_thinking_off_switch(monkeypatch):
    monkeypatch.setenv("STUDIO_THINKING", "off")
    msgs = _fake(monkeypatch, [("submit_storyboard", {"storyboard": "SB", "spec": GOOD})])
    claude_client.storyboard(THEME, "script", {})
    assert "thinking" not in msgs.calls[0]

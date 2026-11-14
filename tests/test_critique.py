"""Render → look → fix loop, with Claude mocked. Needs Playwright Chromium (set CHROMIUM_PATH if needed)."""
import copy
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import claude_client  # noqa: E402

pytest.importorskip("playwright")


def test_merge_fixes_replaces_adds_and_sorts():
    spec = {"look": {}, "frames": [{"id": "0.13", "items": []}, {"id": "4.18", "items": []}]}
    out, changed = claude_client.merge_fixes(spec, {"fixes": [
        {"id": "4.18", "frame": {"items": [{"t": "htab", "text": "x"}]}},
        {"id": "1.12", "frame": {"id": "1.12", "items": []}},
    ]})
    assert changed == ["4.18", "1.12"]
    assert [f["id"] for f in out["frames"]] == ["0.13", "1.12", "4.18"]
    assert out["frames"][2]["items"][0]["text"] == "x"


def test_critique_loop_fixes_off_frame_asset(monkeypatch):
    import app

    spec = json.loads((app.THEMES / "varsity-english/scenes/example_spec.json").read_text())
    good = copy.deepcopy(next(f for f in spec["frames"] if f["id"] == "1.12"))
    bad = next(f for f in spec["frames"] if f["id"] == "1.12")
    for it in bad["items"]:
        if it["t"] == "asset":
            it["x"] = 1700  # pushes the building off the right edge / into the anchor
    calls = []

    def fake_fix(theme_dir, sp, storyboard, **kw):
        calls.append(kw)
        if kw["round_no"] == 1:
            assert kw["sheets"], "contact sheets must be sent"
            assert "1.12" in kw["warns"], "off-frame building must be flagged"
            assert kw["closeups"] and kw["closeups"][0][0] == "1.12"
            return {"fixes": [{"id": "1.12", "why": "moved building back on frame", "frame": good}]}
        return {"fixes": []}

    monkeypatch.setattr(claude_client, "fix_frames", fake_fix)
    p = {"theme": "varsity-english", "look": spec.get("look") or {}, "storyboard": ""}
    out, report = app._critique_spec(p, spec, "", "", None)
    assert calls, "Claude should have been asked to review"
    assert "1.12" in report["changed"]
    fixed = next(f for f in out["frames"] if f["id"] == "1.12")
    assert fixed == good
    assert report["warns_after"] <= report["warns_before"]


def test_critique_reverts_fix_that_adds_warns(monkeypatch):
    import app

    spec = json.loads((app.THEMES / "varsity-english/scenes/example_spec.json").read_text())
    orig = copy.deepcopy(next(f for f in spec["frames"] if f["id"] == "11.05"))
    worse = copy.deepcopy(orig)
    worse["items"].append({"t": "asset", "src": "setA/building_company_3d.png", "x": 1750, "h": 900})

    monkeypatch.setattr(
        claude_client, "fix_frames",
        lambda *a, **kw: {"fixes": [{"id": "11.05", "frame": worse}]} if kw["round_no"] == 1 else {"fixes": []},
    )
    p = {"theme": "varsity-english", "look": spec.get("look") or {}, "storyboard": ""}
    out, report = app._critique_spec(p, spec, "", "", None)
    assert "11.05" in report["reverted"]
    assert next(f for f in out["frames"] if f["id"] == "11.05") == orig
    assert "11.05" not in report["changed"]

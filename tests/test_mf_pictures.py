import claude_client as cc


def test_chart_pictures_are_flagged():
    spec = {"frames": [
        {"id": "01", "type": "scene", "hero": {"asset": "TODO:bar chart of Rs 100 growing to Rs 596 small cap"}},
        {"id": "02", "type": "scene", "hero": {"asset": "TODO:a bank vault with gold coins"}},
        {"id": "03", "type": "html", "html": "<div class='abs'>Rs 596</div>"},
    ]}
    iss = cc.mf_picture_issues(spec)
    assert len(iss) == 1 and iss[0].startswith('Frame "01"')
    assert cc.spec_quality_issues(spec, theme="varsity-mf-graphics") == iss


def test_fix_only_when_needed(monkeypatch):
    called = {}
    monkeypatch.setattr(cc, "fix_frames", lambda *a, **k: called.setdefault("ids", k.get("focus_ids")) or {"frames": []})
    out = {"spec": {"frames": [{"id": "02", "type": "scene", "hero": {"asset": "TODO:a vault"}}]}}
    cc.mf_fix_pictures(None, out)
    assert "ids" not in called
    out = {"spec": {"frames": [{"id": "01", "type": "scene", "hero": {"asset": "TODO:pie chart 50% telecom"}}]}}
    cc.mf_fix_pictures(None, out)
    assert called["ids"] == ["01"]

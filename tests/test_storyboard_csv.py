from storyboard_csv import parse_storyboard_lines, storyboard_csv_text


def test_parse_varsity_lines():
    sb = """SB <> Doc: ESOPs
Look: anchor right
~0:00 – Footage – hook to camera
~0:47 – OST – Title "What are ESOPs?" → 0.47
~2:05 – Screen capture – incometaxindia.gov.in
Totals: 3 graphics
"""
    rows = parse_storyboard_lines(sb)
    assert len(rows) == 3
    assert rows[0]["beat_type"] == "Footage"
    assert rows[0]["timestamp_seconds"] == 0
    assert rows[1]["frame_id"] == "0.47"
    assert rows[1]["approximate"] == "yes"
    assert rows[2]["beat_type"] == "Screen capture"


def test_csv_includes_spec_mode():
    sb = "~1:05 – FSS – Kite chart → 1.05\n"
    spec = {"frames": [{"id": "1.05", "mode": "fss"}]}
    csv = storyboard_csv_text(sb, spec, project_name="Ep1")
    assert "1.05" in csv
    assert "fss" in csv
    assert "Ep1" in csv

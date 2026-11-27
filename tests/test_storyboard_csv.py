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


def test_actions_column_names_item_ids():
    import csv, io
    sb = """~0:20 – FSS – "5 money decisions to automate", 5 points blurred, tick as per VO → 0.20
~1:58 – FSS – reuse 0.20, reveal 3. Automate savings for financial goals
~5:00 – FSS – SIP 2nd & Home loan EMI 3rd turn red → 5.00
~2:24 – FSS – twelve coins appear one by one → 2.24
~3:00 – Footage – anchor to camera
"""
    spec = {"frames": [{"id": "0.20", "items": [{"t": "heading", "text": "5 money decisions"}, {"t": "list", "items": [
        "Automate your bills", "Automate investing", "Automate savings for financial goals", "Automate insurance", "Automate emergency fund"]}]},
        {"id": "5.00", "items": [{"t": "calendar", "dates": [{"label": "Rent"}, {"label": "SIP"}, {"label": "Home loan EMI"}]}]}]}
    vo = {"0.20": "pehla automate your bills, teesra saving for your financial goals, chautha insurance"}
    rows = list(csv.DictReader(io.StringIO(storyboard_csv_text(sb, spec, vo_by_frame=vo))))
    assert rows[0]["actions"].startswith("blur point-1..point-5; tick point-1")
    assert rows[1]["frame_id"] == "0.20"                      # a bring-back row gets its frame id
    assert rows[1]["actions"] == 'show point-1, point-2; reveal point-3 @ "saving for your financial goals"'
    assert rows[2]["actions"] == "highlight date-2, date-3 red on VO"
    assert rows[3]["actions"] == "reveal coin-1..coin-12 each on VO"
    assert rows[4]["actions"] == ""
    own = list(csv.DictReader(io.StringIO(storyboard_csv_text("~0:05 – FSS – cards [actions: reveal card-1 on VO] → 0.05\n"))))
    assert own[0]["actions"] == "reveal card-1 on VO"          # actions written in the storyboard itself are kept as written


def test_item_ids_from_spec_match_the_kit_types():
    from item_ids import frame_items, noun_for
    assert frame_items({"items": [{"t": "heading", "text": "x"}, {"t": "recap", "items": ["a", "b", "c"]}]}) == {"noun": "point", "texts": ["a", "b", "c"]}
    assert noun_for("steps") == "step" and noun_for("coins") == "coin" and noun_for("checklist") == "point"

"""Export zips name each frame by the time it comes in when the page sends names (LA Studio places graphics by that time)."""
import exporter


def test_renamed_swaps_frame_id_for_its_name():
    names = {"tk1": "0.50_my_video_tk1", "0.13": "0.13_my_video_0.13"}
    assert exporter.renamed("png/tk1.png", names) == "png/0.50_my_video_tk1.png"
    assert exporter.renamed("png/tk1_overlay.png", names) == "png/0.50_my_video_tk1_overlay.png"
    assert exporter.renamed("html/tk1.html", names) == "html/0.50_my_video_tk1.html"
    assert exporter.renamed("html_overlay/0.13.html", names) == "html_overlay/0.13_my_video_0.13.html"
    assert exporter.renamed("png/tk2.png", names) == "png/tk2.png"
    assert exporter.renamed("README.txt", names) == "README.txt"
    assert exporter.renamed("png/tk1.png", None) == "png/tk1.png"


def test_export_names_cleans_what_the_page_sends():
    import app
    assert app._export_names("") is None
    assert app._export_names("not json") is None
    assert app._export_names('["a"]') is None
    got = app._export_names('{"tk1": "0.50_my video/../x", "f2": ""}')
    assert got == {"tk1": "0.50_my_video_.._x"}


def test_storyboard_csv_from_frames_when_there_is_no_storyboard_text():
    import storyboard_csv
    t = storyboard_csv.frames_csv_text([{"frame_id": "tk2", "t": 50, "mode": "osa", "text": "When can I sell?"},
                                        {"frame_id": "tk1", "t": 13.4, "mode": "fss", "text": "So your IPO\ncame through"},
                                        {"frame_id": ""}], project_name="IPO")
    rows = t.strip().split("\n")
    assert rows[0].startswith("project,line_no,timestamp,timestamp_seconds")
    assert rows[1].startswith("IPO,1,0.13,13.40,,FSS,So your IPO came through,tk1,yes,fss")
    assert rows[2].startswith("IPO,2,0.50,50.00,,OSA,When can I sell?,tk2")
    assert len(rows) == 3


def test_storyboard_csv_marks_worked_out_times_approximate():
    import storyboard_csv
    t = storyboard_csv.frames_csv_text([{"frame_id": "tk1", "t": 12.4, "approx": True, "mode": "osa", "text": "Hi"},
                                        {"frame_id": "tk2", "t": 30, "mode": "fss", "text": "Yo"}])
    rows = t.strip().split("\n")
    assert rows[1].split(",")[2:5] == ["0.12", "12.40", "yes"]
    assert rows[2].split(",")[2:5] == ["0.30", "30.00", ""]

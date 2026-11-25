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

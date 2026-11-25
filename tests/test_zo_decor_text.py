import importlib.util, pathlib

_p = pathlib.Path(__file__).resolve().parents[1] / "themes/zo-product-graphics/scripts/build.py"
_s = importlib.util.spec_from_file_location("zo_build_decor", _p)
b = importlib.util.module_from_spec(_s); _s.loader.exec_module(b)


def test_decor_sent_as_text_renders():
    # a frame from a storyboard PDF batch had decor as a JS object literal string → Export all failed
    f = {"id": "36", "mode": "ost", "plate": "m2_right", "decor": "{seed:1,dark:true,doodleAt:{left:30,top:40}}",
         "html": "<div class='abs' data-name='Heading'>Hi</div>"}
    assert "zoDecor(" in b.frame_html(f)
    assert b._decor_of({"decor": "false"}) is False
    assert b._decor_of({"decor": "nonsense"}) is True
    assert b._decor_of({"decor": {"seed": 2}}) == {"seed": 2}

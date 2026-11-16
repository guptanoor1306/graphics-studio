"""Varsity English people: the team's characters, one per person for the whole video, two women never a man."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "themes" / "varsity-english" / "scripts" / "cast.py"
_spec = importlib.util.spec_from_file_location("ve_cast_for_tests", _p)
cast = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cast)


def test_two_women_get_the_two_female_characters_across_the_video():
    frames = [
        {"id": "0.42", "items": [{"t": "person", "color": "#F2B233", "hair": "long"}]},          # unnamed "you"
        {"id": "1.45", "items": [{"t": "person", "name": "Priya"}, {"t": "person", "name": "Neha"}]},
        {"id": "4.25", "items": [{"t": "person", "name": "Neha", "h": 400}]},
        {"id": "5.00", "items": [{"t": "person", "name": "Rahul"}, {"t": "person", "name": "Mr Kapoor", "who": "c5"}]},
    ]
    c = cast.build_cast(frames)
    assert c["name:priya"] == "c3" and c["name:neha"] == "c7"          # named women first: never a man
    assert c["name:rahul"] == "c1" and c["name:mr kapoor"] == "c5"
    assert cast.character_for({"t": "person", "name": "Neha"}, c) == "c7"   # same character in every frame


def test_gender_hints():
    assert cast.gender_of({"name": "Mrs Sharma"}) == "f"
    assert cast.gender_of({"name": "Anjali"}) == "f"
    assert cast.gender_of({"bindi": True}) == "f"
    assert cast.gender_of({"name": "Rohan"}) == "m"
    assert cast.gender_of({"name": "Arjun", "gender": "f"}) == "f"


def test_characters_render_at_a_readable_size():
    from app import builder
    build = builder("varsity-english")
    f = {"id": "1.45", "mode": "anchor", "items": [{"t": "htab", "text": "Priya & Neha"},
                                                  {"t": "person", "name": "Priya", "gender": "f", "x": 200, "h": 315},
                                                  {"t": "person", "name": "Neha", "gender": "f", "x": 560}]}
    html = build.frame_html(f, {"anchor": "right"}, all_frames=[f])
    assert 'data-char="c3"' in html and 'data-char="c7"' in html
    assert "chars6/c3.png" in html

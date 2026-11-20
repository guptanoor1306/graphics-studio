import pytest
from claude_client import _frame_out


def test_wrapped():
    assert _frame_out({"frame": {"a": 1}}) == {"a": 1}


def test_string_and_fenced():
    assert _frame_out({"frame": '{"a": 1}'}) == {"a": 1}
    assert _frame_out({"frame": '```json\n{"a": 2}\n```'}) == {"a": 2}


def test_bad():
    with pytest.raises(ValueError):
        _frame_out({"frame": "not json"})
    with pytest.raises(ValueError):
        _frame_out({})

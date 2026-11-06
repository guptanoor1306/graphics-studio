from claude_client import episode_transcript_prompt_block


def test_transcript_block_segments():
    tr = {"segments": [{"start": 0, "end": 8.2, "text": "Hello everyone"}]}
    block = episode_transcript_prompt_block(tr)
    assert "0:00" in block
    assert "Hello everyone" in block
    assert "VO TRANSCRIPT" in block


def test_transcript_block_empty():
    assert episode_transcript_prompt_block(None) == ""
    assert episode_transcript_prompt_block({"segments": []}) == ""

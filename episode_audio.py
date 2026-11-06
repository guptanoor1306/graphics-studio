"""Episode VO audio upload + stored transcript (for storyboard timing)."""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
AUDIO_DIR = ROOT / "data" / "episode_audio"
TRANSCRIPT_DIR = ROOT / "data" / "episode_transcripts"
MAX_AUDIO_BYTES = 250 * 1024 * 1024  # raw upload; Whisper prep compresses/splits via ffmpeg
_ALLOWED_EXT = frozenset({".mp3", ".m4a", ".wav", ".mp4", ".mpeg", ".webm", ".ogg"})


def _meta_path(project_id: int) -> pathlib.Path:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    return AUDIO_DIR / f"{project_id}.meta.json"


def audio_path(project_id: int) -> pathlib.Path | None:
    meta = read_meta(project_id)
    if not meta or not meta.get("filename"):
        return None
    p = AUDIO_DIR / meta["filename"]
    return p if p.is_file() else None


def has_audio(project_id: int) -> bool:
    return audio_path(project_id) is not None


def read_meta(project_id: int) -> dict | None:
    p = _meta_path(project_id)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def transcript_path(project_id: int) -> pathlib.Path:
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    return TRANSCRIPT_DIR / f"{project_id}.json"


def has_transcript(project_id: int) -> bool:
    p = transcript_path(project_id)
    if not p.is_file():
        return False
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    return bool((data.get("segments") or []) or (data.get("text") or "").strip())


def read_transcript(project_id: int) -> dict | None:
    p = transcript_path(project_id)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def save_audio(project_id: int, raw: bytes, original_name: str) -> pathlib.Path:
    if len(raw) > MAX_AUDIO_BYTES:
        raise ValueError(f"Audio exceeds {MAX_AUDIO_BYTES // (1024 * 1024)}MB upload limit")
    if not raw:
        raise ValueError("Empty file")
    ext = pathlib.Path(original_name or "episode.mp3").suffix.lower()
    if ext not in _ALLOWED_EXT:
        raise ValueError(f"Unsupported audio type {ext or '(none)'} — use mp3, m4a, wav, or webm.")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.-]+", "_", pathlib.Path(original_name).stem)[:40] or "episode"
    filename = f"{project_id}_{safe}{ext}"
    dest = AUDIO_DIR / filename
    try:
        dest.write_bytes(raw)
        _meta_path(project_id).write_text(
            json.dumps({"filename": filename, "original_name": original_name or filename})
        )
    except OSError as e:
        raise OSError(
            f"Could not write audio to server storage ({e}). "
            "On Railway, mount a volume at /app/data so uploads survive redeploys."
        ) from e
    return dest


def save_transcript(project_id: int, data: dict) -> None:
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    transcript_path(project_id).write_text(json.dumps(data, ensure_ascii=False))


def delete_transcript(project_id: int) -> None:
    p = transcript_path(project_id)
    if p.is_file():
        p.unlink()

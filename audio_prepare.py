"""Compress / split audio so each Whisper API request stays under 25MB."""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile

WHISPER_MAX_BYTES = 24 * 1024 * 1024  # under OpenAI 25MB cap
SEGMENT_SECONDS = 600  # 10 min chunks when still too large after compression


def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def _run_ffmpeg(args: list[str]) -> None:
    exe = ffmpeg_path()
    if not exe:
        raise ValueError(
            "This audio file is too large for Whisper as-is. Install ffmpeg on the server "
            "(Docker: apt install ffmpeg; Mac: brew install ffmpeg), or upload a compressed mp3/m4a under 25MB."
        )
    try:
        subprocess.run([exe, *args], check=True, capture_output=True, timeout=3600)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode(errors="replace")[-400:]
        raise RuntimeError(f"ffmpeg failed: {err or e}") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("ffmpeg timed out while preparing audio") from e


def whisper_chunks(path: pathlib.Path) -> list[tuple[pathlib.Path, float]]:
    """Return (file, time_offset_seconds) pieces each ≤ WHISPER_MAX_BYTES."""
    if not path.is_file():
        raise FileNotFoundError("Audio file missing")
    size = path.stat().st_size
    if size <= WHISPER_MAX_BYTES:
        return [(path, 0.0)]

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="gs_whisper_"))
    mp3 = tmp / "episode.mp3"
    _run_ffmpeg(
        [
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "64k",
            "-y",
            str(mp3),
        ]
    )
    if mp3.stat().st_size <= WHISPER_MAX_BYTES:
        return [(mp3, 0.0)]

    pattern = tmp / "part_%03d.mp3"
    _run_ffmpeg(
        [
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(mp3),
            "-f",
            "segment",
            "-segment_time",
            str(SEGMENT_SECONDS),
            "-c",
            "copy",
            "-reset_timestamps",
            "1",
            "-y",
            str(pattern),
        ]
    )
    parts = sorted(tmp.glob("part_*.mp3"))
    if not parts:
        raise RuntimeError("Could not split audio for Whisper")
    out: list[tuple[pathlib.Path, float]] = []
    for i, p in enumerate(parts):
        if p.stat().st_size > WHISPER_MAX_BYTES:
            raise ValueError(
                f"Audio chunk still exceeds Whisper limit after compression ({p.name}). "
                "Try a shorter clip or lower-bitrate mp3."
            )
        out.append((p, float(i * SEGMENT_SECONDS)))
    return out

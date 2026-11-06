"""Transcribe episode audio (OpenAI Whisper API)."""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import urllib.error
import urllib.request

from audio_prepare import WHISPER_MAX_BYTES, whisper_chunks

_ROOT = pathlib.Path(__file__).resolve().parent


def _looks_like_placeholder(key: str) -> bool:
    k = (key or "").strip().lower()
    if not k or k in {"sk-...", "changeme", "xxx"}:
        return True
    if "your_" in k or "key_here" in k or "paste" in k or "example" in k:
        return True
    return not k.startswith("sk-")


def openai_api_key() -> str:
    """OPENAI_API_KEY from env; if env is a placeholder, prefer graphics-studio/.env."""
    env_k = (os.environ.get("OPENAI_API_KEY") or "").strip()
    file_k = ""
    env_path = _ROOT / ".env"
    if env_path.is_file():
        try:
            from dotenv import dotenv_values

            file_k = (dotenv_values(env_path).get("OPENAI_API_KEY") or "").strip()
        except Exception:
            pass
    if _looks_like_placeholder(env_k) and file_k and not _looks_like_placeholder(file_k):
        return file_k
    return env_k or file_k


def _transcribe_one(path: pathlib.Path, api_key: str) -> dict:
    data = path.read_bytes()
    if len(data) > WHISPER_MAX_BYTES + 1024 * 1024:
        raise ValueError("Audio chunk exceeds 25MB Whisper limit")

    boundary = "----GraphicsStudioBoundary7MA4YWxk"
    body = bytearray()
    for name, val in (
        ("model", "whisper-1"),
        ("response_format", "verbose_json"),
    ):
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(f"{val}\r\n".encode())
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'.encode()
    )
    body.extend(b"Content-Type: application/octet-stream\r\n\r\n")
    body.extend(data)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        if e.code == 401:
            raise RuntimeError(
                "OpenAI rejected the API key (401). Check OPENAI_API_KEY in graphics-studio/.env "
                "(must start with sk-). If you fixed .env, restart uvicorn. "
                "Also run: echo $OPENAI_API_KEY — a placeholder in your shell overrides .env."
            ) from e
        detail = raw[:500]
        raise RuntimeError(f"Transcription failed ({e.code}): {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Transcription request failed: {e}") from e

    segments = []
    for s in payload.get("segments") or []:
        if not isinstance(s, dict):
            continue
        segments.append(
            {
                "start": float(s.get("start") or 0),
                "end": float(s.get("end") or 0),
                "text": (s.get("text") or "").strip(),
            }
        )
    return {
        "text": (payload.get("text") or "").strip(),
        "segments": segments,
        "language": payload.get("language") or "",
    }


def transcribe_file(path: pathlib.Path) -> dict:
    """Return {text, segments: [{start, end, text}], language?}."""
    api_key = openai_api_key()
    if not api_key:
        raise ValueError(
            "Set OPENAI_API_KEY in graphics-studio/.env to transcribe episode audio (Whisper API)."
        )
    if _looks_like_placeholder(api_key):
        raise ValueError(
            "OPENAI_API_KEY looks like a placeholder, not a real key. "
            "Put your sk-… key in graphics-studio/.env and restart the app."
        )
    chunks = whisper_chunks(path)
    tmp_dirs = {c.parent for c, _ in chunks if c.resolve() != path.resolve()}
    try:
        merged_text: list[str] = []
        merged_segments: list[dict] = []
        language = ""
        for chunk_path, offset in chunks:
            part = _transcribe_one(chunk_path, api_key)
            if part.get("language"):
                language = part["language"]
            if part.get("text"):
                merged_text.append(part["text"])
            for seg in part.get("segments") or []:
                merged_segments.append(
                    {
                        "start": float(seg["start"]) + offset,
                        "end": float(seg["end"]) + offset,
                        "text": seg.get("text") or "",
                    }
                )
        return {
            "text": " ".join(merged_text).strip(),
            "segments": merged_segments,
            "language": language,
        }
    finally:
        for d in tmp_dirs:
            shutil.rmtree(d, ignore_errors=True)

"""Fill "TODO:<description>" asset placeholders with real images in the theme's style.

Kits mark art they don't have as `"TODO:<what>"` (the MF renderer draws an "ASSET NEEDED" box). This module
replaces each one with a generated file at `themes/<kit>/assets/gen/<slug>.png`, so preview, the render
review and the export zip treat it exactly like built-in kit art.

  1. Library first: the same description in the same kit is generated once and reused (Postgres/SQLite
     table `generated_assets`; files are restored to disk on startup because Railway wipes the disk).
  2. Gemini (GEMINI_API_KEY): the kit's style image + a few of its illustrations go in as style references;
     the object comes back on a flat key colour, which is cut out to a transparent PNG.
  3. Claude fallback (no Gemini key, or Gemini failed): a flat SVG in the kit's line style.

Env: STUDIO_ASSET_GEN=0 disables it; STUDIO_GEMINI_IMAGE_MODEL picks the model; STUDIO_ASSET_GEN_MAX caps
new images per run (default 24).
"""
from __future__ import annotations

import base64
import concurrent.futures as cf
import hashlib
import io
import json
import os
import pathlib
import re
import time
from typing import Callable

ROOT = pathlib.Path(__file__).parent
THEMES = ROOT / "themes"
GEN_DIR = "gen"
TODO_RE = re.compile(r"^\s*TODO:\s*(.+?)\s*$", re.S)
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_FALLBACK_MODELS = ("gemini-3-pro-image-preview", "gemini-2.5-flash-image")

_SCHEMA = """CREATE TABLE IF NOT EXISTS generated_assets (
    key TEXT PRIMARY KEY, theme TEXT, description TEXT, filename TEXT, mime TEXT,
    data TEXT, source TEXT, created DOUBLE PRECISION)"""


def enabled() -> bool:
    return os.environ.get("STUDIO_ASSET_GEN", "1") != "0"


def gemini_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()


# ------------------------------------------------------------------ library (DB + disk)
def _db():
    from db_store import connect
    return connect()


def _ensure_table(c) -> None:
    c.execute(_SCHEMA)
    c.commit()


def _key(theme: str, desc: str) -> str:
    norm = re.sub(r"\s+", " ", desc.strip().lower())
    return f"{theme}:{hashlib.sha1(norm.encode()).hexdigest()[:12]}"


def _slug(desc: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", desc.lower()).strip("-")
    return s[:40].strip("-") or "asset"


def _write_file(theme: str, filename: str, raw: bytes) -> None:
    p = THEMES / theme / "assets" / GEN_DIR / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or p.stat().st_size != len(raw):
        p.write_bytes(raw)


def lookup(theme: str, desc: str) -> str | None:
    """Relative asset path (gen/<file>) if this description was made before; restores the file if needed."""
    try:
        with _db() as c:
            _ensure_table(c)
            row = c.execute("select filename, data from generated_assets where key=?", (_key(theme, desc),)).fetchone()
    except Exception:
        return None
    if not row:
        return None
    _write_file(theme, row["filename"], base64.b64decode(row["data"]))
    return f"{GEN_DIR}/{row['filename']}"


def store(theme: str, desc: str, raw: bytes, ext: str, source: str) -> str:
    key = _key(theme, desc)
    filename = f"{_slug(desc)}-{key.split(':')[1][:8]}.{ext}"
    _write_file(theme, filename, raw)
    mime = "image/svg+xml" if ext == "svg" else "image/png"
    try:
        with _db() as c:
            _ensure_table(c)
            c.execute("delete from generated_assets where key=?", (key,))
            c.execute(
                "insert into generated_assets(key,theme,description,filename,mime,data,source,created) "
                "values(?,?,?,?,?,?,?,?)",
                (key, theme, desc, filename, mime, base64.b64encode(raw).decode(), source, time.time()),
            )
            c.commit()
    except Exception as e:  # file on disk still works until the next deploy
        print(f"asset_gen: could not save {filename} to the database ({e})")
    return f"{GEN_DIR}/{filename}"


def restore_all() -> int:
    """Write every stored asset back to disk (call on startup)."""
    try:
        with _db() as c:
            _ensure_table(c)
            rows = c.execute("select theme, filename, data from generated_assets").fetchall()
    except Exception as e:
        print(f"asset_gen: restore skipped ({e})")
        return 0
    n = 0
    for r in rows:
        if (THEMES / r["theme"]).is_dir():
            _write_file(r["theme"], r["filename"], base64.b64decode(r["data"]))
            n += 1
    return n


# ------------------------------------------------------------------ Gemini
def _style_refs(theme: str, limit: int = 4) -> list[tuple[str, bytes]]:
    """style_at_a_glance + the kit's largest illustrations (not backgrounds, anchors, decor or UI)."""
    d = THEMES / theme
    refs: list[tuple[str, bytes]] = []
    s = d / "references" / "style_at_a_glance.jpg"
    if s.is_file():
        refs.append(("image/jpeg", s.read_bytes()))
    skip = ("bg", "anchor", "decor", "ui", "fonts", GEN_DIR, "plates", "uploads")
    cands = [
        p for p in (d / "assets").rglob("*.png")
        if not any(part in skip for part in p.relative_to(d / "assets").parts[:-1])
        and "logo" not in p.name and "map" not in p.name
    ] if (d / "assets").is_dir() else []
    cands.sort(key=lambda p: p.stat().st_size, reverse=True)
    for p in cands[: max(0, limit - len(refs))]:
        refs.append(("image/png", _shrink(p.read_bytes(), 768)))
    return refs


def _shrink(raw: bytes, side: int) -> bytes:
    from PIL import Image

    im = Image.open(io.BytesIO(raw))
    if max(im.size) <= side:
        return raw
    im.thumbnail((side, side))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def _key_color(desc: str) -> tuple[str, tuple[int, int, int]]:
    if re.search(r"green|leaf|plant|tree|grass|emerald|money plant", desc, re.I):
        return "pure magenta #FF00FF", (255, 0, 255)
    return "pure green #00FF00", (0, 255, 0)


def _http_post(url: str, body: dict, headers: dict, timeout: float) -> tuple[int, str]:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def gemini_image(theme: str, desc: str, *, timeout: float = 120.0) -> bytes:
    """Generate one isolated object in the kit's style; returns a transparent, cropped PNG."""
    key = gemini_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    color_name, rgb = _key_color(desc)
    prompt = (
        f"Create ONE isolated object for a YouTube explainer graphic: {desc}.\n"
        "Match the illustration style of the reference images exactly: same rendering, texture and grain, "
        "outline weight, colour palette, lighting and three-quarter angle. The references only show the style; "
        "do not copy their objects.\n"
        "Show the whole object, centred, filling about 80% of the canvas. Nothing else: no people, no hands, "
        "no floor, no cast shadow, no scenery. No text, labels or logos unless the description asks for them.\n"
        f"Background: perfectly flat {color_name} across the whole canvas, with no gradient or texture, and do "
        "not use that colour anywhere on the object."
    )
    parts: list[dict] = [{"text": prompt}]
    for mime, raw in _style_refs(theme):
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(raw).decode()}})
    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "1:1"}},
    }
    models = [m for m in [os.environ.get("STUDIO_GEMINI_IMAGE_MODEL", "").strip()] if m] + list(GEMINI_FALLBACK_MODELS)
    last = ""
    for model in dict.fromkeys(models):
        status, text = _http_post(
            GEMINI_URL.format(model=model), body,
            {"x-goog-api-key": key, "content-type": "application/json"}, timeout,
        )
        if status in (400, 404) and "model" in text.lower() and "not" in text.lower():
            last = f"{model}: {text[:200]}"
            continue  # model name not available on this key → try the next one
        if status != 200:
            raise RuntimeError(f"Gemini {model} HTTP {status}: {text[:300]}")
        for cand in json.loads(text).get("candidates") or []:
            for part in (cand.get("content") or {}).get("parts") or []:
                data = (part.get("inlineData") or part.get("inline_data") or {}).get("data")
                if data:
                    return cut_out(base64.b64decode(data), rgb)
        raise RuntimeError(f"Gemini {model} returned no image")
    raise RuntimeError(f"no Gemini image model available ({last})")


def cut_out(raw: bytes, key_rgb: tuple[int, int, int] = (0, 255, 0), max_side: int = 1024) -> bytes:
    """Remove a flat key-colour background (sampled from the corners), despill edges, crop, return PNG."""
    import numpy as np
    from PIL import Image, ImageFilter

    im = Image.open(io.BytesIO(raw)).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    h, w, _ = a.shape
    k = max(4, min(h, w) // 40)
    corners = np.concatenate([a[:k, :k].reshape(-1, 3), a[:k, -k:].reshape(-1, 3),
                              a[-k:, :k].reshape(-1, 3), a[-k:, -k:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    if np.abs(bg - np.array(key_rgb)).max() > 90:  # model ignored the key colour: fall back to the corners
        key_rgb = tuple(int(x) for x in bg)
    dist = np.sqrt(((a - np.array(key_rgb)) ** 2).sum(axis=2))
    alpha = np.clip((dist - 60) / 80, 0, 1)  # soft edge between ~60 and ~140 away from the key colour
    rgb = a.copy()
    # despill: pull the key channel(s) down on semi-transparent / edge pixels
    if key_rgb == (0, 255, 0):
        rgb[..., 1] = np.minimum(rgb[..., 1], np.maximum(rgb[..., 0], rgb[..., 2]) + 10)
    elif key_rgb == (255, 0, 255):
        g = rgb[..., 1] + 10
        rgb[..., 0] = np.minimum(rgb[..., 0], g + 40)
        rgb[..., 2] = np.minimum(rgb[..., 2], g + 40)
    edge = alpha < 1
    a2 = np.where(edge[..., None], rgb, a)
    out = Image.fromarray(np.dstack([a2.clip(0, 255), (alpha * 255)]).astype("uint8"), "RGBA")
    out.putalpha(out.getchannel("A").filter(ImageFilter.GaussianBlur(0.6)))
    bbox = out.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if not bbox:
        raise RuntimeError("cut-out left nothing (object matched the background colour)")
    pad = 8
    out = out.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(w, bbox[2] + pad), min(h, bbox[3] + pad)))
    out.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    out.save(buf, "PNG", optimize=True)
    return buf.getvalue()


# ------------------------------------------------------------------ Claude SVG fallback
_SVG_BAD = re.compile(r"<\s*(script|foreignObject|iframe|object|embed)\b.*?(</\s*\1\s*>|/>)", re.I | re.S)


def sanitize_svg(svg: str) -> str:
    m = re.search(r"<svg\b.*</svg>", svg, re.S | re.I)
    if not m:
        raise ValueError("no <svg> element")
    s = _SVG_BAD.sub("", m.group(0))
    s = re.sub(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*')", "", s, flags=re.I)
    s = re.sub(r"(href\s*=\s*[\"'])\s*(javascript:|https?:)[^\"']*", r"\1#", s, flags=re.I)
    if "xmlns=" not in s[:200]:
        s = s.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return s


def claude_svg(theme: str, desc: str) -> bytes:
    import claude_client

    return sanitize_svg(claude_client.draw_asset_svg(THEMES / theme, desc)).encode()


# ------------------------------------------------------------------ spec walk
def todo_descriptions(spec: dict) -> list[str]:
    found: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            m = TODO_RE.match(o)
            if m and m.group(1) not in found:
                found.append(m.group(1))
    walk((spec or {}).get("frames") or [])
    return found


def _replace(o, mapping: dict[str, str]):
    if isinstance(o, dict):
        return {k: _replace(v, mapping) for k, v in o.items()}
    if isinstance(o, list):
        return [_replace(v, mapping) for v in o]
    if isinstance(o, str):
        m = TODO_RE.match(o)
        if m and m.group(1) in mapping:
            return mapping[m.group(1)]
    return o


def make_one(theme: str, desc: str) -> tuple[str, str]:
    """(path, source) for one description: library → Gemini → Claude SVG. Raises if all fail."""
    hit = lookup(theme, desc)
    if hit:
        return hit, "library"
    errors = []
    if gemini_key():
        try:
            return store(theme, desc, gemini_image(theme, desc), "png", "gemini"), "gemini"
        except Exception as e:
            errors.append(f"gemini: {e}")
    try:
        return store(theme, desc, claude_svg(theme, desc), "svg", "claude-svg"), "claude-svg"
    except Exception as e:
        errors.append(f"claude: {e}")
    raise RuntimeError("; ".join(errors))


def fill_spec(theme: str, spec: dict, log: Callable[[str], None] | None = None) -> tuple[dict, dict]:
    """Replace every TODO asset in spec. Returns (spec, report). Never raises; failures keep the placeholder."""
    report = {"filled": {}, "failed": {}, "skipped": []}
    if not enabled() or not spec:
        return spec, report
    descs = todo_descriptions(spec)
    if not descs:
        return spec, report
    cap = int(os.environ.get("STUDIO_ASSET_GEN_MAX", "24"))
    todo, report["skipped"] = descs[:cap], descs[cap:]
    say = log or (lambda m: None)
    mapping: dict[str, str] = {}
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get("STUDIO_ASSET_GEN_WORKERS", "4"))) as ex:
        futs = {ex.submit(make_one, theme, d): d for d in todo}
        for f in cf.as_completed(futs):
            d = futs[f]
            try:
                path, source = f.result()
                mapping[d] = path
                report["filled"][d] = {"path": path, "source": source}
            except Exception as e:
                report["failed"][d] = str(e)[:300]
                say(f"asset_gen: '{d}' failed ({e})")
    say(f"asset_gen: filled {len(mapping)}/{len(descs)} placeholder(s)")
    return {**spec, "frames": _replace(spec.get("frames") or [], mapping)}, report

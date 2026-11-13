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


STYLE_VERSION = "2"  # bump when generation changes, so images made the old way are not reused


def _key(theme: str, desc: str) -> str:
    norm = re.sub(r"\s+", " ", desc.strip().lower())
    return f"{theme}:{hashlib.sha1((STYLE_VERSION + norm).encode()).hexdigest()[:12]}"


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
REF_BG = (243, 239, 230)  # the kits' cream paper; references are shown on it, never as transparent PNGs


def _style_text(theme: str) -> str:
    """How this kit's illustrations look, in words: references/asset_style.md, else the style guide's
    lines about illustrations."""
    d = THEMES / theme / "references"
    f = d / "asset_style.md"
    if f.is_file():
        return f.read_text().strip()
    guide = d / "style_guide.md"
    if guide.is_file():
        lines = [ln.strip("-* ").strip() for ln in guide.read_text().splitlines()
                 if re.search(r"illustrat|asset|texture|grain|outline|3d|flat|shading", ln, re.I)]
        if lines:
            return "\n".join(lines[:8])
    return "Match the reference illustrations exactly."


def _ref_paths(theme: str, limit: int = 5) -> list[pathlib.Path]:
    d = THEMES / theme / "assets"
    if not d.is_dir():
        return []
    skip = ("bg", "anchor", "decor", "ui", "fonts", GEN_DIR, "plates", "uploads")
    cands = [p for p in d.rglob("*.png")
             if not any(part in skip for part in p.relative_to(d).parts[:-1])
             and not re.search(r"logo|map|legend|plate|cutout", p.name)]
    cands.sort(key=lambda p: p.stat().st_size, reverse=True)
    return cands[:limit]


def _on_cream(raw: bytes, side: int = 640) -> bytes:
    """Cut-out PNG composited on the kit paper colour (transparent pixels read as black to image models)."""
    from PIL import Image

    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    if im.getbbox():
        im = im.crop(im.getchannel("A").getbbox() or im.getbbox())
    scale = (side - 40) / max(im.size)  # scale up small art too, so its texture is visible
    im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    bg = Image.new("RGB", (side, side), REF_BG)
    bg.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    buf = io.BytesIO()
    bg.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def _style_refs(theme: str) -> list[tuple[str, bytes]]:
    """The kit's own object illustrations on cream; the full-frame style sheet only if the kit has none."""
    refs = [("image/jpeg", _on_cream(p.read_bytes())) for p in _ref_paths(theme)]
    if not refs:
        s = THEMES / theme / "references" / "style_at_a_glance.jpg"
        if s.is_file():
            refs.append(("image/jpeg", _shrink(s.read_bytes(), 1280)))
    return refs


def _shrink(raw: bytes, side: int) -> bytes:
    from PIL import Image

    im = Image.open(io.BytesIO(raw))
    if max(im.size) <= side:
        return raw
    im.thumbnail((side, side))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=88)
    return buf.getvalue()


def _key_color(desc: str) -> tuple[str, tuple[int, int, int]]:
    """Magenta by default (finance objects are green notes, gold, silver, paper); green for pink/purple things."""
    if re.search(r"pink|magenta|purple|violet|rose|lavender|fuchsia", desc, re.I):
        return "pure green #00FF00", (0, 255, 0)
    return "pure magenta #FF00FF", (255, 0, 255)


def _http_post(url: str, body: dict, headers: dict, timeout: float) -> tuple[int, str]:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def gemini_image(theme: str, desc: str, feedback: str = "", *, timeout: float = 150.0) -> bytes:
    """Generate one isolated object in the kit's style; returns a transparent, cropped PNG."""
    key = gemini_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    color_name, rgb = _key_color(desc)
    refs = _style_refs(theme)
    prompt = (
        f"Draw ONE object for a YouTube explainer graphic: {desc}.\n\n"
        f"The {len(refs)} attached images are illustrations from this channel. Draw the new object so it looks "
        "like it came from the same illustrator and the same print run: same rendering technique, texture, "
        "grain, colour palette, level of detail, lighting and viewing angle. They show the style only; do not "
        "copy their objects.\n\n"
        f"House style for illustrations:\n{_style_text(theme)}\n\n"
        "Never: glossy or shiny surfaces, specular highlights, reflections, chrome, 3D render / CGI look, "
        "photorealism, bevels, lens blur, emoji or stock-icon look.\n"
        "Composition: the whole object, centred, about 75% of the canvas. Nothing else in the picture: no "
        "people, hands, floor, ground, podium, pedestal, platform, cast shadow or scenery. No text unless the "
        "description asks for it; any text that is asked for must be spelled exactly.\n"
        f"Background: perfectly flat {color_name} edge to edge, no gradient, no texture, no grain on the "
        "background. Do not use that colour anywhere on the object."
    )
    if feedback:
        prompt += f"\n\nA previous attempt was rejected by the art director: {feedback}\nFix exactly that."
    parts: list[dict] = [{"text": prompt}]
    for mime, raw in refs:
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


def cut_out(raw: bytes, key_rgb: tuple[int, int, int] = (255, 0, 255), max_side: int = 1024) -> bytes:
    """Remove the key-colour background by hue (any shade of it, not just the exact colour): everything
    connected to the border plus large enclosed pockets. Desaturates the fringe, crops, returns RGBA PNG."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter

    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    hsv = np.asarray(im.convert("HSV")).astype(np.int16)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    k = max(4, min(h, w) // 40)
    corner = np.concatenate([hsv[:k, :k].reshape(-1, 3), hsv[:k, -k:].reshape(-1, 3),
                             hsv[-k:, :k].reshape(-1, 3), hsv[-k:, -k:].reshape(-1, 3)])
    key_h = int(np.asarray(Image.new("RGB", (1, 1), key_rgb).convert("HSV"))[0, 0, 0])
    c_h, c_s = int(np.median(corner[:, 0])), int(np.median(corner[:, 1]))
    if c_s > 100:  # trust the actual background hue if it's saturated (model drifted from the exact key)
        key_h = c_h
    dh = np.abs(H - key_h)
    dh = np.minimum(dh, 256 - dh)
    keyish = (dh < 24) & (S > 90) & (V > 60)

    m = Image.fromarray((keyish * 255).astype("uint8"), "L")
    draw = ImageDraw.Draw(m)
    arr = np.asarray(m)
    for x, y in [(x, 0) for x in range(0, w, 8)] + [(x, h - 1) for x in range(0, w, 8)] + \
                [(0, y) for y in range(0, h, 8)] + [(w - 1, y) for y in range(0, h, 8)]:
        if m.getpixel((x, y)) == 255:
            ImageDraw.floodfill(m, (x, y), 128)
    # enclosed pockets of key colour (gaps between parts) larger than 0.2% of the image
    arr = np.array(m)
    for _ in range(200):
        left = np.argwhere(arr == 255)
        if not len(left):
            break
        y, x = left[0]
        ImageDraw.floodfill(m, (int(x), int(y)), 64)
        arr2 = np.array(m)
        region = (arr2 == 64)
        arr2[region] = 128 if region.sum() > 0.002 * w * h else 0
        m = Image.fromarray(arr2, "L")
        arr = arr2
    bg = (np.asarray(m) == 128)
    soft = np.asarray(Image.fromarray((bg * 255).astype("uint8"), "L").filter(ImageFilter.GaussianBlur(1.2)))
    alpha = np.where(bg, 0, 255 - soft).astype(np.uint8)
    fringe = (alpha < 250) & (alpha > 0) | ((dh < 30) & (S > 60) & ~bg)
    hsv2 = hsv.copy()
    hsv2[..., 1] = np.where(fringe, hsv2[..., 1] // 4, hsv2[..., 1])
    rgb = np.asarray(Image.fromarray(hsv2.astype("uint8"), "HSV").convert("RGB"))
    out = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")
    bbox = out.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if not bbox:
        raise RuntimeError("cut-out left nothing (object matched the background colour)")
    pad = 8
    out = out.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(w, bbox[2] + pad), min(h, bbox[3] + pad)))
    out.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    out.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def leftover_key(png: bytes) -> float:
    """Share of visible pixels that are still strongly magenta/green (a failed cut-out)."""
    import numpy as np
    from PIL import Image

    im = Image.open(io.BytesIO(png)).convert("RGBA")
    a = np.asarray(im)
    vis = a[..., 3] > 128
    if not vis.any():
        return 1.0
    hsv = np.asarray(im.convert("RGB").convert("HSV")).astype(np.int16)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mag = (np.minimum(np.abs(H - 213), 256 - np.abs(H - 213)) < 16) & (S > 170) & (V > 150)
    grn = (np.abs(H - 85) < 14) & (S > 200) & (V > 200)
    return float(((mag | grn) & vis).sum() / vis.sum())


def review(theme: str, desc: str, png: bytes) -> dict:
    """Claude as art director: does the candidate match the kit's illustrations? {"ok", "problems"}."""
    import claude_client

    if leftover_key(png) > 0.03:
        return {"ok": False, "problems": "background colour left on the object (a coloured patch or base); "
                "draw the object alone with nothing under it"}
    refs = [_on_cream(p.read_bytes(), 480) for p in _ref_paths(theme, 4)]
    return claude_client.review_asset(THEMES / theme, desc, _on_cream(png, 640), refs, _style_text(theme))


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




def _qa_on() -> bool:
    return os.environ.get("STUDIO_ASSET_QA", "1") != "0"


def make_one(theme: str, desc: str, force: bool = False) -> tuple[str, str, str]:
    """(path, source, note) for one description: library → Gemini (+ Claude style check, one retry)
    → Claude SVG. Raises if all fail."""
    if not force:
        hit = lookup(theme, desc)
        if hit:
            return hit, "library", ""
    errors = []
    if gemini_key():
        try:
            feedback, png, note = "", None, ""
            for attempt in range(int(os.environ.get("STUDIO_ASSET_ATTEMPTS", "2"))):
                png = gemini_image(theme, desc, feedback)
                if not _qa_on():
                    break
                try:
                    verdict = review(theme, desc, png)
                except Exception as e:  # style check unavailable: keep the image
                    note = f"style check skipped ({str(e)[:80]})"
                    break
                if verdict.get("ok"):
                    note = ""
                    break
                feedback = verdict.get("problems") or "does not match the reference style"
                note = f"style check: {feedback}"
            return store(theme, desc, png, "png", "gemini"), "gemini", note
        except Exception as e:
            errors.append(f"gemini: {e}")
    try:
        return store(theme, desc, claude_svg(theme, desc), "svg", "claude-svg"), "claude-svg", ""
    except Exception as e:
        errors.append(f"claude: {e}")
    raise RuntimeError("; ".join(errors))


def generated_paths(spec: dict) -> list[str]:
    out: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and o.startswith(f"{GEN_DIR}/") and o not in out:
            out.append(o)
    walk((spec or {}).get("frames") or [])
    return out


def _desc_for(theme: str, path: str) -> str | None:
    try:
        with _db() as c:
            _ensure_table(c)
            row = c.execute("select description from generated_assets where theme=? and filename=?",
                            (theme, path.split("/", 1)[1])).fetchone()
        return row.get("description") if row else None
    except Exception:
        return None


def _replace_values(o, by_desc: dict[str, str], by_value: dict[str, str]):
    if isinstance(o, dict):
        return {k: _replace_values(v, by_desc, by_value) for k, v in o.items()}
    if isinstance(o, list):
        return [_replace_values(v, by_desc, by_value) for v in o]
    if isinstance(o, str):
        if o in by_value:
            return by_value[o]
        m = TODO_RE.match(o)
        if m and m.group(1) in by_desc:
            return by_desc[m.group(1)]
    return o


def fill_spec(theme: str, spec: dict, log: Callable[[str], None] | None = None,
              redo: bool = False) -> tuple[dict, dict]:
    """Replace every TODO asset in spec (redo=True also remakes images generated earlier).
    Returns (spec, report). Never raises; failures keep what was there."""
    report = {"filled": {}, "failed": {}, "skipped": []}
    if not enabled() or not spec:
        return spec, report
    jobs: list[tuple[str, bool, str | None]] = [(d, False, None) for d in todo_descriptions(spec)]
    if redo:
        for path in generated_paths(spec):
            d = _desc_for(theme, path)
            if d:
                jobs.append((d, True, path))
    if not jobs:
        return spec, report
    cap = int(os.environ.get("STUDIO_ASSET_GEN_MAX", "24"))
    report["skipped"] = [d for d, _, _ in jobs[cap:]]
    jobs = jobs[:cap]
    say = log or (lambda m: None)
    by_desc: dict[str, str] = {}
    by_value: dict[str, str] = {}
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get("STUDIO_ASSET_GEN_WORKERS", "4"))) as ex:
        futs = {ex.submit(make_one, theme, d, force): (d, old) for d, force, old in jobs}
        for f in cf.as_completed(futs):
            d, old = futs[f]
            try:
                path, source, note = f.result()
                (by_value.__setitem__(old, path) if old else by_desc.__setitem__(d, path))
                report["filled"][d] = {"path": path, "source": source, **({"note": note} if note else {})}
            except Exception as e:
                report["failed"][d] = str(e)[:300]
                say(f"asset_gen: '{d}' failed ({e})")
    say(f"asset_gen: filled {len(report['filled'])}/{len(jobs)}")
    return {**spec, "frames": _replace_values(spec.get("frames") or [], by_desc, by_value)}, report

"""Zero1 Hindi plates: turn every `gen:<key>` in a spec into a real image, the way the kit's gen_images.py does.

The kit (themes/zero1-hindi-graphics) never draws a stand-in: each plate is a photographed-miniature look that
only an image model can make. So, per key:
  1. Library: the same prompt + references made before is reused (asset_gen's generated_assets table, restored
     to disk on startup).
  2. Image model through the kit's own script: build_request() adds the world/figure/Arjun bible and the house
     reference plates (+ the Arjun cut-out when he is in the shot). Gemini (GEMINI_API_KEY / GOOGLE_API_KEY)
     first, then OpenAI (OPENAI_API_KEY).
  3. Nothing else: without a key the frame keeps its labelled dashed placeholder.

The file lands at themes/zero1-hindi-graphics/assets/gen/<file> and spec["gen"][key]["file"] = "gen/<file>",
which the kit's studio adapter (build.frame_html) resolves.
"""
from __future__ import annotations

import concurrent.futures as cf
import importlib.util
import io
import json
import os
import pathlib
import re
import sys
from typing import Callable

import asset_gen

THEME = "zero1-hindi-graphics"
KIT = asset_gen.THEMES / THEME
GEN_RE = re.compile(r'"gen:([A-Za-z0-9_.-]+)"')
_gi = None


def is_theme(theme: str) -> bool:
    return theme == THEME


def _gen_images():
    """The kit's gen_images.py (it imports the kit's build.py as `build`)."""
    global _gi
    if _gi is None:
        scripts = str(KIT / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        spec = importlib.util.spec_from_file_location("z1h_gen_images", KIT / "scripts" / "gen_images.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _gi = m
    return _gi


def used_keys(spec: dict) -> list[str]:
    return sorted(set(GEN_RE.findall(json.dumps((spec or {}).get("frames") or [], ensure_ascii=False))))


def missing_prompts(spec: dict) -> list[str]:
    gen = (spec or {}).get("gen") or {}
    return [k for k in used_keys(spec) if not (isinstance(gen.get(k), dict) and gen[k].get("prompt"))]


def _have(entry: dict) -> bool:
    f = (entry or {}).get("file")
    return bool(f) and (KIT / "assets" / f).is_file()


def pending(spec: dict) -> list[str]:
    gen = (spec or {}).get("gen") or {}
    return [k for k in used_keys(spec) if isinstance(gen.get(k), dict) and gen[k].get("prompt") and not _have(gen[k])]


def _desc(req: dict) -> str:
    """Library key: the full prompt plus which references went in, so a changed prompt makes a new image."""
    refs = ",".join((f"{pathlib.Path(r).parent.name}/" if "pdf_refs" in str(r) else "") + pathlib.Path(r).name
                    for r in req["refs"])
    return f"{req['prompt']} || refs={refs} || aspect={req['aspect']} || cutout={req['cutout']}"


def _provider():
    gi = _gen_images()
    if not os.environ.get("IMG_MODEL") and os.environ.get("STUDIO_GEMINI_IMAGE_MODEL"):
        os.environ["IMG_MODEL"] = os.environ["STUDIO_GEMINI_IMAGE_MODEL"]
    return gi.pick_provider(None)


def available() -> bool:
    return asset_gen.enabled() and _provider()[1] is not None


def _postprocess(raw: bytes, req: dict) -> bytes:
    from PIL import Image
    gi = _gen_images()
    im = Image.open(io.BytesIO(raw))
    if req["cutout"]:
        im = gi.remove_white(im)
        im.thumbnail((1920, 1920))
    else:
        im = gi.cover(im.convert("RGB")) if req["aspect"] == "16:9" else im.convert("RGB")
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


PDF_REF_DIR = pathlib.Path(__file__).resolve().parent / "data" / "pdf_refs"
_TEXT_RE = re.compile(r'[“"][^”"]{1,80}[”"]|₹\s?[\d,.]+(?:\s?(?:lakh|crore|k))?|\b\d{1,3}(?:,\d{2,3})+\b', re.I)


def pdf_page_images(pdf: pathlib.Path, page: int, cache_key: str) -> list[str]:
    """The pictures on one page of a storyboard PDF, biggest first (the team's styleframe, then its thumbnail)."""
    out_dir = PDF_REF_DIR / cache_key
    hits = sorted(out_dir.glob(f"p{page}_*.png"))
    if hits:
        return [str(h) for h in hits]
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf))
        if not 1 <= page <= doc.page_count:
            return []
        pg = doc[page - 1]
        found = []
        for img in pg.get_images(full=True):
            pix = fitz.Pixmap(doc, img[0])
            if pix.n - pix.alpha >= 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            if pix.width >= 240 and pix.height >= 140:
                found.append((pix.width * pix.height, pix))
        found.sort(key=lambda x: -x[0])
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, (_, pix) in enumerate(found[:2]):
            dest = out_dir / f"p{page}_{i}.png"
            pix.save(str(dest))
            paths.append(str(dest))
        return paths
    except Exception as e:
        print(f"z1_plates: could not read page {page} of the storyboard PDF ({e})")
        return []


def no_text(prompt: str) -> str:
    """Drop quoted on-screen words and ₹ amounts from a prompt: text is a kit layer, never painted."""
    return re.sub(r"\s{2,}", " ", _TEXT_RE.sub("", prompt or "")).strip()


def make_one(key: str, entry: dict, spec: dict, force: bool = False, pdf: dict | None = None) -> tuple[str, str]:
    """(path under assets/, source) for one gen key. Raises when no image could be made.
    pdf = {"path": storyboard PDF, "key": cache name}: an entry with pdf_page gets that page's styleframe as its
    main reference (human-storyboard mode)."""
    gi = _gen_images()
    page = entry.get("pdf_page") if isinstance(entry, dict) else None
    if pdf and page:
        entry = {**entry, "prompt": no_text(entry.get("prompt", ""))}
    req = gi.build_request(key, entry, spec)
    if pdf and page:
        try:
            frames = pdf_page_images(pathlib.Path(pdf["path"]), int(page), pdf["key"])
        except (TypeError, ValueError):
            frames = []
        if frames:
            req["refs"] = [frames[0]] + list(req["refs"])
            req["prompt"] += (" The FIRST reference image is the team's approved styleframe for this exact shot: keep "
                              "its set, camera angle, composition, props, Arjun's pose and the lighting, and repaint it "
                              "in the house miniature look of the other references. Leave out every word, number, "
                              "label and UI text that appears in it.")
    desc = _desc(req)
    if not force:
        hit = asset_gen.lookup(THEME, desc)
        if hit:
            return hit, "library"
    name, fn, api_key = _provider()
    if not fn:
        raise RuntimeError("no image API key (set GEMINI_API_KEY or OPENAI_API_KEY)")
    tries = int(os.environ.get("STUDIO_ASSET_ATTEMPTS", "2"))
    err = None
    for _ in range(max(1, tries)):
        try:
            png = _postprocess(fn(req, api_key), req)
            return asset_gen.store(THEME, desc, png, "png", name), name
        except Exception as e:  # network, blocked prompt, empty response
            err = e
            body = getattr(e, "read", None)
            if callable(body):
                try:
                    err = RuntimeError(f"HTTP {getattr(e, 'code', '?')}: {body().decode(errors='ignore')[:200]}")
                except Exception:
                    pass
    raise RuntimeError(str(err)[:300])


def fill(spec: dict, log: Callable[[str], None] | None = None, redo: bool = False,
         only: list[str] | None = None, pdf: dict | None = None,
         on_plate: Callable[[str, str], None] | None = None) -> tuple[dict, dict]:
    """Make every pending plate (redo=True remakes the ones already made). Never raises."""
    report = {"filled": {}, "failed": {}, "skipped": []}
    if not spec or not asset_gen.enabled():
        return spec, report
    gen = dict(spec.get("gen") or {})
    keys = only or (
        [k for k in used_keys(spec) if isinstance(gen.get(k), dict) and gen[k].get("prompt")] if redo else pending(spec)
    )
    for k in missing_prompts(spec):
        report["failed"][f"gen:{k}"] = "used in a frame but has no prompt in spec.gen"
    if not keys:
        return spec, report
    say = log or (lambda m: None)
    cap = int(os.environ.get("STUDIO_ASSET_GEN_MAX", "24"))
    report["skipped"] = keys[cap:]
    keys = keys[:cap]
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get("STUDIO_ASSET_GEN_WORKERS", "4"))) as ex:
        futs = {ex.submit(make_one, k, gen[k], spec, redo, pdf): k for k in keys}
        for f in cf.as_completed(futs):
            k = futs[f]
            try:
                path, source = f.result()
                gen[k] = {**gen[k], "file": path}
                if on_plate:
                    try:
                        on_plate(k, path)
                    except Exception as e:
                        say(f"z1_plates: preview save for {k} skipped ({e})")
                report["filled"][f"gen:{k}"] = {"path": path, "source": source}
            except Exception as e:
                report["failed"][f"gen:{k}"] = str(e)[:300]
                say(f"z1_plates: gen:{k} failed ({e})")
    say(f"z1_plates: made {len(report['filled'])}/{len(keys)} plate(s)")
    return {**spec, "gen": gen}, report


def attach(spec: dict, frame: dict) -> dict:
    """Copy of frame with the spec.gen entries it uses under "_gen" (what the kit adapter reads)."""
    gen = (spec or {}).get("gen") or {}
    keys = set(GEN_RE.findall(json.dumps(frame, ensure_ascii=False)))
    return {**frame, "_gen": {k: gen[k] for k in keys if isinstance(gen.get(k), dict)}}


def image_prompts_md(spec: dict) -> str:
    """The kit's _image_prompts.md: full prompt (style + character bible) for every plate, marked done/pending."""
    gi = _gen_images()
    gen = (spec or {}).get("gen") or {}
    frames = (spec or {}).get("frames") or []
    lines = ["# Image-generation prompts (Gemini, Magnific or any image model)\n",
             "16:9 = 1920x1080 plate; cutout = isolated on white (remove the background). Generated images carry no text.\n"]
    for key in used_keys(spec):
        g = gen.get(key)
        if not isinstance(g, dict) or not g.get("prompt"):
            lines.append(f"## {key} — NO PROMPT IN spec.gen\n")
            continue
        p, ar = gi.build.prompt_text(key, g, spec.get("arjun", "city"))
        status = "done" if _have(g) else "PENDING"
        used = ", ".join(str(f.get("id")) for f in frames if f"gen:{key}" in json.dumps(f, ensure_ascii=False))
        lines.append(f"## {key}  ({ar}{', cutout' if g.get('cutout') else ''}) — {status}\nUsed in: {used}\n\n```\n{p}\n```\n")
    return "\n".join(lines)


def export_files(p: dict) -> dict[str, str]:
    out = {"image_prompts.md": image_prompts_md(p.get("spec") or {})}
    if (p.get("storyboard") or "").strip():
        out["storyboard.md"] = p["storyboard"]
    return out

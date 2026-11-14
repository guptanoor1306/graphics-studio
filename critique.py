"""Render → look → fix: the chat skill's QA step, run inside the app after Claude writes a spec.

In chat, the skill builds every frame, reads the kit's WARN lines, looks at contact sheets and fixes the
broken frames before anyone sees them. The app used to save the first spec blind. This module closes that gap:

  1. render every graphic frame with the theme's own renderer (headless Chromium, no server needed);
  2. run the theme's CHECK_JS / QA_JS on each page (overlap, off-frame, clipped, off-palette…);
  3. tile the renders into labelled contact sheets;
  4. send sheets + WARN lines (+ close-ups of flagged frames) to Claude, which returns only the frames to change;
  5. re-render just those frames and keep a fix only if it doesn't add WARNs; repeat (default 2 rounds).

STUDIO_CRITIQUE_ROUNDS=0 turns it off.
"""
from __future__ import annotations

import asyncio
import io
import os
import pathlib
import re
import tempfile
from typing import Callable

import claude_client
import exporter

ROUNDS = int(os.environ.get("STUDIO_CRITIQUE_ROUNDS", "2"))
MAX_CLOSEUPS = 4

# Kit checks miss some placements (e.g. Varsity's CHECK_JS only scans `.z`, but the app renderer puts
# assets/people at body level). This catches any illustration or spec layer that is mostly off the canvas.
GENERIC_JS = r"""(srcs) => {
  const W = [], cw = innerWidth, ch = innerHeight;
  // only content the spec placed: images named in the frame JSON (decorative floors/bursts bleed on purpose)
  const names = (srcs || []).map(s => String(s).split('/').pop()).filter(Boolean);
  if (!names.length) return W;
  const els = [...document.querySelectorAll('img:not(.plate)')]
    .filter(e => names.some(n => (e.getAttribute('src') || '').endsWith(n)));
  for (const e of els) {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    const area = r.width * r.height;
    if (!area || area < cw * ch * 0.01) continue;
    const ix = Math.max(0, Math.min(r.right, cw) - Math.max(r.left, 0));
    const iy = Math.max(0, Math.min(r.bottom, ch) - Math.max(r.top, 0));
    const out = 1 - (ix * iy) / area;
    if (out > 0.15) {
      const t = (e.getAttribute('src') || e.innerText || e.className || e.tagName).toString()
        .split('/').pop().replace(/\s+/g, ' ').slice(0, 40);
      W.push(`${Math.round(out * 100)}% off-canvas: "${t}" (${r.left|0},${r.top|0},${r.right|0},${r.bottom|0})`);
    }
  }
  return [...new Set(W)].slice(0, 6);
}"""


# ------------------------------------------------------------------ render
def _frame_srcs(frame) -> list[str]:
    """Every image path named anywhere in a frame's JSON (asset src, plate images, etc.)."""
    found: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("src", "img", "image") and isinstance(v, str) and "." in v:
                    found.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(frame)
    return found


async def _render_async(pages, check_js: str, canvas: tuple[int, int], arg_srcs=None) -> dict[str, tuple[bytes | None, list[str]]]:
    """pages: [(fid, html | Exception, check_arg)] → {fid: (png, warns)}."""
    arg_srcs = arg_srcs or {}
    from playwright.async_api import async_playwright

    out: dict[str, tuple[bytes | None, list[str]]] = {}
    cw, ch = canvas
    with tempfile.TemporaryDirectory(prefix="studio_critique_") as td:
        async with async_playwright() as pw:
            browser = await exporter.launch_chromium(pw)
            pg = await browser.new_page(viewport={"width": cw, "height": ch})
            errors: list[str] = []
            pg.on("pageerror", lambda e: errors.append(str(e)[:200]))
            for n, (fid, html, arg) in enumerate(pages):
                if isinstance(html, BaseException):
                    out[fid] = (None, [f"render failed: {html}"[:300]])
                    continue
                errors.clear()
                path = pathlib.Path(td) / f"f{n}.html"
                path.write_text(html)
                warns: list[str] = []
                try:
                    await pg.goto(path.as_uri(), wait_until="load", timeout=120_000)
                    if "window.RENDERED" in html or "render.js" in html:
                        try:
                            await pg.wait_for_function("window.RENDERED === true", timeout=20_000)
                        except Exception:
                            warns.append("renderer never finished (window.RENDERED not set)")
                    await pg.evaluate("document.fonts.ready")
                    await pg.wait_for_timeout(150)
                    try:
                        res = await (pg.evaluate(check_js, arg) if arg is not None else pg.evaluate(check_js))
                        warns += [str(w) for w in (res or [])]
                    except Exception as e:
                        warns.append(f"layout check could not run: {str(e)[:160]}")
                    try:
                        srcs = list(arg_srcs.get(fid, []))
                        warns += [w for w in await pg.evaluate(GENERIC_JS, srcs) if w not in warns]
                    except Exception:
                        pass
                    warns += [f"page error: {e}" for e in errors]
                    png = await pg.screenshot(type="png")
                except Exception as e:
                    out[fid] = (None, [f"render failed: {str(e)[:200]}"])
                    continue
                out[fid] = (png, warns)
            await browser.close()
    return out


def render_frames(pages, check_js: str, canvas: tuple[int, int], srcs: dict | None = None):
    return asyncio.run(_render_async(pages, check_js, canvas, srcs))


# ------------------------------------------------------------------ contact sheets
def _font(size: int):
    from PIL import ImageFont

    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        str(pathlib.Path(__file__).parent / "themes/varsity-english/fonts/Inter-Bold.ttf"),
    ):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def contact_sheets(renders: dict, order: list[str], canvas: tuple[int, int]) -> list[bytes]:
    """Labelled tiles, 6 landscape (3×2) or 8 portrait (4×2) per sheet, as JPEG — like the skill's _sheet_N.jpg."""
    from PIL import Image, ImageDraw

    cw, ch = canvas
    portrait = ch > cw
    cols, per = (4, 8) if portrait else (3, 6)
    tw = 320 if portrait else 640
    th = round(tw * ch / cw)
    label_h, gap = 36, 8
    font = _font(22)
    ids = [f for f in order if f in renders]
    sheets: list[bytes] = []
    for s in range(0, len(ids), per):
        chunk = ids[s:s + per]
        rows = (len(chunk) + cols - 1) // cols
        W = cols * tw + (cols + 1) * gap
        H = rows * (th + label_h) + (rows + 1) * gap
        sheet = Image.new("RGB", (W, H), (34, 34, 38))
        d = ImageDraw.Draw(sheet)
        for k, fid in enumerate(chunk):
            png, warns = renders[fid]
            x = gap + (k % cols) * (tw + gap)
            y = gap + (k // cols) * (th + label_h + gap)
            if png:
                tile = Image.open(io.BytesIO(png)).convert("RGB").resize((tw, th))
                sheet.paste(tile, (x, y))
            else:
                d.rectangle([x, y, x + tw, y + th], fill=(90, 20, 20))
                d.text((x + 16, y + 16), "RENDER FAILED", fill=(255, 255, 255), font=font)
            label = str(fid) + (f"  ·  {len(warns)} WARN" if warns else "")
            d.text((x + 4, y + th + 6), label, fill=(255, 120, 110) if warns else (235, 235, 235), font=font)
        buf = io.BytesIO()
        sheet.save(buf, "JPEG", quality=82)
        sheets.append(buf.getvalue())
    return sheets


def _closeup(png: bytes, canvas: tuple[int, int]) -> bytes:
    from PIL import Image

    im = Image.open(io.BytesIO(png)).convert("RGB")
    cw, ch = canvas
    w = 1280 if cw >= ch else 720
    im = im.resize((w, round(w * ch / cw)))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return buf.getvalue()


# ------------------------------------------------------------------ loop
def run(
    *,
    theme_dir: pathlib.Path,
    spec: dict,
    storyboard: str,
    render_html: Callable[[dict, dict], str],
    renderable: Callable[[dict], bool],
    check_js: str,
    check_arg: Callable[[dict], object] | None = None,
    canvas: tuple[int, int] = (1920, 1080),
    finalize: Callable[[dict], dict] | None = None,
    script: str = "",
    rounds: int | None = None,
    only_ids: set[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> tuple[dict, dict]:
    """Returns (spec, report). Never raises for render/critique failures: the original spec is kept."""
    rounds = ROUNDS if rounds is None else rounds
    report = {"rounds": 0, "changed": {}, "reverted": [], "warns_before": None, "warns_after": None, "remaining": []}
    say = log or (lambda m: None)
    if rounds <= 0 or not (spec or {}).get("frames"):
        return spec, report

    def srcs_for(sp: dict) -> dict:
        return {str(f.get("id")): _frame_srcs(f) for f in sp.get("frames") or [] if isinstance(f, dict)}

    def pages_for(sp: dict, ids: set[str] | None):
        pages = []
        for f in sp.get("frames") or []:
            if not isinstance(f, dict) or not renderable(f):
                continue
            fid = str(f.get("id"))
            if ids is not None and fid not in ids:
                continue
            try:
                html: str | BaseException = render_html(f, sp)
            except (KeyboardInterrupt, SystemError):
                raise
            except BaseException as e:  # Hindi kits raise SystemExit on bad specs
                html = e
            pages.append((fid, html, check_arg(f) if check_arg else None))
        return pages

    try:
        renders = render_frames(pages_for(spec, set(only_ids) if only_ids else None), check_js, canvas, srcs_for(spec))
    except Exception as e:
        say(f"critique: render failed, keeping spec as is ({e})")
        report["error"] = f"render: {e}"
        return spec, report
    order = [str(f.get("id")) for f in spec.get("frames") or [] if isinstance(f, dict)]
    report["warns_before"] = sum(len(w) for _, w in renders.values())
    focus: set[str] | None = set(only_ids) if only_ids else None  # round 1 = every frame (or only_ids)

    for n in range(1, rounds + 1):
        shown = [fid for fid in order if fid in renders and (focus is None or fid in focus)]
        if not shown:
            break
        warns = {fid: renders[fid][1] for fid in shown if renders[fid][1]}
        flagged = [fid for fid in shown if renders[fid][1] and renders[fid][0]][:MAX_CLOSEUPS]
        try:
            res = claude_client.fix_frames(
                theme_dir, spec, storyboard,
                warns=warns,
                sheets=contact_sheets(renders, shown, canvas),
                closeups=[(fid, _closeup(renders[fid][0], canvas)) for fid in flagged],
                focus_ids=None if focus is None else shown,
                script=script,
                round_no=n,
            )
        except Exception as e:
            say(f"critique round {n}: Claude call failed ({e}); keeping current spec")
            report["error"] = f"fix: {e}"
            break
        report["rounds"] = n
        new_spec, changed = claude_client.merge_fixes(spec, res)
        if not changed and not res.get("remove_ids"):
            say(f"critique round {n}: no changes needed")
            break
        if finalize:
            new_spec = finalize(new_spec)
        try:
            new_renders = render_frames(pages_for(new_spec, set(changed)), check_js, canvas, srcs_for(new_spec))
        except Exception as e:
            say(f"critique round {n}: re-render failed ({e}); keeping previous spec")
            break
        # keep a fix only if it renders and doesn't add WARNs
        old_by_id = {str(f.get("id")): f for f in spec.get("frames") or [] if isinstance(f, dict)}
        frames = []
        for f in new_spec.get("frames") or []:
            fid = str(f.get("id"))
            if fid in new_renders and fid in renders:
                nr, orr = new_renders[fid], renders[fid]
                if nr[0] is None or len(nr[1]) > len(orr[1]):
                    frames.append(old_by_id.get(fid, f))
                    report["reverted"].append(fid)
                    continue
            frames.append(f)
        new_spec = {**new_spec, "frames": frames}
        whys = {str(fx.get("id")): fx.get("why", "") for fx in res.get("fixes") or [] if isinstance(fx, dict)}
        for fid in changed:
            if fid not in report["reverted"]:
                report["changed"][fid] = whys.get(fid, "")
                if fid in new_renders:
                    renders[fid] = new_renders[fid]
        for fid in res.get("remove_ids") or []:
            renders.pop(str(fid), None)
        spec = new_spec
        order = [str(f.get("id")) for f in spec.get("frames") or [] if isinstance(f, dict)]
        say(f"critique round {n}: changed {len(changed)} frame(s), reverted {len(report['reverted'])}")
        still = {fid for fid, (_, w) in renders.items() if w}
        focus = (set(changed) - set(report["reverted"])) | still
        if not focus:
            break

    report["warns_after"] = sum(len(w) for _, w in renders.values())
    report["remaining"] = [f"{fid}: {w}" for fid in order if fid in renders for w in renders[fid][1]]
    return spec, report

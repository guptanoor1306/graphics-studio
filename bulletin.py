"""Layered "Bulletin" export (the ZO team format, from the zo-graphic-maker skill).

<Video>_layers/
  html/<NN>_<What-it-shows>.html   self-contained 1920x1080, Inter embedded, no scripts or classes
  png/<same>.png                    rendered from that html
  layers/<same>.json                layer tree (group/box/text/svg/img with absolute x,y,w,h and styles)
  LAYERS.txt  README.txt  spec.json

Frames are rendered with the kit renderer, every visible element is walked into named layers (studio layer
labels become layer names), re-emitted as absolutely positioned HTML and re-rendered; a pixel diff against
the original render flags anything the flattening missed.
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import mimetypes
import os
import pathlib
import re
import tempfile
import urllib.parse
import zipfile

import exporter

FONT_WEIGHTS = [(400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold")]

# Name layers before walking: studio layer labels → data-name; decor, plate and grid get fixed names.
NAME_JS = r"""() => {
  const st = document.getElementById('stage');
  if (st && !st.dataset.name) st.dataset.name = st.classList.contains('fss') ? 'Background grid' : 'Stage';
  document.querySelectorAll('img.plate').forEach(e => e.dataset.name = 'Presenter plate');
  document.querySelectorAll('img.cutout').forEach(e => e.dataset.name = 'Presenter cut-out');
  document.querySelectorAll('.decor').forEach((e, i) => {
    if (e.dataset.name) return;
    const svg = e.querySelector('svg path');
    const d = svg ? (svg.getAttribute('d') || '') : '';
    e.dataset.name = d.startsWith('M6 40c') ? 'Decor / Squiggle' : d.startsWith('M8 6 L36') ? 'Decor / Triangle'
      : d.startsWith('M20 2') ? 'Decor / Sparkle' : (e.firstElementChild && !svg) ? 'Decor / Dash' : 'Decor / Shape';
  });
  document.querySelectorAll('[data-layer-label]').forEach(e => {
    if (e.dataset.name) return;
    const t = (e.dataset.layerType || 'Layer'), l = (e.dataset.layerLabel || '').split(' · ').pop();
    e.dataset.name = (t.charAt(0).toUpperCase() + t.slice(1)) + (l && l !== t ? ' / ' + l : '');
  });
  document.querySelectorAll('.heading').forEach(e => { if (!e.dataset.name) e.dataset.name = 'Heading'; });
  const nice = t => (t || 'Layer').replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
  const txt = e => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 28);
  document.querySelectorAll('[data-zo-t]').forEach(e => { if (!e.dataset.name) e.dataset.name = nice(e.dataset.zoT); });
  const parts = [['.v2-step', 'Step'], ['.v2-card', 'Card'], ['.v2-t tr', 'Row'], ['.v2-pill,.pillv,.v2-rail .pp,.v2-rel .pl', 'Pill'],
    ['.v2-fbox', 'Box'], ['.v2-cat .c', 'Card'], ['.v2-opt .o', 'Option'], ['.v2-opt .src', 'Card'], ['.v2-person', 'Card'],
    ['.v2-build .it', 'Item'], ['.v2-recap .it', 'Item'], ['.v2-check .row', 'Row'], ['.v2-split .bar > div', 'Bar'],
    ['.v2-split .labs > div', 'Label'], ['.v2-cost .r', 'Row'], ['.v2-ud .col', 'Bar'], ['.v2-tl .f', 'Folder'],
    ['.v2-ybox,.v2-ovy', 'Box'], ['.v2-bubble .bx', 'Bubble'], ['.note .box', 'Note'], ['.icard', 'Card'], ['.pcard', 'Card'],
    ['.obj', 'Card'], ['.ticket', 'Card'], ['.bigpill', 'Pill'], ['.hubc', 'Circle'], ['.mtable tr', 'Row']];
  for (const [sel, label] of parts) document.querySelectorAll(sel).forEach((e, i) => {
    if (e.dataset.name) return; const t = txt(e); e.dataset.name = label + ' / ' + (t || String(i + 1));
  });
}"""

WALK_JS = r"""(() => {
const R = v => Math.round(v*100)/100;
const scaleOf = el => { const r = el.getBoundingClientRect(); return (el.offsetWidth > 0 && r.width > 0) ? r.width / el.offsetWidth : 1; };
const px = (v, s) => String(v).replace(/(-?[\d.]+)px/g, (m, n) => R(parseFloat(n) * s) + 'px');
const visBox = cs => {
  const bg = cs.backgroundColor, hasBg = bg && !/rgba\(.*, 0\)$/.test(bg) && bg !== 'transparent';
  const hasImg = cs.backgroundImage && cs.backgroundImage !== 'none';
  const bw = ['Top','Right','Bottom','Left'].some(s => parseFloat(cs['border'+s+'Width']) > 0 && cs['border'+s+'Style'] !== 'none');
  const sh = cs.boxShadow && cs.boxShadow !== 'none';
  return hasBg || hasImg || bw || sh;
};
const opa = el => { let o = 1; for (let e = el; e && e !== document.documentElement; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity); return R(o); };
const boxLeaf = (el, name) => {
  const cs = getComputedStyle(el), r = el.getBoundingClientRect(), s = scaleOf(el);
  const sides = ['Top','Right','Bottom','Left'];
  const bw = sides.some(x => parseFloat(cs['border'+x+'Width']) > 0 && cs['border'+x+'Style'] !== 'none');
  const rad = [cs.borderTopLeftRadius, cs.borderTopRightRadius, cs.borderBottomRightRadius, cs.borderBottomLeftRadius].map(v => px(v, s).split(' '));
  const h = rad.map(v => v[0]), v = rad.map(v => v[1] || v[0]);
  return {type:'box', name, x:R(r.left), y:R(r.top), w:R(r.width), h:R(r.height), bg:cs.backgroundColor,
    bgimg:cs.backgroundImage, bgsize:cs.backgroundImage !== 'none' ? px(cs.backgroundSize, s) : '', bgpos:px(cs.backgroundPosition, s), bgrepeat:cs.backgroundRepeat,
    radius: h.join(' ') === v.join(' ') ? h.join(' ') : h.join(' ') + ' / ' + v.join(' '),
    border: bw ? sides.map(x => `${R(parseFloat(cs['border'+x+'Width']) * s)}px ${cs['border'+x+'Style']} ${cs['border'+x+'Color']}`) : null,
    shadow: cs.boxShadow === 'none' ? '' : px(cs.boxShadow, s), opacity: opa(el)};
};
const textLeaves = node => {
  const el = node.parentElement, cs = getComputedStyle(el), s = scaleOf(el), out = [];
  const str = node.textContent, re = /\S+/g; let m; const words = [];
  while ((m = re.exec(str))) { const rg = document.createRange(); rg.setStart(node, m.index); rg.setEnd(node, m.index + m[0].length);
    const rs = [...rg.getClientRects()].filter(q => q.width > 0); if (!rs.length) continue;
    const q = rs[0]; words.push({t:m[0], l:q.left, t0:q.top, r:Math.max(...rs.map(z => z.right)), b:q.bottom}); }
  const lines = []; for (const w of words) { const L = lines.find(l => Math.abs(l.t0 - w.t0) < 3); if (L) L.ws.push(w); else lines.push({t0:w.t0, ws:[w]}); }
  for (const L of lines) { let txt = L.ws.map(w => w.t).join(' '); if (cs.textTransform === 'uppercase') txt = txt.toUpperCase();
    const l = Math.min(...L.ws.map(w => w.l)), r = Math.max(...L.ws.map(w => w.r)), t = Math.min(...L.ws.map(w => w.t0)), b = Math.max(...L.ws.map(w => w.b));
    out.push({type:'text', name:txt, text:txt, x:R(l), y:R(t), w:R(r - l + 2), h:R(b - t), size:R(parseFloat(cs.fontSize) * s), weight:cs.fontWeight,
      color:cs.color, ls: cs.letterSpacing === 'normal' ? 0 : R(parseFloat(cs.letterSpacing) * s),
      shadow: cs.textShadow === 'none' ? '' : px(cs.textShadow, s), opacity: opa(el)}); }
  return out;
};
const warn = [];
const hasContent = el => el.textContent.trim().length > 0 || el.querySelector('svg,div,span,img');
const walk = el => {
  const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return [];
  const name = el.getAttribute('data-name');
  if (el.tagName.toLowerCase() === 'svg') {
    if (el.querySelector('text')) warn.push('svg text in ' + (name || 'svg'));
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) return [];
    const c = el.cloneNode(true);
    if (!c.getAttribute('viewBox')) c.setAttribute('viewBox', `0 0 ${el.width.baseVal.value || r.width} ${el.height.baseVal.value || r.height}`);
    ['class','style','data-name','width','height'].forEach(a => c.removeAttribute(a));
    c.setAttribute('width', '100%'); c.setAttribute('height', '100%'); c.setAttribute('preserveAspectRatio', 'none');
    return [{type:'svg', name:name || 'Shapes', x:R(r.left), y:R(r.top), w:R(r.width), h:R(r.height), opacity:opa(el), svg:c.outerHTML}];
  }
  if (el.tagName === 'IMG') { const r = el.getBoundingClientRect(); if (!r.width || !r.height) return [];
    return [{type:'img', name:name || 'Image', x:R(r.left), y:R(r.top), w:R(r.width), h:R(r.height), src:el.src, fit:cs.objectFit || 'fill', opacity:opa(el)}]; }
  const t = cs.transform; if (t && t !== 'none' && !/^matrix\(1, 0, 0, 1,|^matrix\([\d.]+, 0, 0, [\d.]+,/.test(t)) warn.push('rotated element: ' + (name || el.className || el.tagName));
  const kids = [];
  if (visBox(cs)) kids.push(boxLeaf(el, name && !hasContent(el) ? name : 'Background'));
  for (const ch of el.childNodes) {
    if (ch.nodeType === 3) { if (ch.textContent.trim()) kids.push(...textLeaves(ch)); }
    else if (ch.nodeType === 1 && !['SCRIPT','STYLE','DEFS','LINK','META'].includes(ch.tagName)) kids.push(...walk(ch));
  }
  if (name && !(kids.length === 1 && kids[0].type === 'box' && kids[0].name === name)) {
    if (!kids.length) return [];
    if (kids.length === 1 && kids[0].type !== 'group' && !name.includes('/')) { if (kids[0].type !== 'text') kids[0].name = name; return [kids[0]]; }
    return [{type:'group', name, children:kids}];
  }
  return kids;
};
const top = []; for (const ch of document.body.children) { if (!['SCRIPT','STYLE','LINK'].includes(ch.tagName)) top.push(...walk(ch)); }
return {tree: top, warn};
})()"""


def _fonts_css(theme_dir: pathlib.Path) -> str:
    out = []
    for w, n in FONT_WEIGHTS:
        f = theme_dir / "fonts" / f"Inter-{n}.ttf"
        if f.is_file():
            out.append(f"@font-face{{font-family:Inter;font-weight:{w};src:url(data:font/ttf;base64,"
                       f"{base64.b64encode(f.read_bytes()).decode()}) format('truetype')}}")
    return "".join(out)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "layer"


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _bbox(n):
    if n["type"] == "group":
        bs = [_bbox(c) for c in n["children"]]
        return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    return (n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"])


def _dedupe(children):
    seen: dict[str, int] = {}
    for c in children:
        k = c["name"]; seen[k] = seen.get(k, 0) + 1
        if seen[k] > 1:
            c["name"] = f"{k} {seen[k]}"
        if c["type"] == "group":
            _dedupe(c["children"])


def _img_data(src: str) -> str:
    if src.startswith("data:"):
        return src
    if src.startswith("file://"):
        p = pathlib.Path(urllib.parse.unquote(urllib.parse.urlparse(src).path))
        if p.is_file():
            mt = mimetypes.guess_type(str(p))[0] or "image/png"
            return f"data:{mt};base64,{base64.b64encode(p.read_bytes()).decode()}"
    return src


def _emit(n, px, py, ids, ind) -> str:
    R = lambda v: round(v, 2)
    sp = "  " * ind

    def uid(name):
        b = _slug(name); i = b; k = 2
        while i in ids:
            i = f"{b}-{k}"; k += 1
        ids.add(i); return i

    if n["type"] == "group":
        x0, y0, x1, y1 = _bbox(n)
        s = (f'{sp}<div data-name="{_esc(n["name"])}" id="{uid(n["name"])}" data-type="group" '
             f'style="position:absolute;left:{R(x0 - px)}px;top:{R(y0 - py)}px;width:{R(x1 - x0)}px;height:{R(y1 - y0)}px">\n')
        for c in n["children"]:
            s += _emit(c, x0, y0, ids, ind + 1)
        return s + f"{sp}</div>\n"
    pos = f'position:absolute;left:{R(n["x"] - px)}px;top:{R(n["y"] - py)}px;width:{n["w"]}px;height:{n["h"]}px;'
    op = f'opacity:{n["opacity"]};' if n.get("opacity", 1) < 1 else ""
    if n["type"] == "text":
        st = (pos + f'line-height:{n["h"]}px;font-family:Inter,sans-serif;font-size:{n["size"]}px;font-weight:{n["weight"]};'
              f'font-style:normal;color:{n["color"]};white-space:pre;')
        if n.get("ls"):
            st += f'letter-spacing:{n["ls"]}px;'
        if n.get("shadow"):
            st += f'text-shadow:{n["shadow"]};'
        return f'{sp}<div data-name="Text / {_esc(n["name"])}" id="{uid(n["name"])}" data-type="text" style="{st}{op}">{_esc(n["text"])}</div>\n'
    if n["type"] == "box":
        st = pos + f'background-color:{n["bg"]};border-radius:{n["radius"]};'
        if n["bgimg"] != "none":
            st += (f'background-image:{n["bgimg"]};background-size:{n["bgsize"]};background-position:{n["bgpos"]};'
                   f'background-repeat:{n["bgrepeat"]};')
        if n.get("border"):
            for side, b in zip(["top", "right", "bottom", "left"], n["border"]):
                st += f"border-{side}:{b};"
        if n.get("shadow"):
            st += f'box-shadow:{n["shadow"]};'
        st = st.replace('"', "'")
        return f'{sp}<div data-name="{_esc(n["name"])}" id="{uid(n["name"])}" data-type="shape" style="{st}{op}"></div>\n'
    if n["type"] == "img":
        return (f'{sp}<img data-name="{_esc(n["name"])}" id="{uid(n["name"])}" data-type="image" src="{_img_data(n["src"])}" '
                f'style="{pos}object-fit:{n["fit"]};{op}">\n')
    if n["type"] == "svg":
        return f'{sp}<div data-name="{_esc(n["name"])}" id="{uid(n["name"])}" data-type="vector" style="{pos}{op}">{n["svg"]}</div>\n'
    return ""


def _jsonify(n):
    if n["type"] == "group":
        return {"type": "group", "name": n["name"], "children": [_jsonify(c) for c in n["children"]]}
    d = {k: v for k, v in n.items() if k != "svg"}
    if d.get("type") == "img" and str(d.get("src", "")).startswith("file://"):
        d["src"] = pathlib.Path(urllib.parse.urlparse(d["src"]).path).name
    return d


def _outline(n, ind, lines):
    sp = "  " * ind
    if n["type"] == "group":
        lines.append(f"{sp}▸ {n['name']}")
        for c in n["children"]:
            _outline(c, ind + 1, lines)
    else:
        lines.append(f"{sp}· {n['name']}  [{n['type']}]")


def _texts(n, out):
    if n["type"] == "group":
        for c in n["children"]:
            _texts(c, out)
    elif n["type"] == "text":
        out.append(n["text"])


def frame_file_name(n: int, fid: str, mode: str, texts: list[str]) -> str:
    what = next((t for t in texts if len(t) > 3), fid)
    what = "-".join(re.sub(r"[^A-Za-z0-9₹]+", " ", what).split()[:5]) or fid
    tos = "_TOS" if mode in ("osa", "ost", "tos") else ""
    return f"{n:02d}_{re.sub(r'[^A-Za-z0-9]+', '', str(fid)) or n}{tos}_{what}"[:80]


async def _build(pages, theme_dir, viewport):
    from playwright.async_api import async_playwright

    vw, vh = viewport
    fonts = _fonts_css(theme_dir)
    results = []
    with tempfile.TemporaryDirectory(prefix="bulletin_") as td:
        async with async_playwright() as pw:
            b = await exporter.launch_chromium(pw)
            pg = await b.new_page(viewport={"width": vw, "height": vh})
            for k, (fid, html, mode) in enumerate(pages):
                src = pathlib.Path(td) / f"src_{k}.html"
                src.write_text(html)
                await pg.goto(src.as_uri(), wait_until="load", timeout=120_000)
                if "window.RENDERED" in html or "render.js" in html:
                    try:
                        await pg.wait_for_function("window.RENDERED === true", timeout=20_000)
                    except Exception:
                        pass
                await pg.evaluate("document.fonts.ready")
                await pg.wait_for_timeout(120)
                src_png = await pg.screenshot()
                await pg.evaluate(NAME_JS)
                res = await pg.evaluate(WALK_JS)
                tree = res["tree"]; _dedupe(tree)
                ids: set[str] = set()
                body = "".join(_emit(n, 0, 0, ids, 1) for n in tree)
                texts: list[str] = []
                for n in tree:
                    _texts(n, texts)
                name = frame_file_name(k + 1, fid, mode, [t for t in texts])
                out_html = (f'<!doctype html>\n<html><head><meta charset="utf-8"><title>{_esc(name)}</title>\n<style>{fonts}\n'
                            f'*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{vw}px;height:{vh}px;overflow:hidden;background:#fff}}'
                            f'body{{position:relative;-webkit-font-smoothing:antialiased}}</style></head>\n<body data-name="Frame {_esc(name)}">\n{body}</body></html>\n')
                flat = pathlib.Path(td) / f"flat_{k}.html"
                flat.write_text(out_html)
                await pg.goto(flat.as_uri(), wait_until="load", timeout=120_000)
                await pg.evaluate("document.fonts.ready")
                await pg.wait_for_timeout(120)
                png = await pg.screenshot()
                results.append({"fid": fid, "mode": mode, "name": name, "html": out_html, "png": png, "src_png": src_png,
                                "tree": {"type": "group", "name": f"Frame {name}", "children": [_jsonify(n) for n in tree]},
                                "raw_tree": tree, "texts": texts, "warn": res.get("warn") or []})
            await b.close()
    return results


def _diff(a: bytes, b: bytes) -> int:
    from PIL import Image, ImageChops

    # half size: sub-pixel text placement (the kit scales content to fit) washes out; moved/missing shapes don't
    ia = Image.open(io.BytesIO(a)).convert("RGB"); ib = Image.open(io.BytesIO(b)).convert("RGB")
    from PIL import ImageFilter
    ia = ia.resize((ia.width // 2, ia.height // 2), Image.BOX).filter(ImageFilter.GaussianBlur(1.5))
    ib = ib.resize((ib.width // 2, ib.height // 2), Image.BOX).filter(ImageFilter.GaussianBlur(1.5))
    d = ImageChops.difference(ia, ib).convert("L").point(lambda v: 255 if v > 60 else 0)
    return sum(1 for v in d.getdata() if v)


def export_bulletin(pages, theme_dir: pathlib.Path, video: str, meta: dict, *, viewport=(1920, 1080),
                    skipped: list[dict] | None = None, notes: list[str] | None = None,
                    zip_path: pathlib.Path | None = None) -> bytes:
    """pages: [(frame_id, html_with_file_base_href, mode)]; meta: {frame_id: {"vo": str}}."""
    if not pages:
        raise ValueError("No frames to export")
    results = asyncio.run(_build(pages, theme_dir, viewport))
    root = f"{re.sub(r'[^A-Za-z0-9]+', '_', video).strip('_') or 'Video'}_layers"
    outline: list[str] = []
    frames = []
    check = []
    for r in results:
        outline.append(f"▸ Frame {r['name']}")
        for n in r["raw_tree"]:
            _outline(n, 1, outline)
        outline.append("")
        changed = _diff(r["src_png"], r["png"])
        if changed > 600:
            check.append(f"{r['name']}: {changed} px differ from the kit render — check it")
        frames.append({"id": r["fid"], "name": r["name"], "mode": "Over presenter" if r["mode"] in ("osa", "ost", "tos") else "FSS",
                       "vo": (meta.get(r["fid"]) or {}).get("vo", ""), "html": f"html/{r['name']}.html", "png": f"png/{r['name']}.png",
                       "layers": f"layers/{r['name']}.json", "text": r["texts"], "warnings": r["warn"]})
    over = [f["name"] for f in frames if f["mode"] == "Over presenter"]
    all_notes = list(notes or [])
    if over:
        all_notes.append("Over-presenter frames use stand-in plates unless a still was supplied: " + ", ".join(over))
    spec = {"video": video, "frames": frames, "skipped": skipped or [], "notes": all_notes}
    readme = (f"{root}/\n  html/    one self-contained 1920x1080 page per frame (Inter embedded, no scripts or classes)\n"
              "  png/     rendered from that html\n  layers/  layer tree per frame (group/box/text/svg/img, absolute x,y,w,h)\n"
              "  LAYERS.txt  outline of every frame's layers\n  spec.json   frames, voice-over, text, skipped beats, notes\n\n"
              f"Frames: {len(frames)} ({frames[0]['name']} … {frames[-1]['name']})\n")
    if over:
        readme += "Over the presenter (stand-in plates): " + ", ".join(over) + "\n"
    if skipped:
        readme += "Skipped beats: " + "; ".join(f"{s.get('beat', '')[:60]} ({s.get('reason', '')})" for s in skipped) + "\n"
    if check:
        readme += "\nCheck after flattening:\n" + "\n".join(check) + "\n"
    buf: io.BytesIO | None = None if zip_path else io.BytesIO()
    with zipfile.ZipFile(zip_path or buf, "w", zipfile.ZIP_DEFLATED) as z:
        for r in results:
            z.writestr(f"{root}/html/{r['name']}.html", r["html"])
            z.writestr(f"{root}/png/{r['name']}.png", r["png"])
            z.writestr(f"{root}/layers/{r['name']}.json", json.dumps(r["tree"], indent=1, ensure_ascii=False))
        z.writestr(f"{root}/LAYERS.txt", "\n".join(outline))
        z.writestr(f"{root}/README.txt", readme)
        z.writestr(f"{root}/spec.json", json.dumps(spec, indent=1, ensure_ascii=False))
    if zip_path is not None:
        return b""
    assert buf is not None
    return buf.getvalue()

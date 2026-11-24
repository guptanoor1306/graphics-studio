"""Toolkit: ready-made frames (ZO Product first) that a video can use instead of generating a frame.

The toolkit of a kit is one hidden project (look.toolkit = true) whose frames ARE the templates, so making and editing
templates uses the normal editor (layers, text, Edit with AI, presenter shot upload, undo) and they live in the same
database as everything else. A video takes a copy of a template for the script lines picked; "Generate the rest" then
asks Claude only for the lines no toolkit frame covers.
"""
from __future__ import annotations

import copy
import json
import re

THEMES_WITH_TOOLKIT = ("zo-product-graphics",)
NAME = {"zo-product-graphics": "Toolkit · ZO Product"}


def enabled(theme: str) -> bool:
    return theme in THEMES_WITH_TOOLKIT


def is_toolkit(p: dict) -> bool:
    look = p.get("look") if isinstance(p.get("look"), dict) else {}
    return bool(look.get("toolkit"))


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9₹%]+", " ", str(s or "").lower()).strip()


def next_id(frames: list, prefix: str = "tk") -> str:
    n = 1
    have = {str(f.get("id")) for f in frames if isinstance(f, dict)}
    while f"{prefix}{n}" in have:
        n += 1
    return f"{prefix}{n}"


def template_view(f: dict) -> dict:
    return {"fid": str(f.get("id")), "name": f.get("name") or f"Template {f.get('id')}", "tags": f.get("tk_tags") or [],
            "mode": f.get("mode") or "fss"}


# ---------------------------------------------------------------- making templates
def from_frame(src_project: dict, frame: dict, name: str, tk_frames: list) -> dict:
    """A template copied from a video's frame. The presenter shot that video uploaded for this frame's side goes with
    it (as the template's own photo)."""
    import presenter
    f = copy.deepcopy(frame)
    for k in ("vo", "section", "lines", "lines_src", "tk_from"):
        f.pop(k, None)
    f["id"] = next_id(tk_frames, "t")
    f["name"] = (name or frame.get("name") or "").strip()[:80] or f"Template {len(tk_frames) + 1}"
    look = src_project.get("look") if isinstance(src_project.get("look"), dict) else {}
    pres = look.get("presenter") if isinstance(look.get("presenter"), dict) else {}
    side = presenter.slot_of(src_project.get("theme") or "", f, look)
    if side and pres.get(side) and not f.get("plate_img"):
        f["plate_img"] = pres[side]
    return f


def blank(plate: str, tk_frames: list) -> dict:
    """A starting template on one of the kit's presenter photos: a heading and a line of text to restyle."""
    if plate == "fss":         # full screen: white grid, dark words
        html = ("<div class='abs' data-name='Heading' style='left:130px;top:140px;font-size:84px;font-weight:700;color:#222222;"
                "letter-spacing:-1px;white-space:nowrap'>Your <span style='color:#387ED1'>heading</span></div>"
                "<div class='abs' data-name='Text' style='left:130px;top:320px;font-size:48px;color:#424242;line-height:1.3;"
                "max-width:1500px'>A line of text that changes in every video</div>")
        return {"id": next_id(tk_frames, "t"), "name": f"New template {len(tk_frames) + 1}", "mode": "fss", "decor": {"seed": 2},
                "html": html}
    left = "left" in plate     # presenter on the left: words on the right
    x = 1010 if left else 130
    html = (f"<div class='abs ov' data-name='Heading' style='left:{x}px;top:200px'>"
            "<div data-name='Heading text' style='font-size:84px;letter-spacing:-1px;line-height:1.1;white-space:nowrap'>"
            "Your <span class='y'>heading</span></div><div class='ov-line' data-name='Thin underline' style='width:420px'></div></div>"
            f"<div class='abs ov' data-name='Text' style='left:{x}px;top:420px;font-size:48px;line-height:1.3;max-width:760px'>"
            "A line of text that changes in every video</div>")
    return {"id": next_id(tk_frames, "t"), "name": f"New template {len(tk_frames) + 1}", "mode": "osa", "plate": plate,
            "decor": {"seed": 1, "dark": True}, "html": html}


# ---------------------------------------------------------------- using a template in a video
def place(project: dict, template: dict, tk_look: dict, lines: list, text: str, src: str) -> tuple[dict, str]:
    """The video's spec with a copy of the template for script lines [a, b] (inclusive), at its place in the order.
    Returns (spec, new frame id)."""
    import presenter
    spec = copy.deepcopy(project.get("spec") or {})
    frames = [f for f in (spec.get("frames") or []) if isinstance(f, dict)]
    f = copy.deepcopy(template)
    f["id"] = next_id(frames, "tk")
    f["tk_from"] = str(template.get("id"))
    f["name"] = template.get("name") or ""
    f["vo"] = (text or "").strip()
    a, b = int(lines[0]), int(lines[-1])
    f["lines"], f["lines_src"] = [a, b], src or "script"
    pres = (tk_look or {}).get("presenter") if isinstance((tk_look or {}).get("presenter"), dict) else {}
    side = presenter.slot_of(project.get("theme") or "", f)
    if side and pres.get(side) and not f.get("plate_img"):
        f["plate_img"] = pres[side]          # the template's own photo, unless this video uploads one for that side
    # a frame that already sits on these lines loses them (the toolkit frame takes its place)
    at = len(frames)
    for i, g in enumerate(frames):
        gl = g.get("lines")
        if isinstance(gl, list) and len(gl) == 2 and gl[0] > b:
            at = i
            break
    frames.insert(at, f)
    spec["frames"] = frames
    return spec, f["id"]


# ---------------------------------------------------------------- "Generate the rest"
REST_NOTE = ("Some script lines already have a frame picked from the team's toolkit. They are marked "
             "[[ALREADY A FRAME: ...]] in the script. Do NOT make frames for those lines: make frames only for the other "
             "lines, in script order, and put the lines each frame covers in its \"vo\" field. Frame ids must not start "
             "with \"tk\".")


def marked_script(lines: list[str], covered: set[int]) -> str:
    out = []
    for i, ln in enumerate(lines):
        if i in covered and ln.strip():
            out.append(f"[[ALREADY A FRAME: {ln.strip()}]]")
        else:
            out.append(ln)
    return "\n".join(out)


def _line_of(vo: str, lines: list[str], start: int) -> int | None:
    """Index of the script line where this frame's words begin (searching from `start`)."""
    w = _norm(vo).split()[:6]
    if not w:
        return None
    probe = " ".join(w[:4])
    for i in range(start, len(lines)):
        if probe and probe in _norm(lines[i]):
            return i
    for i in range(start, len(lines)):
        n = _norm(lines[i])
        if n and sum(x in n.split() for x in w) >= max(2, len(w) // 2):
            return i
    return None


def merge_rest(kept: list[dict], new: list[dict], lines: list[str], src: str) -> list[dict]:
    """Toolkit frames + newly generated frames, in script order, each with the lines it covers."""
    covered = set()
    for f in kept:
        a, b = f["lines"]
        covered.update(range(a, b + 1))
    placed, cursor = [], 0
    for f in new:
        vo = f.get("vo") or ""
        i = _line_of(vo, lines, cursor)
        if i is None:
            i = _line_of(vo, lines, 0)
        if i is not None and i in covered:       # Claude made a frame for a toolkit line anyway: drop it
            continue
        if i is None:
            i = cursor
        cursor = max(cursor, i)
        placed.append((i, f))
    allf = [(f["lines"][0], 0, f) for f in kept] + [(i, 1, f) for i, f in placed]
    allf.sort(key=lambda t: (t[0], t[1]))
    out = [f for _, _, f in allf]
    starts = [t[0] for t in allf]
    n = len(lines)
    for k, (s, kind, f) in enumerate(allf):
        if kind == 1:
            e = (starts[k + 1] - 1) if k + 1 < len(starts) else n - 1
            # never run over the next toolkit frame's lines
            while e > s and e in covered:
                e -= 1
            f["lines"], f["lines_src"] = [s, max(s, e)], src
    return out


def pdf_lines(raw: bytes) -> list[str]:
    """A storyboard PDF's text as lines (page headers repeated on every page and very short bits dropped)."""
    import collections
    import fitz
    doc = fitz.open(stream=raw, filetype="pdf")
    pages = [[ln.strip() for ln in (pg.get_text("text") or "").splitlines()] for pg in doc]
    count = collections.Counter(ln for pl in pages for ln in set(pl) if ln)
    rep = {ln for ln, n in count.items() if len(pages) > 2 and n >= max(3, len(pages) * 0.6)}
    out = []
    for pl in pages:
        for ln in pl:
            if len(ln) >= 3 and ln not in rep and not re.fullmatch(r"[\d\s:.\-–|/]+", ln):
                out.append(ln)
    return out[:1500]


# ---------------------------------------------------------------- PSD -> template
def psd_to_template(raw: bytes, theme: str, tk_frames: list, store) -> dict:
    """A template from a layered PSD: the biggest picture layer at the bottom is the presenter photo; text layers
    become editable text; shape layers become boxes; other picture layers become pictures. `store(desc, bytes, ext)`
    saves a picture and returns its asset path."""
    import io
    from psd_tools import PSDImage
    psd = PSDImage.open(io.BytesIO(raw))
    W, H = psd.width, psd.height
    sx, sy = 1920 / W, 1080 / H
    layers = [l for l in psd.descendants() if l.is_visible() and not l.is_group()]
    if not layers:
        raise ValueError("the PSD has no visible layers")
    area = lambda l: max(0, (l.bbox[2] - l.bbox[0])) * max(0, (l.bbox[3] - l.bbox[1]))
    from PIL import Image
    # the photo: the full-frame picture layers at the bottom (background colour, presenter photo, a shade over it)
    base = []
    for l in layers:                          # bottom to top
        if l.kind in ("pixel", "smartobject", "solidcolorfill", "gradientfill", "patternfill") and area(l) >= 0.6 * W * H:
            base.append(l)
        else:
            break
    photo = base[-1] if base else None
    photo_rel = None
    if base:
        canvas = Image.new("RGBA", (W, H), (17, 17, 17, 255))
        for l in base:
            im = (l.composite() if hasattr(l, "composite") else l.topil()).convert("RGBA")
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); layer.paste(im, (l.bbox[0], l.bbox[1]))
            canvas = Image.alpha_composite(canvas, layer)
        canvas = canvas.convert("RGB").resize((1920, 1080))
        b = io.BytesIO(); canvas.save(b, "JPEG", quality=90)
        photo_rel = store(f"toolkit psd photo {len(raw)} {photo.name}", b.getvalue(), "jpg")
    parts, ink = [], []
    for l in layers:
        if l in base:
            continue
        x0, y0, x1, y1 = l.bbox
        if x1 <= x0 or y1 <= y0:
            continue
        L, T, Wd, Ht = round(x0 * sx), round(y0 * sy), round((x1 - x0) * sx), round((y1 - y0) * sy)
        raw_name = re.sub(r"[<>]", "", (l.name or "").replace("'", "’")).strip()
        kind = "Text" if l.kind == "type" else "Shape" if l.kind == "shape" else "Picture"
        name = f"{kind}: {raw_name or kind}"[:60]   # the editor's layer list shows the kind and the PSD layer's name
        if l.kind == "type":
            t = _type_info(l)
            txt = (t["text"] or "").replace("\r", "\n").strip()
            if not txt:
                continue
            body = "<br>".join(_esc(s) for s in txt.split("\n"))
            parts.append(f"<div class='abs' data-name='{name}' style='left:{L}px;top:{T}px;font-size:{round(t['size'] * sy)}px;"
                         f"font-weight:{t['weight']};color:{t['color']};line-height:1.15;white-space:nowrap'>{body}</div>")
            ink.append((L, Wd))
        elif l.kind == "shape":
            fill, stroke, sw = _shape_info(l)
            r = min(Ht // 2, 24)
            st = f"left:{L}px;top:{T}px;width:{Wd}px;height:{Ht}px;border-radius:{r}px;background:{fill or 'transparent'}"
            if stroke:
                st += f";border:{max(1, round(sw * sx))}px solid {stroke};box-sizing:border-box"
            parts.append(f"<div class='abs' data-name='{name}' style='{st}'></div>")
        else:
            im = l.composite() if hasattr(l, "composite") else l.topil()
            if im is None:
                continue
            b = io.BytesIO(); im.save(b, "PNG")
            rel = store(f"toolkit psd layer {len(raw)} {l.name} {x0},{y0}", b.getvalue(), "png")
            parts.append(f"<img class='abs' data-name='{name}' src='../assets/{rel}' style='left:{L}px;top:{T}px;width:{Wd}px;height:{Ht}px'>")
            ink.append((L, Wd))
    # which side is the presenter on? words on the left -> presenter on the right
    mid = sum(x + w / 2 for x, w in ink) / len(ink) if ink else 400
    plate = "m2_right" if mid < 960 else "m2_left"
    f = {"id": next_id(tk_frames, "t"), "name": "", "mode": "osa" if photo_rel else "fss", "decor": False,
         "html": "".join(parts)}
    if photo_rel:
        f["plate"], f["plate_img"] = plate, photo_rel
    return f


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _rgb(c) -> str | None:
    try:
        v = [float(x) for x in c]
        if len(v) == 4:      # psd engine data: [a, r, g, b] in 0..1
            v = v[1:]
        if max(v) <= 1.0:
            v = [x * 255 for x in v]
        return "#%02X%02X%02X" % tuple(int(round(x)) for x in v[:3])
    except Exception:
        return None


def _type_info(l) -> dict:
    out = {"text": getattr(l, "text", "") or "", "size": 48.0, "color": "#FFFFFF", "weight": 600}
    try:
        ed = l.engine_dict
        rs = ed["StyleRun"]["RunArray"][0]["StyleSheet"]["StyleSheetData"]
        size = float(rs.get("FontSize", 48))
        try:
            t = l.transform     # (xx, xy, yx, yy, tx, ty): text scaled by its transform
            size *= abs(float(t[3])) or 1.0
        except Exception:
            pass
        out["size"] = size
        fc = rs.get("FillColor", {}).get("Values")
        if fc is not None:
            out["color"] = _rgb(list(fc)) or out["color"]
        fonts = l.resource_dict["FontSet"]
        fi = int(rs.get("Font", 0))
        fname = str(fonts[fi]["Name"]).strip("'\"\x00").lower()
        out["weight"] = 800 if "extrabold" in fname or "black" in fname else 700 if "bold" in fname and "semi" not in fname \
            else 600 if "semibold" in fname or "medium" in fname else 400
    except Exception:
        pass
    return out


def _shape_info(l):
    fill = stroke = None
    sw = 0.0
    try:
        sc = l.tagged_blocks.get_data(b"SoCo")
        if sc:
            c = sc.get(b"Clr ")
            fill = _rgb([c.get(b"Rd  ", 0), c.get(b"Grn ", 0), c.get(b"Bl  ", 0)])
    except Exception:
        pass
    try:
        st = l.stroke
        if st and st.enabled:
            sw = float(st.line_width)
            c = st.content.get(b"Clr ") if hasattr(st.content, "get") else None
            if c is not None:
                stroke = _rgb([c.get(b"Rd  ", 0), c.get(b"Grn ", 0), c.get(b"Bl  ", 0)])
    except Exception:
        pass
    if fill is None and stroke is None:
        fill = "#FFFFFF"
    return fill, stroke, sw

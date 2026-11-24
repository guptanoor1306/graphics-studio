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

THEMES_WITH_TOOLKIT = ("zo-product-graphics", "zo-ipo-graphics")
NAME = {"zo-product-graphics": "Toolkit · ZO Product", "zo-ipo-graphics": "Toolkit · ZO IPO"}


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
             "[[ALREADY A FRAME: ...]] in the script. Lines marked [[NO FRAME: ...]] need no graphic at all. Do NOT make "
             "frames for either kind: make frames only for the other lines, in script order, and put the lines each "
             "frame covers in its \"vo\" field. Frame ids must not start with \"tk\".")


def marked_script(lines: list[str], covered: set[int], skip: set[int] | None = None) -> str:
    out, skip = [], skip or set()
    for i, ln in enumerate(lines):
        if i in covered and ln.strip():
            out.append(f"[[ALREADY A FRAME: {ln.strip()}]]")
        elif i in skip and ln.strip():
            out.append(f"[[NO FRAME: {ln.strip()}]]")
        else:
            out.append(ln)
    return "\n".join(out)


def carry(old: dict | None, new: dict | None) -> None:
    """Keep the video's "no frame needed" marks when its frames are made again."""
    if isinstance(old, dict) and isinstance(new, dict) and old.get("tk_skip") is not None and "tk_skip" not in new:
        new["tk_skip"], new["tk_skip_src"] = old.get("tk_skip"), old.get("tk_skip_src")


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


def merge_rest(kept: list[dict], new: list[dict], lines: list[str], src: str, skip: set[int] | None = None) -> list[dict]:
    """Toolkit frames + newly generated frames, in script order, each with the lines it covers.
    Lines marked "no frame needed" (skip) are left out: a new frame never starts on or runs over them."""
    covered = set()
    for f in kept:
        a, b = f["lines"]
        covered.update(range(a, b + 1))
    covered |= set(skip or ())
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


_PDF_HEADS = {"script", "graphics", "graphic", "visual", "visuals", "vo", "voiceover", "voice over", "notes", "note",
              "scene", "time", "timestamp", "timecode", "audio", "video", "on screen", "on-screen text", "b-roll",
              "broll", "shot", "description", "remarks", "reference", "references", "sl no", "s.no", "sr no"}


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
            if (len(ln) >= 3 and ln not in rep and not re.fullmatch(r"[\d\s:.\-–|/]+", ln)
                    and not re.match(r"(https?://|www\.)\S+$", ln) and ln.lower().rstrip(":") not in _PDF_HEADS):
                out.append(ln)
    return out[:1500]


# ---------------------------------------------------------------- PSD -> template
# Imported as is: every layer that is not text is the PSD's own pixels (rendered by psd-tools, effects included) at
# its exact place, so shapes, icons, cursors and strokes look exactly like Photoshop. Only text layers are rebuilt as
# live text (font, size, weight, colour, tracking, coloured words) so their words can be changed.
INTER_ASC, INTER_H = 0.96875, 1.2109375          # Inter's ascent and content height (em): baseline placement
WEIGHTS = (("thin", 100), ("extralight", 200), ("ultralight", 200), ("light", 300), ("regular", 400), ("book", 400),
           ("medium", 500), ("semibold", 600), ("demibold", 600), ("extrabold", 800), ("ultrabold", 800),
           ("bold", 700), ("black", 900), ("heavy", 900))


def _font_css(ps_name: str) -> tuple[str, int, bool]:
    n = str(ps_name or "").strip("'\"\x00")
    fam, _, style = n.partition("-")
    st = style.lower().replace(" ", "")
    w = next((v for k, v in WEIGHTS if k in st), 400)
    fam = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", fam)
    fam = re.sub(r"\s*(PSMT|PS|MT|Std|Pro)$", "", fam).strip() or "Inter"
    return fam, w, "italic" in st or "oblique" in st


def psd_to_template(raw: bytes, theme: str, tk_frames: list, store) -> dict:
    """A template from a layered PSD. `store(desc, bytes, ext)` saves a picture and returns its asset path."""
    import io
    from PIL import Image
    from psd_tools import PSDImage
    psd = PSDImage.open(io.BytesIO(raw))
    W, H = psd.width, psd.height
    sx, sy = 1920 / W, 1080 / H
    full = (0, 0, W, H)
    layers = [l for l in psd.descendants() if not l.is_group() and l.is_visible()]
    if not layers:
        raise ValueError("the PSD has no visible layers")
    area = lambda l: max(0, l.bbox[2] - l.bbox[0]) * max(0, l.bbox[3] - l.bbox[1])

    def render(l):
        """The layer alone on a transparent canvas the size of the PSD, effects included."""
        im = None
        try:
            im = l.composite(viewport=full)
        except Exception:
            im = None
        if im is None:
            try:
                px = l.topil()
                if px is not None:
                    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); im.paste(px.convert("RGBA"), l.offset)
            except Exception:
                im = None
        return im.convert("RGBA") if im is not None else None

    base = []
    for l in layers:                          # bottom to top: the full-frame background layers
        if l.kind != "type" and area(l) >= 0.6 * W * H:
            base.append(l)
        else:
            break
    photo_rel = None
    if base:
        canvas = Image.new("RGBA", (W, H), (17, 17, 17, 255))
        for l in base:
            im = render(l)
            if im is not None:
                canvas = Image.alpha_composite(canvas, im)
        canvas = canvas.convert("RGB").resize((1920, 1080), Image.LANCZOS)
        b = io.BytesIO(); canvas.save(b, "JPEG", quality=92)
        photo_rel = store(f"toolkit psd photo {len(raw)} {base[-1].name}", b.getvalue(), "jpg")
    parts, ink = [], []
    for n, l in enumerate(layers):
        if l in base:
            continue
        raw_name = re.sub(r"[<>]", "", (l.name or "").replace("'", "’")).strip()
        if l.kind == "type":
            h, x = _text_html(l, sx, sy, raw_name)
            if h:
                parts.append(h); ink.append(x)
            continue
        im = render(l)
        if im is None:
            continue
        bb = im.getbbox()
        if not bb:
            continue
        crop = im.crop(bb)
        L, T = round(bb[0] * sx), round(bb[1] * sy)
        Wd, Ht = max(1, round((bb[2] - bb[0]) * sx)), max(1, round((bb[3] - bb[1]) * sy))
        if (sx, sy) != (1, 1):
            crop = crop.resize((Wd, Ht), Image.LANCZOS)
        b = io.BytesIO(); crop.save(b, "PNG", optimize=True)
        rel = store(f"toolkit psd layer {len(raw)} {n} {l.name}", b.getvalue(), "png")
        kind = "Shape" if l.kind == "shape" else "Picture"
        name = f"{kind}: {raw_name or kind}"[:60]
        parts.append(f"<img class='abs' data-name='{name}' src='../assets/{rel}' style='left:{L}px;top:{T}px;width:{Wd}px;height:{Ht}px'>")
        ink.append(L + Wd / 2)
    mid = sum(ink) / len(ink) if ink else 400
    plate = "m2_right" if mid < 960 else "m2_left"
    f = {"id": next_id(tk_frames, "t"), "name": "", "mode": "osa" if photo_rel else "fss", "decor": False, "as_is": True,
         "html": "".join(parts)}
    if photo_rel:
        f["plate"], f["plate_img"] = plate, photo_rel
        f["shade"] = "display:none"      # the PSD's own look: no extra shade over its background
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


def _text_html(l, sx, sy, raw_name):
    """A PSD text layer as live text: runs keep their own colour/size/weight; placed on the PSD's baseline."""
    try:
        ed = l.engine_dict
        tv = ed["Editor"]["Text"]
        text = str(getattr(tv, "value", tv)).replace("\r", "\n").rstrip("\n")
        runs = ed["StyleRun"]
        lens = [int(x) for x in runs["RunLengthArray"]]
        sheets = [r["StyleSheet"]["StyleSheetData"] for r in runs["RunArray"]]
        fonts = l.resource_dict["FontSet"]
        try:
            just = int(ed["ParagraphRun"]["RunArray"][0]["ParagraphSheet"]["Properties"].get("Justification", 0))
        except Exception:
            just = 0
        try:
            shp = ed["Rendered"]["Shapes"]["Children"][0]
            box = int(shp["ShapeType"]) == 1
            bounds = [float(v) for v in shp["Cookie"]["Photoshop"]["BoxBounds"]] if box else None
        except Exception:
            box, bounds = False, None
    except Exception:
        text, lens, sheets, fonts, just, box, bounds = (getattr(l, "text", "") or ""), [], [], [], 0, False, None
    if not text.strip():
        return None, 0
    try:
        t = l.transform
        scale, xscale = abs(float(t[3])) or 1.0, abs(float(t[0])) or 1.0
        tx, ty = float(t[4]), float(t[5])
    except Exception:
        scale, xscale, tx, ty, box, bounds = 1.0, 1.0, float(l.bbox[0]), float(l.bbox[1]), True, None

    def style(sh):
        size = float(sh.get("FontSize", 48)) * scale * sy
        fn = fonts[int(sh.get("Font", 0))]["Name"] if fonts else "Inter-Regular"
        fam, w, it = _font_css(str(getattr(fn, "value", fn)))
        if sh.get("FauxBold"):
            w = max(w, 700)
        col = _rgb(list(sh.get("FillColor", {}).get("Values", [1, 1, 1, 1]))) or "#FFFFFF"
        tr = float(sh.get("Tracking", 0) or 0) / 1000
        lead = None if sh.get("AutoLeading", True) else float(sh.get("Leading", 0) or 0) * scale * sy
        caps = int(sh.get("FontCaps", 0) or 0)
        return {"size": size, "fam": fam, "w": w, "it": it, "col": col, "tr": tr, "lead": lead, "caps": caps}

    sts = [style(sh) for sh in sheets] or [style({})]
    first = sts[0]
    fs = first["size"]
    lh = (first["lead"] / fs) if first["lead"] else 1.2
    # the text, run by run (a coloured word is a span inside the one text layer)
    body, pos = [], 0
    for ln, st in zip(lens or [len(text)], sts):
        seg = text[pos:pos + ln]; pos += ln
        if not seg:
            continue
        h = _esc(seg).replace("\n", "<br>")
        diff = []
        if st["col"] != first["col"]:
            diff.append(f"color:{st['col']}")
        if abs(st["size"] - fs) > 0.5:
            diff.append(f"font-size:{round(st['size'])}px")
        if st["w"] != first["w"]:
            diff.append(f"font-weight:{st['w']}")
        body.append(f"<span style='{';'.join(diff)}'>{h}</span>" if diff else h)
    html_text = "".join(body).replace("\n", "<br>")
    # where: point text sits on its baseline (tx, ty); a text box fills its box, aligned as in Photoshop
    ascent = ((lh - INTER_H) / 2 + INTER_ASC) * fs
    align = {1: "right", 2: "center"}.get(just, "left")
    width = ""
    if box and bounds:
        # BoxBounds is [left, top, right, bottom] in the text's own units
        left = (tx + bounds[0] * xscale) * sx
        top = (ty + bounds[1] * scale) * sy
        squeeze = xscale / scale
        bw = (bounds[2] - bounds[0]) * xscale * sx
        if abs(squeeze - 1) > 0.02:            # horizontally scaled type: draw it narrower, not reflowed
            width = (f"width:{round(bw / squeeze)}px;text-align:{align};"
                     f"transform:scaleX({squeeze:.3f});transform-origin:0 0;")
        else:
            width = f"width:{round(bw)}px;text-align:{align};"
    else:
        left = l.bbox[0] * sx - 0.04 * fs
        top = ty * sy - ascent if not box else l.bbox[1] * sy
    css = (f"left:{round(left)}px;top:{round(top)}px;{width}font-family:&quot;{first['fam']}&quot;,Inter,sans-serif;font-size:{round(fs)}px;"
           f"font-weight:{first['w']};color:{first['col']};line-height:{lh:.3f};white-space:" + ("pre-wrap" if width else "pre"))
    if first["it"]:
        css += ";font-style:italic"
    if first["caps"] == 1:
        css += ";font-variant:small-caps"
    elif first["caps"] == 2:
        css += ";text-transform:uppercase"
    if first["tr"]:
        css += f";letter-spacing:{first['tr']:.3f}em"
    name = f"Text: {raw_name or text.strip()[:40]}"[:60]
    return f"<div class='abs' data-name='{name}' style='{css}'>{html_text}</div>", (l.bbox[0] + l.bbox[2]) / 2 * sx

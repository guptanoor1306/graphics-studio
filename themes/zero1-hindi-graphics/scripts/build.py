#!/usr/bin/env python3
"""Zero1 Hindi IP graphics builder.

spec.json  ->  one HTML per frame  ->  1920x1080 PNG (Playwright/Chromium)
            ->  _sheet_N.jpg contact sheets, _text.txt, _image_prompts.md, WARN lines
            ->  --package NAME : NAME.zip with flat PNG/ and HTML/ (self-contained HTML)

Usage:
  python3 build.py spec.json --out out [--only 0.12,1.05] [--package Ep04_Gold_graphics]
"""
import argparse, base64, html, json, mimetypes, os, re, shutil, sys, zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
CSS = KIT / "templates" / "z1.css"
PALETTE = {"red": "#B23636", "ink": "#1F1F1F", "black": "#000000", "gold": "#E0A422", "blue": "#447599",
           "tblue": "#30749B", "teal": "#127FA6", "navy": "#083061", "white": "#FFFFFF", "grey": "#777777",
           "yellow": "#F2C66D", "tagbrown": "#592D25", "xblue": "#9EC3D6", "olive": "#A39E66", "sand": "#DAB08D"}
PIE = ["#C0533F", "#317E76", "#1E404C", "#F5D8AE", "#E0A43A", "#CFE6DE"]
BACKDROPS = {"sky": "asset:backdrops/sky_paper.jpg", "paper": "asset:backdrops/plain_paper.jpg",
             "desk": "asset:backdrops/desk_gridpaper.jpg"}
WARN = []
SPELL = {}

# ---------------------------------------------------------------- image prompts (Magnific / any image model)
WORLD = ("Handcrafted miniature diorama photographed in a studio, tactile stop-motion feel: buildings, props and "
         "ground are clay, wood, card and fabric miniatures with soft rounded edges. Warm golden-hour light, soft shadows, "
         "shallow depth of field, rich but natural colours, authentic Indian regional details. "
         "No text, no letters, no numbers, no logos, no watermark.")
FIGURES = ("Every person is a blocky wooden toy figure: rectangular light-wood block head with visible grain, two small "
           "vertical black oval eyes, no nose, no mouth unless an expression is requested, hair of layered black "
           "cut-paper/cardstock fringe (women: long black cut-paper hair, bun or braid), jointed wooden block arms with "
           "mitten hands, grey-silver block shoes, clothes of real fabric and felt. Never Lego minifigures, never smooth "
           "plastic faces, never realistic humans.")
STYLE = WORLD
CUTOUT = (" Isolated on a plain pure white background, full object visible with a small patch of ground under it, "
          "soft contact shadow, nothing else in frame (for cut-out).")
ARJUN = {
    "city": "ARJUN: 30-year-old salaried man, red short-sleeve t-shirt with a front kangaroo pouch pocket, wooden block legs.",
    "kerala": "ARJUN (Kerala): red half-sleeve shirt, white mundu with thin gold kasavu border, wooden sandals.",
    "andhra": "ARJUN (Andhra Pradesh): white shirt, cream angavastram with gold stripes over shoulders, white dhoti with gold border.",
    "meghalaya": "ARJUN (Meghalaya, Khasi): red-and-yellow turban, black embroidered Khasi jacket, red dhoti-pants, red bead necklace, yellow sash.",
}
EXPR = {"neutral": "", "worried": " Expression: raised worried eyebrows and a small down-turned mouth, one hand scratching his head.",
        "happy": " Expression: small curved smile, relaxed eyebrows.", "thinking": " Expression: one hand on chin, eyes looking up.",
        "aged": " Older: greying hair fringe, grey moustache, slight stoop.", "crying": " Tears as small glossy drops under the oval eyes, small smile."}


def prompt_text(key, g, default_arjun):
    p = g.get("prompt", "").strip()
    who = g.get("arjun")
    parts = [p.rstrip(".") + "."]
    if who is not None:
        parts.append(ARJUN.get(who or default_arjun, ARJUN["city"]) + EXPR.get(g.get("expr", "neutral"), ""))
    if who is not None or g.get("people"):
        parts.append(FIGURES)
    parts.append(WORLD)
    if g.get("cutout"):
        parts.append(CUTOUT)
    ar = g.get("aspect", "16:9")
    return " ".join(x for x in parts if x), ar


# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(str(s), quote=False)


def md(s, accent="red"):
    """*x* -> accent colour, _x_ -> italic, **x** -> bold, \\n -> line break."""
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\*(.+?)\*", rf'<span class="{accent}">\1</span>', s)
    s = re.sub(r"(?<![\w/])_(.+?)_(?!\w)", r"<em>\1</em>", s)
    return s.replace("\n", "<br>")


def color(c, default="ink"):
    c = c or default
    if c in PALETTE:
        return PALETTE[c]
    if c.upper() in [v.upper() for v in PALETTE.values()] or c.upper() in [v.upper() for v in PIE]:
        return c
    WARN.append(f"colour {c} is outside the house palette")
    return c


PLATE_SHEETS = KIT / "assets" / "plate_sheets"


def plates_dir():
    """Plates ship tiled 4-per-sheet (skill uploads allow max 200 files, no nested archives).
    Cut them out once into a writable cache and return that folder."""
    mp = PLATE_SHEETS / "map.json"
    if not mp.exists():
        return None
    m = json.loads(mp.read_text())
    cands = [Path(os.environ["ZERO1_PLATES"])] if os.environ.get("ZERO1_PLATES") else []
    cands += [KIT / "assets" / "plates", Path.home() / ".cache" / "zero1_plates", Path("/tmp/zero1_plates")]
    for d in cands:
        if d.is_dir() and len(list(d.glob("*.jpg"))) >= len(m):
            return d
    from PIL import Image
    for d in cands:
        try:
            d.mkdir(parents=True, exist_ok=True)
            sheets = {}
            for name, (sheet, x, y, w, h) in m.items():
                if sheet not in sheets:
                    sheets[sheet] = Image.open(PLATE_SHEETS / sheet).convert("RGB")
                sheets[sheet].crop((x, y, x + w, y + h)).save(d / name, quality=92)
            return d
        except OSError:
            continue
    return None


class Ctx:
    def __init__(self, spec_dir, out_dir):
        self.spec_dir, self.out_dir = Path(spec_dir), Path(out_dir)
        self.pending = []

    def src(self, ref):
        """returns (absolute path or None, gen key or None)"""
        if ref is None:
            return None, None
        ref = BACKDROPS.get(ref, ref)
        if ref.startswith("asset:plates/"):
            pd = plates_dir()
            p = (pd / ref[len("asset:plates/"):]) if pd else None
            if p is None or not p.exists():
                WARN.append(f"missing plate {ref}")
                return None, None
            return p, None
        if ref.startswith("asset:"):
            p = KIT / "assets" / ref[6:]
            if not p.exists():
                WARN.append(f"missing kit asset {ref}")
                return None, None
            return p, None
        if ref.startswith("gen:"):
            key = ref[4:]
            for ext in (".png", ".jpg", ".jpeg", ".webp"):
                p = self.spec_dir / "gen" / (key + ext)
                if p.exists():
                    return p, key
            self.pending.append(key)
            return None, key
        p = (self.spec_dir / ref)
        if not p.exists():
            WARN.append(f"missing image {ref}")
            return None, None
        return p, None

    def url(self, p):
        return Path(os.path.relpath(p, self.out_dir / "html")).as_posix()


def ph(key, x, y, w, h, gen):
    g = gen.get(key, {}) if key else {}
    txt = esc(g.get("prompt", "image to generate"))[:220]
    return (f'<div class="ph" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"><div><b>GEN: {esc(key)}</b>{txt}</div></div>')


def img_layer(ctx, gen, l):
    x, y, w = l.get("x", 0), l.get("y", 0), l.get("w", 400)
    p, key = ctx.src(l.get("img"))
    cls = "L" + (" shadow" if l.get("shadow") else "") + (f" {l['look']}" if l.get("look") else "")
    st = f"left:{x}px;top:{y}px;width:{w}px;"
    if l.get("rot"):
        st += f"transform:rotate({l['rot']}deg);"
    if l.get("flip"):
        st += "transform:scaleX(-1);"
    if l.get("opacity") is not None:
        st += f"opacity:{l['opacity']};"
    if l.get("z") is not None:
        st += f"z-index:{l['z']};"
    if p is None:
        return ph(key, x, y, w, l.get("h", int(w * 0.75)), gen)
    return f'<div class="{cls}" style="{st}"><img src="{ctx.url(p)}"></div>'


def text_layer(l, dark=False):
    font = l.get("font", "br")
    size = l.get("size", 50)
    wt = l.get("weight", 400 if font == "br" else 400)
    col = color(l.get("color", "white" if dark else ("ink")))
    st = f"left:{l.get('x', 0)}px;top:{l.get('y', 0)}px;font-size:{size}px;font-weight:{wt};color:{col};"
    if l.get("w"):
        st += f"width:{l['w']}px;"
    if l.get("align"):
        st += f"text-align:{l['align']};"
    if l.get("italic"):
        st += "font-style:italic;"
    if l.get("rot"):
        st += f"transform:rotate({l['rot']}deg);"
    if l.get("z") is not None:
        st += f"z-index:{l['z']};"
    if l.get("opacity") is not None:
        st += f"opacity:{l['opacity']};"
    cls = "imp" if font == "imp" else "br"
    return f'<div class="L t {cls}" style="{st}">{md(l["text"], "gold" if dark else "red")}</div>'


def layers(ctx, gen, ls, dark=False):
    out = []
    for l in ls or []:
        if "img" in l:
            out.append(img_layer(ctx, gen, l))
        elif "text" in l:
            out.append(text_layer(l, dark))
        elif "arrow" in l:
            out.append(arrow_svg(*l["arrow"], curve=l.get("curve", 0), dashed=l.get("dashed", False), col=l.get("color", "ink")))
        elif "rect" in l:
            x, y, w, h = l["rect"]
            out.append(f'<div class="L" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{color(l.get("color","xblue"))};opacity:{l.get("opacity",.55)};border-radius:{l.get("radius",0)}px"></div>')
        elif "dot" in l:
            x, y = l["dot"]
            out.append(f'<div class="dot" style="left:{x-26}px;top:{y-26}px;width:52px;height:52px;background:{color(l.get("color","red"))}"></div>')
    return "\n".join(out)


def arrow_svg(x1, y1, x2, y2, curve=0, dashed=False, col="ink", width=4):
    c = color(col)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    cx, cy = mx - dy * curve, my + dx * curve
    da = 'stroke-dasharray="10 10"' if dashed else ""
    mid = f"m{abs(hash((x1,y1,x2,y2)))%9999}"
    return (f'<svg class="ov"><defs><marker id="{mid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker></defs>'
            f'<path d="M{x1},{y1} Q{cx},{cy} {x2},{y2}" fill="none" stroke="{c}" stroke-width="{width}" {da} marker-end="url(#{mid})"/></svg>')


def background(ctx, gen, f):
    bg = f.get("bg", "sky")
    look = None
    if isinstance(bg, dict):
        look, bg = bg.get("look"), bg.get("img")
    if bg == "dark":
        return '<div class="bg" style="background:#191610"></div>', True
    p, key = ctx.src(bg)
    dark = look in ("dark", "blur")
    if p is None:
        h = ph(key, 0, 0, 1920, 1080, gen)
        if dark:
            h = h.replace('class="ph"', 'class="ph" ').replace('style="', 'style="background:#2a2620;color:#8a8170;', 1)
        return h, dark
    cls = "bg" + (f" {look}" if look else "")
    return f'<div class="{cls}" style="background-image:url(\'{ctx.url(p)}\')"></div>', dark


# ---------------------------------------------------------------- frame types
def t_scene(ctx, gen, f, dark):
    return ""


def t_chapter(ctx, gen, f, dark):
    x, y = f.get("pos", [139, 170])
    size = f.get("size", 139)
    kick = f.get("kicker", f"Chapter-{f.get('n', 1)}")
    scrim = ""
    if f.get("scrim"):
        scrim = '<div class="L" style="left:0;top:0;width:1300px;height:1080px;background:linear-gradient(90deg,rgba(245,245,243,.92),rgba(245,245,243,.75) 55%,rgba(245,245,243,0))"></div>'
    col = "#FFFFFF" if dark else "#070707"
    return (scrim + f'<div class="L t br" style="left:{x+2}px;top:{y}px;font-size:{int(size*0.39)}px;font-weight:300;font-style:italic;color:{col}">{esc(kick)}</div>'
            f'<div class="L t imp" style="left:{x}px;top:{y+int(size*0.52)}px;font-size:{size}px;color:{col};width:{f.get("w",1500)}px">{md(f["title"])}</div>')


def t_word(ctx, gen, f, dark):
    size = f.get("size", 300)
    col = color(f.get("color", "gold" if dark else "red"))
    font = f.get("font", "imp")
    cls = "imp" if font == "imp" else "br"
    extra = "font-style:italic;font-weight:500;" if font == "italic" else ""
    x, y = f.get("pos", [None, None])
    pos = f"left:{x}px;top:{y}px;" if x is not None else "left:0;width:1920px;text-align:center;top:%dpx;" % (540 - size * 0.55)
    if x is not None and f.get("w"):
        pos += f"width:{f['w']}px;"
    if f.get("nowrap") or f.get("runoff"):
        pos += "white-space:nowrap;"
    k = ""
    if f.get("kicker"):
        kx = x if x is not None else 0
        kpos = f"left:{kx}px;" if x is not None else "left:0;width:1920px;text-align:center;"
        ky = (y if y is not None else 540 - size * 0.55) - 70
        k = f'<div class="L t br" style="{kpos}top:{ky}px;font-size:54px;color:{"#fff" if dark else "#000"}">{md(f["kicker"])}</div>'
    sub = ""
    if f.get("sub"):
        sy = (y if y is not None else 540 - size * 0.55) + size * 0.98
        spos = f"left:{x}px;" if x is not None else "left:0;width:1920px;text-align:center;"
        sub = f'<div class="L t br" style="{spos}top:{sy}px;font-size:{f.get("sub_size",50)}px;color:{"#fff" if dark else "#000"}">{md(f["sub"], "gold" if dark else "red")}</div>'
    return k + f'<div class="L t {cls}" style="{pos}font-size:{size}px;color:{col};{extra}">{md(f["text"])}</div>' + sub


def t_stat(ctx, gen, f, dark):
    x, y = f.get("pos", [140, 180])
    size = f.get("size", 136)
    col = color(f.get("color", "gold" if dark else "red"))
    lab = f.get("label", "")
    lsize = f.get("label_size", 50)
    lcol = "#FFFFFF" if dark else "#000000"
    al = f.get("align", "left")
    w = f.get("w", 1100)
    left = x if al == "left" else (x - w // 2 if al == "center" else x - w)
    num = f'<div class="L t imp" style="left:{left}px;width:{w}px;text-align:{al};top:{y}px;font-size:{size}px;color:{col}">{md(f["value"])}</div>'
    if not lab:
        return num
    if f.get("label_pos", "below") == "above":
        return (f'<div class="L t br" style="left:{left}px;width:{w}px;text-align:{al};top:{y-lsize*1.25}px;font-size:{lsize}px;color:{lcol}">{md(lab, "gold" if dark else "red")}</div>' + num)
    return num + f'<div class="L t br" style="left:{left}px;width:{w}px;text-align:{al};top:{y+size*0.98}px;font-size:{lsize}px;font-weight:{f.get("label_weight",400)};color:{lcol}">{md(lab, "gold" if dark else "red")}</div>'


def t_timeline(ctx, gen, f, dark):
    size = f.get("size", 150)
    yy = f.get("year_y", 400)
    out = ['<div class="tl-line"></div>']
    if f.get("grid", True):
        gp, _ = ctx.src("asset:props/grid_patch.png")
        out.append(f'<div class="L" style="left:200px;top:{yy - 230}px;width:600px;opacity:.9"><img src="{ctx.url(gp)}"></div>')
    if f.get("curve"):
        pts = f["curve"]["points"]
        d = "M" + " ".join(f"{a},{b}" for a, b in pts[:1]) + " " + " ".join(
            f"Q{pts[i][0]},{pts[i][1]} {(pts[i][0]+pts[i+1][0])/2},{(pts[i][1]+pts[i+1][1])/2}" for i in range(len(pts) - 1)) + f" L{pts[-1][0]},{pts[-1][1]}"
        out.append(f'<svg class="ov"><path d="{d}" fill="none" stroke="#111" stroke-width="4"/></svg>')
        if f["curve"].get("label"):
            lx, ly = pts[-1] if not f["curve"].get("label_at") else f["curve"]["label_at"]
            out.append(f'<div class="L t br" style="left:{lx-105}px;top:{ly-105}px;width:210px;height:210px;border-radius:50%;background:#B23636;color:#fff;font-size:76px;font-weight:600;display:flex;align-items:center;justify-content:center">{esc(f["curve"]["label"])}</div>')
    out.append(f'<div class="tl-dot" style="top:{yy + size*0.45}px"></div>')
    if f.get("year"):
        out.append(f'<div class="L t imp" style="left:228px;top:{yy}px;font-size:{size}px;color:#1F1F1F">{md(f["year"])}</div>')
    if f.get("year_sub"):
        out.append(f'<div class="L t br" style="left:232px;top:{yy+size*1.0}px;font-size:{int(size*0.42)}px;color:#1F1F1F">{md(f["year_sub"])}</div>')
    if f.get("caption"):
        cx, cy = f.get("caption_pos", [760, 900])
        out.append(f'<div class="L t br" style="left:{cx}px;top:{cy}px;font-size:{f.get("caption_size",64)}px;color:#1F1F1F;width:{f.get("caption_w",1100)}px">{md(f["caption"])}</div>')
    return "\n".join(out)


def t_table(ctx, gen, f, dark):
    if f.get("mount") == "desk":
        x, y, w = f.get("x", 390), f.get("y", 230), f.get("w", 1140)
    else:
        x, y, w = f.get("x", 300), f.get("y", 190), f.get("w", 1320)
    desk = f.get("mount", "hung") == "desk"
    fs = f.get("font_size", 40 if desk else 44)
    pad = f.get("pad", int(fs * (1.05 if desk else 0.42)))
    hc = {"blue": "#30749B", "red": "#B23636"}.get(f.get("header", "blue"), color(f.get("header")))
    upto = f.get("upto", len(f["rows"]))
    styles = {int(k): v for k, v in (f.get("row_styles") or {}).items()}
    ncol = max(len(r) for r in f["rows"])
    rows = []
    if f.get("cols"):
        rows.append('<tr class="sub">' + "".join(f'<th style="padding:{pad}px 24px;font-size:{fs*0.86:.0f}px">{md(c)}</th>' for c in f["cols"]) + "</tr>")
    for i, r in enumerate(f["rows"]):
        cls = styles.get(i, "")
        if i >= upto:
            cls += " hidden"
        cells = []
        for j, c in enumerate(r):
            al = "left" if j == 0 else f.get("value_align", "left")
            wt = 300 if (j == 0 and "total" not in cls and "hl" not in cls) else 400
            cells.append(f'<td style="padding:{pad}px 28px;font-size:{fs}px;font-weight:{wt};text-align:{al}">{md(c)}</td>')
        rows.append(f'<tr class="{cls.strip()}">' + "".join(cells) + "</tr>")
    head = f'<tr><th colspan="{ncol}" style="background:{hc};padding:{pad+4}px;font-size:{fs*1.25:.0f}px">{md(f["title"])}</th></tr>' if f.get("title") else ""
    ropes = ""
    if f.get("mount", "hung") == "hung":
        rp, _ = ctx.src("asset:props/rope_segment.png")
        for rx in (x + int(w * 0.13), x + int(w * 0.87)):
            ropes += (f'<div class="L" style="left:{rx-8}px;top:0;width:16px;height:{y+6}px;background:url(\'{ctx.url(rp)}\') repeat-y center top/16px auto"></div>'
                      f'<div class="L" style="left:{rx-11}px;top:{y-14}px;width:22px;height:22px;border-radius:50%;border:4px solid #7a5a32;background:#f3e8d2"></div>')
    return ropes + f'<div class="tbl" style="left:{x}px;top:{y}px;width:{w}px"><table>{head}{"".join(rows)}</table></div>'


def t_idtag(ctx, gen, f, dark):
    p, _ = ctx.src("asset:props/id_tag_hanging_blank.png")
    out = []
    for tg in f["tags"]:
        s = tg.get("scale", 1.0)
        x, top = tg.get("x", 200), tg.get("top", -516)
        out.append(f'<div class="L" style="left:{x}px;top:{top}px;width:{595*s}px"><img src="{ctx.url(p)}"></div>')
        fields = tg["fields"]
        for i, (k, v) in enumerate(fields.items()):
            ly = top + (675 + 45 * i) * s
            out.append(f'<div class="L t br" style="left:{x+49*s}px;top:{ly}px;font-size:{19*s:.0f}px;color:#592D25">{esc(k.upper())}</div>')
            red = k in tg.get("highlight", [])
            vs = 28 if (red and v == "?") else 24
            out.append(f'<div class="L t br" style="left:{x+153*s}px;top:{ly-11*s - (8*s if v=="?" else 0)}px;font-size:{(42 if v=="?" else vs)*s:.0f}px;font-weight:{800 if red else 500};color:{"#B23636" if red else "#000"}">{esc(v)}</div>')
    return "\n".join(out)


def hang_card(x, y, kicker, title, rope_top=0, w=None, title_size=56, kick_size=36, title_color="red", ctxurl=None):
    style = f"left:{x}px;top:{rope_top}px;" + (f"width:{w}px;" if w else "")
    tc = color(title_color)
    k = f'<div class="t br" style="font-size:{kick_size}px;color:#1F1F1F;margin-bottom:6px">{md(kicker)}</div>' if kicker else ""
    return (f'<div class="hang" style="{style}transform:translateX(-50%)"><div class="rope" style="height:{y-rope_top}px"></div><div class="eye"></div>'
            f'<div class="card" style="{"min-width:%dpx" % w if w else ""}">{k}<div class="t imp" style="font-size:{title_size}px;color:{tc}">{md(title)}</div></div></div>')


def t_hangtags(ctx, gen, f, dark):
    out = []
    for tg in f["tags"]:
        out.append(hang_card(tg.get("x", 960), tg.get("y", 230), tg.get("kicker"), tg["title"], tg.get("rope_top", 0), tg.get("w"),
                             tg.get("size", 56 if tg.get("kicker") else 72), tg.get("kicker_size", 36), tg.get("color", "red" if tg.get("kicker") else "black")))
    return "\n".join(out)


def t_placards(ctx, gen, f, dark):
    out = []
    for it in f["items"]:
        out.append(f'<div class="placard" style="left:{it["x"]}px;top:{it["y"]}px;transform:translateX(-50%) rotate({it.get("rot",0)}deg)">'
                   f'<div class="board t" style="font-size:{it.get("size",40)}px;{"width:%dpx" % it["w"] if it.get("w") else ""}">{md(it["text"])}</div>'
                   f'<div class="stake" style="height:{it.get("stake",220)}px"></div></div>')
    return "\n".join(out)


def t_checklist(ctx, gen, f, dark):
    x, y, w = f.get("x", 560), f.get("y", 110), f.get("w", 700)
    n = f.get("checked", 0)
    lis = "".join(f'<li class="t"><span class="box{" on" if i < n else ""}"></span><span>{md(t)}</span></li>' for i, t in enumerate(f["items"]))
    out = [f'<div class="clip" style="left:{x}px;top:{y}px;width:{w}px"><div class="clamp"></div><div class="sheet">'
           f'<div class="t imp" style="font-size:76px;color:#111;margin-bottom:18px">{md(f.get("title","Checklist"))}</div><ul>{lis}</ul></div></div>']
    if f.get("photo"):
        px, py, pw = f.get("photo_pos", [x + w - 120, y + 30, 360])
        p, key = ctx.src(f["photo"])
        inner = f'<img src="{ctx.url(p)}" style="width:{pw}px">' if p else ph(key, 0, 0, pw, int(pw * .8), gen).replace("position:absolute", "position:relative")
        out.append(f'<div class="pol" style="left:{px}px;top:{py}px;transform:rotate(6deg)">{inner}</div>'
                   f'<div class="L" style="left:{px+pw/2-60}px;top:{py-18}px;width:120px;height:38px;background:rgba(240,228,190,.85);transform:rotate(-4deg)"></div>')
    return "\n".join(out)


def t_sop(ctx, gen, f, dark):
    out = []
    frames = ["#E2B33C", "#3A79B0", "#C24A3A", "#2F8A5E"]
    for i, it in enumerate(f["items"]):
        x, y = it["x"], it["y"]
        pw = it.get("w", 230)
        p, key = ctx.src(it.get("img"))
        inner = f'<img src="{ctx.url(p)}" style="width:{pw}px;height:{int(pw*.8)}px;object-fit:cover">' if p else \
            f'<div class="ph" style="position:relative;width:{pw}px;height:{int(pw*.8)}px;font-size:16px">{esc(key or "photo")}</div>'
        out.append(f'<div class="pol" style="left:{x}px;top:{y}px;transform:rotate({it.get("rot", -5 if i%2==0 else 6)}deg);border:10px solid {frames[i%4]}">{inner}</div>')
        out.append(f'<div class="badge" style="left:{x-34}px;top:{y-34}px">{it.get("n", i+1)}.</div>')
        tx, ty = it.get("text_pos", [x + pw + 50, y + 40])
        out.append(f'<div class="L t br" style="left:{tx}px;top:{ty}px;font-size:33px;font-weight:300;color:#040404">{md(it.get("kicker",""))}</div>')
        out.append(f'<div class="L t imp" style="left:{tx}px;top:{ty+40}px;font-size:{it.get("size",54)}px;color:#070707;width:{it.get("tw",460)}px">{md(it["title"])}</div>')
    return "\n".join(out)


def t_news_wall(ctx, gen, f, dark):
    out = []
    items = f["items"]
    for i, it in enumerate(items):
        x = it.get("x", 470 if i % 2 == 0 else 980)
        y = it.get("y", 120 + i * (860 // max(1, len(items))))
        w = it.get("w", 900)
        out.append(f'<div class="L t" style="left:{x}px;top:{y}px;width:{w}px">'
                   f'<div class="br" style="font:700 28px \'Bricolage\';color:#B23636;letter-spacing:.02em;text-align:right;border-bottom:2px solid #333;padding-bottom:4px;margin-bottom:8px">{esc(it["source"])}</div>'
                   f'<div class="br" style="font-size:{it.get("size",46)}px;font-weight:600;color:#000">{md(it["headline"])}</div></div>')
    return "\n".join(out)


def t_article(ctx, gen, f, dark):
    x, y, w = f.get("x", 230), f.get("y", 130), f.get("w", 1460)
    body = esc(f.get("body", ""))
    if f.get("highlight"):
        h = esc(f["highlight"])
        if h not in body:
            WARN.append(f"article highlight not found in body: {f['highlight'][:40]}")
        body = body.replace(h, f"<mark>{h}</mark>")
    out = []
    if f.get("mount", "hung") == "hung":
        rp, _ = ctx.src("asset:props/rope_segment.png")
        for rx in (x + 120, x + w - 120):
            out.append(f'<div class="L" style="left:{rx-8}px;top:0;width:16px;height:{y+30}px;background:url(\'{ctx.url(rp)}\') repeat-y center top/16px auto"></div>')
    date = f'<div class="t imp" style="font-size:52px;color:#777;margin-top:18px">{esc(f["date"])}</div>' if f.get("date") else ""
    out.append(f'<div class="article t" style="left:{x}px;top:{y}px;width:{w}px"><div class="src">{esc(f.get("source",""))}</div><h2 style="font-size:{f.get("title_size",52)}px">{md(f["title"])}</h2><p style="font-size:{f.get("body_size",34)}px">{body}</p>{date}</div>')
    return "\n".join(out)


def t_calc(ctx, gen, f, dark):
    out = []
    x, y = f.get("pos", [980, 300])
    size = f.get("size", 60)
    for i, ln in enumerate(f.get("lines", [])):
        col = color(ln.get("color", "black"))
        out.append(f'<div class="L t br" style="left:{x}px;top:{y + i*size*1.55}px;font-size:{size*0.8:.0f}px;color:{col}">{md(ln["l"])}'
                   f'<span style="font-size:{size}px;font-weight:500;margin-left:18px">{md(ln["r"])}</span></div>')
    if f.get("equation"):
        ans = f.get("answer", "?")
        ac = color(f.get("answer_color", "red" if ans != "?" else "black"))
        afont = "imp" if ans != "?" else "br"
        eqpos = f"left:{x}px;" if f.get("pos") and x else "left:0;width:1920px;text-align:center;"
        out.append(f'<div class="L t br" style="{eqpos}top:{y}px;font-size:{size*1.6:.0f}px;color:#070707;white-space:nowrap">{md(f["equation"])} '
                   f'<span class="{afont}" style="font-size:{size*(3.2 if ans=="?" else 2.0):.0f}px;color:{ac};vertical-align:middle;{"font-weight:600" if ans=="?" else ""}">{md(ans)}</span></div>')
    return "\n".join(out)


def t_dots(ctx, gen, f, dark):
    out = []
    for g in f["groups"]:
        n, cols, d, gap = g["n"], g.get("cols", 5), g.get("d", 44), g.get("gap", 32)
        fill = g.get("filled", n)
        for i in range(n):
            cx, cy = g["x"] + (i % cols) * (d + gap), g["y"] + (i // cols) * (d + gap)
            c = color(g.get("color", "red")) if i < fill else "#FFFFFF"
            border = "" if i < fill else "border:3px solid #999;"
            out.append(f'<div class="dot" style="left:{cx}px;top:{cy}px;width:{d}px;height:{d}px;background:{c};{border}"></div>')
        rows = (n + cols - 1) // cols
        ly = g["y"] + rows * (d + gap) + 10
        gw = cols * (d + gap) - gap
        out.append(f'<div class="L t br" style="left:{g["x"]}px;top:{ly}px;width:{gw}px;text-align:center;font-size:{g.get("label_size",42)}px">{md(g["label"])}</div>')
        if g.get("pct"):
            out.append(f'<div class="L t imp" style="left:{g["x"]}px;top:{ly+60}px;width:{gw}px;text-align:center;font-size:110px;color:{color(g.get("color","red"))}">{esc(g["pct"])}</div>')
    if f.get("sign"):
        sx, sy = f.get("sign_pos", [920, 420])
        out.append(f'<div class="L t imp" style="left:{sx}px;top:{sy}px;font-size:215px">{esc(f["sign"])}</div>')
    if f.get("title"):
        out.append(f'<div class="L t imp" style="left:0;width:1920px;text-align:center;top:{f.get("title_y",150)}px;font-size:100px">{md(f["title"])}</div>')
    return "\n".join(out)


def t_callouts(ctx, gen, f, dark):
    out = []
    for c in f["labels"]:
        st = c.get("style", "pill")
        x, y = c["x"], c["y"]
        if c.get("to"):
            tx, ty = c["to"]
            out.append(f'<svg class="ov"><line x1="{x}" y1="{y}" x2="{tx}" y2="{ty}" stroke="{"#fff" if dark else "#7a2a22"}" stroke-width="3"/>'
                       f'<circle cx="{tx}" cy="{ty}" r="8" fill="#7a2a22"/></svg>')
        if st == "pill":
            out.append(f'<div class="pill t" style="left:{x}px;top:{y}px;transform:translate(-50%,-100%)">{md(c["text"])}</div>')
        elif st == "dpill":
            out.append(f'<div class="dpill t" style="left:{x}px;top:{y}px;transform:translate(-50%,-50%)"><i>{esc(c.get("n",""))}</i>{md(c["text"])}</div>')
        else:  # italic leader label
            out.append(f'<div class="L t br" style="left:{x}px;top:{y}px;transform:translate(-50%,-110%);font-size:{c.get("size",54)}px;font-style:italic;color:{"#fff" if dark else "#070707"}">{md(c["text"])}</div>')
    return "\n".join(out)


def ticklist(items, size=38):
    return "".join(f'<div class="t br" style="font-size:{size}px;color:#1F1F1F;margin:6px 0">{md(t)}<span class="{"ok" if ok else "no"}"></span></div>' for t, ok in items)


def t_compare(ctx, gen, f, dark):
    out = []
    b = f.get("board")
    if b:
        out.append(hang_card(b.get("x", 960), b.get("y", 230), b.get("kicker"), b["title"], 0, None, b.get("size", 56)))
    for side in ("left", "right"):
        s = f.get(side)
        if not s:
            continue
        if s.get("img"):
            out.append(img_layer(ctx, gen, {"img": s["img"], "x": s.get("x"), "y": s.get("y"), "w": s.get("w", 360), "shadow": True}))
        if s.get("list"):
            lx, ly = s.get("list_pos", [s.get("x", 200), s.get("y", 600) - 170])
            out.append(f'<div class="L" style="left:{lx}px;top:{ly}px">{ticklist(s["list"], s.get("size",38))}</div>')
    return "\n".join(out)


def t_hub(ctx, gen, f, dark):
    out = []
    if f.get("title"):
        out.append(f'<div class="L t br" style="left:{f.get("title_x",1056)}px;top:80px;font-size:45px;border-bottom:4px solid #1F1F1F;padding-bottom:2px">{md(f["title"])}</div>')
    c = f["center"]
    cx, cy = c.get("x", 1230), c.get("y", 560)
    out.append(f'<div class="L t" style="left:{cx}px;top:{cy}px;transform:translate(-50%,-50%);background:#127FA6;padding:18px 34px;color:#fff;box-shadow:0 10px 18px rgba(0,0,0,.25)">'
               f'<div class="br" style="font-size:28px">{md(c["label"])}</div><div class="imp" style="font-size:68px">{md(c["value"])}</div></div>')
    for it in f["items"]:
        if it.get("img"):
            out.append(img_layer(ctx, gen, {"img": it["img"], "x": it["x"], "y": it["y"], "w": it.get("w", 240), "shadow": True}))
        lx, ly = it.get("label_pos", [it["x"], it["y"] - 80])
        out.append(f'<div class="L t" style="left:{lx}px;top:{ly}px"><div class="br" style="font-size:27px">{md(it["label"])}</div>'
                   f'<div class="imp red" style="font-size:62px">{md(it["value"])}</div></div>')
    return "\n".join(out)


def t_flow(ctx, gen, f, dark):
    out = []
    items = f["items"]
    n = len(items)
    w = f.get("w", 300)
    gap = (1920 - 2 * f.get("margin", 240) - n * w) / max(1, n - 1)
    y = f.get("y", 330)
    for i, it in enumerate(items):
        x = f.get("margin", 240) + i * (w + gap)
        out.append(img_layer(ctx, gen, {"img": it["img"], "x": x, "y": y, "w": w, "shadow": True, "h": int(w * .9)}))
        out.append(f'<div class="L t br" style="left:{x-40}px;width:{w+80}px;text-align:center;top:{y+w*0.95+30}px;font-size:{f.get("label_size",62)}px">{md(it["label"])}</div>')
        if i < n - 1:
            ax = x + w + 15
            out.append(arrow_svg(ax, y + w * 0.45, ax + gap - 30, y + w * 0.45, width=3))
    return "\n".join(out)


def t_pie(ctx, gen, f, dark):
    out = []
    for pi in f["pies"]:
        cx, cy, r = pi["x"], pi["y"], pi.get("r", 200)
        acc, segs, labels = 0.0, [], []
        import math
        for k, (lab, v) in enumerate(pi["data"]):
            a0, a1 = acc / 100 * 2 * math.pi, (acc + v) / 100 * 2 * math.pi
            x0, y0 = cx + r * math.sin(a0), cy - r * math.cos(a0)
            x1, y1 = cx + r * math.sin(a1), cy - r * math.cos(a1)
            large = 1 if v > 50 else 0
            col = PIE[k % len(PIE)]
            segs.append(f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" fill="{col}" stroke="#1d1d1d" stroke-width="3"/>')
            am = (a0 + a1) / 2
            lr = r * (0.62 if v >= 8 else 1.18)
            tc = "#fff" if col in ("#C0533F", "#317E76", "#1E404C") and v >= 8 else "#111"
            labels.append(f'<div class="L t br" style="left:{cx + lr*math.sin(am) - 60:.0f}px;top:{cy - lr*math.cos(am) - 30:.0f}px;width:120px;text-align:center;font-size:{56 if v>=8 else 28}px;font-weight:500;color:{tc}">{v}%</div>')
            acc += v
        out.append('<svg class="ov">' + "".join(segs) + "</svg>")
        out += labels
        out.append(f'<div class="L t imp" style="left:{cx-250}px;width:500px;text-align:center;top:{cy+r+20}px;font-size:66px">{md(pi["title"])}</div>')
    if f.get("legend"):
        lx, ly = f.get("legend_pos", [580, 880])
        cells = "".join(f'<div style="display:inline-flex;align-items:center;width:290px;margin:6px 0;font-size:34px"><span style="width:30px;height:30px;background:{PIE[i%len(PIE)]};margin-right:14px;border:2px solid #333"></span>{esc(l)}</div>' for i, l in enumerate(f["legend"]))
        out.append(f'<div class="L t br" style="left:{lx}px;top:{ly}px;width:900px">{cells}</div>')
    return "\n".join(out)


def t_vignette(ctx, gen, f, dark):
    """binocular / lens mask over the background (set bg to the scene)."""
    col = color(f.get("color", "red"))
    return (f'<svg class="ov"><defs><mask id="bino"><rect width="1920" height="1080" fill="white"/>'
            f'<circle cx="620" cy="560" r="560" fill="black"/><circle cx="1300" cy="560" r="560" fill="black"/></mask>'
            f'<radialGradient id="soft"><stop offset="85%" stop-color="{col}" stop-opacity="0"/></radialGradient></defs>'
            f'<rect width="1920" height="1080" fill="{col}" mask="url(#bino)"/></svg>')


TYPES = {k[2:]: v for k, v in globals().items() if k.startswith("t_")}


# ---------------------------------------------------------------- page assembly
def page(ctx, gen, f, css_href):
    bg_html, dark = background(ctx, gen, f)
    typ = f.get("type", "scene")
    if typ not in TYPES:
        WARN.append(f"{f['id']}: unknown type {typ}")
        body = ""
    else:
        body = TYPES[typ](ctx, gen, f, dark)
    under = layers(ctx, gen, f.get("under"), dark)   # drawn before the type content
    over = layers(ctx, gen, f.get("layers"), dark)    # drawn after
    tint = ""
    if f.get("tint"):
        tint = f'<div class="L" style="inset:0;left:0;top:0;width:1920px;height:1080px;background:{color(f["tint"].get("color","red"))};opacity:{f["tint"].get("opacity",.35)};mix-blend-mode:multiply"></div>'
    return (f'<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{css_href}"></head><body>'
            f'<div class="frame" data-id="{esc(f["id"])}">{bg_html}{under}{body}{over}{tint}</div></body></html>')


def safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(s)).strip("-")[:60]


# ---------------------------------------------------------------- QA
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
WESTERN_RS = re.compile(r"₹\s?\d{1,3}(?:,\d{3}){2,}")
INDIAN_OK = re.compile(r"₹\s?\d{1,2}(?:,\d{2})*,\d{3}")
KNOWN_TYPOS = {"helo": "help", "sghs": "SHGs", "sikkam": "Sikkim", "matrilinieal": "matrilineal", "alloted": "allotted",
               "wasteage": "wastage", "recieve": "receive", "seperate": "separate", "goverment": "government",
               "occured": "occurred", "lorem": "(placeholder text)", "ipsum": "(placeholder text)"}


HINGLISH = set("""hai hain ka ki ke ko se mein me par pe aur ya bhi toh nahi na kya kyun kaise kahan kab kitna kitni kitne ab ek do teen
char paanch sirf saal mahine mahina din pehle baad baaki baki bas lekin magar agar phir fir yeh ye woh wo iss is us uss apna apni apne
aapka aapki aapke hum hamara hamari humare mera meri tera kuch sab sabse bahut bohot zyada kam accha bura asli matlab yaani jaise wala
wali wale karo karna kar raha rahi rahe hota hoti hote hua hui gaya gayi kiya liya diya dena lena milta milega padega chahiye sakte
akhir ayi aaya aayi lakh lakhs crore crores cr rs ji bhai ghar paisa paise kharcha kamai naukri shaadi sona chandi""".split())
FIN = set("""arjun noida kerala andhra pradesh meghalaya khasi bengaluru bangalore mumbai delhi kochi shillong gurugram gurgaon pune chennai
hyderabad kolkata india indian shgs shg mfi mfis etf etfs nbfc nbfcs sebi rbi nse bse stcg ltcg ter emi emis ctc gst demat upi kyc
kirana rera zerodha jewellery annum upto sciencedirect rupee rupees tryst centre colour favour labour metre""".split())


def qa_text(fid, text, extra_allow=frozenset()):
    w = []
    if DEVANAGARI.search(text):
        w.append(f"{fid}: Devanagari on screen (graphics are English / Roman Hinglish only)")
    for m in WESTERN_RS.findall(text):
        w.append(f"{fid}: '{m}' uses western grouping — use Indian lakh/crore grouping (e.g. ₹1,18,000)")
    for word in re.findall(r"[A-Za-z]+", text):
        if word.lower() in KNOWN_TYPOS:
            w.append(f"{fid}: '{word}' — likely typo/placeholder ({KNOWN_TYPOS[word.lower()]})")
        if re.search(r"(.)\1\1", word.lower()):
            w.append(f"{fid}: '{word}' has a tripled letter")
    try:
        from spellchecker import SpellChecker  # optional
        sp = SpellChecker()
        allow = HINGLISH | FIN | set(extra_allow) | set(x.lower() for x in ["arjun", "noida", "kerala", "andhra", "pradesh", "meghalaya", "khasi", "shgs", "mfi", "mfis", "etf",
                                         "etfs", "nbfc", "nbfcs", "sebi", "rbi", "nse", "bse", "stcg", "ltcg", "ter", "emi", "ctc", "gst", "demat",
                                         "lakh", "lakhs", "crore", "crores", "kirana", "rera", "zerodha", "kochi", "shillong", "lekin", "magar",
                                         "kya", "hai", "jewellery", "annum", "upto", "sciencedirect", "rupee", "rupees", "tryst", "ka", "ki", "ke", "aur", "ya", "se", "kahan", "ayi", "akhir", "ab", "ek", "toh", "nahi"])
        for word in set(re.findall(r"[A-Za-z]{4,}", text)):
            if word.lower() not in allow and not word.isupper() and sp.unknown([word.lower()]):
                SPELL.setdefault(word, []).append(fid)
    except Exception:
        pass
    return w


JS_CHECK = """() => {
 const out=[]; const F=document.querySelector('.frame').getBoundingClientRect();
 document.querySelectorAll('.t').forEach(e=>{const rg=document.createRange(); rg.selectNodeContents(e); const r=rg.getBoundingClientRect(); if(r.width==0) return;
  const txt=e.innerText.trim().slice(0,30);
  if(r.left< -2||r.top< -2||r.right>1922||r.bottom>1082) out.push('text off-frame: "'+txt+'"');
  if(e.scrollWidth>e.clientWidth+4 && getComputedStyle(e).width!='auto') out.push('text overflows its box: "'+txt+'"');});
 return out;}"""


# ---------------------------------------------------------------- main
def inline_html(html_text, html_path):
    """Make an HTML file self-contained: CSS, fonts and images as data URIs."""
    base = Path(html_path).parent

    def data_uri(p):
        mt = mimetypes.guess_type(str(p))[0] or ("font/woff2" if str(p).endswith("woff2") else "application/octet-stream")
        return f"data:{mt};base64," + base64.b64encode(Path(p).read_bytes()).decode()

    def css_inline(m):
        cssp = (base / m.group(1)).resolve()
        css = cssp.read_text()
        css = re.sub(r"url\(([^)'\"]+)\)", lambda mm: f"url({data_uri((cssp.parent / mm.group(1)).resolve())})", css)
        return f"<style>{css}</style>"

    h = re.sub(r'<link rel="stylesheet" href="([^"]+)">', css_inline, html_text)
    h = re.sub(r'src="([^"]+)"', lambda m: f'src="{data_uri((base / m.group(1)).resolve())}"' if not m.group(1).startswith("data:") else m.group(0), h)
    h = re.sub(r"url\('([^']+)'\)", lambda m: f"url('{data_uri((base / m.group(1)).resolve())}')" if not m.group(1).startswith("data:") else m.group(0), h)
    return h


def main():
    ap = argparse.ArgumentParser()
    if len(sys.argv) >= 2 and sys.argv[1] == "--unpack-plates":
        d = plates_dir()
        print(f"plates unpacked at: {d}" if d else "assets/plate_sheets not found")
        return
    ap.add_argument("spec")
    ap.add_argument("--out", default="out")
    ap.add_argument("--only", default="")
    ap.add_argument("--package", default="")
    a = ap.parse_args()
    spec_path = Path(a.spec).resolve()
    spec = json.loads(spec_path.read_text())
    out = Path(a.out).resolve()
    (out / "html").mkdir(parents=True, exist_ok=True)
    (out / "png").mkdir(parents=True, exist_ok=True)
    # keep relative links working: out/html -> ../templates/z1.css -> ../fonts, ../assets
    for d in ("templates", "fonts", "assets"):
        link = out / d
        if link.is_symlink() or link.exists():
            if link.is_symlink():
                link.unlink()
            else:
                shutil.rmtree(link)
        os.symlink(KIT / d, link)
    ctx = Ctx(spec_path.parent, out)
    gen = spec.get("gen", {})
    only = set(x for x in a.only.split(",") if x)
    frames = spec["frames"]
    ids = [f["id"] for f in frames]
    for d in set(i for i in ids if ids.count(i) > 1):
        WARN.append(f"duplicate frame id {d}")
    # structure checks
    chapters = [f for f in frames if f.get("type") == "chapter"]
    sops = [f for f in frames if f.get("type") == "sop"]
    if sops and chapters and len(sops[-1]["items"]) != len(chapters):
        WARN.append(f"SOP lists {len(sops[-1]['items'])} questions but there are {len(chapters)} chapter reveals")
    for s in sorted(set(f.get("section", "") for f in frames)):
        if re.match(r"(?i)^(ch|chapter|section)", s) and not any(f.get("type") == "chapter" and f.get("section") == s for f in frames):
            WARN.append(f"section '{s}' has no chapter reveal frame")
    names = {}
    for i, f in enumerate(frames, 1):
        names[f["id"]] = f"{i:02d}_{safe(f['id'])}_{safe(f.get('name', f.get('type','frame')))}"
    from playwright.sync_api import sync_playwright
    texts = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        pg = br.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        for f in frames:
            if only and f["id"] not in only:
                continue
            n = names[f["id"]]
            hp = out / "html" / f"{n}.html"
            hp.write_text(page(ctx, gen, f, "../templates/z1.css"))
            pg.goto(hp.as_uri())
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=str(out / "png" / f"{n}.png"), clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
            for w in pg.evaluate(JS_CHECK):
                if f.get("runoff") and "off-frame" in w:
                    continue
                WARN.append(f"{f['id']}: {w}")
            txt = pg.evaluate("() => { const c=document.querySelector('.frame').cloneNode(true); c.querySelectorAll('.ph').forEach(e=>e.remove()); document.body.appendChild(c); c.style.position='absolute'; c.style.left='-5000px'; const t=c.innerText; c.remove(); return t; }").strip()
            WARN.extend(qa_text(f["id"], txt, set(w.lower() for w in spec.get("allow_words", []))))
            texts.append(f"[{f['id']}] {f.get('section','')} :: {n}\n{txt}\n")
        br.close()
    # contact sheets
    from PIL import Image, ImageDraw
    pngs = [out / "png" / f"{names[f['id']]}.png" for f in frames if (out / "png" / f"{names[f['id']]}.png").exists()]
    for k in range(0, len(pngs), 6):
        sheet = Image.new("RGB", (1920, 790), "white")
        d = ImageDraw.Draw(sheet)
        for j, p in enumerate(pngs[k:k + 6]):
            im = Image.open(p).convert("RGB").resize((640, 360))
            x, y = (j % 3) * 640, (j // 3) * 390
            sheet.paste(im, (x, y + 30))
            d.text((x + 6, y + 8), p.stem, fill="black")
        sheet.save(out / f"_sheet_{k//6+1}.jpg", quality=85)
    if not only:
        (out / "_text.txt").write_text("\n".join(texts))
    # image prompts
    lines = ["# Image-generation prompts (Magnific / any image model)\n",
             "Generate each image, save it as `gen/<key>.png` next to spec.json, then rebuild. 16:9 = 1920x1080 plate; cutout = isolated on white (remove bg).\n"]
    allrefs = set(re.findall(r'"gen:([A-Za-z0-9_.-]+)"', json.dumps(frames)))
    def have(k):
        return any((spec_path.parent / "gen" / (k + e)).exists() for e in (".png", ".jpg", ".jpeg", ".webp"))
    ctx.pending = [k for k in allrefs if not have(k)]
    used = sorted(allrefs | set(gen.keys()))
    for key in used:
        g = gen.get(key)
        if not g:
            WARN.append(f"gen:{key} is used but has no prompt in spec['gen']")
            continue
        p, ar = prompt_text(key, g, spec.get("arjun", "city"))
        status = "PENDING" if key in ctx.pending else ("done" if key in allrefs else "unused")
        lines.append(f"## {key}  ({ar}{', cutout' if g.get('cutout') else ''}) — {status}\nUsed in: {', '.join(fr['id'] for fr in frames if ('gen:'+key) in json.dumps(fr))}\n\n```\n{p}\n```\n")
    (out / "_image_prompts.md").write_text("\n".join(lines))
    # report
    pend = sorted(set(ctx.pending))

    for w in dict.fromkeys(WARN):
        print("WARN", w)
    if SPELL:
        print("SPELL? (not errors — confirm each is a real word / intended Hinglish, or add to spec['allow_words']): "
              + ", ".join(f"{w} [{','.join(sorted(set(v)))}]" for w, v in sorted(SPELL.items())))
    print(f"built {len(pngs)} frames -> {out}/png ; sheets {out}/_sheet_*.jpg ; pending images: {len(pend)} {pend[:12]}")
    if a.package:
        pkg = out / a.package
        if pkg.exists():
            shutil.rmtree(pkg)
        (pkg / "PNG").mkdir(parents=True)
        (pkg / "HTML").mkdir(parents=True)
        for f in frames:
            n = names[f["id"]]
            if (out / "png" / f"{n}.png").exists():
                shutil.copy(out / "png" / f"{n}.png", pkg / "PNG" / f"{n}.png")
                hp = out / "html" / f"{n}.html"
                (pkg / "HTML" / f"{n}.html").write_text(inline_html(hp.read_text(), hp))
        shutil.copy(out / "_image_prompts.md", pkg / "image_prompts.md")
        sb = spec_path.parent / "storyboard.md"
        if sb.exists():
            shutil.copy(sb, pkg / "storyboard.md")
        zp = out / f"{a.package}.zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(pkg.rglob("*")):
                if p.is_file():
                    z.write(p, Path(a.package) / p.relative_to(pkg))
        print("package ->", zp)


# ---------------------------------------------------------------- Graphics Studio adapter
# The web app loads this module and calls frame_html(); the CLI above is untouched. Pages are served with
# <base href="/themes/zero1-hindi-graphics/scenes/">, so every URL is relative to KIT/scenes. Generated plates
# live at KIT/assets/<file> (asset_gen library) and reach the frame as frame["_gen"][key]["file"].
CANVAS = (1920, 1080)
CHECK_JS = JS_CHECK
SCENES = KIT / "scenes"


class StudioCtx(Ctx):
    def __init__(self, gen):
        super().__init__(SCENES, SCENES)
        self.gen = gen or {}

    def src(self, ref):
        if isinstance(ref, str) and ref.startswith("gen:"):
            key = ref[4:]
            f = (self.gen.get(key) or {}).get("file")
            if f:
                p = KIT / "assets" / f
                if p.exists():
                    return p, key
            self.pending.append(key)
            return None, key
        if isinstance(ref, str) and (ref.startswith("/") or ref.startswith("data:")):
            return None, None
        return super().src(ref)

    def url(self, p):
        return Path(os.path.relpath(p, SCENES)).as_posix()


def gen_keys(obj):
    """Every gen:<key> a frame (or list of frames) refers to."""
    return sorted(set(re.findall(r'"gen:([A-Za-z0-9_.-]+)"', json.dumps(obj, ensure_ascii=False))))


def _tag(html_s, path, idx, l):
    """Edit-mode hooks on one free layer: the studio drags it (x/y) and resizes it (w for images, size for text)."""
    if "arrow" in l or not html_s.lstrip().startswith("<div"):
        return html_s
    kind = "asset" if "img" in l else ("text" if "text" in l else "shape")
    resize = {"asset": ' data-resize="asset"', "text": ' data-resize="font"'}.get(kind, "")
    attrs = (f' data-spec-idx="{idx}" data-mf-drag="{path}" data-layer-type="{kind}"{resize}'
             f' data-layer-label="{esc((l.get("text") or l.get("img") or kind))[:40]}"')
    s = html_s.lstrip()
    s = s.replace("<div", "<div" + attrs, 1)
    return re.sub(r'class="([^"]*)"', lambda m: f'class="{m.group(1)} studio-editable"', s, count=1)


def frame_html(frame, look=None, all_frames=None, edit=False):
    f = {k: v for k, v in frame.items() if k != "_gen"}
    f.setdefault("id", "frame")
    ctx = StudioCtx(frame.get("_gen"))
    del WARN[:]
    if not edit:
        return page(ctx, ctx.gen, f, "../templates/z1.css")
    plain = globals()["layers"]
    # data-spec-idx = row number in the studio's layer list (arrows are not listed or tagged)
    n_under = sum(1 for l in f.get("under") or [] if "arrow" not in l)

    def tagged(ctx_, gen_, ls, dark=False):
        if ls is None or not (ls is f.get("under") or ls is f.get("layers")):
            return plain(ctx_, gen_, ls, dark)
        key = "under" if ls is f.get("under") else "layers"
        row = 0 if key == "under" else n_under
        out = []
        for i, l in enumerate(ls):
            out.append(_tag(plain(ctx_, gen_, [l], dark), f"{key}.{i}", row, l))
            row += "arrow" not in l
        return "\n".join(out)

    globals()["layers"] = tagged
    try:
        html_s = page(ctx, ctx.gen, f, "../templates/z1.css")
    finally:
        globals()["layers"] = plain
    return html_s.replace("<body>", '<body class="studio-edit-mode">', 1)


def frame_warnings(frame, allow=()):
    """Static checks (palette, Devanagari, ₹ grouping, typos) on a frame's on-screen text."""
    txt = " ".join(re.findall(r'"text"\s*:\s*"([^"]*)"', json.dumps(frame, ensure_ascii=False)))
    return qa_text(frame.get("id", "?"), txt, set(allow))


if __name__ == "__main__":
    main()

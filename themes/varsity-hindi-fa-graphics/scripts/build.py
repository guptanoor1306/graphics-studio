#!/usr/bin/env python3
"""Varsity Hindi FA graphics: spec.json -> self-contained HTML + 1920x1080 PNG per frame.

usage: python3 build.py spec.json --out out [--only 0.21,1.16] [--package Ep10_Title_graphics]
"""
import argparse, base64, html, json, math, os, random, re, sys, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import charrig, scenes

KIT = Path(__file__).resolve().parent.parent
A = KIT / "assets"
W, H = 1920, 1080
CANVAS_W, CANVAS_H = W, H


def _studio_web() -> bool:
    return os.environ.get("STUDIO_WEB") == "1"

# ---------------------------------------------------------------- palette
C = {
    "ink": "#141414", "white": "#FFFFFF", "coral": "#EF5143", "blue": "#2F7CF6",
    "chart_blue": "#2F7CF6", "green": "#86BD65", "orange": "#E8611A", "yellow": "#F6C21C",
    "pale_blue": "#8DB6FA", "pale_yellow": "#F3D98A", "pale_orange": "#E9A27E",
    "hl_yellow": "#F5D36B", "hl_blue": "#8DB6FA", "grey": "#8A94A0", "divider": "#2F7CF6",
}
DATA_COLOURS = {"green", "coral", "blue", "orange", "yellow", "pale_blue", "pale_yellow", "pale_orange", "grey"}
HINGLISH = set("""hai hain mein aur toh nahi kya kaise yeh woh matlab kitna liye chahiye sakte wala wali
hota hoti humne aap apna apni kyunki lekin agar jaise isko usko kaafi bahut dekhiye chaliye""".split())

WARN = []
def warn(fid, msg):
    WARN.append(f"WARN [{fid}] {msg}")

# ---------------------------------------------------------------- assets
_b64 = {}
def asset(rel):
    """rel like 'chars/trader_seated' or 'plates/floor.png' -> data URI or ../assets/ in studio."""
    rp = str(rel).replace("\\", "/")
    p = A / rp
    if p.suffix == "":
        p = p.with_suffix(".png")
        rp = rp + (".png" if not Path(rp).suffix else "")
    if not p.exists():
        raise FileNotFoundError(f"asset not found: {rel} (see references/assets.md)")
    if _studio_web():
        return f"../assets/{rp}"
    if p not in _b64:
        mime = "image/png" if p.suffix == ".png" else "image/jpeg"
        _b64[p] = f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()
    return _b64[p]

def font_css():
    out = []
    for w in (400, 500, 600, 700, 800):
        for st in ("normal", "italic"):
            f = KIT / "fonts" / f"inter-latin-{w}-{st}.woff2"
            out.append("@font-face{font-family:Inter;font-weight:%d;font-style:%s;src:url(data:font/woff2;base64,%s) format('woff2');}"
                       % (w, st, base64.b64encode(f.read_bytes()).decode()))
    return "\n".join(out)

CSS = (KIT / "templates" / "fa.css").read_text()

# ---------------------------------------------------------------- text markup
def md(s):
    """==yellow block==  ^^blue block^^  **bold**  __coral underline__  \\n line break"""
    s = html.escape(str(s))
    s = re.sub(r"==(.+?)==", r'<span class="hl hl-y">\1</span>', s)
    s = re.sub(r"\^\^(.+?)\^\^", r'<span class="hl hl-b">\1</span>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"__(.+?)__", r'<span class="ul">\1</span>', s)
    return s.replace("\n", "<br>")

def style(d):
    return ";".join(f"{k}:{v}" for k, v in d.items() if v is not None)

def pos(e, extra=None):
    st = {"left": f"{e.get('x', 0)}px", "top": f"{e.get('y', 0)}px"}
    if e.get("w"): st["width"] = f"{e['w']}px"
    if e.get("h") and e.get("type") not in ("img",): st["height"] = f"{e['h']}px"
    tr = []
    if e.get("align") == "center": tr.append("translateX(-50%)")
    if e.get("align") == "right": tr.append("translateX(-100%)")
    if e.get("tilt"): tr.append(f"rotate({e['tilt']}deg)")
    if tr: st["transform"] = " ".join(tr)
    if e.get("opacity") is not None: st["opacity"] = e["opacity"]
    if e.get("blur"): st["filter"] = f"blur({e['blur']}px)"
    if e.get("z") is not None: st["z-index"] = e["z"]
    if extra: st.update(extra)
    return style(st)


def pos_font(e, px, **more):
    return pos(e, {"font-size": f"{px}px", **more})

# ---------------------------------------------------------------- svg helpers
def arrow_svg(x1, y1, x2, y2, bend=0.25, dashed=False, color="#1d1d1d", width=3, head=True):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    cx, cy = mx - dy * bend, my + dx * bend
    ang = math.atan2(y2 - cy, x2 - cx)
    hl = 16
    a1 = (x2 - hl * math.cos(ang - 0.45), y2 - hl * math.sin(ang - 0.45))
    a2 = (x2 - hl * math.cos(ang + 0.45), y2 - hl * math.sin(ang + 0.45))
    dash = 'stroke-dasharray="8 9"' if dashed else ""
    h = (f'<path d="M{a1[0]:.1f},{a1[1]:.1f} L{x2},{y2} L{a2[0]:.1f},{a2[1]:.1f}" fill="none" stroke="{color}" '
         f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>') if head else ""
    return (f'<path d="M{x1},{y1} Q{cx:.1f},{cy:.1f} {x2},{y2}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" {dash}/>' + h), (cx, cy)

def qpoint(x1, y1, cx, cy, x2, y2, t):
    return ((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2,
            (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2)

def svg_layer(inner, z=5):
    return f'<svg class="svg" style="z-index:{z}" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{inner}</svg>'

# ---------------------------------------------------------------- elements
def el_text(e, fid):
    st = {"font-size": f"{e.get('size', 40)}px", "font-weight": e.get("weight", 600),
          "color": C.get(e.get("color", "ink"), e.get("color", C["ink"])),
          "font-style": "italic" if e.get("italic") else None, "text-align": e.get("text_align"),
          "line-height": e.get("lh")}
    return f'<div class="el text" style="{pos(e, st)}">{md(e["text"])}</div>'

def el_header(e, fid):
    s = e.get("style", "bar")
    t = e["text"]
    size = e.get("size")
    if s == "bar":          # coral bar + ExtraBold Italic (Ep 2 section headers)
        return f'<div class="el hdr-bar" style="{pos_font(e, size or 60)}">{md(t)}</div>'
    if s == "giant":        # huge ExtraBold word, props may overlap it (Ep 5 concept scenes)
        return f'<div class="el hdr-giant" style="{pos_font(e, size or 140)}">{md(t)}</div>'
    if s == "plain":        # Bold black heading (Ep 8)
        return f'<div class="el hdr-plain" style="{pos_font(e, size or 72)}">{md(t)}</div>'
    if s == "stack":        # coral bar + 2 lines: "Financial Ratios" / "Profitability Ratios"
        st = pos_font(e, size or 50)
        return (f'<div class="el hdr-stack" style="{st}">'
                f'<div class="l1">{md(t)}</div><div class="l2">{md(e.get("sub", ""))}</div></div>')
    if s == "title":        # title stack: small lead / big ExtraBold Italic key / small tail (Ep 2 0.18)
        st = pos_font(e, size or 64)
        return (f'<div class="el hdr-title" style="{st}">'
                f'<div class="lead">{md(e.get("lead", ""))}</div><div class="key">{md(t)}</div>'
                f'<div class="tail">{md(e.get("tail", ""))}</div></div>')
    if s == "box":          # white rounded box (Ep 9)
        return f'<div class="el hdr-box" style="{pos_font(e, size or 56)}">{md(t)}</div>'
    if s == "label":        # light-blue label block (Ep 9)
        return f'<div class="el hdr-label" style="{pos_font(e, size or 40)}">{md(t)}</div>'
    if s == "glass":        # big glass title card (Ep 8 2.16 / 6.20)
        return f'<div class="el glass hdr-glass" style="{pos_font(e, size or 84)}">{md(t)}</div>'
    warn(fid, f"unknown header style {s}")
    return ""

def el_pill(e, fid, svg):
    cls = "pill"
    if e.get("italic", True): cls += " it"
    if e.get("bold"): cls += " bd"
    if e.get("active"): cls += " active"
    if e.get("faded"): cls += " faded"
    st = {"font-size": f"{e.get('size', 32)}px"}
    out = f'<div class="el {cls}" data-arrow="{1 if e.get("arrow_to") else 0}" style="{pos(e, st)}">{md(e["text"])}</div>'
    if e.get("arrow_to"):
        # arrow starts near the pill's bottom-right or bottom-left (estimated), hand-drawn bend
        fx, fy = e.get("arrow_from") or (e["x"] + (0 if e.get("align") == "center" else 60), e["y"] + 70)
        tx, ty = e["arrow_to"]
        p, _ = arrow_svg(fx, fy, tx, ty, bend=e.get("bend", 0.3), width=2.5)
        svg.append(p)
    return out

def el_pills(e, fid, svg):
    out = []
    gap = e.get("gap", 96)
    for i, it in enumerate(e["items"]):
        d = {"type": "pill", "text": it, "x": e["x"] + (e.get("stagger", 0) * (i % 2)), "y": e["y"] + i * gap,
             "italic": e.get("italic", False), "size": e.get("size", 32)}
        if e.get("active") is not None:
            act = e["active"] if isinstance(e["active"], list) else [e["active"]]
            d["active"] = i in act
            d["faded"] = e.get("fade_rest", False) and i not in act
        out.append(el_pill(d, fid, svg))
    return "".join(out)

def el_img(e, fid):
    src = e["src"]
    if src.startswith("chars/standing"):
        warn(fid, f"{src} retired: use a 'char' element (team characters with poses)")
    track(src, e.get("as"), fid)
    h = e.get("h")
    if e.get("x") is not None and e.get("y") is not None:
        st = {"left": f"{e['x']}px", "top": f"{e['y']}px", "height": f"{h}px" if h else None,
              "width": f"{e['w']}px" if e.get("w") else None}
        tr = []
    else:
        st = {"left": f"{e['cx']}px", "top": f"{e['by']}px", "height": f"{h}px" if h else None,
              "width": f"{e['w']}px" if e.get("w") else None}
        tr = ["translate(-50%,-100%)"]
    if e.get("flip"): tr.append("scaleX(-1)")
    if e.get("tilt"): tr.append(f"rotate({e['tilt']}deg)")
    st["transform"] = " ".join(tr)
    if e.get("opacity") is not None: st["opacity"] = e["opacity"]
    if e.get("blur"): st["filter"] = f"blur({e['blur']}px)"
    if e.get("z") is not None: st["z-index"] = e["z"]
    if src.startswith("chars/") and (e.get("tint") or e.get("recolor")):
        warn(fid, f"{src}: characters are fixed team artwork; only position/size/flip may change")
    shadow = '<div class="el floor-shadow" style="left:%dpx;top:%dpx;width:%dpx"></div>' % (
        e["cx"] - (h or 300) * 0.35, e["by"] - 18, (h or 300) * 0.7) if e.get("shadow") else ""
    return shadow + f'<img class="el img" src="{asset(src)}" style="{style(st)}" data-src="{src}">'

def el_card(e, fid):
    k = e.get("kind", "text")
    body = ""
    if e.get("title"):
        tcls = "ctitle" + (" hl hl-y" if e.get("title_hl") == "yellow" else " hl hl-b" if e.get("title_hl") == "blue" else "")
        body += f'<div class="{tcls}">{md(e["title"])}</div>'
    if k == "quote":
        body += f'<div class="quote">“{md(e["text"])}”</div>'
    elif k == "text":
        body += f'<div class="ctext">{md(e["text"])}</div>'
    elif k == "bullets":
        mk = e.get("marker", "dot")
        lis = []
        for i, it in enumerate(e["items"]):
            c = "faded" if e.get("active") is not None and i != e["active"] and e.get("fade_rest") else ""
            lis.append(f'<li class="{c}"><span class="mk mk-{mk}"></span>{md(it)}</li>')
        body += f'<ul class="bul">{"".join(lis)}</ul>'
    elif k == "formula":
        hl = "hl-y" if e.get("hl", "blue") == "yellow" else "hl-b"
        term = f'<span class="hl {hl} fterm">{md(e["term"])}</span>'
        if e.get("num") is not None:
            rhs = f'<span class="frac"><span class="num">{md(e["num"])}</span><span class="den">{md(e["den"])}</span></span>'
        else:
            rhs = f'<span class="rhs">{md(e.get("rhs", ""))}</span>'
        res = f'<span class="res">{md(e["result"])}</span>' if e.get("result") else ""
        body += f'<div class="formula">{term}<span class="eq">=</span>{rhs}{res}</div>'
    elif k == "calc":
        rows = []
        for r in e["lines"]:
            lab = f'<span class="hl hl-y clab">{md(r["label"])}</span>' if r.get("hl", True) else f'<span class="clab">{md(r["label"])}</span>'
            if r.get("num") is not None:
                val = (f'<span class="eq">=</span><span class="frac sm"><span class="num">{md(r["num"])}</span>'
                       f'<span class="den">{md(r["den"])}</span></span>')
                if r.get("result"): val += f'<span class="eq">=</span><b>{md(r["result"])}</b>'
            else:
                val = f'<span class="eq">=</span><span class="cval">{md(r["value"])}</span>'
            rows.append(f'<div class="crow">{lab}{val}</div>')
        body += "".join(rows)
    elif k == "lines":   # triangle bullets with highlighted values (Ep 8 5.00)
        rows = [f'<div class="tline"><span class="mk mk-triangle"></span>{md(r)}</div>' for r in e["items"]]
        body += "".join(rows)
    glass = "glass" if e.get("glass", True) else "plaincard"
    st = {"font-size": f"{e.get('size', 32)}px", "padding": e.get("pad")}
    return f'<div class="el card {glass} card-{k}" style="{pos(e, st)}">{body}</div>'

def el_bigword(e, fid):
    st = {"font-size": f"{e.get('size', 260)}px", "z-index": e.get("z", 1)}
    return f'<div class="el bigword" style="{pos(e, st)}">{md(e["text"])}</div>'

def el_split(e, fid, svg):
    x = e.get("x", 960)
    svg.append(f'<line x1="{x}" y1="{e.get("y1", 130)}" x2="{x}" y2="{e.get("y2", 1010)}" stroke="{C["divider"]}" stroke-width="3"/>')
    return ""

def el_coinflow(e, fid, svg):
    (x1, y1), (x2, y2) = e["from"], e["to"]
    p, (cx, cy) = arrow_svg(x1, y1, x2, y2, bend=e.get("bend", -0.25), dashed=True, color="#333", width=2.5)
    svg.append(p)
    out = []
    n = e.get("coins", 2)
    for i in range(n):
        t = (i + 1) / (n + 1)
        px, py = qpoint(x1, y1, cx, cy, x2, y2, t)
        out.append(f'<img class="el img" src="{asset("props/coin")}" style="left:{px:.0f}px;top:{py:.0f}px;width:46px;transform:translate(-50%,-50%)">')
    return "".join(out)

def el_branch(e, fid, svg):
    """elbow connectors from a point to round icon badges with labels (Ep 5 0.38 / 5.38)"""
    fx, fy = e["from"]
    bx = e.get("badge_x", fx + 220)
    jx = e.get("joint_x", (fx + bx) / 2)
    out = []
    ys = [it["y"] for it in e["items"]]
    svg.append(f'<circle cx="{fx}" cy="{fy}" r="8" fill="{C["blue"]}"/>')
    svg.append(f'<path d="M{fx},{fy} H{jx}" stroke="{C["blue"]}" stroke-width="3" fill="none"/>')
    svg.append(f'<path d="M{jx},{min(ys + [fy])} V{max(ys + [fy])}" stroke="{C["blue"]}" stroke-width="3" fill="none"/>')
    for it in e["items"]:
        y = it["y"]
        svg.append(f'<path d="M{jx},{y} H{bx - 70}" stroke="{C["blue"]}" stroke-width="3" fill="none"/>')
        svg.append(f'<path d="M{bx-84},{y-8} L{bx-70},{y} L{bx-84},{y+8}" fill="{C["blue"]}"/>')
        icon = f'<img src="{asset(it["icon"])}">' if it.get("icon") else ""
        out.append(f'<div class="el badge" style="left:{bx - 62}px;top:{y - 62}px">{icon}</div>')
        out.append(f'<div class="el badge-label" style="left:{bx + 76}px;top:{y - 22}px">{md(it["text"])}</div>')
    return "".join(out)

def bar_svg(e, fid, w, h):
    bars = e["bars"]
    ymax = e.get("ymax") or max(abs(b["value"]) for b in bars) * 1.15
    ymin = min(0, min(b["value"] for b in bars))
    pad_l, pad_r, pad_t, pad_b = 70, 30, 70, (150 if ymin < 0 else 60)
    pw, ph = w - pad_l - pad_r, h - pad_t - pad_b
    zero = pad_t + ph * (ymax / (ymax - ymin)) if ymin < 0 else pad_t + ph
    scale = (zero - pad_t) / ymax
    n = len(bars)
    slot = pw / n
    bw = min(slot * 0.55, e.get("bar_w", 120))
    s = [f'<line x1="{pad_l}" y1="{pad_t-30}" x2="{pad_l}" y2="{pad_t+ph}" stroke="#1d1d1d" stroke-width="3"/>',
         f'<line x1="{pad_l}" y1="{zero}" x2="{pad_l+pw}" y2="{zero}" stroke="#1d1d1d" stroke-width="3"/>']
    for t in e.get("yticks", []):
        ty = zero - t["v"] * scale
        s.append(f'<line x1="{pad_l-8}" y1="{ty}" x2="{pad_l+8}" y2="{ty}" stroke="#1d1d1d" stroke-width="3"/>'
                 f'<text x="{pad_l-16}" y="{ty+8}" text-anchor="end" class="ax">{html.escape(t["label"])}</text>')
    for i, b in enumerate(bars):
        col = b.get("color", "green")
        if col not in DATA_COLOURS: warn(fid, f"bar colour '{col}' not in palette {sorted(DATA_COLOURS)}")
        x = pad_l + slot * i + (slot - bw) / 2
        v = b["value"]
        bh = abs(v) * scale
        y = zero - bh if v >= 0 else zero
        if bh > 0:
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{C[col]}" rx="3"/>')
        if b.get("tag"):
            ty = (y - 40) if v >= 0 else (y + bh + 40)
            if e.get("bubbles", True):
                s.append(f'<circle cx="{x+bw/2:.1f}" cy="{ty:.1f}" r="30" fill="#fff" stroke="#c9d3dd" stroke-width="2"/>')
            s.append(f'<text x="{x+bw/2:.1f}" y="{ty+8:.1f}" text-anchor="middle" class="tag">{html.escape(b["tag"])}</text>')
        ly = zero + 38 if v >= 0 else zero - 14
        s.append(f'<text x="{x+bw/2:.1f}" y="{ly:.1f}" text-anchor="middle" class="xl">{html.escape(b.get("label",""))}</text>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(s)}</svg>'

def gen_points(n, trend, seed, lo=0, hi=100):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        if trend == "up": base = 0.15 + 0.7 * t
        elif trend == "down": base = 0.85 - 0.7 * t
        elif trend == "flat": base = 0.5
        elif trend == "smooth": base = 0.12 + 0.75 * (t ** 1.6)
        else: base = 0.2 + 0.6 * t  # lumpy up
        amp = {"flat": 0.06, "smooth": 0.0, "lumpy": 0.16}.get(trend, 0.07)
        pts.append(lo + (hi - lo) * max(0.02, min(0.98, base + rnd.uniform(-amp, amp))))
    return pts

def line_svg(e, fid, w, h):
    if e.get("points"):
        pts = e["points"]
    else:
        glo, ghi = e.get("ymin", 0), e.get("ymax", 100)
        span = ghi - glo
        pts = gen_points(e.get("n", 40), e.get("trend", "up"), e.get("seed", 3),
                         glo + span * e.get("from", 0.08), glo + span * e.get("to", 0.92))
    lo, hi = e.get("ymin", min(pts)), e.get("ymax", max(pts))
    if hi == lo: hi = lo + 1
    pad_l, pad_r, pad_t, pad_b = e.get("pad_l", 60), e.get("pad_r", 260 if any(l.get("note") for l in e.get("levels", [])) else 110), 40, 60
    pw, ph = w - pad_l - pad_r, h - pad_t - pad_b
    X = lambda i: pad_l + pw * i / (len(pts) - 1)
    Y = lambda v: pad_t + ph * (1 - (v - lo) / (hi - lo))
    col = e.get("color", "blue")
    if col not in DATA_COLOURS: warn(fid, f"line colour '{col}' not in palette")
    s = []
    if e.get("axes", True):
        s.append(f'<path d="M{pad_l},{pad_t-10} V{pad_t+ph} H{pad_l+pw+40}" fill="none" stroke="#1d1d1d" stroke-width="3"/>')
    for lv in e.get("levels", []):   # horizontal reference lines with a right label (Ep 2 0.25)
        y = Y(lv["v"])
        s.append(f'<line x1="{pad_l}" y1="{y}" x2="{pad_l+pw+20}" y2="{y}" stroke="#1d1d1d" stroke-width="2"/>'
                 f'<text x="{pad_l+pw+28}" y="{y+8}" class="lvl">{html.escape(lv["label"])}</text>')
        if lv.get("note"): s.append(f'<text x="{pad_l+pw+28}" y="{y+34}" class="lvln">{html.escape(lv["note"])}</text>')
    d = " ".join(f"{'M' if i == 0 else 'L'}{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(pts))
    s.append(f'<path d="{d}" fill="none" stroke="{C[col]}" stroke-width="{e.get("stroke", 4)}" stroke-linejoin="round"/>')
    for m in e.get("marks", []):     # {"i": idx, "label": "₹106", "drop": true}
        i = m["i"] if m["i"] >= 0 else len(pts) + m["i"]
        x, y = X(i), Y(pts[i])
        if m.get("drop", True):
            s.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{pad_t+ph}" stroke="#555" stroke-width="2" stroke-dasharray="6 7"/>')
        s.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{C["coral"] if m.get("coral") else C[col]}" stroke="#fff" stroke-width="3"/>')
        if m.get("label"):
            s.append(f'<text x="{x + m.get("dx", 0)}" y="{y - 22 + m.get("dy", 0)}" text-anchor="{m.get("anchor", "middle")}" class="mk-l">{html.escape(m["label"])}</text>')
    for xl in e.get("xlabels", []):  # {"i": idx, "label": "1 year"}
        i = xl["i"] if xl["i"] >= 0 else len(pts) + xl["i"]
        s.append(f'<text x="{X(i)}" y="{pad_t+ph+40}" text-anchor="middle" class="xl">{html.escape(xl["label"])}</text>')
    if e.get("axis_label"):
        s.append(f'<text x="{pad_l+pw/2}" y="{pad_t+ph+44}" text-anchor="middle" class="xl">{html.escape(e["axis_label"])}</text>')
    for t in e.get("yticks", []):
        y = Y(t)
        s.append(f'<text x="{pad_l+pw+30}" y="{y+7}" class="ax">{t:,.0f}</text>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(s)}</svg>'

def el_chart(e, fid):
    w, h = e.get("w", 900), e.get("h", 520)
    svg = bar_svg(e, fid, w, h - (70 if e.get("title") else 0)) if e["type"] == "bar" else line_svg(e, fid, w, h - (70 if e.get("title") else 0))
    title = f'<div class="chart-title">{md(e["title"])}</div>' if e.get("title") else ""
    legend = ""
    if e.get("legend"):
        legend = '<div class="legend">' + "".join(
            f'<span><i style="background:{C[l["color"]]}"></i>{md(l["label"])}</span>' for l in e["legend"]) + "</div>"
    cls = "glass" if e.get("glass", True) else ""
    st = pos({**e, "w": None, "h": None}, {"width": f"{w}px"})
    box = f'<div class="el chart {cls}" style="{st}">{title}{svg}{legend}</div>'
    if e.get("stand") == "phone":    # chart standing on a landscape phone lying flat (Ep 2)
        cx = e["x"] + w / 2 if e.get("align") != "center" else e["x"]
        box += (f'<img class="el img" src="{asset("props/phone_landscape")}" '
                f'style="left:{cx}px;top:{e["y"] + h + 120}px;width:{w + 160}px;transform:translate(-50%,-100%)">')
    return box

def el_window(e, fid):
    """Kite-style price window for a real stock (Ep 2 0.25, Ep 8 chart 7)"""
    w, h = e.get("w", 1100), e.get("h", 620)
    inner = line_svg({**e, "axes": False, "pad_l": 30, "pad_r": 150}, fid, w - 60, h - 110)
    st = pos({**e, "w": None, "h": None}, {"width": f"{w}px", "height": f"{h}px"})
    return (f'<div class="el window glass" style="{st}"><div class="wbar"><span class="tk">{md(e.get("ticker", "XYZ"))}</span>'
            f'<span class="tools"><i></i><i></i><i></i><i></i></span><img class="chev" src="{asset("props/kite_chevron")}"></div>'
            f'<div class="wbody">{inner}</div></div>')

def el_linecards(e, fid):
    out = []
    for i, c in enumerate(e["cards"]):
        x = e["x"] + i * (e.get("w", 400) + e.get("gap", 40))
        out.append(f'<div class="el hl hl-y lc-title" style="left:{x + e.get("w",400)/2}px;top:{e["y"]}px;transform:translateX(-50%)">{md(c["title"])}</div>')
        svg = line_svg({"trend": c.get("trend", "up"), "seed": c.get("seed", i + 4), "n": 24, "axes": False,
                        "pad_l": 20, "pad_r": 20, "stroke": 5}, fid, e.get("w", 400) - 20, 220)
        out.append(f'<div class="el glass lc" style="left:{x}px;top:{e["y"] + 80}px;width:{e.get("w",400)}px">{svg}</div>')
    return "".join(out)

def el_pie(e, fid):
    cx, cy, r = e["cx"], e["cy"], e.get("r", 220)
    tot = sum(s["value"] for s in e["slices"])
    a = -90
    parts = []
    for s in e["slices"]:
        col = s.get("color", "blue")
        if col not in DATA_COLOURS: warn(fid, f"pie colour '{col}' not in palette")
        sweep = 360 * s["value"] / tot
        a2 = a + sweep
        if s.get("hidden"):
            a = a2; continue
        off = s.get("explode", 0)
        mid = math.radians(a + sweep / 2)
        ox, oy = off * math.cos(mid), off * math.sin(mid)
        x1, y1 = r + ox + r * math.cos(math.radians(a)), r + oy + r * math.sin(math.radians(a))
        x2, y2 = r + ox + r * math.cos(math.radians(a2)), r + oy + r * math.sin(math.radians(a2))
        large = 1 if sweep > 180 else 0
        parts.append(f'<path d="M{r+ox},{r+oy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} Z" fill="{C[col]}" stroke="#fff" stroke-width="6"/>')
        lx, ly = r + ox + r * 0.58 * math.cos(mid), r + oy + r * 0.58 * math.sin(mid)
        parts.append(f'<text x="{lx:.1f}" y="{ly+9:.1f}" text-anchor="middle" class="pie-l">{html.escape(s["label"])}</text>')
        a = a2
    pad = 40
    svg = f'<svg width="{2*r+pad*2}" height="{2*r+pad*2}" viewBox="{-pad} {-pad} {2*r+pad*2} {2*r+pad*2}">{"".join(parts)}</svg>'
    return f'<div class="el pie" style="left:{cx - r - pad}px;top:{cy - r - pad}px">{svg}</div>'

def el_phone(e, fid):
    """portrait phone watchlist / order screen with BUY / SELL (Ep 2 0.09, Ep 9 1.57)"""
    rows = "".join(f'<div class="prow"><span class="ex">{html.escape(r.get("ex","NSE"))}</span><span class="nm">{md(r["name"])}</span><span class="plus">+</span></div>'
                   for r in e.get("rows", []))
    card = e.get("card", {"name": "XYZ", "price": "114.47"})
    st = pos(e, {"width": f"{e.get('w', 380)}px"})
    return (f'<div class="el phone" style="{st}"><div class="notch"></div><div class="ptitle">{md(e.get("title","WATCHLIST"))}</div>'
            f'<div class="ptabs"><span>#</span><span>MF</span><span>IPO</span><span>Events</span><span>Brands</span></div>{rows}'
            f'<div class="pcard"><div class="pcn">{md(card["name"])}</div><div class="pcp">NSE <span>{html.escape(str(card.get("price","")))}</span></div>'
            f'<div class="pbtn"><span class="buy">BUY</span><span class="sell">SELL</span></div><div class="pl"></div><div class="pl"></div></div></div>')

def el_cardset(e, fid):
    """labelled folder/glass cards; active one upright and sharp, others tilted/blurred (Ep 9 0.29, 1.42)"""
    out = []
    items = e["items"]
    n = len(items)
    cw, ch = e.get("cw", 300), e.get("ch", 260)
    gap = e.get("gap", 40)
    style_ = e.get("style", "folder")
    x0 = e.get("x", (W - (n * cw + (n - 1) * gap)) / 2)
    for i, it in enumerate(items):
        act = e.get("active")
        x = x0 + i * (cw + gap)
        y = e.get("y", 300)
        tilt, blur, op = 0, 0, 1
        if act is not None and i != act:
            if e.get("arc", style_ == "folder"):
                tilt = -22 if i < act else 22
                y += 80
            blur = e.get("blur_rest", 3)
            op = 0.85
        img = f'<img src="{asset(it["img"])}">' if it.get("img") else ""
        st = f"left:{x}px;top:{y}px;width:{cw}px;height:{ch}px;transform:rotate({tilt}deg);filter:blur({blur}px);opacity:{op}"
        out.append(f'<div class="el cset cset-{style_}" style="{st}"><div class="ctab"></div><div class="clabel">{md(it["label"])}</div>{img}</div>')
    if e.get("road"):
        warn(fid, "cardset road style was rejected by the design team as childish: use the module page or a clean card row")
    return "".join(out)

def el_module(e, fid):
    """chapter/module page: 4 glass number cards, current one white with black number (Ep 2 0.03)"""
    out = [f'<div class="el hdr-bar mod-h" style="left:{W/2}px;top:110px;transform:translateX(-50%);font-size:62px;font-style:normal">{md(e.get("module","Module 3"))}</div>']
    chs = e["chapters"]
    cur = e.get("current", 1)
    n = len(chs)
    cw, gap = 366, 44
    x0 = (W - (n * cw + (n - 1) * gap)) / 2
    for i, c in enumerate(chs):
        k = i + 1
        cls = "cur" if k == cur else ("done" if k < cur else "next")
        out.append(f'<div class="el mcard {cls}" style="left:{x0 + i*(cw+gap)}px;top:384px"><div class="mn">{e.get("start",1)+i}</div><div class="mt">{md(c)}</div></div>')
        if k == cur:
            out.append(f'<svg class="el" style="left:{x0 + i*(cw+gap) + 290}px;top:840px" width="64" height="84" viewBox="0 0 64 84"><path d="M6 4 L6 66 L22 52 L34 80 L44 75 L32 48 L54 48 Z" fill="#fff" stroke="#111" stroke-width="4" stroke-linejoin="round"/></svg>')
    return "".join(out)

def el_takeaways(e, fid):
    items = "".join(f'<li><span class="n">{i+1}.</span><span>{md(t)}</span></li>' for i, t in enumerate(e["items"]))
    fs = 30 if len(e["items"]) <= 7 else 26 if len(e["items"]) <= 9 else 23
    title = md(e.get("title", "Key\nTakeaways"))
    return (f'<div class="el swoosh"></div><img class="el img" src="{asset("props/megaphone")}" style="left:20px;top:716px;width:360px">'
            f'<div class="el hdr-bar tk-h" style="left:150px;top:400px;font-size:66px;font-style:normal">{title}</div>'
            f'<ol class="el tk-list" style="font-size:{fs}px">{items}</ol>')

def el_shape(e, fid):
    """plain rounded block (e.g. the big blue capsule behind the investor, Ep 2 1.34)"""
    col = C.get(e.get("color", "blue"), e.get("color"))
    radius = e.get("radius", 999)
    shape_st = {"background": col, "border-radius": f"{radius}px", "opacity": e.get("opacity", 1)}
    return f'<div class="el" style="{pos(e, shape_st)}"></div>'

def el_arrow(e, fid, svg):
    p, _ = arrow_svg(*e["from"], *e["to"], bend=e.get("bend", 0.25), dashed=e.get("dashed", False),
                     color=e.get("color", "#1d1d1d"), width=e.get("width", 3))
    svg.append(p)
    return ""

def el_tri(e, fid):
    """coral triangle arrow between items (Ep 2 1.53)"""
    return f'<div class="el tri" style="left:{e["x"]}px;top:{e["y"]}px;border-left-width:{e.get("size",44)}px;border-top-width:{e.get("size",44)*0.8}px;border-bottom-width:{e.get("size",44)*0.8}px"></div>'

def el_scale(e, fid):
    """balance scale with labels on its two box strips (Ep 8 1.16 / 6.40). cx, by, w; left/right text; tilt_to: left|right"""
    w = e.get("w", 1150); cx, by = e["cx"], e["by"]
    hgt = w * 656 / 1153
    out = [f'<img class="el img" src="{asset("props/balance_scale")}" style="left:{cx}px;top:{by}px;width:{w}px;transform:translate(-50%,-100%)">']
    for side, fx, fy in (("left", -0.299, -0.186), ("right", 0.35, -0.183)):
        if e.get(side):
            out.append(f'<div class="el scale-l" style="left:{cx + fx*w:.0f}px;top:{by + fy*w:.0f}px;font-size:{max(14, w*0.019):.0f}px">{md(e[side])}</div>')
    return "".join(out)

CAST = {}
FRAME_CHARS = []

def el_char(e, fid):
    """one of the team's six characters in a pose with an expression.
    {"type":"char","who":"rajesh"|"c1","pose":"idle","expr":"neutral","cx","by","h":420,"flip":false,
     "holding":"props/wheat_sack","hold_h":90,"label":"Rajesh","label_dy":-40}"""
    who = e["who"]
    cid = CAST.get(who, {}).get("char", who)
    if cid not in charrig.RIG:
        warn(fid, f"char '{who}': not in cast and not c1..c6"); return ""
    pose, expr = e.get("pose", "idle"), e.get("expr", "neutral")
    if pose not in charrig.POSES: warn(fid, f"unknown pose {pose}; use {sorted(charrig.POSES)}"); pose = "idle"
    if expr not in charrig.EXPRESSIONS: warn(fid, f"unknown expr {expr}; use {charrig.EXPRESSIONS}"); expr = "neutral"
    FRAME_CHARS.append((who, cid, pose, expr))
    svg, info = charrig.char_svg(cid, pose, expr, data_uri=asset(f"chars6/{cid}"))
    h = e.get("h", 420); s = h / info["h"]
    W_, H_ = (info["w"] + 2 * info["pad_x"]) * s, (info["h"] + info["pad_t"]) * s
    if e.get("x") is not None and e.get("y") is not None:
        left, top = e["x"], e["y"]
    else:
        left, top = e["cx"] - W_ / 2, e["by"] - H_
    flip = e.get("flip", False)
    tr = "transform:scaleX(-1);" if flip else ""
    z = f"z-index:{e['z']};" if e.get("z") is not None else ""
    out = [f'<div class="el charwrap" data-src="char:{cid}" style="left:{left:.0f}px;top:{top:.0f}px;width:{W_:.0f}px;height:{H_:.0f}px;{tr}{z}">'
           + svg.replace("<svg ", '<svg style="width:100%;height:100%" ', 1) + "</div>"]
    def to_frame(pt):
        lx, ly = pt
        x = e["cx"] + (lx - info["w"] / 2) * s * (-1 if flip else 1)
        y = e["by"] - (info["h"] - ly) * s
        return x, y
    if e.get("holding"):
        side = e.get("hold_side", "a")
        if side in info["hands"]:
            hx, hy = to_frame(info["hands"][side])
            ph = e.get("hold_h", h * 0.22)
            out.append(f'<img class="el img" src="{asset(e["holding"])}" data-src="{e["holding"]}" '
                       f'style="left:{hx:.0f}px;top:{hy + ph*0.35:.0f}px;height:{ph:.0f}px;transform:translate(-50%,-100%);z-index:{(e.get("z") or 10)+1}">')
    lab = e.get("label") or CAST.get(who, {}).get("name") if e.get("label", True) else None
    if lab and e.get("label") is not False:
        hy_top = e["by"] - h
        out.append(f'<div class="el pill it" style="left:{e["cx"]:.0f}px;top:{hy_top + e.get("label_dy", -70):.0f}px;transform:translateX(-50%);font-size:{e.get("label_size", 28)}px">{md(lab)}</div>')
    return "".join(out)

def el_html(e, fid):
    for hx in re.findall(r"#[0-9a-fA-F]{6}", e["html"]):
        if hx.upper() not in {v.upper() for v in C.values()}:
            warn(fid, f"html uses off-palette colour {hx}")
    return f'<div class="el" style="{pos(e)}">{e["html"]}</div>'

# ---------------------------------------------------------------- drawn props, bubbles, logos, OSA block
STYLE = {"buildings/tower_xyz": "flat"}      # everything else in assets/buildings + 3D props is "3d"
ASSET_AS = {}                                  # src -> {label: [frame ids]} for the repeat check
FRAME_SRCS = []
SERIES = {"theme": "light"}

def track(src, label, fid):
    FRAME_SRCS.append(src)
    if label:
        ASSET_AS.setdefault(src, {}).setdefault(label, []).append(fid)

LAYOUT_KEYS = {"type", "kind", "cx", "by", "w", "h", "z", "tilt", "flip", "opacity", "as"}
def el_prop(e, fid):
    """drawn story prop (scenes.PROPS): sack, stall, shop, calendar, document, timeline, handshake, lock,
    price_tag, arrow, truck, money. {"type":"prop","kind":"sack","cx","by","w", ...kind args}"""
    k = e["kind"]
    if k not in scenes.PROPS: warn(fid, f"unknown prop '{k}': {sorted(scenes.PROPS)}"); return ""
    args = {a: v for a, v in e.items() if a not in LAYOUT_KEYS}
    try: svg = scenes.PROPS[k](**args)
    except TypeError as ex: warn(fid, f"prop {k}: {ex}"); return ""
    track(f"prop:{k}", e.get("as") or args.get("sign") or args.get("label"), fid)
    tr = ["translate(-50%,-100%)"]
    if e.get("flip"): tr.append("scaleX(-1)")
    if e.get("tilt"): tr.append(f"rotate({e['tilt']}deg)")
    z = f"z-index:{e['z']};" if e.get("z") is not None else ""
    return (f'<div class="el prop" data-src="prop:{k}" style="left:{e["cx"]}px;top:{e["by"]}px;width:{e.get("w", 260)}px;'
            f'transform:{" ".join(tr)};{z}">{svg.replace("<svg ", "<svg style=\'width:100%;height:auto;display:block\' ", 1)}</div>')

def _content_html(e):
    parts = []
    if e.get("prop"):
        p = e["prop"]; args = {a: v for a, v in p.items() if a not in ("kind", "w")}
        parts.append(f'<div style="width:{p.get("w",120)}px">{scenes.PROPS[p["kind"]](**args).replace("<svg ", "<svg style=\'width:100%;height:auto;display:block\' ",1)}</div>')
    if e.get("img"):
        parts.append(f'<img src="{asset(e["img"])}" style="height:{e.get("img_h",90)}px">')
    if e.get("logo"):
        parts.append(logo_html(e["logo"], e.get("logo_h", 70), e.get("_fid", "")))
    txt = ""
    if e.get("text"): txt += f'<div class="bt">{md(e["text"])}</div>'
    if e.get("items"):
        txt += "".join(f'<div class="bi">{md(i)}</div>' for i in e["items"])
    if txt: parts.append(f'<div>{txt}</div>')
    return "".join(parts)

def el_bubble(e, fid):
    """thought / speech bubble holding a character's facts. {"type":"bubble","kind":"thought","x","y","w","h",
    "tail":[x,y] (frame coords, near the character's head), "text"|"items", "prop":{kind,...,w}, "img", "logo"}"""
    w, h = e.get("w", 420), e.get("h", 260)
    tx, ty = e.get("tail", [e["x"] + w * 0.2, e["y"] + h + 80])
    svg = scenes.bubble_svg(e.get("kind", "thought"), w, h, (tx - e["x"], ty - e["y"]))
    e = {**e, "_fid": fid}
    return (f'<div class="el bubble" style="left:{e["x"]}px;top:{e["y"]}px;width:{w}px;height:{h}px;font-size:{e.get("size",32)}px">'
            f'{svg}<div class="bc" style="padding:{h*0.18:.0f}px {w*0.16:.0f}px">{_content_html(e)}</div></div>')

_LISTED = None
def _listed():
    """all ~3,150 NSE/BSE-listed company logo tiles packed in one file: {TICKER: {name, svg}}"""
    global _LISTED
    if _LISTED is None:
        import gzip
        f = A / "logos" / "listed_logos.json.gz"
        _LISTED = json.loads(gzip.open(f).read()) if f.exists() else {}
    return _LISTED

def logo_data(name):
    """1) assets/logos/<name>.svg|png (institutions: nse, sebi, rbi...), 2) listed-company tile by NSE/BSE
    ticker (SBIN, HDFCBANK, BAJAJ_AUTO), 3) company-name match ("State Bank of India").
    Returns (bytes, mime, is_tile) or None."""
    for ext, mime in ((".svg", "image/svg+xml"), (".png", "image/png"), (".jpg", "image/jpeg")):
        p = A / "logos" / f"{name}{ext}"
        if p.exists(): return p.read_bytes(), mime, False
    L = _listed()
    t = re.sub(r"[^A-Z0-9&-]", "_", name.upper())
    hit = L.get(t)
    if not hit:
        q = name.casefold().replace("limited", "").replace("ltd", "").strip()
        hits = [v for v in L.values() if len(q) >= 4 and re.search(r"\b" + re.escape(q) + r"\b", v["name"].casefold())]
        hit = min(hits, key=lambda v: len(v["name"])) if hits else None
    return (hit["svg"].encode(), "image/svg+xml", True) if hit else None

def logo_html(name, h, fid):
    d = logo_data(name)
    if not d:
        warn(fid, f"logo '{name}' missing: add assets/logos/{name}.svg|png (or attach it) - placeholder used")
        return f'<span class="logo-missing" style="height:{h}px;line-height:{h}px">{html.escape(name.upper())} LOGO</span>'
    data, mime, tile = d
    uri = f"data:{mime};base64," + base64.b64encode(data).decode()
    rad = f";border-radius:{int(h*0.22)}px" if tile else ""
    return f'<img src="{uri}" style="height:{h}px;max-width:{h*4}px;object-fit:contain{rad}">'

def el_logo(e, fid):
    """real organisation/company logo on a white card. {"type":"logo","name":"nse","x","y","h":80,"card":true,"align"}"""
    track(f"logo:{e['name']}", e["name"], fid)
    inner = logo_html(e["name"], e.get("h", 80), fid)
    cls = "el logo-card" if e.get("card", True) else "el"
    return f'<div class="{cls}" style="{pos({**e, "h": None})}">{inner}</div>'

OSA_X, OSA_HDR_Y, OSA_Y, OSA_W = 120, 250, 370, 820
def el_osa(e, fid):
    """the one layout for content beside the presenter: header + one block at fixed positions.
    kind: quote | list | tags | formula | calc | text. theme comes from spec "series" (futures = dark)."""
    theme = e.get("theme", SERIES["theme"])
    k = e.get("kind", "quote")
    out = []
    if e.get("header"):
        hcls = "osa-h dark" if theme == "dark" else "osa-h"
        out.append(f'<div class="el {hcls}" style="left:{OSA_X}px;top:{OSA_HDR_Y}px">{md(e["header"])}</div>')
    body = ""
    if k == "quote": body = f'<div class="quote">“{md(e["text"])}”</div>'
    elif k == "text": body = f'<div class="ctext">{md(e["text"])}</div>'
    elif k == "list":
        rows = []
        for i, it in enumerate(e["items"]):
            it = it if isinstance(it, dict) else {"text": it}
            if it.get("icon", "").startswith("logo:"): ic = logo_html(it["icon"][5:], 52, fid)
            elif it.get("icon", "").startswith("prop:"):
                pk = it["icon"][5:]; ic = scenes.PROPS[pk]().replace("<svg ", "<svg style='width:56px;height:56px' ", 1)
            elif it.get("icon"): ic = f'<img src="{asset(it["icon"])}" style="max-width:58px;max-height:58px">'
            else: ic = f'<span class="num">{i+1}</span>'
            act = e.get("active")
            cls = "orow" + (" dim" if act is not None and i != act and e.get("fade_rest", True) else "") + (" on" if act == i else "")
            rows.append(f'<div class="{cls}"><span class="oic">{ic}</span><span>{md(it["text"])}</span></div>')
        body = "".join(rows)
    elif k == "tags":
        body = "".join(f'<div class="otag"><span class="ol">{md(t.get("label",""))}</span><span class="ov">{md(t["value"])}</span></div>' for t in e["items"])
    elif k in ("formula", "calc"):
        return "".join(out) + el_card({**e, "kind": k, "x": OSA_X, "y": OSA_Y, "w": OSA_W, "glass": theme != "dark",
                                       **({"pad": None} if theme != "dark" else {})}, fid).replace('class="el card', f'class="el card {"darkcard" if theme=="dark" else ""}', 1)
    ccls = "darkcard" if theme == "dark" else "glass"
    out.append(f'<div class="el card osa-b {ccls} osa-{k}" style="left:{OSA_X}px;top:{OSA_Y}px;width:{OSA_W}px;font-size:{e.get("size", 34)}px">{body}</div>')
    return "".join(out)

RENDER = {"text": el_text, "header": el_header, "img": el_img, "card": el_card, "bigword": el_bigword,
          "bar": el_chart, "line": el_chart, "window": el_window, "linecards": el_linecards, "pie": el_pie,
          "phone": el_phone, "cardset": el_cardset, "module": el_module, "takeaways": el_takeaways,
          "shape": el_shape, "tri": el_tri, "scale": el_scale, "char": el_char, "prop": el_prop, "bubble": el_bubble, "logo": el_logo, "osa": el_osa, "html": el_html}
NEEDS_SVG = {"pill": el_pill, "pills": el_pills, "split": el_split, "coinflow": el_coinflow,
             "branch": el_branch, "arrow": el_arrow}

# ---------------------------------------------------------------- frame
def background(f):
    mode = f.get("mode", "fss")
    layers = []
    if f.get("backdrop"):
        FRAME_SRCS.append("backdrop:" + f["backdrop"])
        layers.append(scenes.backdrop_svg(f["backdrop"], f.get("seed")))
        layers.append(f'<img class="eye" src="{asset("plates/varsity_eye")}"' + (' style="left:1716px"' if f.get("eye") == "right" else '') + '>')
        return "".join(layers)
    if mode == "blur":
        layers.append('<div class="bg"></div>')
        if f.get("blur_src"):
            layers.append(f'<img class="bgblur" src="{asset(f["blur_src"])}">')
    else:
        layers.append('<div class="bg"></div>' if mode != "takeaways" else '<div class="bg bg-light"></div>')
    layers.append(f'<img class="lineart l" src="{asset("plates/lineart_left")}">')
    layers.append(f'<img class="lineart r" src="{asset("plates/lineart_right")}">')
    if f.get("floor", mode in ("fss",)):
        layers.append(f'<img class="floor" src="{asset("plates/floor")}">')
    if mode == "osa":
        layers.append(f'<img class="anchor" src="{asset("plates/anchor_right")}">')
    if mode == "osa_center":
        layers.append(f'<img class="anchor" src="{asset("plates/anchor_center")}">')
    top_left_busy = any(e.get("y", 999) < 170 and e.get("x", 999) < 420 and e.get("align") not in ("center", "right")
                        for e in f.get("els", []) if e.get("type") in ("header", "text", "pill"))
    eye_right = f.get("eye") == "right" or (f.get("eye") is None and top_left_busy)
    layers.append(f'<img class="eye" src="{asset("plates/varsity_eye")}"' + (' style="left:1716px"' if eye_right else '') + '>')
    if f.get("sparkle", True):
        sx, sy = f.get("sparkle_at", (1750, 230) if eye_right else (1750, 150))
        layers.append(f'<img class="sparkle" src="{asset("plates/sparkle")}" style="left:{sx}px;top:{sy}px">')
    for (cx, cy, sz) in f.get("deco_coins", [(96, 560, 56), (1806, 660, 40)] if mode not in ("takeaways",) else []):
        layers.append(f'<img class="deco-coin" src="{asset("props/coin")}" style="left:{cx}px;top:{cy}px;width:{sz}px">')
    return "".join(layers)

_INLINE_FA = {"text": "text", "pill": "text", "header": "text", "card": "text", "bigword": "text", "osa": "text"}
_RESIZE_FA = {
    "img": "wh", "char": "wh", "card": "w", "bar": "wh", "line": "wh", "pie": "wh",
    "window": "wh", "bubble": "wh", "prop": "wh", "text": "font", "header": "font", "pill": "font",
}


def _fa_layer_label(e):
    t = e.get("type") or "?"
    if t in ("char", "prop"):
        return t, str(e.get("who") or e.get("kind") or t)[:32]
    if t == "img":
        return t, str(e.get("src") or "")[-28:]
    if t == "header":
        return t, str(e.get("text") or e.get("lead") or "")[:32]
    if t == "card":
        return t, str(e.get("title") or e.get("text") or "")[:32]
    for k in ("text", "title", "header", "who", "kind"):
        if e.get(k):
            return t, str(e[k])[:32]
    return t, ""


def _fa_edit_attrs(idx, e, edit):
    if not edit:
        return "", ""
    lt, ll = _fa_layer_label(e)
    attrs = (
        f' data-spec-idx="{idx}" data-mf-path="els.{idx}"'
        f' data-layer-type="{html.escape(lt)}" data-layer-label="{html.escape(ll)}"'
    )
    et = e.get("type")
    if et in _INLINE_FA:
        attrs += f' data-inline-field="{_INLINE_FA[et]}"'
    if et in _RESIZE_FA:
        attrs += f' data-resize="{_RESIZE_FA[et]}"'
    return attrs, 'studio-editable'


def _fa_wrap_edit(html, idx, e, edit):
    if not edit or not html:
        return html
    attrs, cls = _fa_edit_attrs(idx, e, edit)

    def _add_cls(m):
        c = m.group(1)
        if "studio-editable" not in c:
            c = (c + " studio-editable").strip()
        return f'class="{c}"{attrs}'

    out, n = re.subn(r'class="([^"]*)"', _add_cls, html, count=1)
    if n:
        return out
    return f'<div class="{cls}"{attrs}>{html}</div>'


def frame_html(f, look=None, edit=False, all_frames=None, overlay=False):
    _ = look, all_frames
    fonts = font_css()
    fid = f["id"]
    FRAME_CHARS.clear(); FRAME_SRCS.clear()
    svg, body = [], []
    for idx, e in enumerate(f.get("els", [])):
        t = e["type"]
        try:
            if t in NEEDS_SVG:
                body.append(_fa_wrap_edit(NEEDS_SVG[t](e, fid, svg), idx, e, edit))
            elif t in RENDER:
                body.append(_fa_wrap_edit(RENDER[t](e, fid), idx, e, edit))
            else:
                warn(fid, f"unknown element type '{t}'")
        except FileNotFoundError as ex:
            warn(fid, str(ex))
        except KeyError as ex:
            warn(fid, f"{t}: missing field {ex}")
    if FRAME_CHARS:
        ids = [c[1] for c in FRAME_CHARS]
        for c in set(ids):
            if ids.count(c) > 1: warn(fid, f"character {c} appears {ids.count(c)}x in one frame: give each person a different character")
        pe = [(c[2], c[3]) for c in FRAME_CHARS]
        if len(pe) > 1 and len(set(pe)) < len(pe): warn(fid, "two people share the same pose + expression: vary them")
        if f.get("mode", "fss").startswith("osa") and not f.get("allow_chars"):
            warn(fid, "characters in an OSA frame: only when the storyboard asks (set allow_chars)")
        names = [c[0] for c in FRAME_CHARS]
        for n in names:
            if n in CAST:
                pass
    styles = {STYLE.get(x, "3d") for x in FRAME_SRCS if x.startswith("buildings/")}
    if len(styles) > 1: warn(fid, "flat and 3D buildings mixed in one frame: use one style")
    if f.get("backdrop") and any(x.startswith("buildings/") for x in FRAME_SRCS):
        warn(fid, "3D building on a drawn backdrop: use drawn props (shop, stall...) or a 3D frame without backdrop")
    for x in set(FRAME_SRCS):
        if x.startswith(("buildings/", "props/factory")) and FRAME_SRCS.count(x) > 1 and not f.get("allow_repeat"):
            warn(fid, f"{x} used {FRAME_SRCS.count(x)}x in one frame: different things need different assets/logos")
    anchor_front = ""
    if f.get("mode") in ("osa", "osa_center") and f.get("anchor_front"):
        src = "plates/anchor_right" if f["mode"] == "osa" else "plates/anchor_center"
        anchor_front = f'<img class="anchor front" src="{asset(src)}">'
    bg = "" if overlay else background(f)
    ov = " overlay" if overlay else ""
    stage_cls = f'mode-{f.get("mode", "fss")}{ov}'
    body_cls = "studio-edit-mode" if edit else ""
    return (f'<!doctype html><html class="{ov.strip()}"><head><meta charset="utf-8"><title>{html.escape(fid)} {html.escape(f.get("name",""))}</title>'
            f'<style>{fonts}\n{CSS}</style></head><body class="{body_cls}"><div id="stage" class="{stage_cls}">'
            f'{bg}{"".join(body)}{svg_layer("".join(svg), f.get("svg_z", 6))}{"" if overlay else anchor_front}</div></body></html>')

# ---------------------------------------------------------------- checks
def text_checks(f):
    fid = f["id"]
    txt = json.dumps(f.get("els", []), ensure_ascii=False)
    words = re.findall(r"[A-Za-z]+", " ".join(re.findall(r'"(?:text|title|sub|lead|tail|label|items|term|num|den|rhs|value|result)"\s*:\s*("(?:[^"\\]|\\.)*"|\[[^\]]*\])', txt)))
    hits = sorted({w for w in words if w.lower() in HINGLISH})
    if hits: warn(fid, f"Hinglish words on screen: {hits} (rewrite in English)")
    if re.search(r"₹\s*-?\d[\d,.]*\s*%", txt): warn(fid, "₹ in front of a percentage")
    if re.search(r"price\s*to\s*equity", txt, re.I): warn(fid, "'Price to Equity': P/E is Price to Earnings")
    for g in ("green", "coral"):
        boxes = [e for e in f.get("els", []) if e.get("type") not in ("bar", "line", "pie", "prop", "bubble")]
        if re.search(rf'"(hl|title_hl|color)"\s*:\s*"{g}"', json.dumps(boxes)):
            warn(fid, f"{g} used on a box/highlight: green and red go only on data marks and BUY/SELL")

JS_CHECK = """
() => { const out=[]; const stage=document.getElementById('stage').getBoundingClientRect();
 const osa = document.getElementById('stage').classList.contains('mode-osa');
 document.querySelectorAll('.el').forEach(el=>{ const r=el.getBoundingClientRect(); if(!r.width) return;
   const name=(el.className+' '+(el.innerText||el.dataset.src||'').slice(0,30)).replace(/\\s+/g,' ');
   const deco=el.classList.contains('img')||el.classList.contains('charwrap')||el.classList.contains('prop')||el.classList.contains('swoosh')||el.classList.contains('road')||el.classList.contains('bigword');
   if(!deco && (r.left<-4||r.top<-4||r.right>1924||r.bottom>1084)) out.push('off-frame: '+name+' '+[r.left,r.top,r.right,r.bottom].map(Math.round));
   if(osa && !el.classList.contains('img') && !el.classList.contains('deco') && r.right>1010 && r.top<760) out.push('crosses the presenter (keep text left of x=1000): '+name);
   if(el.classList.contains('bubble')){const c=el.querySelector('.bc'); if(c && (c.scrollWidth>c.clientWidth+2||c.scrollHeight>c.clientHeight+2)) out.push('bubble text overflows: make the bubble bigger or the text shorter');}
   if((el.classList.contains('card')||el.classList.contains('pill')) && (el.scrollWidth>el.clientWidth+2||el.scrollHeight>el.clientHeight+2)) out.push('text overflows its box: '+name);
 }); return out; }
"""

CONFUSABLE = {r"\bfloor mill": "Flour Mill", r"\bprinciple amount": "principal amount", r"\bstationary\b": "stationery?",
              r"\bloose\b": "lose?", r"\bcompliment": "complement?", r"\bbreath\b": "breadth?", r"\bpreceed": "precede",
              r"\bseperat": "separat-", r"\boccured": "occurred", r"\brecieve": "receive", r"\bdefinate": "definite"}
DOMAIN = set("""ebitda pat roe roce eps nse bse mcx ncdex sebi rbi nifty sensex kite zerodha varsity futures options hedging
crore crores lakh lakhs rupee standardised favourable counterparty organised colour behaviour analyse centre programme labour licence realise utilise bajaj calc payables watchlist nifty50 debentures fno f&o p/e p/b p/s dcf fcf ipo etf etfs amc mf demat kyc mandi atta chakki rajesh ltp ohlc""".split())

def spell_check(text):
    low = text.lower()
    for pat, fix in CONFUSABLE.items():
        if re.search(pat, low): WARN.append(f"WARN [spell] '{re.search(pat, low).group(0)}' -> {fix}")
    try:
        from spellchecker import SpellChecker
    except ImportError:
        return
    sc = SpellChecker()
    words = {w for w in re.findall(r"[A-Za-z]{4,}", text) if not w.isupper()}
    bad = sorted(w for w in sc.unknown([w.lower() for w in words]) if w not in DOMAIN)
    if bad: WARN.append(f"WARN [spell] check these words: {bad[:30]}")

# ---------------------------------------------------------------- main
def slug(s):
    return re.sub(r"[^A-Za-z0-9&.+-]+", "-", s).strip("-")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--out", default="out")
    ap.add_argument("--only", default=""); ap.add_argument("--package", default="")
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text())
    CAST.update(spec.get("cast", {}))
    SERIES["theme"] = "dark" if spec.get("series") == "futures" or spec.get("osa_theme") == "dark" else "light"
    used = {}
    for k, v in CAST.items():
        if v.get("char") in used: print(f"WARN [cast] {k} and {used[v['char']]} share {v['char']}: one character per person")
        used[v.get("char")] = k
    out = Path(a.out); (out / "PNG").mkdir(parents=True, exist_ok=True); (out / "HTML").mkdir(parents=True, exist_ok=True)
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    frames = [f for f in spec["frames"] if not only or f["id"] in only]
    fonts = font_css()
    from playwright.sync_api import sync_playwright
    names, texts = [], []
    with sync_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM_PATH"]} if os.environ.get("CHROMIUM_PATH") else {}
        br = p.chromium.launch(**kw)
        pg = br.new_page(viewport={"width": W, "height": H})
        for f in frames:
            text_checks(f)
            name = f'{f["id"]}_{slug(f.get("name", "frame"))}'
            h = frame_html(f)
            (out / "HTML" / f"{name}.html").write_text(h)
            pg.set_content(h, wait_until="load")
            pg.evaluate("document.fonts.ready")
            for m in pg.evaluate(JS_CHECK): warn(f["id"], m)
            if f.get("mode", "fss").startswith("osa") and spec.get("osa_overlay", True):
                # editor gets a transparent overlay (any presenter); the preview shows it on a plate
                pg.screenshot(path=str(out / "PNG" / f"{name}_preview.png"), clip={"x": 0, "y": 0, "width": W, "height": H})
                ho = frame_html(f, overlay=True)
                (out / "HTML" / f"{name}.html").write_text(ho)
                pg.set_content(ho, wait_until="load"); pg.evaluate("document.fonts.ready")
                pg.screenshot(path=str(out / "PNG" / f"{name}.png"), clip={"x": 0, "y": 0, "width": W, "height": H}, omit_background=True)
                pg.set_content(h, wait_until="load"); pg.evaluate("document.fonts.ready")
            else:
                pg.screenshot(path=str(out / "PNG" / f"{name}.png"), clip={"x": 0, "y": 0, "width": W, "height": H})
            texts.append(f"[{name}]\n" + pg.evaluate("document.getElementById('stage').innerText").strip() + "\n")
            names.append(name); print("built", name, flush=True)
        br.close()
    (out / "_text.txt").write_text("\n".join(texts))
    for src, labels in ASSET_AS.items():
        if len(labels) > 1 and not src.startswith(("logo:", "prop:sack", "prop:price_tag", "prop:arrow", "prop:money")):
            WARN.append(f"WARN [video] {src} is used for different things: {sorted(labels)}. Give each its own asset or logo")
    spell_check("\n".join(texts))
    # contact sheets
    from PIL import Image, ImageDraw
    def tkey(p):
        m = re.match(r"^(\d+)\.(\d+)", p.stem)
        return (int(m.group(1)) * 60 + int(m.group(2)) if m else 10 ** 6, p.stem)
    allpng = sorted([p for p in (out / "PNG").glob("*.png") if not p.stem.endswith("_preview") or True], key=tkey)
    allpng = [p for p in allpng if not (out / "PNG" / f"{p.stem}_preview.png").exists()]
    for si in range(0, len(allpng), 6):
        sheet = Image.new("RGB", (1920, 1080 // 2 * 3 + 90), "white"); d = ImageDraw.Draw(sheet)
        for j, pth in enumerate(allpng[si:si + 6]):
            im = Image.open(pth).convert("RGB").resize((960, 540))
            x, y = (j % 2) * 960, (j // 2) * 570
            sheet.paste(im, (x, y + 30)); d.text((x + 10, y + 6), pth.stem, fill="black")
        sheet.save(out / f"_sheet_{si // 6 + 1}.jpg", quality=85)
    for w_ in WARN: print(w_)
    print(f"{len(names)} frames, {len(WARN)} warnings")
    if a.package:
        z = out / f"{a.package}.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for pth in sorted((out / "PNG").glob("*.png")): zf.write(pth, f"{a.package}/PNG/{pth.name}")
            for pth in sorted((out / "HTML").glob("*.html")): zf.write(pth, f"{a.package}/HTML/{pth.name}")
        print("package:", z)

if __name__ == "__main__":
    main()

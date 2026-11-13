#!/usr/bin/env python3
"""Zerodha Online · Product IP graphics: build every frame of a video from ONE JSON spec.

Usage:  python3 scripts/build.py spec.json [--out out] [--only 3,7a] [--no-sheet]

Renders ONLY full-screen (mode "fss") frames. Anchor beats (osa/ost/tos) are storyboard notes for the editor and are skipped.
Writes <out>/_html/<id>.html, <out>/<id>.png,
<out>/_sheet_N.jpg (QA contact sheets), and prints WARN lines (off-frame, covers anchor face, clipped, tiny text,
off-palette, "~", mixed digit grouping).
Spec format: references/spec_format.md · working example: scenes/example_spec.json
"""
import json, os, sys, html, re, math, random, asyncio
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANVAS_W, CANVAS_H = 1920, 1080
CANVAS = (CANVAS_W, CANVAS_H)
E = html.escape
_pj = os.path.join(KIT, 'assets', 'plates', 'plates.json')
PLATES = json.load(open(_pj)) if os.path.exists(_pj) else {}
_PLATE_KEYS = frozenset(PLATES.keys()) if PLATES else frozenset({
    'm1_wide_centre', 'm1_mid_centre', 'm1_close_left', 'm1_tos',
    'f1_left_circle', 'f1_centre_circle', 'f1_centre', 'f1_close_right',
    'm2_centre', 'm2_centre_dark', 'm2_left', 'm2_right',
})
_SIDE_PANEL = frozenset({'side_list', 'scroll_list', 'ladder', 'mini_table', 'ticket'})


def _resolve_plate(f, look):
    mode = f.get('mode', 'fss')
    if mode == 'fss':
        return None
    raw = f.get('plate') or (look or {}).get('plate') or 'm1_wide_centre'
    if raw in ('', 'default', None):
        raw = 'm1_wide_centre'
    if mode == 'tos':
        return 'm1_tos' if 'm1_tos' in _PLATE_KEYS else raw
    types = {it.get('t') for it in (f.get('items') or []) if isinstance(it, dict)}
    if types & _SIDE_PANEL and 'm1_close_left' in _PLATE_KEYS:
        return 'm1_close_left'
    if 'objcards' in types and 'm2_centre_dark' in _PLATE_KEYS:
        return 'm2_centre_dark'
    if raw in _PLATE_KEYS:
        return raw
    return 'm1_wide_centre' if 'm1_wide_centre' in _PLATE_KEYS else next(iter(_PLATE_KEYS), raw)

def md(s):
    """**yellow**  ++blue++  __bold__  {g:green} {o:orange}  | = line break"""
    s = E(str(s))
    s = re.sub(r'\*\*(.+?)\*\*', r'<span class="k-y">\1</span>', s)
    s = re.sub(r'\+\+(.+?)\+\+', r'<span class="k-b">\1</span>', s)
    s = re.sub(r'__(.+?)__', r'<b>\1</b>', s)
    s = re.sub(r'\{g:(.+?)\}', r'<span class="k-g">\1</span>', s)
    s = re.sub(r'\{o:(.+?)\}', r'<span class="k-o">\1</span>', s)
    return s.replace('|', '<br>')

def asset(src):
    if not src: return ''
    if src.startswith('<svg'): return src
    if src.startswith('svg:'): return icon(src[4:], 120)
    p = src if '/' in src else f'illus/{src}'
    if not re.search(r'\.(png|svg|jpe?g|webp)$', p): p += '.png'
    return f'<img src="../assets/{p}">'

LOCK = '<svg width="26" height="30" viewBox="0 0 26 30"><rect x="2" y="12" width="22" height="17" rx="4" fill="#222"/><path d="M7 12V8a6 6 0 0 1 12 0v4" stroke="#222" stroke-width="3.5" fill="none"/></svg>'
TINT = {'blue': '#E6F0FC', 'green': '#E3F3E4', 'yellow': '#FFF4D6', 'orange': '#FDE8DE', 'purple': '#EFE9FC', 'grey': '#EFEFEF', 'none': 'transparent'}

# ======================================================================= ANCHOR components
def lower(i):
    lead = f'<div class="lead">{md(i["lead"])}</div>' if i.get('lead') else ''
    return f'<div class="lower" style="font-size:{i.get("size",66)}px">{lead}<div>{md(i["text"])}</div></div>'

def punch(i):
    al = i.get('align', 'left')
    lead = f'<div class="lead">{md(i["lead"])}</div>' if i.get('lead') else ''
    tail = f'<div class="tail">{md(i["tail"])}</div>' if i.get('tail') else ''
    ks = i.get('key_size') or (180 if len(i['key']) <= 9 else 130)
    return f'<div class="punch" style="text-align:{al}">{lead}<div class="key {i.get("color","")}" style="font-size:{ks}px">{md(i["key"])}</div>{tail}</div>'

def bignum(i):
    lead = f'<div class="lead">{md(i["lead"])}</div>' if i.get('lead') else ''
    sub = f'<div class="sub">{md(i["sub"])}</div>' if i.get('sub') else ''
    val = f'<div class="val" style="font-size:{i.get("size",140)}px">{md(i["value"])}</div>'
    if i.get('boxed'):
        val = f'<div class="box"><span class="val" style="font-size:{i.get("size",136)}px">{md(i["value"])}</span><small>{md(i.get("unit",""))}</small></div>'
    return f'<div class="bignum" style="text-align:{i.get("align","left")}">{lead}{sub}{val}</div>'

def side_list(i):
    a = i.get('active', 'all'); rows = ''
    for n, r in enumerate(i['rows']):
        off = '' if a == 'all' or n <= (a if isinstance(a, int) else 99) else 'off'
        if isinstance(a, int) and i.get('only_active') and n != a: off = 'off'
        rows += f'<div class="a {off}">{md(r[0])}</div><div class="op {off}">{E(i.get("op","→"))}</div><div class="{off}">{md(r[1])}</div>'
    hd = f'<div class="side-h">{md(i["heading"])}</div>' if i.get('heading') else ''
    return f'<div>{hd}<div class="side-rows">{rows}</div></div>'

def scroll_list(i):
    a = i.get('active', 0); n = len(i['items'])
    lis = ''.join(f'<li class="{"on" if k == a else ""}">{md(t)}</li>' for k, t in enumerate(i['items']))
    top = 100 * (a + .5) / n
    hd = f'<div class="hd">{md(i["heading"])}</div>' if i.get('heading') else ''
    return f'<div>{hd}<div class="scroll"><div class="rail"><i style="top:calc({top}% - 30px)"></i></div><ul>{lis}</ul></div></div>'

def objcards(i):
    parts = []
    for k, c in enumerate(i['items']):
        cap = f'<div class="objcap">{md(c["caption"])}</div>' if c.get('caption') else ''
        img = asset(c.get('icon'))
        inner = (f'{img}<div class="sep"></div><b>{md(c["label"])}</b>') if c.get('icon_side', 'left') == 'left' else (f'<b>{md(c["label"])}</b><div class="sep"></div>{img}')
        parts.append(f'<div style="display:flex;flex-direction:column;align-items:center"><div class="obj {c.get("color","yellow")}">{inner}</div>{cap}</div>')
        if k == 0 and i.get('between'):
            b = i['between']
            sub = f'<span>{md(b["sub"])}</span>' if b.get("sub") else ""
            parts.append(f'<div class="between"><b>{md(b.get("text",""))}</b>{sub}</div>' if isinstance(b, dict)
                         else f'<div style="width:120px;text-align:center;font-size:80px;color:#fff">{E(b)}</div>')
    alert = ''
    if i.get('alert'):
        alert = (f'<div style="text-align:center;margin-bottom:26px;color:#fff;font-size:34px;font-weight:600">'
                 f'<svg width="90" height="80" viewBox="0 0 90 80"><path d="M45 4 L86 76 H4 Z" fill="#E5534B" stroke="#fff" stroke-width="5"/>'
                 f'<rect x="41" y="28" width="8" height="26" fill="#fff"/><circle cx="45" cy="64" r="5" fill="#fff"/></svg><br>{md(i["alert"])}</div>')
    return f'<div>{alert}<div class="objrow" style="gap:{i.get("gap",40)}px">{"".join(parts)}</div></div>'

def ticket(i):
    rows = ''.join(f'<div class="row {"em" if n == i.get("em", len(i["rows"])-1) else ""}"><span>{md(r[0])}</span><span>{md(r[1])}</span></div>'
                   for n, r in enumerate(i['rows']))
    chip = f'<span class="chip">{E(i["chip"])}</span>' if i.get('chip') else ''
    bt = i.get('button', True); btn = f'<div class="btn" style="{"width:auto;padding:0 34px;font-size:34px" if isinstance(bt, str) else ""}">{E(bt) if isinstance(bt, str) else "→"}</div>' if bt else ''
    return f'<div class="ticket"><div class="top"><div class="ic">{asset(i.get("icon"))}</div><div><h2>{md(i["title"])}</h2>{chip}</div></div>{rows}{btn}</div>'

def mini_table(i):
    hc = i.get('head_colors', ['', 'y'])
    th = '<th style="background:none"></th>' + ''.join(f'<th class="{hc[n] if n < len(hc) else ""}">{md(h)}</th>' for n, h in enumerate(i['head']))
    rows = ''.join('<tr><td class="lab">' + md(r[0]) + '</td>' + ''.join(f'<td>{md(c)}</td>' for c in r[1:]) + '</tr>' for r in i['rows'])
    return f'<table class="mtable">{"<tr>"+th+"</tr>"}{rows}</table>'

def ladder(i):
    segs = i['segments']  # bottom → top: {left, right, pct, color}
    bar = ''.join(f'<div style="height:{s["pct"]}%;background:var(--{s.get("color","yellow")})"></div>' for s in segs)
    L = ''.join(f'<div style="height:{s["pct"]}%">{md(s["left"])}</div>' for s in segs)
    R = ''.join(f'<div class="r" style="height:{s["pct"]}%">{md(s["right"])}</div>' for s in segs)
    return f'<div class="ladder"><div class="lbl" style="text-align:right;align-items:flex-end">{L}</div><div class="bar">{bar}</div><div class="lbl">{R}</div><div class="cap">{md(i.get("caption",""))}</div></div>'

# ======================================================================= shared
def note(i):
    loop = '<svg class="loop" viewBox="0 0 150 80"><path d="M5 40 C20 5,35 5,30 40 C25 70,50 70,55 35 C60 5,80 10,75 45 C70 75,95 70,100 40 C105 15,125 20,120 50 C118 62,130 70,145 62" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/></svg>'
    hd = f'<div class="hd">{md(i["lead"])}</div>' if i.get('lead') else ''
    return (f'<div class="note" style="--w:{i.get("w",1100)}px;--ns:{i.get("size",44)}px"><div class="t">{loop}<u>{md(i.get("title","Important note"))}</u></div>'
            f'<div class="box">{hd}{md(i["text"])}</div><div class="base"></div></div>')

def text(i):
    return f'<div style="font-size:{i.get("size",36)}px;font-weight:{i.get("weight",500)};color:{i.get("color","inherit")};text-align:{i.get("align","center")};line-height:1.25">{md(i["text"])}</div>'

def img(i):
    return f'<div style="text-align:center"><img src="../assets/{i["src"] if "/" in i["src"] else "illus/"+i["src"]}{"" if i["src"].endswith(".png") else ".png"}" style="width:{i.get("w","auto")}{"px" if isinstance(i.get("w"),int) else ""};height:{i.get("h","auto")}{"px" if isinstance(i.get("h"),int) else ""}"></div>'

def pillv(i): return f'<div style="text-align:center"><span class="pillv {i.get("color","")}">{md(i["text"])}</span></div>'

# ======================================================================= FSS components
def heading(i):
    cls = 'heading ' + ('left ' if i.get('align') == 'left' else '') + ('ul' if i.get('underline') else '')
    t = md(i['text'])
    if i.get('pill'): t = f'<span class="pill">{t}</span>'
    if i.get('underline'): t = f'<span class="u">{t}</span>'
    sub = f'<div class="subhead" style="color:var(--{i.get("sub_color","grey")})">{md(i["sub"])}</div>' if i.get('sub') else ''
    if i.get('icon'):
        s2 = f'<span>{md(i["line2"])}</span>' if i.get('line2') else ''
        return f'<div class="ihead"><div class="ic">{asset(i["icon"])}</div><div><b>{md(i["text"])}</b>{s2}</div></div>'
    return f'<div><div class="{cls}">{t}</div>{sub}</div>'

def _sq_grid(n, color, cell=None):
    cols = 10 if n > 10 else n; rows = math.ceil(n / cols)
    cell = cell or (34 if n > 10 else 110)
    return f'<div class="sq" style="grid-template-columns:repeat({cols},{cell}px)">' + ''.join(f'<i style="width:{cell}px;height:{cell}px;background:var(--{color})"></i>' for _ in range(n)) + '</div>'

def _col(c, ih):
    out = []
    if c.get('top'): out.append(f'<div class="top">{md(c["top"])}</div>')
    if c.get('tag'): out.append(f'<span class="pillv {c.get("tag_color","yellow")}">{md(c["tag"])}</span>')
    if c.get('squares'):
        out.append(f'<div class="ill">{_sq_grid(c["squares"], c.get("sq_color","green"))}</div>')
    elif c.get('img'):
        im = asset(c['img'])
        if c.get('disc'): im = f'<div class="disc" style="background:{TINT.get(c["disc"],c["disc"])}">{im}</div>'
        out.append(f'<div class="ill" style="--ih:{c.get("ih",ih)}px">{im}</div>')
    if c.get('value'): out.append(f'<span class="pillv {c.get("value_color","yellow")}" style="font-size:{c.get("value_size",44)}px">{md(c["value"])}</span>')
    if c.get('caption'): out.append(f'<div class="cap">{md(c["caption"])}</div>')
    return f'<div class="col">{"".join(out)}</div>'

def compare(i):
    ih = i.get('ih', 360)
    op = f'<div class="opmid">{E(i["op"])}</div>' if i.get('op') else ''
    div = '' if i.get('op') else f'<div class="div {i.get("divider","dashed")}"></div>'
    return f'<div class="cmp">{_col(i["left"], ih)}{div or op}{_col(i["right"], ih)}</div>'

def hub2(i):
    hc = i.get('hub_color', 'blue'); d = i.get('hub_size', 230)
    hub_sub = f'<small>{E(i.get("hub_sub", ""))}</small>' if i.get("hub_sub") else ""
    hub = (
        f'<div class="hubc" style="width:{d}px;height:{d}px;background:var(--{hc});font-size:{int(d*0.3)}px">'
        f'{md(i["hub"])}{hub_sub}</div>'
        if i.get("hub") and d
        else '<div style="height:60px"></div>'
    )
    arms = ''; act = i.get('active')
    for n_, a in enumerate(i['arms']):
        sub = f'<small>{E(a["sub"])}</small>' if a.get('sub') else ''
        facts = f'<div class="fact">{md(a["fact"])}</div>' if a.get('fact') else ''
        bl = '<ul class="bullets">' + ''.join(f'<li>{md(b)}</li>' for b in a.get('bullets', [])) + '</ul>' if a.get('bullets') else ''
        im = f'<div style="display:flex;gap:40px">{"".join(asset(x) for x in a["imgs"])}</div>' if a.get('imgs') else ''
        arms += f'<div class="arm" style="{"opacity:.3" if act is not None and act != n_ else ""}"><div class="bigpill {a.get("color","green")}">{md(a["label"])}{sub}</div>{facts}{bl}{im}</div>'
    svg = ('<svg width="100%" height="110" viewBox="0 0 1300 110" preserveAspectRatio="none" style="position:absolute;left:0;top:-115px">'
           '<path d="M330 105 C 420 10, 560 0, 650 0 C 740 0, 880 10, 970 105" fill="none" stroke="#4993E9" stroke-width="4"/>'
           '<circle cx="420" cy="38" r="9" fill="#fff" stroke="#4993E9" stroke-width="4"/><circle cx="880" cy="38" r="9" fill="#fff" stroke="#4CAF52" stroke-width="4"/></svg>')
    return f'<div class="hub2">{hub}<div class="arms">{svg}{arms}</div></div>'

def hub_fan(i):
    W, H = i.get('w', 1450), i.get('h', 800); items = i['items']; n = len(items)
    style = i.get('style', 'fan')  # fan: hub at bottom, cards in an arc above · mind: hub centre, pills around
    if style == 'fan':
        hx, hy, d = W / 2, H - 150, i.get('hub_size', 260)
        pos = [(W / 2 + (k - (n - 1) / 2) * min(300, (W - 150) / n), 170) for k in range(n)]
    else:
        hx, hy, d = W / 2, H / 2, i.get('hub_size', 220)
        rx, ry = min(620, W / 2 - 110), 300
        pos = [(hx + rx * math.cos(math.pi * (k / n * 2) - math.pi / 2 - math.pi / n), hy + ry * math.sin(math.pi * (k / n * 2) - math.pi / 2 - math.pi / n)) for k in range(n)]
    svg = [f'<svg width="{W}" height="{H}">']
    for (x, y) in pos:
        if style == 'fan':
            svg.append(f'<path d="M{hx + (x - hx) * 0.18} {hy - d/2 + 20} Q {x} {hy - 60}, {x} {y + 130}" fill="none" stroke="#B5B5B5" stroke-width="4" marker-end="url(#ah)"/>')
        else:
            sx, sy = hx + (x - hx) * 0.32, hy + (y - hy) * 0.32; ex, ey = hx + (x - hx) * 0.62, hy + (y - hy) * 0.62
            svg.append(f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" stroke="#4993E9" stroke-width="4"/>')
    svg.append('<defs><marker id="ah" markerWidth="12" markerHeight="12" refX="6" refY="6" orient="auto"><path d="M0 0 L12 6 L0 12 z" fill="#B5B5B5"/></marker></defs></svg>')
    nodes = ''
    for (x, y), it in zip(pos, items):
        if style == 'fan':
            nodes += f'<div class="node card" style="left:{x}px;top:{y}px">{asset(it.get("icon"))}<b>{md(it["label"])}</b></div>'
        else:
            nodes += f'<div class="node pillnode" style="left:{x}px;top:{y}px">{asset(it.get("icon"))}{md(it["label"])}</div>'
    hc = i.get('hub_color', 'blue')
    hub = (f'<div class="node" style="left:{hx}px;top:{hy}px"><div class="hubc" style="width:{d}px;height:{d}px;background:var(--{hc});'
           f'font-size:{int(d*0.32 if len(i["hub"])<5 else d*0.2)}px;{"color:var(--ink)" if hc=="yellow" else ""}">{md(i["hub"])}</div></div>')
    return f'<div class="hubfan" style="height:{H}px">{"".join(svg)}{nodes}{hub}</div>'

def cards(i):
    a = i.get('active'); out = ''
    i.setdefault('w', 520); i.setdefault('icon_size', 210)
    for n, c in enumerate(i['items']):
        st = '' if a is None else ('on' if n == a else 'off')
        im = asset(c.get('icon'))
        im = f'<div class="disc" style="background:{TINT.get(c.get("disc","none"),"transparent")}">{im}</div>' if c.get('disc') else f'<div class="iw">{im}</div>'
        bl = ('<div class="rule"></div><ul class="bullets">' + ''.join(f'<li>{md(b)}</li>' for b in c['bullets']) + '</ul>') if c.get('bullets') else ''
        out += f'<div class="icard {st}">{im}<b>{md(c["label"])}</b>{bl}</div>'
    return f'<div class="icards" style="--cw:{i.get("w",380)}px;--icn:{i.get("icon_size",170)}px;gap:{i.get("gap",40)}px">{out}</div>'

def positions(i):
    cs = ''
    for c in i['cards']:
        chip = f'<span class="chip {c.get("chip_color","green")}">{E(c["chip"])}</span>' if c.get('chip') else ''
        v = f'<span class="v" style="color:var(--{c.get("value_color","green")})">{md(c["value"])}</span>' if c.get('value') else ''
        cs += f'<div class="pcard"><div class="ic">{asset(c.get("icon"))}</div><div><b>{md(c["title"])}</b><small>{md(c.get("sub",""))}</small>{chip}</div>{v}</div>'
    return f'<div class="pos"><div class="poslabel">{md(i.get("label","Your positions"))}</div><div class="panel" style="width:{i.get("w",620)}px">{cs}</div></div>'

def _series(kind, n=60, seed=7):
    rnd = random.Random(seed); v = []; x = 0.3
    for k in range(n):
        t = k / (n - 1)
        if kind == 'up': base = 0.15 + 0.7 * t
        elif kind == 'down': base = 0.85 - 0.7 * t
        elif kind == 'up_then_down': base = 0.1 + 1.6 * t if t < .55 else 0.98 - 1.1 * (t - .55)
        elif kind == 'flat_then_up': base = 0.3 + (0 if t < .5 else (t - .5) * 1.0)
        elif kind == 'volatile': base = .5 + .28 * math.sin(t * 9.5 + seed) + .1 * math.sin(t * 23)
        else: base = .5
        v.append(max(.02, min(.98, base + rnd.uniform(-.06, .06) * (1.6 if kind == 'volatile' else 1))))
    return v

def chart(i):
    W, H = i.get('w', 1400), i.get('h', 600); L, B, T, Rr = 130, 70, 30, 40
    ys = i.get('y_labels', []); xs = i.get('x_labels', [])
    vals = i.get('values') or _series(i.get('shape', 'up'), seed=i.get('seed', 7))
    lo, hi = i.get('min', 0), i.get('max', 1)
    if i.get('values'): lo, hi = i.get('min', min(vals)), i.get('max', max(vals))
    if i.get('y_range') and not i.get('values'):   # map a generic shape onto a data range so strike / y_labels can be given in ₹
        a_, b_ = i['y_range']; vals = [a_ + v * (b_ - a_) for v in vals]; lo, hi = a_, b_
    px = lambda k: L + (W - L - Rr) * k / (len(vals) - 1)
    py = lambda v: H - B - (H - B - T) * (v - lo) / (hi - lo)
    s = [f'<svg width="{W}" height="{H}">']
    for k, lab in enumerate(ys):
        y = H - B - (H - B - T) * k / max(1, len(ys) - 1)
        s.append(f'<line x1="{L}" y1="{y}" x2="{W-Rr}" y2="{y}" stroke="#EDEDED" stroke-width="2"/><text x="{L-18}" y="{y+9}" text-anchor="end" font-size="28" font-weight="500" fill="{"#387ED1" if lab==i.get("y_hl") else "#424242"}">{E(lab)}</text>')
    for k, lab in enumerate(xs):
        x = L + (W - L - Rr) * k / max(1, len(xs) - 1)
        s.append(f'<text x="{x}" y="{H-B+44}" text-anchor="middle" font-size="28" font-weight="500" fill="#424242">{E(lab)}</text>')
    s.append(f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H-B}" stroke="#424242" stroke-width="3"/><line x1="{L}" y1="{H-B}" x2="{W-Rr}" y2="{H-B}" stroke="#424242" stroke-width="3"/>')
    pts = ' '.join(f'{px(k):.1f},{py(v):.1f}' for k, v in enumerate(vals))
    split = i.get('split_at')  # index where colour changes (e.g. rise → fall)
    s.append(f'<polygon points="{L},{H-B} {pts} {px(len(vals)-1)},{H-B}" fill="#E6F0FC"/>')
    if 'strike' in i:
        sy = py(i['strike']); zone = i.get('zone', 'above')
        clip = f'<clipPath id="cp"><polygon points="{L},{H-B} {pts} {px(len(vals)-1)},{H-B}"/></clipPath>'
        zcol = '#7FC38B' if zone == 'above' else '#F4A57F'
        zrect = f'<rect x="{L}" y="{T}" width="{W-L-Rr}" height="{sy-T}" fill="{zcol}" clip-path="url(#cp)"/>' if zone == 'above' else \
                f'<rect x="{L}" y="{sy}" width="{W-L-Rr}" height="{H-B-sy}" fill="{zcol}" />'
        if zone == 'below':  # area between strike and line, below the strike
            zrect = f'<clipPath id="cb"><polygon points="{L},{sy} {pts} {px(len(vals)-1)},{sy}"/></clipPath><rect x="{L}" y="{sy}" width="{W-L-Rr}" height="{H-B-sy}" fill="{zcol}" clip-path="url(#cb)"/>'
        s.append(clip + zrect)
        s.append(f'<line x1="{L}" y1="{sy}" x2="{W-Rr+20}" y2="{sy}" stroke="#777" stroke-width="3" stroke-dasharray="10 8"/>')
        if i.get('strike_label'):
            lw = 27 * len(i['strike_label']) * .58 + 40; pos = i.get('strike_label_pos', 'right')
            lx = {'right': W - Rr - lw, 'left': L + 10, 'centre': L + (W - L - Rr - lw) / 2, 'center': L + (W - L - Rr - lw) / 2}[pos]
            s.append(f'<rect x="{lx}" y="{sy-22}" width="{lw}" height="44" rx="6" fill="#4993E9"/><text x="{lx+lw/2}" y="{sy+10}" text-anchor="middle" font-size="27" font-weight="600" fill="#fff">{E(i["strike_label"])}</text>')
    for lv in i.get('levels', []):
        ly = py(lv['value']); col = {'green': '#4CAF52', 'orange': '#F07339', 'blue': '#4993E9', 'purple': '#9B7BEA', 'grey': '#424242'}.get(lv.get('color', 'green'), '#4CAF52')
        s.append(f'<line x1="{L}" y1="{ly}" x2="{W-Rr}" y2="{ly}" stroke="{col}" stroke-width="3" stroke-dasharray="10 8"/>')
        if lv.get('label'):
            lw = 27 * len(lv['label']) * .58 + 40; lx = W - Rr - lw if lv.get('pos', 'right') == 'right' else L + 10
            s.append(f'<rect x="{lx}" y="{ly-22}" width="{lw}" height="44" rx="6" fill="{col}"/><text x="{lx+lw/2}" y="{ly+10}" text-anchor="middle" font-size="27" font-weight="600" fill="#fff">{E(lv["label"])}</text>')
    if split:
        a = ' '.join(f'{px(k):.1f},{py(v):.1f}' for k, v in enumerate(vals[:split + 1]))
        b = ' '.join(f'{px(k):.1f},{py(v):.1f}' for k, v in enumerate(vals) if k >= split)
        s.append(f'<polyline points="{a}" fill="none" stroke="#4993E9" stroke-width="4"/><polyline points="{b}" fill="none" stroke="#F07339" stroke-width="4"/>')
    else:
        s.append(f'<polyline points="{pts}" fill="none" stroke="#4993E9" stroke-width="4"/>')
    for t in i.get('tags', []):
        k = t.get('at', len(vals) - 1)
        if k == 'strike' and 'strike' in i:
            sv = i['strike']; k = next((n for n in range(1, len(vals)) if (vals[n-1] - sv) * (vals[n] - sv) <= 0), len(vals) - 1)
        k = max(0, min(int(k), len(vals) - 1)); lines = t['text'].split('|'); h = 46 * len(lines)
        w = 27 * len(max(lines, key=len)) * .58 + 50
        x, y = px(k), py(vals[k]) + t.get('dy', -70)
        x = min(max(x, L + w / 2), W - w / 2 - 4) - t.get('dx', 0); y = min(max(y, h / 2 + 2), H - B - h / 2)
        col = {'green': '#4CAF52', 'orange': '#F07339', 'blue': '#4993E9', 'purple': '#9B7BEA', 'yellow': '#E0A21B', 'grey': '#424242'}.get(t.get('color', 'orange'), '#4993E9')
        s.append(f'<rect x="{x-w/2+t.get("dx",0)}" y="{y-h/2}" width="{w}" height="{h}" rx="{min(23,h/2)}" fill="{col}"/>')
        for n, ln in enumerate(lines):
            s.append(f'<text x="{x+t.get("dx",0)}" y="{y-h/2+34+n*42}" text-anchor="middle" font-size="27" font-weight="600" fill="#fff">{E(ln)}</text>')
        if t.get('dot', True): s.append(f'<circle cx="{px(k)}" cy="{py(vals[k])}" r="10" fill="#fff" stroke="{col}" stroke-width="4"/>')
    if i.get('arrow'):
        up = i['arrow'] == 'up'; c = '#4CAF52' if up else '#F07339'; x = W - Rr + 70
        y0, y1 = (py(i.get('strike', .5)) - 20, T + 10) if up else (py(i.get('strike', .5)) + 20, H - B - 10)
        s.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1 + (30 if up else -30)}" stroke="{c}" stroke-width="22"/>'
                 f'<path d="M{x-34} {y1 + (40 if up else -40)} L{x} {y1} L{x+34} {y1 + (40 if up else -40)} z" fill="{c}"/>')
        W2 = W + 110; s[0] = f'<svg width="{W2}" height="{H}">'
    s.append('</svg>')
    return f'<div class="chartcard">{"".join(s)}</div>'

def bars(i):
    W, H = i.get('w', 1200), i.get('h', 640); items = i['items']; mx = max(b['value'] for b in items)
    n = len(items); gap = (W - 100) / n; bw = min(200, gap * .5); base = H - 110
    s = [f'<svg width="{W}" height="{H}">', f'<line x1="40" y1="{base}" x2="{W-40}" y2="{base}" stroke="#222" stroke-width="4"/>']
    for k, b in enumerate(items):
        x = 50 + gap * k + (gap - bw) / 2; h = max(14, (base - 170) * b['value'] / mx)
        col = {'blue': '#4993E9', 'orange': '#F07339', 'green': '#4CAF52', 'yellow': '#FFC02E'}[b.get('color', 'blue')]
        s.append(f'<rect x="{x}" y="{base-h}" width="{bw}" height="{h}" fill="{col}"/>')
        ty = base - h - 70
        s.append(f'<line x1="{x+bw/2}" y1="{ty+8}" x2="{x+bw/2}" y2="{base-h}" stroke="{col}" stroke-width="3" stroke-dasharray="6 6"/><circle cx="{x+bw/2}" cy="{ty+8}" r="9" fill="{col}"/>')
        s.append(f'<text x="{x+bw/2}" y="{ty-14}" text-anchor="middle" font-size="36" font-weight="600" fill="#222">{E(b["display"])}</text>')
        s.append(f'<foreignObject x="{x+bw/2-160}" y="{base+24}" width="320" height="80"><div xmlns="http://www.w3.org/1999/xhtml" style="text-align:center"><span class="pillv {b.get("color","blue")}" style="font-size:36px">{E(b["label"])}</span></div></foreignObject>')
    s.append('</svg>')
    return f'<div>{"".join(s)}</div>'

def formula(i):
    parts = []
    for k, t in enumerate(i['terms']):
        if k: parts.append(f'<div class="fop">{E(i["ops"][k-1])}</div>')
        parts.append(f'<div class="fterm {t.get("color","")}"><b>{md(t["value"])}</b><span>{md(t["label"])}</span></div>')
    d = f'<div class="fdef">{md(i["definition"])}</div>' if i.get('definition') else ''
    return f'<div style="display:flex;flex-direction:column;align-items:center;gap:30px"><div class="formula">{"".join(parts)}</div>{d}</div>'

def status(i):
    out = f'<div class="status"><div class="bar">← {md(i.get("title","Account status"))}</div>'
    ghost = '<div class="ghost"><s style="width:90px"></s><s style="width:260px"></s></div>'
    for sec in i['sections']:
        out += ghost + f'<div class="sec">⌄ {md(sec["name"])}</div>'
        for ok, t in sec['rows']:
            out += f'<div class="row"><i class="{"ok" if ok else "no"}">{"✓" if ok else "✕"}</i>{md(t)}</div>'
    return out + ghost + '</div>'

def phone(i):
    chip = f'<div class="phone-chip">{E(i["chip"])}</div>' if i.get('chip') else ''
    return (f'<div class="phone">{chip}<div class="app">‹ &nbsp;{E(i.get("app","Zerodha"))}</div><div class="notif"><div class="nh"><span>● {E(i["title"])}</span><span>Now</span></div>'
            f'<p>{md(i["text"])}</p><small>{E(i.get("time",""))}</small></div></div>')

def week(i):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']; on = set(i.get('on', []))
    return f'<div class="week"><div class="wl">{md(i.get("label",""))}</div><div class="days">' + ''.join(f'<div class="d {"on" if d in on or d[:3] in on else ""}">{d}</div>' for d in days) + '</div></div>'

def notepad(i):
    a = i.get('active', 0)
    return '<div class="notepad"><div class="rings">' + '<i></i>' * 12 + '</div><ul>' + ''.join(f'<li class="{"on" if k == a else ""}">{md(t)}</li>' for k, t in enumerate(i['items'])) + '</ul></div>'

def objstat(i):
    t = f'<div class="ot">{md(i["title"])}</div>' if i.get('title') else ''
    tag = f'<div class="tag">{md(i["tag"])}</div>' if i.get('tag') else ''
    chips = '<div class="chips">' + ''.join(f'<span class="lockchip">{LOCK}{md(c)}</span>' for c in i.get('chips', [])) + '</div>' if i.get('chips') else ''
    return f'<div class="objstat" style="--oh:{i.get("ih",200)}px">{t}{asset(i.get("img"))}<div class="val">{md(i["value"])}</div>{tag}{chips}</div>'

def calendar(i):
    s = f'<div class="s">{md(i["sub"])}</div>' if i.get('sub') else ''
    return f'<div class="cal"><div class="m">{E(i["month"])}</div><div class="d">{E(str(i["day"]))}</div>{s}</div>'

def exchange(i):
    def av(x): return f'<div class="avatar"><div class="c">{asset(x.get("img"))}</div>{md(x["label"])}</div>'
    arc = ('<svg width="420" height="250"><path d="M30 90 C 120 0, 300 0, 390 90" fill="none" stroke="#333" stroke-width="3" marker-end="url(#a1)"/>'
           '<path d="M390 160 C 300 250, 120 250, 30 160" fill="none" stroke="#333" stroke-width="3" marker-end="url(#a1)"/>'
           '<defs><marker id="a1" markerWidth="12" markerHeight="12" refX="6" refY="6" orient="auto"><path d="M0 0 L12 6 L0 12 z" fill="#4993E9"/></marker></defs>'
           f'<text x="210" y="142" text-anchor="middle" font-size="62" font-weight="600" fill="#222">{E(i.get("action","BUY / SELL"))}</text></svg>')
    return f'<div class="flowrow">{av(i["left"])}{arc}{av(i["right"])}</div>'

def row(i):
    inner = ''.join(R[c['t']](c) for c in i['items'])
    return f'<div style="display:flex;align-items:{i.get("align","center")};justify-content:center;gap:{i.get("gap",60)}px">{inner}</div>'

def raw(i): return f'<div>{i["html"]}</div>'

# ======================================================================= Kite / market UI (V4: Why do stock prices move every second)
_FAKE = ['ABC', 'PQR', 'AAA', 'CDAA', 'LMN', 'FFF', 'ASASA', 'CCCE', 'ABBB', 'BBCC', 'CCAA', 'PPPA', 'BBAA', 'PPPP', 'ABBC', 'CCCC', 'DEF', 'GHI']
def _status_bar(): return '<div class="sbar"><span>11:33</span><span>▂▄▆ ◔ ▮</span></div>'

def kite_watchlist(i):
    """Phone with a Kite-style watchlist; one row popped out and highlighted."""
    rnd = random.Random(i.get('seed', 4)); n = i.get('rows', 17); hl = i.get('hl', {}); at = i.get('hl_at', 7)
    rows = ''
    for k in range(n):
        if k == at:
            rows += '<div class="wrow ghost"></div>'; continue
        up = rnd.random() > .6; px = f'{rnd.uniform(20, 3000):.2f}'; ch = f'{rnd.uniform(-40, 40):.2f}'; pc = f'{rnd.uniform(-3, 3):.2f}%'
        rows += f'<div class="wrow"><b>{_FAKE[k % len(_FAKE)]}</b><span>{ch}</span><span>{pc}</span><i class="{"up" if up else "dn"}">{px}</i></div>'
    top = 220 + at * 46
    pop = (f'<div class="wpop" style="top:{top}px"><b>{E(hl.get("name","XYZ"))}</b><span>{E(hl.get("change",""))}</span><span>{E(hl.get("pct",""))}</span>'
           f'<i class="{hl.get("dir","dn")}">{md(hl.get("price","100.00"))}</i></div>')
    idx = '<div class="widx"><b>NIFTY 50</b> <i class="dn">24,181.75</i> &nbsp; <b>SENSEX</b> <i class="dn">79,560.64</i></div>'
    return f'<div class="kphone"><div class="kscreen">{_status_bar()}{idx}<div class="wsearch">Search</div>{rows}</div>{pop}</div>'

def kite_depth(i):
    """Phone, Kite market-depth sheet: stock header, BUY/SELL, bid/offer rows (+ optional status tags per row)."""
    bids, offers = i['bids'], i['offers']; st = i.get('status', [])
    head = (f'<div class="dhd"><b>{E(i.get("name","XYZ"))}</b><span>{E(i.get("exchange","NSE"))} <i class="up">{E(i.get("ltp",""))}</i> {E(i.get("change",""))}</span></div>'
            '<div class="dbtn"><span class="b">BUY</span><span class="s">SELL</span></div>')
    rows = '<div class="drow dh"><span>Bid</span><span>Orders</span><span>Qty</span><span>Offer</span><span>Orders</span><span>Qty</span></div>'
    hl = set(i.get('hl', []))
    for k in range(max(len(bids), len(offers))):
        b = bids[k] if k < len(bids) else ['', '', '']; o = offers[k] if k < len(offers) else ['', '', '']
        rows += f'<div class="drow {"hl" if k in hl else ""}"><span class="bd">{E(str(b[0]))}</span><span class="bd">{E(str(b[1]))}</span><span class="bd">{E(str(b[2]))}</span><span class="of">{E(str(o[0]))}</span><span class="of">{E(str(o[1]))}</span><span class="of">{E(str(o[2]))}</span></div>'
    tags = ''.join(f'<div class="dtag {"ok" if t and ("xecut" in t or t.lower().startswith("trade")) else "no"}" style="top:{k*58}px">{E(t)}</div>' for k, t in enumerate(st) if t)
    return (f'<div class="kphone depth"><div class="kscreen">{_status_bar()}{head}<div class="dlinks"><span>View chart</span><span>Option chain</span></div>'
            f'<div class="dtable">{rows}</div></div><div class="dtags">{tags}</div></div>')

def kite_chart(i):
    """Kite desktop chart window with a volatile line; `ticks` = point indices to mark with orange dots."""
    W, H = i.get('w', 1400), i.get('h', 640); vals = _series(i.get('shape', 'volatile'), n=i.get('points', 140), seed=i.get('seed', 11))
    L, R_, T, B = 30, 90, 20, 40
    px = lambda k: L + (W - L - R_) * k / (len(vals) - 1); py = lambda v: T + (H - T - B) * (1 - v)
    pts = ' '.join(f'{px(k):.1f},{py(v):.1f}' for k, v in enumerate(vals))
    dots = ''.join(f'<circle cx="{px(k)}" cy="{py(vals[k])}" r="22" fill="#F07339" opacity=".25"/><circle cx="{px(k)}" cy="{py(vals[k])}" r="11" fill="#F07339"/>' for k in i.get('ticks', []))
    xl = i.get('x_labels', ['14:32', '14:33', '14:35', '14:37', '14:38', '14:40', '14:42'])
    xs = ''.join(f'<text x="{L + (W-L-R_)*n/(len(xl)-1)}" y="{H-8}" text-anchor="middle" font-size="22" fill="#666">{E(t)}</text>' for n, t in enumerate(xl))
    ticks = ''.join(f'<line x1="{W-R_+30}" x2="{W-R_+70}" y1="{T+k*(H-T-B)/20}" y2="{T+k*(H-T-B)/20}" stroke="#CCC" stroke-width="5"/>' for k in range(21))
    nav = ''.join(f'<span>{x}</span>' for x in ['Dashboard', 'Orders', 'Holdings', 'Positions', 'Funds'])
    return (f'<div class="kwin" style="width:{W+40}px"><div class="kbar"></div><div class="knav"><b class="klogo"></b><span>{E(i.get("watchlist","Default"))}</span><div style="flex:1"></div>{nav}</div>'
            f'<div class="ktabs"><span class="on">Chart</span><span>Option chain</span><span>Fundamentals</span></div>'
            f'<div class="ktool"><b>{E(i.get("name","XYZ"))} · NSE</b><span class="b">BUY</span><span class="s">SELL</span></div>'
            f'<svg width="{W}" height="{H}" style="margin:0 20px">{ticks}<polyline points="{pts}" fill="none" stroke="#4993E9" stroke-width="3"/>{dots}{xs}</svg></div>')

def auction(i):
    """Buyers (green, left) and sellers (orange, right) with price chips meeting in the middle."""
    def side(items, role):
        av = (['buyer_woman', 'buyer_man_green', 'buyer_man_blue'] if role == 'buy' else ['seller_man_blue', 'seller_man_purple', 'seller_woman'])
        out = ''
        for k, pr in enumerate(items[:3]):
            big = str(pr) == str(i.get('match', ''))
            out += (f'<div class="aperson {"big" if big else ""} p{k}"><img src="../assets/illus/{av[k]}.png">'
                    f'<span class="achip {"g" if role == "buy" else "o"}">{md(pr)}</span></div>')
        return out
    res = i.get('result', 'Trade executed'); ok = i.get('matched', True)
    mid = (f'<div class="amid"><div class="acirc {"" if ok else "no"}">{"✓" if ok else "✕"}</div><div class="ares">{md(res)}</div></div>')
    return (f'<div class="auction"><div class="aside"><div class="alab g">{md(i.get("left","Buyers"))}</div><div class="agrp">{side(i["buyers"], "buy")}</div></div>'
            f'<div class="aarrow g">⇢</div>{mid}<div class="aarrow o">⇠</div>'
            f'<div class="aside"><div class="alab o">{md(i.get("right","Sellers"))}</div><div class="agrp r">{side(i["sellers"], "sell")}</div></div></div>')

R = dict(lower=lower, punch=punch, bignum=bignum, side_list=side_list, scroll_list=scroll_list, objcards=objcards, ticket=ticket,
         mini_table=mini_table, ladder=ladder, note=note, text=text, img=img, pillv=pillv, heading=heading, compare=compare, hub2=hub2,
         hub_fan=hub_fan, cards=cards, positions=positions, chart=chart, bars=bars, formula=formula, status=status, phone=phone,
         week=week, notepad=notepad, objstat=objstat, calendar=calendar, exchange=exchange, row=row, html=raw,
         kite_watchlist=kite_watchlist, kite_depth=kite_depth, kite_chart=kite_chart, auction=auction)

# ======================================================================= v2 recipes (zo-graphic-maker skill)
# Learned from 78 shipped frames (Family Portfolio, Life Cycle Fund, MTF, Charges, Physical delivery PSDs).
INK = '#1D2228'
COL = {'blue': '#387FD1', 'orange': '#F07339', 'yellow': '#FEC02D', 'green': '#4DAB4D', 'purple': '#A77BF3',
       'ink': INK, 'grey': '#C9CBCF', 'red': '#D23C3C'}
CYCLE = ['blue', 'orange', 'yellow', 'green', 'purple']


def _c(name, default='blue'):
    n = name or default
    return COL.get(n, n)


def _txt_on(col):
    return INK if col in ('yellow', COL['yellow'], 'grey') else '#fff'


# simple inline line-art icons (2–6px ink strokes, flat blue/orange/yellow fills) — no emoji, no logos
_S = 'fill="none" stroke="#1D2228" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    'wallet': f'<rect x="10" y="26" width="80" height="58" rx="10" fill="#387FD1" {_S}/><path d="M18 26 L64 10 L72 26" {_S}/><rect x="60" y="44" width="30" height="22" rx="6" fill="#FEC02D" {_S}/>',
    'moneybag': f'<path d="M36 22 C30 12 70 12 64 22 L60 30 C82 42 88 86 50 88 C12 86 18 42 40 30Z" fill="#FEC02D" {_S}/><path d="M40 52 H60 M40 62 H60 M46 52 C58 52 58 66 46 66 L58 78" {_S}/>',
    'calendar': f'<rect x="12" y="20" width="76" height="68" rx="10" fill="#fff" {_S}/><path d="M12 40 H88" {_S}/><rect x="12" y="20" width="76" height="20" rx="8" fill="#387FD1" {_S}/><path d="M32 12 V28 M68 12 V28" {_S}/><circle cx="34" cy="58" r="4" fill="#1D2228"/><circle cx="50" cy="58" r="4" fill="#1D2228"/><circle cx="66" cy="58" r="4" fill="#F07339"/><circle cx="34" cy="74" r="4" fill="#1D2228"/><circle cx="50" cy="74" r="4" fill="#1D2228"/>',
    'coins': f'<ellipse cx="50" cy="76" rx="32" ry="10" fill="#FEC02D" {_S}/><path d="M18 76 V62 M82 76 V62" {_S}/><ellipse cx="50" cy="62" rx="32" ry="10" fill="#FEC02D" {_S}/><path d="M18 62 V48 M82 62 V48" {_S}/><ellipse cx="50" cy="48" rx="32" ry="10" fill="#FEC02D" {_S}/>',
    'parcel': f'<path d="M50 10 L88 28 V72 L50 90 L12 72 V28Z" fill="#F7C98B" {_S}/><path d="M12 28 L50 46 L88 28 M50 46 V90" {_S}/><path d="M31 19 L69 37" {_S}/>',
    'tag': f'<path d="M12 50 L50 12 H86 V48 L48 86Z" fill="#F07339" {_S}/><circle cx="70" cy="30" r="7" fill="#fff" {_S}/>',
    'gift': f'<rect x="14" y="40" width="72" height="48" rx="6" fill="#A77BF3" {_S}/><rect x="10" y="28" width="80" height="16" rx="5" fill="#A77BF3" {_S}/><path d="M50 28 V88 M50 28 C40 10 22 18 34 28 M50 28 C60 10 78 18 66 28" {_S}/>',
    'scale': f'<path d="M50 14 V84 M28 84 H72 M18 30 H82" {_S}/><path d="M18 30 L6 60 H30Z" fill="#FEC02D" {_S}/><path d="M82 30 L70 60 H94Z" fill="#387FD1" {_S}/>',
    'growth': f'<path d="M10 88 H90" {_S}/><rect x="16" y="60" width="16" height="28" fill="#FEC02D" {_S}/><rect x="42" y="44" width="16" height="44" fill="#F07339" {_S}/><rect x="68" y="26" width="16" height="62" fill="#387FD1" {_S}/><path d="M14 46 L40 30 L58 38 L86 12 M72 12 H86 V26" {_S}/>',
    'warning': f'<path d="M50 10 L92 86 H8Z" fill="#FEC02D" {_S}/><path d="M50 38 V60" {_S}/><circle cx="50" cy="72" r="4" fill="#1D2228"/>',
    'down': f'<circle cx="50" cy="50" r="40" fill="#F07339" {_S}/><path d="M50 28 V70 M32 54 L50 72 L68 54" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>',
    'up': f'<circle cx="50" cy="50" r="40" fill="#4DAB4D" {_S}/><path d="M50 72 V30 M32 46 L50 28 L68 46" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>',
    'tick': '<circle cx="50" cy="50" r="44" fill="#387FD1"/><path d="M28 52 L44 68 L74 36" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>',
    'cross': '<circle cx="50" cy="50" r="44" fill="#D23C3C"/><path d="M34 34 L66 66 M66 34 L34 66" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/>',
    'phone': f'<rect x="28" y="8" width="44" height="84" rx="9" fill="#fff" {_S}/><rect x="34" y="20" width="32" height="54" rx="3" fill="#387FD1"/><circle cx="50" cy="83" r="3.5" fill="#1D2228"/>',
    'doc': f'<path d="M22 8 H62 L80 26 V92 H22Z" fill="#fff" {_S}/><path d="M62 8 V26 H80 M34 44 H68 M34 58 H68 M34 72 H56" {_S}/>',
    'bank': f'<path d="M10 36 L50 12 L90 36Z" fill="#387FD1" {_S}/><path d="M22 42 V76 M40 42 V76 M60 42 V76 M78 42 V76 M12 84 H88" {_S}/>',
    'clock': f'<circle cx="50" cy="50" r="40" fill="#fff" {_S}/><path d="M50 26 V50 L66 60" {_S}/>',
    'cart': f'<path d="M8 16 H22 L32 66 H80 L88 32 H26" fill="none" {_S}/><circle cx="38" cy="80" r="6" fill="#FEC02D" {_S}/><circle cx="74" cy="80" r="6" fill="#FEC02D" {_S}/>',
    'shield': f'<path d="M50 8 L86 20 V48 C86 72 68 86 50 92 C32 86 14 72 14 48 V20Z" fill="#4DAB4D" {_S}/><path d="M34 50 L46 62 L68 38" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>',
    'rupee': f'<circle cx="50" cy="50" r="40" fill="#FEC02D" {_S}/><path d="M36 30 H66 M36 42 H66 M42 30 C64 30 64 54 42 54 L62 74" {_S}/>',
    'chevron': '<path d="M38 26 L62 50 L38 74" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>',
    # line faces for people cards (Family Portfolio style)
    'man': f'<circle cx="50" cy="52" r="26" fill="#fff" {_S}/><path d="M26 44 C28 22 72 22 74 44 C66 36 46 34 26 44Z" fill="#1D2228"/><circle cx="41" cy="54" r="3" fill="#1D2228"/><circle cx="59" cy="54" r="3" fill="#1D2228"/><path d="M42 66 C46 70 54 70 58 66" {_S}/>',
    'woman': f'<path d="M22 70 C14 30 30 20 50 20 C70 20 86 30 78 70Z" fill="#1D2228"/><circle cx="50" cy="52" r="24" fill="#fff" {_S}/><path d="M28 48 C36 30 64 30 72 48 C60 42 40 42 28 48Z" fill="#1D2228"/><circle cx="42" cy="54" r="3" fill="#1D2228"/><circle cx="58" cy="54" r="3" fill="#1D2228"/><path d="M43 65 C47 69 53 69 57 65" {_S}/>',
    'child': f'<circle cx="50" cy="56" r="24" fill="#fff" {_S}/><path d="M36 34 C40 26 46 30 50 26 C54 30 60 26 64 34" {_S}/><circle cx="42" cy="58" r="3" fill="#1D2228"/><circle cx="58" cy="58" r="3" fill="#1D2228"/><path d="M43 68 C47 72 53 72 57 68" {_S}/>',
    'elder': f'<circle cx="50" cy="52" r="26" fill="#fff" {_S}/><path d="M26 46 C24 30 34 22 50 22 C66 22 76 30 74 46" fill="none" stroke="#C9CBCF" stroke-width="9"/><rect x="36" y="50" width="12" height="9" rx="3" {_S}/><rect x="52" y="50" width="12" height="9" rx="3" {_S}/><path d="M48 54 H52 M42 68 C47 72 53 72 58 68" {_S}/>',
}


def icon(name, size=84, color=None):
    body = ICONS.get(name)
    if not body:
        return ''
    return f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" aria-label="{E(name)}">{body}</svg>'


def any_img(src, size=84):
    """svg:<icon> → inline line-art icon; anything else → kit/generated asset."""
    if not src:
        return ''
    if isinstance(src, str) and src.startswith('svg:'):
        return icon(src[4:], size)
    return asset(src)


def acronym(i):
    kick = f'<div class="v2-kicker">{md(i["kicker"])}</div>' if i.get('kicker') else ''
    if i.get('words'):
        body = ' '.join(f'<b>{E(w[0])}</b>{E(w[1:])}' for w in i['words'])
    else:
        body = md(i.get('text', ''))
    return f'<div style="text-align:center">{kick}<div class="v2-ybox">{body}</div></div>'


def qtitle(i):
    lines = ''.join(f'<div class="l">{md(l)}</div>' for l in i['lines'])
    return (f'<div class="v2-q"><div class="glow"></div><div class="n">{E(str(i.get("n", 1)))}.</div>'
            f'<div>{lines}<div class="dash"></div></div></div>')


def steps(i):
    cols = i.get('colors') or ['blue', 'orange', 'yellow', 'green']
    out = ''.join(f'<div class="v2-step {cols[k % len(cols)]}"><div class="n">{k + 1}</div><div>{md(t)}</div><div class="hole"></div></div>'
                  for k, t in enumerate(i['items']))
    return f'<div class="v2-steps">{out}</div>'


def slab_table(i):
    subs = i.get('subs') or []
    th = ''.join(f'<th>{md(h)}{f"<small>{md(subs[n])}</small>" if n < len(subs) and subs[n] else ""}</th>'
                 for n, h in enumerate(i['head']))
    hl = i.get('hl'); hl = set(hl if isinstance(hl, list) else ([] if hl is None else [hl]))
    loss = set(i.get('loss') or [])
    rows = ''.join(f'<tr class="{"hl" if n in hl else ("loss" if n in loss else "")}">' + ''.join(f'<td>{md(c)}</td>' for c in r) + '</tr>'
                   for n, r in enumerate(i['rows']))
    left = ' left' if i.get('align', 'left') == 'left' else ''
    return (f'<div class="v2-card" style="width:{i.get("w", 1300)}px;padding:10px 30px 34px"><div class="v2-dots"><i></i><i></i><i></i></div>'
            f'<table class="v2-t{left}"><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table></div>')


def split_bar(i):
    parts = i['parts']; tot = sum(float(p.get('pct', 1)) for p in parts) or 1
    bar = ''.join(f'<div style="width:{100 * float(p.get("pct", 1)) / tot:.2f}%;background:{_c(p.get("color"), CYCLE[k])};color:{_txt_on(p.get("color", CYCLE[k]))}">{md(p.get("value", ""))}</div>'
                  for k, p in enumerate(parts))
    labs = ''.join(f'<div style="width:{100 * float(p.get("pct", 1)) / tot:.2f}%">{any_img(p.get("icon"), 84)}<span>{md(p.get("label", ""))}</span></div>'
                   for p in parts)
    stock = (f'<div class="stock">{icon("growth", 70)}<span>{md(i["stock"])}</span>'
             f'{f"<span class=tagx>{E(i[chr(116)+chr(97)+chr(103)])}</span>" if i.get("tag") else ""}</div>') if i.get('stock') else ''
    itag = f'<div class="itag">{md(i["interest"])}</div>' if i.get('interest') else ''
    br = ('<svg width="1300" height="46" viewBox="0 0 1300 46"><path d="M6 4 V16 Q6 26 30 26 H620 Q650 26 650 44 Q650 26 680 26 H1270 Q1294 26 1294 16 V4" '
          'fill="none" stroke="#1D2228" stroke-width="4" stroke-linecap="round"/></svg>') if i.get('total') else ''
    tot_l = f'<div class="total">{md(i["total"])}</div>' if i.get('total') else ''
    return f'<div class="v2-split">{stock}{itag}<div class="bar">{bar}</div><div class="labs">{labs}</div>{br}{tot_l}</div>'


def cost_compare(i):
    rows = i['rows']
    mx = max(sum(float(p['v']) for p in r['parts']) for r in rows) or 1
    out = ''
    for r in rows:
        tag = f'<span class="lower">{E(r["tag"])}</span>' if r.get('tag') else ''
        segs = ''.join(f'<div style="width:{900 * float(p["v"]) / mx:.0f}px;background:{_c(p.get("color"), "blue")}"></div>' for p in r['parts'])
        out += (f'<div class="r"><div class="nm">{md(r["name"])}{tag}<small>{md(r.get("sub", ""))}</small></div>'
                f'<div class="track"><div class="stack">{segs}</div><div class="tot">{md(r.get("total", ""))}</div></div></div>')
    leg = ''.join(f'<span><i style="background:{_c(l.get("color"))}"></i>{md(l["label"])}</span>' for l in i.get('legend', []))
    return f'<div class="v2-cost">{out}{f"<div class=v2-legend>{leg}</div>" if leg else ""}</div>'


def updown(i):
    def panel(p, down):
        bars = p['bars']; mx = max(abs(float(b['v'])) for b in bars) or 1
        cols = ''
        for b in bars:
            h = int(320 * abs(float(b['v'])) / mx)
            col = _c(p.get('color'), 'orange' if down else 'green')
            if down:
                cols += (f'<div class="col down" style="justify-content:flex-start;padding-top:60px"><div class="bar" style="height:{h}px;background:{col}"></div>'
                         f'<div class="val" style="color:{col}">{md(b.get("label", b["v"]))}</div><div class="cap">{md(b.get("caption", ""))}</div></div>')
            else:
                cols += (f'<div class="col" style="justify-content:flex-end;padding-bottom:70px"><div class="val" style="color:{col}">{md(b.get("label", b["v"]))}</div>'
                         f'<div class="bar" style="height:{h}px;background:{col}"></div><div class="cap" style="position:absolute;bottom:14px">{md(b.get("caption", ""))}</div></div>')
        base = f'<div class="base" style="{"top:58px" if down else "bottom:66px"}"></div>'
        return f'<div class="p {"down" if down else ""}"><div class="ttl">{md(p.get("title", ""))}</div><div class="plot">{base}{cols}</div></div>'
    return f'<div class="v2-ud">{panel(i["left"], False)}{panel(i["right"], True)}</div>'


def donut(i):
    d = i.get('size', 420); sw = i.get('stroke', 70); r = (d - sw) / 2; c = 2 * math.pi * r
    pct = float(str(i['pct']).rstrip('%'))
    col = _c(i.get('color'), 'blue')
    fs = i.get('pct_size') or int(d * 0.28)
    svg = (f'<svg width="{d}" height="{d}" viewBox="0 0 {d} {d}"><circle cx="{d/2}" cy="{d/2}" r="{r}" fill="none" stroke="#ECEEF1" stroke-width="{sw}"/>'
           f'<circle cx="{d/2}" cy="{d/2}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" '
           f'stroke-dasharray="{c * pct / 100:.1f} {c:.1f}" transform="rotate(-90 {d/2} {d/2})"/></svg>')
    label = i.get('label') or f'{i["pct"]}{"" if str(i["pct"]).endswith("%") else "%"}'
    return (f'<div class="v2-donut"><div class="ring" style="width:{d}px;height:{d}px">{svg}'
            f'<div class="pct" style="font-size:{fs}px;color:{col}">{md(label)}</div></div>'
            f'{f"<div class=cap>{md(i[chr(99)+chr(97)+chr(112)+chr(116)+chr(105)+chr(111)+chr(110)])}</div>" if i.get("caption") else ""}</div>')


def pie(i):
    size = i.get('size', 520); pad = i.get('pad', 170); R_ = size / 2; cx = cy = R_ + pad; W = size + 2 * pad
    a = -90.0; paths = ''; labs = ''
    for k, s in enumerate(i['slices']):
        v = float(s['v']); sw = v * 3.6
        col = _c(s.get('color'), CYCLE[k % 5])
        x1, y1 = cx + R_ * math.cos(math.radians(a)), cy + R_ * math.sin(math.radians(a))
        x2, y2 = cx + R_ * math.cos(math.radians(a + sw)), cy + R_ * math.sin(math.radians(a + sw))
        if v >= 99.99:
            paths += f'<circle cx="{cx}" cy="{cy}" r="{R_}" fill="{col}"/>'
        else:
            paths += f'<path d="M{cx} {cy} L{x1:.1f} {y1:.1f} A{R_} {R_} 0 {1 if sw > 180 else 0} 1 {x2:.1f} {y2:.1f} Z" fill="{col}" stroke="#fff" stroke-width="3"/>'
        m = math.radians(a + sw / 2); big = v >= 30; sm = v < 8
        rr = R_ * (.55 if big else .8 if sm else .66)
        tc = s.get('text') or _txt_on(s.get('color', CYCLE[k % 5]))
        labs += f'<div class="lab" style="left:{cx + rr * math.cos(m):.0f}px;top:{cy + rr * math.sin(m):.0f}px;font-size:{110 if big else 40 if sm else 56}px;color:{tc}">{E(s.get("display", f"{s[chr(118)]:g}%" if isinstance(s["v"], (int, float)) else s["v"]))}</div>'
        if s.get('label'):
            lx, ly = cx + (R_ + 56) * math.cos(m), cy + (R_ + 56) * math.sin(m); cm = math.cos(m)
            tx = '0' if cm > .2 else '-100%' if cm < -.2 else '-50%'
            labs += f'<div class="lab" style="left:{lx:.0f}px;top:{ly:.0f}px;font-size:44px;color:{INK};transform:translate({tx},-50%)">{md(s["label"])}</div>'
        a += sw
    return f'<div class="v2-pie" style="width:{W}px;height:{W}px"><svg width="{W}" height="{W}" viewBox="0 0 {W} {W}">{paths}</svg>{labs}</div>'


def fbox(i):
    h = i.get('hero') or {}
    hero = f'<div class="v2-fbox hero"><b>{md(h.get("value", ""))}</b><span>{md(h.get("label", ""))}</span></div>'
    before = ''.join(f'<div class="v2-fbox faded"><b>{md(b["value"])}</b><span>{md(b.get("label", ""))}</span><div class="strike"></div></div>'
                     for b in i.get('before', []))
    ill = f'<div class="v2-blobwrap"><div class="blob"></div>{any_img(i["img"], 300)}</div>' if i.get('img') else ''
    col = f'<div style="display:flex;flex-direction:column;gap:30px;align-items:center">{before}{hero}</div>'
    return f'<div class="v2-fwrap">{ill}{col}</div>'


def people(i):
    out = ''
    for k, p in enumerate(i['items']):
        col = p.get('color', CYCLE[k % 5])
        out += (f'<div class="v2-person"><div class="face" style="background:{TINT.get(col, "#EEF3FB")}">{any_img(p.get("icon", "svg:man"), 150)}</div>'
                f'<div class="lb">{md(p["label"])}</div><div class="vv" style="color:{_c(col)}">{md(p.get("value", ""))}</div>'
                f'{f"<div class=nt>{md(p[chr(110)+chr(111)+chr(116)+chr(101)])}</div>" if p.get("note") else ""}</div>')
    return f'<div class="v2-people">{out}</div>'


def catgrid(i):
    items = i['items']; c3 = ' c3' if len(items) in (3, 6) else ''
    out = ''.join(f'<div class="c" style="box-shadow:0 10px 0 -2px {_c(it.get("color"), CYCLE[k % 5])}">'
                  f'<div class="ic" style="background:{TINT.get(it.get("color", CYCLE[k % 5]), "#EEF3FB")}">{any_img(it.get("icon"), 78)}</div>{md(it["label"])}</div>'
                  for k, it in enumerate(items))
    return f'<div class="v2-cat{c3}">{out}</div>'


def checklist(i):
    dim = set(i.get('dim') or [])
    rows = ''.join(f'<div class="row {"dim" if k in dim else ""}">{icon("tick", 58)}<span>{md(t)}</span></div>' for k, t in enumerate(i['items']))
    ill = f'<div class="ill">{any_img(i["img"], 300)}</div>' if i.get('img') else ''
    return f'<div class="v2-check">{ill}<div class="v2-card plain"><div class="v2-dots"><i></i><i></i><i></i></div><div class="rows">{rows}</div></div></div>'


_ARROW = '<svg class="v2-arrow" viewBox="0 0 120 40"><path d="M4 20 H104 M88 6 L108 20 L88 34" fill="none" stroke="#1D2228" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def options(i):
    src = i.get('source') or {}
    s = f'<div class="src">{any_img(src.get("img"), 150)}{md(src.get("text", ""))}</div>'
    opts = ''.join(f'<div class="o"><div class="bd" style="background:{_c(CYCLE[k % 5])};color:{_txt_on(CYCLE[k % 5])}">{k + 1}</div>{md(t)}</div>'
                   for k, t in enumerate(i['items']))
    return f'<div class="v2-opt">{s}{_ARROW}<div class="grid2"><div class="ttl">{md(i.get("title", ""))}</div>{opts}</div></div>'


def buildlist(i):
    a = i.get('active', 0)
    chev = f'<div class="chev">{icon("chevron", 60)}</div>'
    out = ''.join(f'<div class="it {"on" if k == a else ""}">{chev if k == a else "<div class=sp></div>"}<span>{md(t)}</span></div>'
                  for k, t in enumerate(i['items']))
    return f'<div class="v2-build">{out}</div>'


def recap(i):
    out = ''.join(f'<div class="it"><div class="bd" style="background:{_c(CYCLE[k % 5])};color:{_txt_on(CYCLE[k % 5])}">{k + 1}</div><span>{md(t)}</span></div>'
                  for k, t in enumerate(i['items']))
    return f'<div class="v2-recap">{out}</div>'


def pills(i):
    a = i.get('active', 0); col = i.get('color', 'green')
    out = ''
    for k, t in enumerate(i['items']):
        cls = col if k == a else ('yellow' if k == a + 1 and i.get('next', True) else 'ghost')
        out += f'<span class="v2-pill {cls}">{md(t)}</span>'
    return f'<div class="v2-pills">{out}</div>'


def timeline(i):
    items = i['items']; n = len(items)
    dots = '<i style="left:-6px"></i><i style="right:-6px"></i>'
    fs = ''.join(f'<div class="f" style="left:{(k + .5) * 100 / n:.1f}%"><div class="v2-folder" style="background:{_c(it.get("color"), CYCLE[k % 5])};color:{_txt_on(it.get("color", CYCLE[k % 5]))}">'
                 f'<div class="tab" style="background:{_c(it.get("color"), CYCLE[k % 5])}"></div>{md(it["label"])}</div><div class="cap">{md(it.get("caption", ""))}</div></div>'
                 for k, it in enumerate(items))
    return f'<div class="v2-tl"><div class="axis">{dots}</div>{fs}</div>'


def bigphrase(i):
    ill = any_img(i.get('img'), 300) if i.get('img') else ''
    blob = '<div class="blob"></div>' if i.get('blob', True) else ''
    al = i.get('align', 'center')
    return (f'<div class="v2-big">{ill}<div class="v2-blobwrap" style="flex-direction:column;align-items:{"center" if al == "center" else "flex-start"};text-align:{al}">'
            f'{blob}<div class="w">{md(i["word"])}</div><div class="ph">{md(i.get("phrase", ""))}</div></div></div>')


# ---- over the presenter (white text, soft shadow, yellow keywords; never over the face)
def ov_title(i):
    sub = f'<div class="sub">{md(i["sub"])}</div>' if i.get('sub') else ''
    return f'<div class="v2-ov" style="text-align:{i.get("align", "left")}"><div class="v2-ovtitle" style="font-size:{i.get("size", 150)}px">{md(i["title"])}</div><div class="v2-ovline"></div>{sub}</div>'


def ybox(i):
    lead = f'<div class="v2-ovlead">{md(i["lead"])}</div>' if i.get('lead') else ''
    return f'<div class="v2-ov" style="text-align:{i.get("align", "left")}">{lead}<div class="v2-ovy">{md(i["text"])}</div></div>'


def bubble(i):
    tail = '<svg class="tail" width="60" height="46" viewBox="0 0 60 46"><path d="M0 0 H60 L8 46Z" fill="#fff"/></svg>'
    return (f'<div class="v2-ov v2-bubble"><div class="bx"><div class="sm">{md(i.get("small", ""))}</div><div class="bg">{md(i["big"])}</div>{tail}</div>'
            f'<div class="q">?</div></div>')


def caption(i):
    ic = ('<svg width="76" height="76" viewBox="0 0 100 100"><circle cx="50" cy="50" r="46" fill="#FEC02D"/>'
          '<path d="M30 50 H70 M54 32 L72 50 L54 68" fill="none" stroke="#1D2228" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    l2 = f'<div class="l2">{md(i["follow"])}</div>' if i.get('follow') else ''
    return f'<div class="v2-ov v2-cap"><div class="l1">{ic}<span>{md(i["text"])}</span></div>{l2}</div>'


def pill_rail(i):
    a = i.get('active', 0); n = len(i['items'])
    lead = f'<div class="v2-ovlead" style="font-size:52px">{md(i["lead"])}</div>' if i.get('lead') else ''
    ps = ''.join(f'<div class="pp {"on" if k == a else ""}">{md(t)}</div>' for k, t in enumerate(i['items']))
    return (f'<div class="v2-ov">{lead}<div class="v2-rail"><div class="rl"><i style="top:{100 * a / n:.1f}%;height:{100 / n:.1f}%"></i></div>'
            f'<div class="ps">{ps}</div></div></div>')


def relation(i):
    note_ = f'<div class="nt">{md(i["note"])}</div>' if i.get('note') else ''
    return (f'<div class="v2-ov v2-rel"><div class="t">{md(i["title"])}</div><div class="v2-ovline" style="width:60%"></div>'
            f'<div class="row"><span class="pl">{md(i["left"])}</span>'
            f'<svg width="90" height="36" viewBox="0 0 90 36"><path d="M4 18 H76 M62 6 L80 18 L62 30" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            f'<span class="pl o">{md(i["right"])}</span></div>{note_}</div>')


R.update(acronym=acronym, qtitle=qtitle, steps=steps, slab_table=slab_table, split_bar=split_bar, cost_compare=cost_compare,
         updown=updown, donut=donut, pie=pie, fbox=fbox, people=people, catgrid=catgrid, checklist=checklist, options=options,
         buildlist=buildlist, recap=recap, pills=pills, timeline=timeline, bigphrase=bigphrase,
         ov_title=ov_title, ybox=ybox, bubble=bubble, caption=caption, pill_rail=pill_rail, relation=relation)

# ======================================================================= decor
_DOODLE = ('<svg width="150" height="90" viewBox="0 0 150 90"><path d="M6 40c18-26 26-36 18-34-8 2-12 34 6 34s20-24 12-22-6 26 12 26 '
           '18-22 12-20-4 26 14 26 18-18 12-16-2 22 18 30" fill="none" stroke="{c}" stroke-width="4" stroke-linecap="round"/></svg>')


def _tri(c, rot, sz):
    return (f'<svg width="{sz}" height="{sz}" viewBox="0 0 40 40"><path d="M8 6 L36 20 L8 34 Z" fill="{c}" stroke="{c}" stroke-width="5" '
            f'stroke-linejoin="round" transform="rotate({rot} 20 20)"/></svg>')


_STAR = ('<svg width="70" height="70" viewBox="0 0 40 40"><path d="M20 2 L24 16 L38 20 L24 24 L20 38 L16 24 L2 20 L16 16Z" fill="#C9CBCF" '
         'transform="rotate(20 20 20)"/></svg>')


def _pos(d):
    """{'left':'210px','top':110} → css; numbers become px."""
    return ';'.join(f'{k}:{v}px' if isinstance(v, (int, float)) else f'{k}:{v}' for k, v in (d or {}).items()
                    if k in ('left', 'right', 'top', 'bottom'))


def _seed(fid):
    import zlib
    return zlib.crc32(str(fid).encode()) % 997


def fss_decor(seed, f=None):
    """v2 decor around the edges, never touching text: black loop doodle, two rounded triangles,
    grey 4-point star, orange dash left, green dash right. Override any piece per frame with
    f["decor"] = {doodleAt, tri1, tri2, starAt, dash1, dash2: {left|right|top|bottom}, doodle:false, star:false},
    plus optional f["blob"] {x,y,w,h} (grey blob behind a hero) and f["glow"] {x,y,d} (pale yellow circle)."""
    o = (f or {}).get('decor') if isinstance((f or {}).get('decor'), dict) else {}
    rnd = random.Random(seed)
    cols = ['#A77BF3', '#4DAB4D', '#F07339', '#FEC02D']
    c1 = cols[rnd.randrange(4)]; c2 = cols[(cols.index(c1) + 1 + rnd.randrange(3)) % 4]
    add = lambda html_, pos: f'<div class="decor" style="{_pos(pos)}">{html_}</div>'
    out = []
    if f and f.get('blob'):
        b = f['blob']
        out.append(f'<div class="decor" style="left:{b.get("x", 760)}px;top:{b.get("y", 300)}px;width:{b.get("w", 420)}px;height:{b.get("h", 420)}px;'
                   f'background:#F2F2F2;border-radius:46% 54% 60% 40%/50% 42% 58% 50%;z-index:1"></div>')
    if f and f.get('glow'):
        g = f['glow']; d = g.get('d', 520)
        out.append(f'<div class="decor" style="left:{g.get("x", 1100)}px;top:{g.get("y", 280)}px;width:{d}px;height:{d}px;border-radius:50%;background:#FFF6D6;z-index:1"></div>')
    has_note = any(isinstance(it, dict) and it.get('t') == 'note' for it in (f or {}).get('items') or [])
    if o.get('doodle', True) is not False and not has_note:
        out.append(add(_DOODLE.format(c='#1D2228'), o.get('doodleAt') or {'left': 40 + rnd.randint(0, 30), 'top': 60 + rnd.randint(0, 30)}))
    out.append(add(_tri(c1, rnd.randrange(360), 56), o.get('tri1') or {'right': 70 + rnd.randint(0, 60), 'top': 110 + rnd.randint(0, 60)}))
    out.append(add(_tri(c2, rnd.randrange(360), 80), o.get('tri2') or {'left': 60 + rnd.randint(0, 60), 'bottom': 90 + rnd.randint(0, 60)}))
    if o.get('star', True) is not False:
        out.append(add(_STAR, o.get('starAt') or {'right': 70 + rnd.randint(0, 60), 'bottom': 70 + rnd.randint(0, 40)}))
    out.append(add('<div style="width:64px;height:10px;border-radius:10px;background:#F07339"></div>', o.get('dash1') or {'left': 40, 'top': f'{40 + rnd.randint(0, 20)}%'}))
    out.append(add('<div style="width:58px;height:6px;border-radius:6px;background:#4DAB4D"></div>', o.get('dash2') or {'right': 40, 'top': f'{28 + rnd.randint(0, 10)}%'}))
    return ''.join(out)


def anchor_decor(zone, f=None):
    """Over the presenter: one orange triangle, one purple triangle and a white doodle, at the text zone's edges."""
    o = (f or {}).get('decor') if isinstance((f or {}).get('decor'), dict) else {}
    x, y, w, h = zone['x'], zone['y'], zone['w'], zone['h']
    add = lambda html_, pos: f'<div class="decor" style="{_pos(pos)};z-index:8">{html_}</div>'
    return (add(_tri('#F07339', 20, 60), o.get('tri1') or {'left': max(20, x - 70), 'top': max(20, y + 10)})
            + add(_tri('#A77BF3', 200, 64), o.get('tri2') or {'left': min(1840, x + w - 20), 'top': min(1000, y + h - 40)})
            + (add(_DOODLE.format(c='#FFFFFF'), o.get('doodleAt') or {'left': min(1760, x + w - 160), 'top': max(20, y - 70)})
               if o.get('doodle', True) is not False else ''))


# ======================================================================= frame
def _zo_item_placed(it):
    """Only break out of auto flow when the editor (or spec) marks the layer placed."""
    return bool(it.get('abs') or it.get('_abs'))


def _zo_item_scale_style(it):
    sc = it.get('scale')
    if sc is None:
        return ''
    try:
        s = float(sc)
    except (TypeError, ValueError):
        return ''
    if abs(s - 1.0) < 0.02:
        return ''
    return f' style="transform:scale({s:.3f});transform-origin:center center"'


def _render_stage_inner(f, look):
    look = look or {}
    mode = f.get('mode', 'fss')
    flow_parts = []
    absol = []
    for idx, it in enumerate(f.get('items') or []):
        h = R[it['t']](it)
        scale = _zo_item_scale_style(it)
        if _zo_item_placed(it) and (it.get('x') is not None or it.get('y') is not None):
            absol.append(
                f'<div class="abs z zo-item" data-zo-item="{idx}" data-zo-t="{E(str(it.get("t", "")))}" '
                f'style="left:{it.get("x",0)}px;top:{it.get("y",0)}px">{h}</div>'
            )
        else:
            flow_parts.append((it.get('t'), f'<div class="zo-item" data-zo-item="{idx}" data-zo-t="{E(str(it.get("t", "")))}"{scale}>{h}</div>'))
    if mode == 'fss':
        z = f.get('zone', {'x': 210, 'y': 60, 'w': 1500, 'h': 950})
        body, plate, decor, cut = 'fss', '', (fss_decor(_seed(f['id']), f) if f.get('decor', True) is not False else ''), ''
        align = 'center'
    else:
        pname = _resolve_plate(f, look)
        p = PLATES.get(pname) if pname else None
        if p:
            z = dict(p['zone']); z.update(f.get('zone', {}))
            body = 'dark'; plate = f'<img class="plate" src="../assets/plates/{p["file"]}">'
            cut = f'<img class="cutout" src="../assets/plates/{p["cutout"]}">' if mode == 'tos' and p.get('cutout') else ''
        else:
            z = {'x': 960, 'y': 120, 'w': 880, 'h': 880, 'valign': 'center', 'align': 'left'}
            z.update(f.get('zone', {}))
            body = 'dark'; plate = ''; cut = ''
        decor = anchor_decor(z, f) if f.get('decor', True) is not False else ''
        align = z.get('align', 'center')
        if mode == 'tos':
            t = f.get('title')
            if t:
                ty = f.get('title_y', (p or {}).get('tos_y', 500))
                fs = f.get('title_size', 230 if len(t) <= 11 else int(230 * 11 / len(t)))
                absol.append(f'<div class="tos back" style="top:{ty}px;font-size:{fs}px">{E(t)}</div><div class="tos front" style="top:{ty}px;font-size:{fs}px">{E(t)}</div>')
    jc = {'top': 'flex-start', 'center': 'center', 'bottom': 'flex-end'}[z.get('valign', 'center')]
    ai = {'left': 'flex-start', 'center': 'center', 'right': 'flex-end'}[align]
    gap = f.get('gap', 40 if mode == 'fss' else 24)
    heads = [html for t, html in flow_parts if t == 'heading']
    rest = [html for t, html in flow_parts if t != 'heading']
    fitmax = f.get('fit', 1.6 if mode == 'fss' else 0.95)
    if fitmax is False: fitmax = 1
    origin = {'left': 'left', 'center': 'center', 'right': 'right'}[align]
    hd = f'<div style="width:100%;text-align:{align};display:flex;flex-direction:column;align-items:{ai}">{"".join(heads)}</div>' if heads else ''
    fl = (f'<div class="abs z flow" style="left:{z["x"]}px;top:{z["y"]}px;width:{z["w"]}px;height:{z["h"]}px;'
          f'align-items:{ai};gap:{gap}px;text-align:{align}">{hd}'
          f'<div class="fitwrap" style="flex:1;min-height:0;width:100%;display:flex;align-items:{jc};justify-content:{ai}">'
          f'<div class="fitbox" data-max="{fitmax}" style="display:flex;flex-direction:column;align-items:{ai};gap:{gap}px;transform-origin:{origin} center">{"".join(rest)}</div></div></div>')
    pname = _resolve_plate(f, look) if mode != 'fss' else None
    face = json.dumps((PLATES.get(pname) or {}).get('face')) if mode != 'fss' else 'null'
    inner = f'{plate}{decor}{fl}{"".join(absol)}{cut}'
    return inner, body, mode, face


def frame_html(f, look=None, edit=False):
    look = look or {}
    inner, body, mode, face = _render_stage_inner(f, look)
    opts = {'studioEdit': bool(edit)}
    body_cls = 'studio-edit-mode' if edit else ''
    body_attr = f' class="{body_cls}"' if body_cls else ''
    check_fn = CHECK_JS.replace('document.body.dataset.mode', 'document.getElementById("stage")?.dataset.mode||document.body.dataset.mode')
    check_fn = check_fn.replace('document.body.dataset.face', 'document.getElementById("stage")?.dataset.face||document.body.dataset.face')
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="studio-canvas" content="{CANVAS_W},{CANVAS_H}">
<link rel="stylesheet" href="../templates/zo.css"></head><body{body_attr}>
<div id="stage" class="{body}" data-mode="{mode}" data-face='{face}'>{inner}</div>
<script>window.FRAME={json.dumps(f, ensure_ascii=False)};window.OPTS={json.dumps(opts)};</script>
<script>window.__ZO_CHECK={check_fn};</script>
<script src="../templates/render.js"></script></body></html>'''

FIT_JS = r'''() => {
 for (const b of document.querySelectorAll('.fitbox')) {
   const w = b.parentElement, mx = parseFloat(b.dataset.max || 1);
   const s = Math.max(0.55, Math.min(w.clientWidth * 0.94 / b.offsetWidth, w.clientHeight * 0.94 / b.offsetHeight, mx));
   if (Math.abs(s - 1) > 0.02) b.style.transform = `scale(${s.toFixed(3)})`;
   b.dataset.scale = s.toFixed(3);
 }
}'''

CHECK_JS = r'''() => {
 const W=[], mode=document.body.dataset.mode, face=JSON.parse(document.body.dataset.face||'null');
 const els=[...document.querySelectorAll('.z *')].filter(e=>e.children.length===0||e.matches('.obj,.ticket,.note .box,.icard,.pcard,.status,.phone,.notepad,.mtable'));
 const ok=new Set(['rgb(255, 255, 255)','rgb(34, 34, 34)','rgb(66, 66, 66)','rgb(136, 136, 136)','rgb(255, 192, 46)','rgb(73, 147, 233)','rgb(56, 126, 209)',
   'rgb(129, 187, 255)','rgb(76, 175, 82)','rgb(240, 115, 57)','rgb(155, 123, 234)','rgb(178, 178, 178)','rgb(0, 0, 0)','rgb(29, 34, 40)','rgb(56, 127, 209)','rgb(254, 192, 45)','rgb(77, 171, 77)','rgb(167, 123, 243)','rgb(138, 143, 150)','rgb(91, 97, 104)','rgb(210, 60, 60)','rgb(196, 82, 31)','rgb(227, 237, 249)']);
 for(const e of els){ const r=e.getBoundingClientRect(); if(!r.width||!r.height) continue;
   const t=(e.innerText||e.className||'').toString().slice(0,40).replace(/\n/g,' ');
   if(r.left<-2||r.top<-2||r.right>1922||r.bottom>1082) W.push(`off-frame: "${t}" (${r.left|0},${r.top|0},${r.right|0},${r.bottom|0})`);
   if(face && !(r.right<face[0]||r.left>face[2]||r.bottom<face[1]||r.top>face[3])) W.push(`covers anchor face: "${t}"`);
   if(e.scrollWidth>e.clientWidth+2 && getComputedStyle(e).overflow!=='visible') W.push(`text clipped: "${t}"`);
   const cs=getComputedStyle(e);
   const sc=parseFloat((e.closest('.fitbox')||{dataset:{}}).dataset.scale||1), eff=parseFloat(cs.fontSize)*sc;
   if(e.children.length===0 && e.innerText && e.innerText.trim() && eff<25.5 && !e.closest('.phone,.kscreen,.knav,.ktabs,.ktool,.kwin svg')) W.push(`text under 26px: "${t}" (${eff.toFixed(0)}px after fit)`);
   if(e.children.length===0 && e.innerText && e.innerText.trim() && !ok.has(cs.color) && !e.closest('.phone,.kscreen,.kwin,.wpop')) W.push(`off-palette text colour ${cs.color}: "${t}"`);
 }
 for(const sh of document.querySelectorAll('.between,.hubc,.cal,.bigpill,.pillv,.obj,.icard,.note .box,.fterm')){
   const R=sh.getBoundingClientRect();
   for(const c of sh.querySelectorAll('*')){ if(!c.innerText||!c.innerText.trim()) continue; const r=c.getBoundingClientRect();
     if(r.left<R.left-3||r.right>R.right+3||r.top<R.top-3||r.bottom>R.bottom+3){W.push(`text overflows its shape: "${c.innerText.slice(0,30)}"`);break;}}
 }
 if(mode==='tos' && face){ for(const tt of document.querySelectorAll('.tos.front')){ const r=tt.getBoundingClientRect();
   const h=parseFloat(getComputedStyle(tt).fontSize)*0.75, top=r.top+(r.height-h)/2;
   if(top<face[3]) W.push(`TOS title overlaps the face (cap top ${top|0} < chin ${face[3]}) — raise title_y`);
   if(r.bottom>1060) W.push('TOS title runs off the bottom — lower title_y or shorten'); } }
 const fb=document.querySelector('.fitbox'); if(fb && parseFloat(fb.dataset.scale)<0.8) W.push(`content shrunk to ${fb.dataset.scale} to fit — split the frame or cut text`);
 const all=document.body.innerText;
 if(/~/.test(all)) W.push('contains "~" — write "About"/"Nearly" or the exact figure');
 if(/\d{1,3},\d{3},\d{3}/.test(all)) W.push('Western digit grouping found (e.g. 1,200,000) — use Indian grouping (12,00,000)');
 if(mode==='fss'){ const hs=[...document.querySelectorAll('.heading')].map(h=>getComputedStyle(h).fontSize); if(hs.some(s=>s!=='72px')) W.push('FSS heading not 72px');}
 return [...new Set(W)].slice(0,14);
}'''

async def render(ids, out):
    from playwright.async_api import async_playwright
    exe = os.environ.get('CHROMIUM_PATH')
    async with async_playwright() as p:
        try: b = await p.chromium.launch(**({'executable_path': exe} if exe else {}))
        except Exception:
            cand = next((c for c in ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome'] if os.path.isfile(c)), None)
            if not cand: raise
            b = await p.chromium.launch(executable_path=cand)
        pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
        for fid in ids:
            await pg.goto('file://' + os.path.abspath(os.path.join(out, '_html', fid + '.html')))
            await pg.wait_for_function('window.RENDERED === true', timeout=20_000)
            await pg.wait_for_timeout(80)
            await pg.screenshot(path=f'{out}/{fid}.png')
            for w in await pg.evaluate('window.QA ? window.QA() : []'): print(f'WARN {fid}: {w}')
        await b.close()

def sheet(ids, out):
    from PIL import Image, ImageDraw
    cols, tw, th, per = 2, 960, 540, 6
    for old in [f for f in os.listdir(out) if f.startswith('_sheet')]: os.remove(os.path.join(out, old))
    names = []
    for s0 in range(0, len(ids), per):
        chunk = ids[s0:s0 + per]; rows = (len(chunk) + cols - 1) // cols
        S = Image.new('RGB', (cols * tw, rows * (th + 30)), 'white'); d = ImageDraw.Draw(S)
        for k, fid in enumerate(chunk):
            im = Image.open(f'{out}/{fid}.png').convert('RGB').resize((tw, th))
            x, y = (k % cols) * tw, (k // cols) * (th + 30)
            S.paste(im, (x, y + 30)); d.text((x + 8, y + 8), fid, fill='black')
        n = f'{out}/_sheet_{s0 // per + 1}.jpg'; S.save(n, quality=80); names.append(n)
    print('QA sheets (view each once):', ' '.join(names))

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'): print(__doc__); sys.exit(0)
    spec = json.load(open(a[0]))
    out = a[a.index('--out') + 1] if '--out' in a else 'out'; os.makedirs(os.path.join(out, '_html'), exist_ok=True)
    only = set(a[a.index('--only') + 1].split(',')) if '--only' in a else None
    look = spec.get('look', {}); ids = []; skipped = []
    for f in spec['frames']:
        if only and f['id'] not in only: continue
        if f.get('mode', 'fss') != 'fss': skipped.append(f['id']); continue
        open(os.path.join(out, '_html', f['id'] + '.html'), 'w').write(frame_html(f, look)); ids.append(f['id'])
    asyncio.run(render(ids, out))
    print(f'rendered {len(ids)} FSS frames -> {out}/')
    if skipped: print('skipped (anchor beats are editor notes, not rendered):', ', '.join(skipped))
    if '--no-sheet' not in a: sheet([f['id'] for f in spec['frames'] if os.path.exists(f"{out}/{f['id']}.png")], out)

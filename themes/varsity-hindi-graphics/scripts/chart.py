"""Chart engine: OHLC data generation + SVG drawing for mock Kite charts and concept diagrams.
Pure Python, no deps. Used by build.py."""
import random, math, html, datetime
E = html.escape
GREEN, CORAL, BLUE, TAG = '#A5CC65', '#F47964', '#307AD4', '#FFBE30'
CANDLE_CORAL = '#ED6258'   # Kite-window candles (diagrams use CORAL #F47964), measured Ep4-5
FONT = "font-family:Inter"

# --------------------------------------------------------------------------- data
def _pattern(kind, p, s, rnd):
    """Return o,h,l,c for a named single-candle pattern around price p with unit size s."""
    if kind == 'marubozu_bull': o, c = p, p + 4.5*s; return o, c + 0.05*s, o, c
    if kind == 'marubozu_bear': o, c = p, p - 4.5*s; return o, o, c - 0.05*s, c
    if kind in ('hammer', 'hanging_man'):
        o = p; c = p + 0.7*s if kind == 'hammer' else p - 0.7*s
        return o, max(o, c) + 0.12*s, min(o, c) - 2.8*s, c
    if kind in ('inverted_hammer', 'shooting_star'):
        o = p; c = p + 0.7*s if kind == 'inverted_hammer' else p - 0.7*s
        return o, max(o, c) + 2.8*s, min(o, c) - 0.12*s, c
    if kind == 'doji': return p, p + 1.6*s, p - 1.6*s, p + 0.04*s
    if kind == 'dragonfly_doji': return p, p + 0.04*s, p - 2.6*s, p + 0.02*s
    if kind == 'gravestone_doji': return p, p + 2.6*s, p - 0.04*s, p - 0.02*s
    if kind == 'long_bull': o, c = p, p + 5*s; return o, c + 0.6*s, o - 0.6*s, c
    if kind == 'long_bear': o, c = p, p - 5*s; return o, o + 0.6*s, c - 0.6*s, c
    if kind == 'short_bull': o, c = p, p + 1*s; return o, c + 0.5*s, o - 0.5*s, c
    if kind == 'short_bear': o, c = p, p - 1*s; return o, o + 0.5*s, c - 0.5*s, c
    raise ValueError('unknown pattern ' + kind)

def _ohlc(o, c, up, dn): return (o, max(o, c) + up, min(o, c) - dn, c)
MULTI = {
 'bullish_engulfing': lambda p, s: [_ohlc(p, p - 1.2*s, .3*s, .3*s), _ohlc(p - 1.6*s, p + 1.1*s, .3*s, .3*s)],
 'bearish_engulfing': lambda p, s: [_ohlc(p, p + 1.2*s, .3*s, .3*s), _ohlc(p + 1.6*s, p - 1.1*s, .3*s, .3*s)],
 'piercing':          lambda p, s: [_ohlc(p, p - 3*s, .3*s, .3*s), _ohlc(p - 3.8*s, p - 1.0*s, .3*s, .3*s)],
 'dark_cloud':        lambda p, s: [_ohlc(p, p + 3*s, .3*s, .3*s), _ohlc(p + 3.8*s, p + 1.0*s, .3*s, .3*s)],
 'morning_star':      lambda p, s: [_ohlc(p, p - 4*s, .3*s, .3*s), _ohlc(p - 4.8*s, p - 4.75*s, .9*s, .9*s), _ohlc(p - 4.4*s, p - .3*s, .3*s, .3*s)],
 'evening_star':      lambda p, s: [_ohlc(p, p + 4*s, .3*s, .3*s), _ohlc(p + 4.8*s, p + 4.75*s, .9*s, .9*s), _ohlc(p + 4.4*s, p + .3*s, .3*s, .3*s)],
}
MULTI_LEN = {k: (3 if 'star' in k else 2) for k in MULTI}

def gen(cfg):
    """cfg: {n, path:[waypoint prices], vol (fraction, default .006), seed, patterns:{i: kind}, decimals}
    Returns list of dict(o,h,l,c). Deterministic for a given seed."""
    n = int(cfg.get('n', 40)); path = cfg.get('path') or [1000, 1060]
    rnd = random.Random(cfg.get('seed', 7)); vol = cfg.get('vol', .006)
    pats = {int(k): v for k, v in (cfg.get('patterns') or {}).items()}
    seg = (n - 1) / max(1, len(path) - 1)
    def target(i):
        k = min(int(i // seg), len(path) - 2); t = (i - k*seg) / seg
        return path[k] + (path[k+1] - path[k]) * t
    out = []; prev = path[0]; queue = []
    for i in range(n):
        s = target(i) * vol
        if queue:
            o, h, l, c = queue.pop(0)
        elif i in pats and pats[i] in MULTI:
            seq = MULTI[pats[i]](prev, s); o, h, l, c = seq[0]; queue = list(seq[1:])
        elif i in pats:
            o, h, l, c = _pattern(pats[i], prev, s, rnd)
        else:
            o = prev + rnd.gauss(0, .25*s)
            c = target(i) + rnd.gauss(0, 1.3*s)
            h = max(o, c) + abs(rnd.gauss(0, .9*s)); l = min(o, c) - abs(rnd.gauss(0, .9*s))
        d = cfg.get('decimals', 2)
        out.append({'o': round(o, d), 'h': round(h, d), 'l': round(l, d), 'c': round(c, d)}); prev = c
    return out

def check(cs, where):
    w = []
    for i, k in enumerate(cs):
        if not (k['h'] >= max(k['o'], k['c']) - 1e-9 and k['l'] <= min(k['o'], k['c']) + 1e-9):
            w.append(f'{where}: candle {i} is impossible (H must be >= O,C and L <= O,C): {k}')
    return w

# --------------------------------------------------------------------------- axes
def nice_step(span, target=9):
    raw = span / target; mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag: return m * mag
    return 10 * mag

def fmt(v, dec=2): return f'{v:,.{dec}f}'

def x_labels(spec, n):
    """spec: list of strings (spread evenly) or {type: intraday|days|months|years|weeks|index, start, step, every}"""
    if spec is None: return []
    if isinstance(spec, list):
        if not spec: return []
        k = len(spec); return [(round(j * (n - 1) / max(1, k - 1)), s) for j, s in enumerate(spec)]
    t = spec.get('type', 'index'); every = spec.get('every') or max(1, round(n / 10)); lab = []
    if t == 'intraday':
        hh, mm = map(int, spec.get('start', '09:15').split(':')); st = spec.get('step', 5)
        for i in range(0, n, every):
            m = hh*60 + mm + i*st; lab.append((i, f'{m//60:02d}:{m%60:02d}'))
    elif t == 'days':
        d = datetime.date.fromisoformat(spec.get('start', '2026-06-01')); ds = []
        while len(ds) < n:
            if d.weekday() < 5: ds.append(d)
            d += datetime.timedelta(days=1)
        for i in range(0, n, every):
            dd = ds[i]; lab.append((i, dd.strftime('%b') if (i == 0 or ds[i - every].month != dd.month) else str(dd.day)))
    elif t == 'months':
        y, m = map(int, spec.get('start', '2025-05').split('-'))
        for i in range(0, n, every):
            mm = (m - 1 + i) % 12; yy = y + (m - 1 + i) // 12
            lab.append((i, datetime.date(yy, mm + 1, 1).strftime('%b') + (f' {str(yy)[2:]}' if mm == 0 else '')))
    elif t == 'years':
        y0 = int(spec.get('start', 2011)); per = spec.get('per_year', 12)
        for i in range(0, n, per): lab.append((i, str(y0 + i // per)))
    elif t == 'weeks':
        per = spec.get('per_week', 5)
        for i in range(0, n, per): lab.append((i, f'Week {i // per + 1}'))
    else:
        for i in range(0, n, every): lab.append((i, str(i + 1)))
    return lab

# --------------------------------------------------------------------------- drawing helpers
def txt(x, y, s, size=22, w=500, fill='#222', anchor='start', extra=''):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}" style="{FONT}" {extra}>{E(str(s))}</text>'

def tagbox(x, y, s, fill, stroke='#333', color='#111', size=22, anchor='middle', pad=12):
    tw = len(str(s)) * size * .58 + 2*pad; h = size + 16
    x0 = x - tw/2 if anchor == 'middle' else (x if anchor == 'start' else x - tw)
    return (f'<rect x="{x0:.1f}" y="{y - h/2:.1f}" width="{tw:.1f}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            + txt(x0 + tw/2, y + size*.36, s, size, 500, color, 'middle')), tw

# Boxes are never green/red: green/coral live only on candle and bar bodies (house rule)
OHLC_STYLE = {'open': ('#fff', '#111'), 'close': ('#fff', '#111'), 'high': ('#fff', '#111'), 'low': ('#fff', '#111')}

# --------------------------------------------------------------------------- Kite chart
def kite_svg(c, W, H, warns, fid):
    """Draw the inside of a mock Kite window (below the title bar). Returns (svg, meta)."""
    cs = c['candles']; n = len(cs); typ = c.get('type', 'candle'); dark = c.get('bare')
    ink = '#fff' if dark else '#1b1b1b'
    o = []
    if not dark:
        # toolbar + side panel + chevron
        o.append(f'<path d="M78 40 l-10 22 h10 l-6 18 l16 -24 h-10 l6 -16z" fill="none" stroke="{BLUE}" stroke-width="2.2"/>')
        o.append(f'<circle cx="122" cy="58" r="8" fill="none" stroke="#333" stroke-width="2.4"/><path d="M128 64 l7 7" stroke="#333" stroke-width="2.4"/>')
        o.append('<rect x="142" y="54" width="48" height="9" rx="2" fill="#6b6b6b"/>')
        o.append('<circle cx="236" cy="58" r="11" fill="none" stroke="#333" stroke-width="2"/><path d="M230 58h12M236 52v12" stroke="#333" stroke-width="2"/>')
        o.append('<line x1="268" y1="38" x2="268" y2="80" stroke="#7aa8d8" stroke-width="2"/><rect x="284" y="54" width="22" height="9" fill="#bbb"/><rect x="330" y="54" width="22" height="9" fill="#bbb"/>')
        o.append('<line x1="372" y1="38" x2="372" y2="80" stroke="#7aa8d8" stroke-width="2"/><rect x="388" y="54" width="52" height="9" fill="#bbb"/><rect x="452" y="54" width="22" height="9" fill="#bbb"/>')
        o.append(f'<path d="M500 40 l-10 22 h10 l-6 18 l16 -24 h-10 l6 -16z" fill="{BLUE}"/>')
        o.append(f'<line x1="60" y1="96" x2="{W*.55:.0f}" y2="96" stroke="#7aa8d8" stroke-width="2"/>')
        o.append(f'<line x1="58" y1="70" x2="58" y2="{H-40}" stroke="#7aa8d8" stroke-width="2"/><line x1="104" y1="96" x2="104" y2="{H-40}" stroke="#7aa8d8" stroke-width="2"/>')
        for yy in range(120, H - 50, 46): o.append(f'<rect x="70" y="{yy}" width="20" height="8" rx="2" fill="#86B6E8"/>')
        o.append(f'<image href="{c["_chev"]}" x="{W-150}" y="34" width="46" height="32"/>')
    px0, px1 = (30, W - 30) if dark else (150, W - 210)
    py0, py1 = (40, H - 50) if dark else (150, H - 110)
    vis = range(n)
    lo = min(cs[i]['l'] for i in vis); hi = max(cs[i]['h'] for i in vis)
    for hl in c.get('hlines', []): lo, hi = min(lo, hl['price']), max(hi, hl['price'])
    tr = c.get('trade')
    if tr:
        for k in ('entry', 'target', 'stop'):
            if k in tr: lo, hi = min(lo, tr[k]), max(hi, tr[k])
    pad = (hi - lo) * .08 or 1; lo -= pad; hi += pad
    if c.get('y_range'): lo, hi = c['y_range']
    Y = lambda v: py1 - (v - lo) / (hi - lo) * (py1 - py0)
    slots = n + (max(6, n * .55) if tr else 0)
    step = (px1 - px0) / max(1, slots); X = lambda i: px0 + step * (i + .5)
    bw = min(42, step * .62)
    dec = c.get('decimals', 2)
    # axes
    if not dark:
        o.append(f'<line x1="{px1+12}" y1="{py0-60}" x2="{px1+12}" y2="{py1+14}" stroke="#1b1b1b" stroke-width="2"/>')
        o.append(f'<line x1="{px0-14}" y1="{py1+14}" x2="{px1+12}" y2="{py1+14}" stroke="#1b1b1b" stroke-width="2"/>')
        st = nice_step(hi - lo); v = math.ceil(lo / st) * st
        while v <= hi:
            o.append(txt(px1 + 30, Y(v) + 8, fmt(v, dec), c.get('y_size', 22), 500, '#222')); v += st
        for i, s in x_labels(c.get('x_axis'), n):
            o.append(txt(X(i), py1 + 50, s, 22, 500, '#222', 'middle'))
        tk = c.get('ticker')
        if tk:
            o.append(txt(px0 + 6, py0 - 20, tk, 30, 600, '#111'))
            ro = c.get('readout')
            if ro is not None and ro is not False:
                k = cs[n - 1 if ro is True else int(ro)]
                o.append(txt(px0 + 6 + len(tk) * 19 + 40, py0 - 20, f'O: {fmt(k["o"],dec)}   H: {fmt(k["h"],dec)}   L: {fmt(k["l"],dec)}   C: {fmt(k["c"],dec)}', 21, 500, '#333'))
    fade = set(c.get('fade_except') or [])
    # trade zones (drawn under candles)
    if tr:
        xs = X(tr.get('from', n - 1)) + bw; xe = px1 - 6
        e, t_, s_ = tr['entry'], tr['target'], tr['stop']
        o.append(f'<rect x="{xs:.0f}" y="{Y(t_):.0f}" width="{xe-xs:.0f}" height="{Y(e)-Y(t_):.0f}" fill="none" stroke="#307AD4" stroke-width="2" stroke-dasharray="8 6"/>')
        o.append(f'<rect x="{xs:.0f}" y="{Y(e):.0f}" width="{xe-xs:.0f}" height="{Y(s_)-Y(e):.0f}" fill="none" stroke="#333" stroke-width="2" stroke-dasharray="8 6"/>')
        for k, v in (('target', t_), ('entry', e), ('stop', s_)):
            o.append(f'<line x1="{px0}" y1="{Y(v):.0f}" x2="{px1+12}" y2="{Y(v):.0f}" stroke="#7aa8d8" stroke-width="2" stroke-dasharray="3 5"/>')
            b, _ = tagbox(px1 + 66, Y(v), fmt(v, 1), TAG, '#444', '#111', 22)
            o.append(b)
        mid = (xs + xe) / 2; pw = 230
        words = tr.get('labels', 'words') == 'words'
        ph = 60 if words else 44
        ys = {'Target': Y(t_), 'Entry': Y(e), 'Stoploss': Y(s_)}
        if ys['Entry'] - ys['Target'] < ph + 6: ys['Target'] = ys['Entry'] - ph - 6
        if ys['Stoploss'] - ys['Entry'] < ph + 6: ys['Stoploss'] = ys['Entry'] + ph + 6
        for k, v, fill in (('Target', t_, '#FFFFFF'), ('Entry', e, '#FFFFFF'), ('Stoploss', s_, '#FFFFFF')):
            if not words and k == 'Entry': lab = tr.get('pnl_text', f'Risk/Reward Ratio: {abs(t_-e)/abs(e-s_):.1f}')
            elif not words: lab = f'{k if k!="Stoploss" else "Stop"}: {abs(v-e):.1f} ({abs(v-e)/e*100:.2f}%)'
            else: lab = k
            yv = ys[k]
            o.append(f'<rect x="{mid-pw/2:.0f}" y="{yv-26:.0f}" width="{pw}" height="{56 if words else 40}" rx="10" fill="{fill}" stroke="#333" stroke-width="1.5"/>')
            o.append(txt(mid, yv - 4 if words else yv + 6, lab, 22, 500, '#111', 'middle'))
            if words: o.append(txt(mid, yv + 22, fmt(v, 1), 20, 500, '#111', 'middle'))
    # series
    if typ == 'line':
        pts = ' '.join(f'{X(i):.1f},{Y(k["c"]):.1f}' for i, k in enumerate(cs))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{c.get("line_color", BLUE)}" stroke-width="3" stroke-linejoin="round"/>')
    else:
        for i, k in enumerate(cs):
            col = GREEN if k['c'] >= k['o'] else (CORAL if dark else CANDLE_CORAL); op = .28 if (fade and i not in fade) else 1
            x = X(i)
            if typ == 'bar':
                o.append(f'<g opacity="{op}" stroke="{col}" stroke-width="3"><line x1="{x:.1f}" y1="{Y(k["h"]):.1f}" x2="{x:.1f}" y2="{Y(k["l"]):.1f}"/>'
                         f'<line x1="{x-bw*.45:.1f}" y1="{Y(k["o"]):.1f}" x2="{x:.1f}" y2="{Y(k["o"]):.1f}"/><line x1="{x:.1f}" y1="{Y(k["c"]):.1f}" x2="{x+bw*.45:.1f}" y2="{Y(k["c"]):.1f}"/></g>')
            else:
                top, bot = Y(max(k['o'], k['c'])), Y(min(k['o'], k['c']))
                o.append(f'<g opacity="{op}"><line x1="{x:.1f}" y1="{Y(k["h"]):.1f}" x2="{x:.1f}" y2="{Y(k["l"]):.1f}" stroke="{col}" stroke-width="2.5"/>'
                         f'<rect x="{x-bw/2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(3, bot-top):.1f}" fill="{col}"/></g>')
    # horizontal lines
    for hl in c.get('hlines', []):
        yv = Y(hl['price']); da = {'dotted': '2 6', 'dashed': '10 8', 'solid': ''}[hl.get('style', 'dotted')]
        o.append(f'<line x1="{px0}" y1="{yv:.1f}" x2="{px1+12}" y2="{yv:.1f}" stroke="#333" stroke-width="2" stroke-dasharray="{da}"/>')
        if hl.get('tag', True):
            b, _ = tagbox(px1 + 66, yv, fmt(hl['price'], dec), TAG, '#444', '#111', 21); o.append(b)
        if hl.get('label'): o.append(txt(px0 + 10, yv - 12, hl['label'], 22, 500, '#333'))
    # range boxes (consolidation zones): dashed lines top and bottom
    for rg in c.get('ranges', []):
        a, b = rg['from'], rg['to']; top = max(cs[i]['h'] for i in range(a, b + 1)); bot = min(cs[i]['l'] for i in range(a, b + 1))
        for v in (top, bot):
            o.append(f'<line x1="{X(a)-bw:.1f}" y1="{Y(v):.1f}" x2="{X(b)+bw:.1f}" y2="{Y(v):.1f}" stroke="#222" stroke-width="2.2" stroke-dasharray="9 7"/>')
    # value tags on points (line charts): yellow tag + dashed drop
    for p in c.get('points', []):
        i = p['i']; v = cs[i]['c']; x, yv = X(i), Y(v)
        o.append(f'<circle cx="{x:.1f}" cy="{yv:.1f}" r="7" fill="{TAG}" stroke="#555" stroke-width="1.5"/>')
        if p.get('drop', True): o.append(f'<line x1="{x:.1f}" y1="{yv+8:.1f}" x2="{x:.1f}" y2="{py1+14}" stroke="#333" stroke-width="1.6" stroke-dasharray="5 5"/>')
        if p.get('guide', True): o.append(f'<line x1="{x+8:.1f}" y1="{yv:.1f}" x2="{px1+12}" y2="{yv:.1f}" stroke="#333" stroke-width="1.6" stroke-dasharray="5 5"/>')
        b, _ = tagbox(x + 14, yv - 4, p.get('text', fmt(v, 0)), TAG, '#555', '#111', 22, 'start'); o.append(b)
    # OHLC tags on candles
    for tg in c.get('tags', []):
        i = tg['i']; k = cs[i]; kind = tg['kind']; lab = tg.get('text', kind.capitalize()); fill, col = OHLC_STYLE[kind]
        x = X(i)
        if kind == 'high': b, _ = tagbox(x, Y(k['h']) - 30, lab, fill, '#333', col, 22)
        elif kind == 'low': b, _ = tagbox(x, Y(k['l']) + 30, lab, fill, '#333', col, 22)
        elif kind == 'open': b, _ = tagbox(x - bw/2 - 8, Y(k['o']), lab, fill, '#333', col, 22, 'end')
        else: b, _ = tagbox(x + bw/2 + 8, Y(k['c']), lab, fill, '#333', col, 22, 'start')
        o.append(b)
    # dashed highlight boxes + leader labels
    for bx in c.get('boxes', []):
        a, b = bx['from'], bx.get('to', bx['from'])
        top = max(cs[i]['h'] for i in range(a, b + 1)); bot = min(cs[i]['l'] for i in range(a, b + 1))
        x0, x1 = X(a) - bw/2 - 10, X(b) + bw/2 + 10; y0, y1 = Y(top) - 12, Y(bot) + 12
        if bx.get('full_height'): y0, y1 = py0 - 10, py1 + 10
        o.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" fill="none" stroke="{ink}" stroke-width="2" stroke-dasharray="7 6"/>')
        if bx.get('days'):
            cx = (x0 + x1) / 2; m = b - a + 1; sp = max(step, 62)
            for q, ii in enumerate(range(a, b + 1)):
                tx = X(ii) if step >= 62 else cx + (q - (m - 1) / 2) * sp
                o.append(txt(tx, y0 - 12, f'Day {q+1}', 19 if not dark else 22, 600, ink, 'middle'))
        if bx.get('label'):
            pos = bx.get('pos', 'right'); lines = bx['label'].split('\n'); fs = bx.get('size', 26 if not dark else 30)
            if pos == 'right': ax, ay, tx, ty, an = x1 + 4, (y0+y1)/2, x1 + 70, (y0+y1)/2 + 20, 'start'
            elif pos == 'left': ax, ay, tx, ty, an = x0 - 4, (y0+y1)/2, x0 - 70, (y0+y1)/2 + 20, 'end'
            elif pos == 'above': ax, ay, tx, ty, an = (x0+x1)/2, y0 - 4, (x0+x1)/2 + 40, y0 - 60 - fs*(len(lines)-1), 'start'
            else: ax, ay, tx, ty, an = (x0+x1)/2, y1 + 4, (x0+x1)/2 + 40, y1 + 64, 'start'
            o.append(f'<path d="M{tx-(10 if an=="start" else -10):.1f} {ty-fs*.4:.1f} Q{(ax+tx)/2:.1f} {ty-fs*.4:.1f} {ax:.1f} {ay:.1f}" fill="none" stroke="{ink}" stroke-width="1.6"/>'
                     f'<path d="M{ax:.1f} {ay:.1f} l6 -2 M{ax:.1f} {ay:.1f} l2 6" stroke="{ink}" stroke-width="1.6"/>')
            for j, ln in enumerate(lines): o.append(txt(tx, ty + j * fs * 1.15, ln, fs, 500, ink if not dark else '#fff', an))
    # leader lines to the right edge ("High", "Stoploss")
    for ld in c.get('leaders', []):
        k = cs[ld['i']]; v = k[{'high': 'h', 'low': 'l', 'open': 'o', 'close': 'c'}[ld['at']]]; x = X(ld['i']); yv = Y(v)
        x2 = min(px1 - 10, x + ld.get('len', 240))
        o.append(f'<line x1="{x:.1f}" y1="{yv:.1f}" x2="{x2:.1f}" y2="{yv:.1f}" stroke="#222" stroke-width="1.8" stroke-dasharray="6 5"/>' + txt(x2 + 8, yv + 8, ld['text'], 24, 500, '#222'))
    return '\n'.join(o), {'X': X, 'Y': Y, 'bw': bw}

# --------------------------------------------------------------------------- concept candle / bar diagram (over dark)
def diagram_svg(d, warns, fid):
    """d: {candles:[{o,h,l,c, kind:candle|bar, labels:'ohlc'|'parts'|'eq'|'note'|'none', note, pill:'Bullish'|'Bearish', color}],
           scale: bool (single item with price scale + dashed leaders), w, h, time_label}"""
    cs = d['candles']; W = d.get('w', 760); H = d.get('h', 600); o = []
    for j, k in enumerate(cs):
        for kk in ('o', 'h', 'l', 'c'):
            if kk not in k: raise ValueError(f'{fid}: diagram candle needs o,h,l,c')
        if not (k['h'] >= max(k['o'], k['c']) and k['l'] <= min(k['o'], k['c'])):
            warns.append(f'{fid}: diagram candle {j} impossible OHLC {k}')
        p = (k.get('pill') or '').lower()
        if p.startswith('bull') and k['c'] < k['o']: warns.append(f'{fid}: candle {j} labelled Bullish but Close < Open')
        if p.startswith('bear') and k['c'] > k['o']: warns.append(f'{fid}: candle {j} labelled Bearish but Close > Open')
    lo = min(k['l'] for k in cs); hi = max(k['h'] for k in cs)
    scale = d.get('scale', len(cs) == 1)
    top, bot = 50, H - (110 if scale else (120 if d.get('caption') else 60))
    if d.get('y_range'): lo, hi = d['y_range']
    Y = lambda v: bot - (v - lo) / ((hi - lo) or 1) * (bot - top)
    n = len(cs)
    if scale:
        ax = W - 120
        span = hi - lo; st = d.get('step') or max(1, nice_step(span, 10))
        v = math.ceil(lo / st) * st
        o.append(f'<line x1="{ax}" y1="{top-30}" x2="{ax}" y2="{bot+40}" stroke="#fff" stroke-width="3"/>')
        o.append(f'<line x1="{W*.12:.0f}" y1="{bot+40}" x2="{ax}" y2="{bot+40}" stroke="#fff" stroke-width="3"/>')
        o.append(txt((W*.12 + ax)/2, bot + 100, d.get('time_label', 'Time'), 32, 400, '#fff', 'middle'))
        while v <= hi + 1e-9:
            o.append(txt(ax + 22, Y(v) + 11, fmt(v, 0 if st >= 1 else 1), 32, 400, '#fff')); v += st
        xs = [W * .42]
    elif d.get('spacing'):
        sp = d['spacing']; x0 = W/2 - sp*(n-1)/2; xs = [x0 + sp*j for j in range(n)]
    else:
        xs = [W * (j + .5) / n for j in range(n)]
    if d.get('half_of') is not None:
        k = cs[d['half_of']]; hv = (k['o'] + k['c']) / 2
        o.append(f'<line x1="{min(xs)-110}" y1="{Y(hv)}" x2="{max(xs)+110}" y2="{Y(hv)}" stroke="#fff" stroke-width="2" stroke-dasharray="8 7" opacity=".85"/>' + txt(min(xs)-125, Y(hv)+9, '50%', 26, 500, '#fff', 'end'))
    for j, k in enumerate(cs):
        x = xs[j]; bull = k['c'] >= k['o']; col = k.get('color') or (GREEN if bull else CORAL)
        kind = k.get('kind', 'candle'); bw = d.get('body_w', 90 if scale else 110)
        if kind == 'bar':
            o.append(f'<g stroke="{col}" stroke-width="14"><line x1="{x}" y1="{Y(k["h"])}" x2="{x}" y2="{Y(k["l"])}"/>'
                     f'<line x1="{x-70}" y1="{Y(k["o"])}" x2="{x}" y2="{Y(k["o"])}"/><line x1="{x}" y1="{Y(k["c"])}" x2="{x+70}" y2="{Y(k["c"])}"/></g>')
        else:
            t_, b_ = Y(max(k['o'], k['c'])), Y(min(k['o'], k['c']))
            o.append(f'<line x1="{x}" y1="{Y(k["h"])}" x2="{x}" y2="{Y(k["l"])}" stroke="{k.get("wick_color", col if not d.get("white_wicks") else "#fff")}" stroke-width="5"/>')
            o.append(f'<rect x="{x-bw/2}" y="{t_}" width="{bw}" height="{max(14, b_-t_)}" fill="{col}"/>')
        lab = k.get('labels', 'ohlc' if scale else 'parts'); fs = 32
        outer = -1 if (j == 0 and n > 1) or (n == 1) else 1
        if n == 1 and not scale: outer = -1
        def side(sgn, dx=0): return x + sgn * (bw/2 + 26 + dx), ('end' if sgn < 0 else 'start')
        if lab == 'ohlc' and scale:
            ax = W - 120
            for nm, v, sgn in (('High', k['h'], -1), ('Low', k['l'], -1), ('Open', k['o'], -1), ('Close', k['c'], 1)):
                txv = k.get('values') and f'{nm}: {k.get("cur","")}{fmt(v,0)}' or nm
                if kind == 'bar': xx = x - 90 if sgn < 0 else x + 90
                else: xx = x - bw/2 - 30 if sgn < 0 else x + bw/2 + 30
                if nm in ('High', 'Low') and kind != 'bar': xx = x - 30
                o.append(txt(xx, Y(v) + 11, txv, fs, 400, '#fff', 'end' if sgn < 0 else 'start'))
                # dashed leader to the axis
                lx0 = (x + 20) if nm in ('High', 'Low') else (x + (bw/2 if kind != 'bar' else 70) + 10 + (170 if sgn > 0 else 0))
                o.append(f'<line x1="{lx0}" y1="{Y(v)}" x2="{ax-6}" y2="{Y(v)}" stroke="#fff" stroke-width="2" stroke-dasharray="10 8"/>')
        elif lab == 'parts':
            ox, oa = side(outer); ix, ia = side(-outer)
            o.append(txt(ox, Y(max(k['o'], k['c'])) + 11, 'Close' if bull else 'Open', fs, 400, '#fff', oa))
            o.append(txt(ox, Y(min(k['o'], k['c'])) + 11, 'Open' if bull else 'Close', fs, 400, '#fff', oa))
            if d.get('part_names', True) and j == 0:
                ix2 = (xs[0] + xs[1]) / 2 if n > 1 else ix; ia2 = 'middle' if n > 1 else ia
                o.append(txt(ix2, Y(k['h']) - 22, 'Upper Shadow', fs, 400, '#fff', ia2) + txt(ix2, Y(k['h']) + 22, 'High', fs, 400, '#fff', ia2))
                o.append(txt(ix2, (Y(k['o']) + Y(k['c'])) / 2 - 4, 'Central', fs, 400, '#fff', ia2) + txt(ix2, (Y(k['o']) + Y(k['c'])) / 2 + 34, 'Body', fs, 400, '#fff', ia2))
                o.append(txt(ix2, Y(k['l']) - 10, 'Low', fs, 400, '#fff', ia2) + txt(ix2, Y(k['l']) + 34, 'Lower Shadow', fs, 400, '#fff', ia2))
            elif not d.get('part_names', True):
                o.append(txt(ix, Y(k['h']) + 11, 'High', fs, 400, '#fff', ia) + txt(ix, Y(k['l']) + 11, 'Low', fs, 400, '#fff', ia))
        elif lab == 'ohlc':
            sg = -1 if j < n/2 else 1; ox, oa = side(sg, -8); fs2 = d.get('label_size', 26)
            o.append(txt(ox, Y(max(k['o'], k['c'])) + 9, 'Close' if bull else 'Open', fs2, 400, '#fff', oa))
            o.append(txt(ox, Y(min(k['o'], k['c'])) + 9, 'Open' if bull else 'Close', fs2, 400, '#fff', oa))
            if k.get('hl', True):
                o.append(txt(x, Y(k['h']) - 12, 'High', fs2, 400, '#fff', 'middle') + txt(x, Y(k['l']) + 32, 'Low', fs2, 400, '#fff', 'middle'))
        elif lab == 'eq':
            ox, oa = side(outer, -10)
            a, b = ('Close = High', 'Open = Low') if bull else ('Open = High', 'Close = Low')
            o.append(txt(ox, Y(k['h']) + 22, a, 24, 400, '#fff', oa) + txt(ox, Y(k['l']), b, 24, 400, '#fff', oa))
        if k.get('note'):
            nx, na = side(-outer if n > 1 else 1, 40)
            for q, ln in enumerate(k['note'].split('\n')):
                o.append(txt(nx, (Y(k['o']) + Y(k['c'])) / 2 + q * 38, ln, 32, 400, '#fff', na))
        if k.get('title'): o.append(txt(x, bot + 70, k['title'], 32, 600, '#fff', 'middle'))
    if d.get('caption'): o.append(txt(W/2, H - 10, d['caption'], 32, 500, '#fff', 'middle'))
    return f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" overflow="visible">{"".join(o)}</svg>', xs

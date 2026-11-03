#!/usr/bin/env python3
"""Build every graphic of a Varsity Hindi (Technical Analysis) video from ONE spec.json.

Usage:  python3 scripts/build.py spec.json [--out out] [--only 0.47,1.52] [--no-sheet] [--package Ep06_Support-Resistance]

Writes <out>/<id>.png for every frame, <out>/_sheet_N.jpg (6 frames per contact sheet),
<out>/_text.txt (every on-screen string and number per frame, for proofreading against the script)
and prints WARN lines (impossible OHLC, labels contradicting data, Hinglish on screen, text clipped
or off-frame, content over the presenter). Spec format: references/spec_format.md.
"""
import json, os, sys, re, html, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chart
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = html.escape
CANVAS_W, CANVAS_H = 1920, 1080
WARN = []


def _asset_href(rel: str, *, studio: bool) -> str:
    rel = str(rel).replace("\\", "/").lstrip("/")
    if studio:
        return "../assets/" + rel
    return "file://" + os.path.join(KIT, "assets", rel)


def _set_asset_mode(studio: bool):
    global A
    A = lambda p, _s=studio: _asset_href(p, studio=_s)


_set_asset_mode(studio=False)

# Every colour used in the Ep1-5 finals (measured). Anything else is off-theme.
PALETTE = {'#FFFFFF', '#000000', '#111111', '#141414', '#1B1B1B', '#222222', '#333333', '#6E6E6E', '#D8D8D8',
           '#FFBE30', '#EFB32E', '#F0B32A', '#278BED', '#307AD4',
           '#A5CC65', '#E4F0D0', '#F47964', '#ED6258', '#FCD7D0', '#FFF8E8', '#873832', '#6F9A3A'}
SEMANTIC = {'#A5CC65', '#E4F0D0', '#F47964', '#ED6258', '#FCD7D0', '#873832', '#6F9A3A'}
COLOR_WORDS = {'red', 'green', 'crimson', 'lime', 'orange', 'purple', 'pink', 'teal', 'cyan', 'magenta', 'gold', 'navy'}
def palette_check(f):
    """WARN on colours that are not in the house palette, and on green/coral used outside price direction."""
    for it in f.get('items', []) if isinstance(f.get('items'), list) else []:
        if not isinstance(it, dict): continue
        blobs = [json.dumps(it)]
        for b in blobs:
            for h in re.findall(r'#[0-9A-Fa-f]{6}\b', b):
                if h.upper() not in PALETTE:
                    WARN.append(f'{f["id"]}: colour {h} is not in the Varsity Hindi palette (references/storyboard_rules.md §5). Use a kit item or a palette colour')
                elif h.upper() in SEMANTIC and it.get('t') not in ('diagram', 'kite', 'mini'):
                    WARN.append(f'{f["id"]}: green/coral ({h}) used in a {it.get("t")} item. In this IP green/red appear only on candle and bar bodies, never on boxes, pills, tags, rows or bars')
            for w in re.findall(r'(?:color|background|fill|stroke)\s*[:=]\s*["\']?([a-z]+)', b):
                if w in COLOR_WORDS: WARN.append(f'{f["id"]}: named colour "{w}" in {it.get("t")}; use palette hex values only')
        if it.get('t') in ('roto',) and any(c.get('color') in ('green', 'coral') for c in it.get('chips', [])):
            WARN.append(f'{f["id"]}: green/coral chip on roto text; chips are white boxes in this IP')
        if it.get('t') in ('panel', 'row'): palette_check({'id': f['id'], 'items': it.get('items', [])})

HINGLISH = set('hai hain ka ki ke mein mei aur nahi nhi kya toh yeh woh kaise kyun kyunki matlab mtlb jab bhi sabse wala wali lekin agar agr chahiye hota hoti jata jati karte karna kar sakte iska iski uska uski humein aap apne'.split())

def rich(s):
    """**bold** and newlines -> html"""
    s = E(str(s)); s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s); return s.replace('\n', '<br>')

def strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k in ('src', 'plate', 'type', 't', 'id', 'mode', 'section', 'name', 'kind', 'pos', 'style', 'at', 'align', 'color', 'x_axis', 'gen', 'html'): continue
            yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)

# ============================================================== items
def candles_of(i, fid):
    if 'candles' in i:
        cs = [dict(o=c[0], h=c[1], l=c[2], c=c[3]) if isinstance(c, list) else c for c in i['candles']]
    elif 'closes' in i:
        cs = [dict(o=v, h=v, l=v, c=v) for v in i['closes']]
    else:
        cs = chart.gen(i.get('gen', {}))
    WARN.extend(chart.check(cs, fid)); return cs

TOPS = ('shooting_star', 'hanging_man', 'evening_star', 'dark_cloud', 'bearish_engulfing')
BOTTOMS = ('hammer', 'inverted_hammer', 'morning_star', 'piercing', 'bullish_engulfing')
def check_context(i, cs_, fid):
    """Reversal patterns must sit at a real top (bearish) or bottom (bullish) of the generated path."""
    pats = {int(k): v for k, v in ((i.get('gen') or {}).get('patterns') or {}).items()}
    for k, v in pats.items():
        L = chart.MULTI_LEN.get(v, 1); span = range(k, min(len(cs_), k + L))
        nb = range(max(0, k - 5), min(len(cs_), k + L + 4))
        if v in TOPS and max(cs_[j]['h'] for j in span) < max(cs_[j]['h'] for j in nb) - 1e-9:
            WARN.append(f'{fid}: {v} at candle {k} is not at a local top; put it at the peak of gen.path')
        if v in BOTTOMS and min(cs_[j]['l'] for j in span) > min(cs_[j]['l'] for j in nb) + 1e-9:
            WARN.append(f'{fid}: {v} at candle {k} is not at a local bottom; put it at the trough of gen.path')
        boxes = i.get('boxes', [])
        if boxes and not any(b['from'] <= k <= b.get('to', b['from']) for b in boxes):
            WARN.append(f'{fid}: pattern {v} at candle {k} is not inside any dashed box')
        if L > 1 and any(b['from'] == k and b.get('to', k) < k + L - 1 for b in boxes):
            WARN.append(f'{fid}: {v} spans {L} candles; set the box "to": {k+L-1}')

def kite(i, fid, frame):
    x, y, w, h = i.get('x', 240), i.get('y', 150), i.get('w', 1440), i.get('h', 880)
    c = dict(i); c['candles'] = candles_of(i, fid); c['_chev'] = A('props/kite_chevron.png')
    if 'closes' in i: c['type'] = 'line'
    sc = i.get('side_card')
    if sc: w = w - 360
    svg, meta = chart.kite_svg(c, w, h - 62, WARN, fid)
    check_context(i, c['candles'], fid)
    for b in c.get('boxes', []):
        for k in (b['from'], b.get('to', b['from'])):
            if k >= len(c['candles']): WARN.append(f'{fid}: box index {k} beyond {len(c["candles"])} candles')
    lights = ''.join(f'<i style="left:{30+36*j}px;background:{col}"></i>' for j, col in enumerate(('#EF2A41', '#FEBE09', '#01D73D')))
    out = f'<div class="win" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;z-index:4"><div class="bar">{lights}</div><svg width="{w}" height="{h-62}">{svg}</svg></div>'
    if i.get('tab'):
        out += f'<div class="abs chk" style="left:{x}px;width:{w}px;top:{y-86}px;text-align:center;z-index:7"><span class="htab">{E(i["tab"])}</span></div>'
    if sc:
        k = c['candles'][sc['i']]; cx = x + w + 30
        bull = k['c'] >= k['o']; col = chart.GREEN if bull else chart.CORAL
        lo, hi = k['l'], k['h']; Y = lambda v: 140 + (hi - v) / ((hi - lo) or 1) * 260
        top, bot = Y(max(k['o'], k['c'])), Y(min(k['o'], k['c']))
        lab = (('Close', k['c']), ('Open', k['o'])) if bull else (('Open', k['o']), ('Close', k['c']))
        dec = i.get('decimals', 2)
        s = (f'<svg width="300" height="460"><line x1="150" y1="{Y(hi)}" x2="150" y2="{Y(lo)}" stroke="{col}" stroke-width="3"/>'
             f'<rect x="125" y="{top}" width="50" height="{max(6,bot-top)}" fill="{col}"/>'
             + chart.txt(190, Y(hi) + 8, 'High', 22, 400, '#222') + chart.txt(190, Y(lo) + 8, 'Low', 22, 400, '#222')
             + chart.txt(110, top + 8, lab[0][0], 22, 400, '#222', 'end') + chart.txt(110, bot + 8, lab[1][0], 22, 400, '#222', 'end') + '</svg>')
        vals = ''.join(f'<div style="display:flex;justify-content:space-between"><span>{n}:</span><span>{chart.fmt(v,dec)}</span></div>' for n, v in (('Open', k['o']), ('Close', k['c']), ('High', k['h']), ('Low', k['l'])))
        out += (f'<div class="abs chk" style="left:{cx}px;top:{y}px;width:330px;height:{h}px;background:#fff;border-radius:26px;box-shadow:0 18px 50px rgba(30,60,100,.22);z-index:4;color:#111">'
                f'<div style="height:62px;border-radius:26px 26px 0 0;background:linear-gradient(#E9F1F8,#DCE8F2)"></div>'
                f'<div style="text-align:center;font-weight:700;font-size:28px;margin-top:40px">{E(sc.get("title","Candle"))}</div>'
                f'<div style="margin:0 auto;width:300px">{s}</div><div style="font-size:24px;padding:0 50px;line-height:1.5">{vals}</div></div>')
        if not any(b['from'] <= sc['i'] <= b.get('to', b['from']) for b in c.get('boxes', [])):
            WARN.append(f'{fid}: side_card shows candle {sc["i"]} but no dashed box marks that candle on the chart')
    if i.get('dropdown'):
        d = i['dropdown']; sel = d.get('selected', '01 Day')
        groups = d.get('groups') or [('Seconds', ['05 Seconds', '10 Seconds', '15 Seconds', '30 Seconds', '45 Seconds']),
                                     ('Minutes', ['01 Minutes', '02 Minutes', '03 Minutes', '05 Minutes', '10 Minutes', '15 Minutes', '30 Minutes']),
                                     ('Hours', ['01 Hour', '02 Hours', '03 Hours', '04 Hours']), ('Days', ['01 Day', '01 Week', '01 Month', '01 Year'])]
        body = '<div style="font-weight:600;font-size:19px;padding:14px 18px;border-bottom:1px solid #ddd">+&nbsp; Add custom intervals</div>'
        for g, its in groups:
            body += f'<div style="padding:8px 18px 4px;font-weight:700;font-size:19px;display:flex;justify-content:space-between"><span>{g}</span><span>⌄</span></div>'
            for it in its:
                bg = 'background:#F7C430;' if it == sel else ''
                body += f'<div style="padding:2px 18px;font-size:16px;color:#333;{bg}">{it}</div>'
            body += '<div style="border-bottom:1px solid #ddd;margin:6px 0"></div>'
        out += f'<div class="abs" style="left:{x-d.get('overhang',150)}px;top:{y+150}px;width:300px;background:#fff;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.25);z-index:8;color:#111;padding-bottom:10px">{body}</div>'
    return out, True

def table_win(i, fid, frame):
    x, y, w = i.get('x', 200), i.get('y', 40), i.get('w', 1520)
    head = ''.join(f'<th>{rich(h)}</th>' for h in i['head']); hl = i.get('hl')
    rows = ''.join(f'<tr class="{"dim" if (hl is not None and i.get("dim_others") and n != hl) else ""}">' + ''.join(f'<td>{rich(c)}</td>' for c in r) + '</tr>' for n, r in enumerate(i['rows']))
    lights = ''.join(f'<i style="left:{30+36*j}px;background:{col}"></i>' for j, col in enumerate(('#EF2A41', '#FEBE09', '#01D73D')))
    out = f'<div class="win glassbar chk" style="left:{x}px;top:{y}px;width:{w}px;z-index:4"><div class="bar">{lights}</div><table class="tt">{"<thead><tr>"+head+"</tr></thead>"}<tbody>{rows}</tbody></table></div>'
    if i.get('tab'): out += f'<div class="abs" style="left:{x}px;width:{w}px;top:{y-86}px;text-align:center;z-index:7"><span class="htab">{E(i["tab"])}</span></div>'
    if hl is not None: out += f'<img id="mag-{fid}" class="abs" data-row="{hl}" src="{A("props/magnifier.png")}" style="width:300px;z-index:9;left:{x-60}px;top:0">'
    return out, True

def htab(i, fid, frame): return f'<div class="chk" style="text-align:center"><span class="htab {"sm" if i.get("small") else ""}">{E(i["text"])}</span></div>', False

def title_stack(i, fid, frame):
    al = i.get('align', 'left'); ks = i.get('key_size', 64); ls = i.get('lead_size', 44)
    s = f'<div class="chk" style="text-align:{al}">'
    if i.get('lead'): s += f'<div class="lead" style="font-size:{ls}px">{rich(i["lead"])}</div>'
    if i.get('lines'):
        for ln in i['lines']:
            col = {'white': '#fff', 'yellow': 'var(--yellow)'}.get(ln.get('color', 'yellow'), ln.get('color'))
            s += f'<div class="key" style="font-size:{ln.get("size", ks)}px;color:{col};margin-left:{ln.get("indent",0)}px">{rich(ln["text"])}</div>'
    else:
        s += f'<div class="key" style="font-size:{ks}px;color:{i.get("key_color","var(--yellow)")}">{rich(i["key"])}</div>'
    if i.get('tail'): s += f'<div class="lead" style="font-size:{ls}px">{rich(i["tail"])}</div>'
    return s + '</div>', False

def questions(i, fid, frame):
    a = i.get('active', 0); s = '<div class="qs chk" style="width:880px">'
    for n, q in enumerate(i['items']):
        cls = '' if n <= a else ('dim' if n == a + 1 else 'dimmer')
        s += f'<div class="q {cls}"><div class="lead" style="font-size:34px">{rich(q["lead"])}</div><div class="key" style="font-size:54px">{rich(q["key"])}</div></div>'
    return s + '</div>', False

def big(i, fid, frame):
    s = '<div class="chk" style="text-align:center">'
    if i.get('lead'): s += f'<div class="sub">{rich(i["lead"])}</div>'
    s += f'<div class="big-white" style="font-size:{i.get("size",72)}px">{rich(i["text"])}</div>'
    if i.get('sub'): s += f'<div class="sub" style="margin-top:12px">{rich(i["sub"])}</div>'
    return s + '</div>', False

def definition(i, fid, frame):
    st = i.get('style', 'plain')
    if st == 'capsule': return f'<div class="capsule chk" style="max-width:{i.get("w",960)}px">{rich(i["text"])}</div>', False
    col = '#111' if frame['mode'] in ('fss',) else '#fff'
    return f'<div class="deftext chk" style="max-width:{i.get("w",900)}px;color:{col};font-size:{i.get("size",38)}px">{rich(i["text"])}</div>', False

def bullets(i, fid, frame):
    a = i.get('active', 'all')
    lis = ''.join(f'<li class="{"dim" if (a != "all" and n > a) else ""}">{rich(t)}</li>' for n, t in enumerate(i['items']))
    t = f'<div class="title-y">{rich(i["title"])}</div>' if i.get('title') else ''
    return f'<div class="chk" style="width:{i.get("w",860)}px">{t}<ul class="blist">{lis}</ul></div>', False

def callout(i, fid, frame):
    return f'<div class="cpill chk"><b>{rich(i["claim"])}</b><div><small>{E(i.get("label",""))}</small><span>{E(i.get("value",""))}</span></div></div>', False

def panel(i, fid, frame):
    inner = ''.join(render_item(x, fid, frame)[0] for x in i['items'])
    d = i.get('direction', 'column')
    return f'<div class="gpanel chk" style="width:{i.get("w",880)}px;display:flex;flex-direction:{d};align-items:center;justify-content:center;gap:{i.get("gap",30)}px">{inner}</div>', False

def diagram(i, fid, frame):
    svg, xs = chart.diagram_svg(i, WARN, fid)
    pills = [k.get('pill') for k in i['candles']]
    out = f'<div style="position:relative">{svg}'
    if any(pills):
        out += f'<div style="display:flex;justify-content:space-around;width:{i.get("w",760)}px;margin-top:{i.get("pill_gap",10)}px">'
        for p in pills:
            if p: out += f'<span class="vpill {"bull" if p.lower().startswith("bull") else "bear"}">{E(p)}</span>'
        out += '</div>'
    return out + '</div>', False

def mini(i, fid, frame):
    c = dict(i); c['candles'] = candles_of(i, fid); c['bare'] = True; c['_chev'] = ''
    check_context(i, c['candles'], fid)
    w, h = i.get('w', 380), i.get('h', 300)
    svg, _ = chart.kite_svg(c, w, h, WARN, fid)
    cap = f'<div style="text-align:center;font-weight:600;font-size:32px;margin-top:6px">{E(i["caption"])}</div>' if i.get('caption') else ''
    return f'<div><svg width="{w}" height="{h}" overflow="visible">{svg}</svg>{cap}</div>', False

def cards(i, fid, frame):
    a = i.get('active'); pil = i.get('pillars')
    s = f'<div style="display:flex;gap:{i.get("gap",40)}px;align-items:flex-start">'
    for n, t in enumerate(i['items']):
        on = (a == 'all' or a == n)
        col = f'<div class="lcard {"on" if on and a is not None else ""} chk">{rich(t)}</div>'
        if pil: col = f'<div style="display:flex;flex-direction:column;align-items:center">{col}<img src="{A("props/pillar_3d.png")}" style="width:122px;margin-top:-4px"></div>'
        s += col
    return s + '</div>', False

def typo_card(i, fid, frame):
    rows = ''.join(f'<div style="text-align:center;margin:10px 0 22px"><div style="font-weight:700;font-size:32px">{rich(r["head"])}</div><div style="font-size:30px;margin-top:10px">{rich(r["text"])}</div></div>' for r in i['rows'])
    return f'<div class="gcard chk" style="width:{i.get("w",860)}px">{rows}</div>', False

def sentiment(i, fid, frame):
    pos = i.get('pos', .4)
    return (f'<div class="sent chk"><h4>{E(i.get("title","Market Sentiments"))}</h4><div class="track">'
            f'<svg style="position:absolute;left:{pos*100}%;top:-26px;margin-left:-28px" width="56" height="50"><path d="M28 2 L54 48 L2 48Z" fill="#fff" stroke="#333" stroke-width="2"/></svg></div>'
            f'<div class="lab"><span>{E(i.get("left","Fearful"))}</span><span>{E(i.get("right","Optimistic"))}</span></div></div>'), False

def roto(i, fid, frame):
    s = f'<div style="text-align:{i.get("align","center")};position:relative">'
    if i.get('lead'): s += f'<div style="font-weight:{i.get("lead_weight",400)};font-size:{i.get("lead_size",72)}px;color:#fff">{rich(i["lead"])}</div>'
    for wd in i['words']:
        s += f'<div class="roto" style="font-size:{wd.get("size",i.get("size",200))}px;color:{ {"white":"#fff","yellow":"var(--yellow)"}.get(wd.get("color","yellow"), wd.get("color"))};margin-left:{wd.get("indent",0)}px">{rich(wd["text"])}</div>'
    for ch in i.get('chips', []):
        s += f'<span class="chipw {ch.get("color","")}" style="left:{ch["x"]}px;top:{ch["y"]}px">{E(ch["text"])}</span>'
    return s + '</div>', False

def label(i, fid, frame):
    col = i.get('color') or ('#111' if frame['mode'] == 'fss' else '#fff')
    return f'<div class="chk" style="font-size:{i.get("size",34)}px;font-weight:{i.get("weight",500)};color:{col};text-align:{i.get("align","center")}">{rich(i["text"])}</div>', False

def asset(i, fid, frame):
    fl = 'transform:scaleX(-1);' if i.get('flip') else ''
    return f'<img src="{A(i["src"])}" style="width:{i.get("w",300)}px;{fl}opacity:{i.get("opacity",1)}">', False

def bubble(i, fid, frame):
    w = i.get('w', 470)
    return (f'<div style="position:relative;width:{w}px"><img src="{A("props/thought_bubble.png")}" style="width:{w}px">'
            f'<div class="bubble-t chk" style="left:8%;top:22%;width:72%">{rich(i["text"])}</div></div>'), False

def row(i, fid, frame):
    inner = ''.join(render_item(x, fid, frame)[0] for x in i['items'])
    return f'<div style="display:flex;align-items:{i.get("align","center")};gap:{i.get("gap",40)}px">{inner}</div>', False

def raw(i, fid, frame): return i['html'], False

R = dict(kite=kite, table=table_win, htab=htab, title=title_stack, questions=questions, big=big, definition=definition,
         bullets=bullets, callout=callout, panel=panel, diagram=diagram, mini=mini, cards=cards, typo_card=typo_card,
         sentiment=sentiment, roto=roto, label=label, text=label, asset=asset, bubble=bubble, row=row, html=raw)

def render_item(i, fid, frame):
    t = i.get('t')
    if t not in R: raise SystemExit(f'{fid}: unknown item type {t!r}. Types: {", ".join(R)}')
    return R[t](i, fid, frame)

# ============================================================== frames
PLATES = {'fss': 'fss_sky.jpg', 'side': 'sidecam.jpg', 'main': 'maincam.jpg', 'blur': 'maincam.jpg', 'takeaways': 'fss_sky.jpg'}
SWOOSH = ('<svg class="abs" style="left:0;top:0;z-index:1" width="1920" height="1080"><path d="M520 1080 C 560 760 320 520 640 300 C 820 170 980 60 1060 0 L1920 0 L1920 1080 Z" fill="#fff" opacity=".55"/>'
          '<path d="M520 1080 C 560 760 320 520 640 300 C 820 170 980 60 1060 0" fill="none" stroke="#fff" stroke-width="4"/></svg>')

def frame_html(f, look=None, edit=False, all_frames=None, **_kwargs):
    _set_asset_mode(studio=True)
    fid = f['id']; mode = f.get('mode', 'fss'); f['mode'] = mode
    plate = f.get('plate') or PLATES.get(mode)
    if plate and '.' not in plate: plate += '.jpg'
    light = mode in ('fss', 'takeaways', 'scene')
    body = [f'<img class="plate" src="{A("plates/" + plate)}" style="{"filter:blur(14px) brightness(.55);transform:scale(1.06)" if mode=="blur" else ""}">']
    if mode == 'main':
        body.append('<div class="abs" style="inset:0;z-index:1;background:linear-gradient(180deg,rgba(0,0,0,.05) 35%,rgba(0,0,0,.78) 100%)"></div>')
    if mode == 'takeaways':
        body.append(SWOOSH)
        body.append(f'<div class="tk-title chk">{rich(f.get("title","Key\nTakeaways"))}</div>')
        a = f.get('active', 'all')
        rows = ''.join(f'<div class="r {"dim" if (a != "all" and n != a) else ""}"><i>{n+1}.</i><div>{rich(t)}</div></div>' for n, t in enumerate(f['items']))
        body.append(f'<div class="tk-list chk" style="top:{f.get("top",200)}px">{rows}</div>')
        body.append(f'<img class="abs" src="{A("props/megaphone.png")}" style="left:20px;top:716px;width:360px;z-index:3">')
        if len(f['items']) > 6: WARN.append(f'{fid}: {len(f["items"])} takeaways; the template fits 6')
    flow = []
    for it in (f.get('extras', []) if mode == 'takeaways' else f.get('items', [])):
        h, own = render_item(it, fid, f)
        if own: body.append(h)
        elif 'x' in it and 'y' in it: body.append(f'<div class="abs" style="left:{it["x"]}px;top:{it["y"]}px;z-index:{it.get("z",6)}">{h}</div>')
        else: flow.append(h)
    if flow:
        z = f.get('zone') or {'side': [940, 40, 900, 1000], 'main': [120, 120, 1680, 900], 'fss': [160, 60, 1600, 960],
                              'blur': [160, 60, 1600, 960], 'scene': [160, 60, 1600, 960]}.get(mode, [160, 60, 1600, 960])
        just = f.get('justify', 'center')
        body.append(f'<div class="zone" id="zone" style="left:{z[0]}px;top:{z[1]}px;width:{z[2]}px;height:{z[3]}px;gap:{f.get("gap",36)}px;justify-content:{just};align-items:{f.get("align","center")}">{"".join(flow)}</div>')
    # chrome: Varsity eye top-left on every frame, sparkle right edge
    body.append(f'<img class="chrome" src="{A("props/varsity_eye.png")}" style="left:58px;top:61px;width:146px">')
    if f.get('sparkle', True):
        body.append(f'<img class="chrome" src="{A("props/sparkle.png")}" style="left:1801px;top:{f.get("sparkle_y", 180 if mode=="side" else 398)}px;width:58px;{"filter:invert(1)" if not light else ""}">')
    css = "../templates/vh.css"
    return (f'<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{css}"></head>'
            f'<body class="{"light" if light else ""}" data-mode="{mode}">{"".join(body)}</body></html>')

QA_JS = r"""(mode)=>{const w=[];
 const mag=document.querySelector('img[id^=mag-]');
 if(mag){const r=+mag.dataset.row;const tr=document.querySelectorAll('table.tt tbody tr')[r];
   if(tr){const b=tr.getBoundingClientRect();mag.style.top=(b.top+b.height/2-120)+'px';}}
 document.querySelectorAll('.chk').forEach(e=>{const b=e.getBoundingClientRect();
   if(e.scrollWidth>e.clientWidth+3) w.push('text clipped: '+e.innerText.slice(0,50));
   if(b.left<-2||b.top<-2||b.right>1922||b.bottom>1082) w.push('off-frame: '+e.innerText.slice(0,50));
   if(mode==='side'&&b.left<900&&b.width>0) w.push('covers the presenter (x<900): '+e.innerText.slice(0,50));});
 const z=document.getElementById('zone'); if(z&&z.scrollHeight>z.clientHeight+4) w.push('content taller than its zone; split the frame or shrink items');
 return w;}"""

CHECK_JS = "() => (" + QA_JS + ")(document.body.dataset.mode || 'fss')"

async def render(frames, out):
    _set_asset_mode(studio=False)
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        exe = os.environ.get('CHROMIUM_PATH')
        b = await (p.chromium.launch(executable_path=exe) if exe else p.chromium.launch())
        pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
        os.makedirs(os.path.join(out, '_html'), exist_ok=True)
        for f in frames:
            hp = os.path.join(out, '_html', f['id'] + '.html'); open(hp, 'w').write(frame_html(f))
            await pg.goto('file://' + os.path.abspath(hp)); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(150)
            for m in await pg.evaluate(QA_JS, f.get('mode', 'fss')): WARN.append(f'{f["id"]}: {m}')
            await pg.screenshot(path=os.path.join(out, f['id'] + '.png')); print('rendered', f['id'])
        await b.close()

def sheets(frames, out):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 640, 360
    try: font = ImageFont.truetype(os.path.join(KIT, 'fonts', 'Inter-Bold.ttf'), 22)
    except Exception: font = None
    ids = [f['id'] for f in frames]
    for s in range(0, len(ids), 6):
        sh = Image.new('RGB', (W * 2, H * 3), 'white'); d = ImageDraw.Draw(sh)
        for j, fid in enumerate(ids[s:s + 6]):
            im = Image.open(os.path.join(out, fid + '.png')).convert('RGB').resize((W, H)); x, y = (j % 2) * W, (j // 2) * H
            sh.paste(im, (x, y)); d.rectangle([x, y, x + 90, y + 30], fill='black'); d.text((x + 8, y + 3), fid, fill='white', font=font)
        sh.save(os.path.join(out, f'_sheet_{s // 6}.jpg'), quality=82)


# ============================================================== delivery package
def slug(t, n=40):
    t = re.sub(r'\*\*|\n', ' ', str(t)); t = re.sub(r'[^A-Za-z0-9]+', '-', t).strip('-')
    return t[:n].rstrip('-') or 'frame'

def frame_name(f):
    """<id>_<what-it-shows>: from 'name', else the header tab / title / first text of the frame."""
    if f.get('name'): return f"{f['id']}_{slug(f['name'])}"
    if f.get('mode') == 'takeaways': return f"{f['id']}_{slug(f.get('title', 'Key Takeaways'))}"
    def first(items):
        for it in items or []:
            if not isinstance(it, dict): continue
            for k in ('tab', 'text', 'key', 'title', 'ticker', 'caption'):
                if it.get(k) and it.get('t') not in ('asset', 'html'): return it[k]
            if it.get('lines'): return ' '.join(l['text'] for l in it['lines'])
            if it.get('words'): return ' '.join(w['text'] for w in it['words'])
            r = first(it.get('items'))
            if r: return r
    return f"{f['id']}_{slug(first(f.get('items')) or f.get('mode', 'frame'))}"

def package(frames, out, name):
    """Delivery zip: <name>/PNG/<NN_Section>/<id>_<slug>.png and <name>/HTML/<NN_Section>/<id>_<slug>.html
    (same names and grouping in both), HTML self-contained via HTML/_assets, plus spec.json, contact sheets, text proof."""
    import shutil, zipfile
    root = os.path.join(out, name); shutil.rmtree(root, ignore_errors=True)
    secs = []
    for f in frames:
        s_ = f.get('section') or 'Graphics'
        if s_ not in secs: secs.append(s_)
    used = set(); kitpref = 'file://' + KIT + '/'
    for f in frames:
        sec = f'{secs.index(f.get("section") or "Graphics") + 1:02d}_{slug(f.get("section") or "Graphics", 30)}'
        nm = frame_name(f)
        for kind in ('PNG', 'HTML'): os.makedirs(os.path.join(root, kind, sec), exist_ok=True)
        shutil.copy(os.path.join(out, f['id'] + '.png'), os.path.join(root, 'PNG', sec, nm + '.png'))
        h = open(os.path.join(out, '_html', f['id'] + '.html')).read()
        used.update(re.findall(re.escape(kitpref) + r'([^"\')\s]+)', h))
        open(os.path.join(root, 'HTML', sec, nm + '.html'), 'w').write(h.replace(kitpref, '../_assets/'))
    used.update('fonts/' + x for x in os.listdir(os.path.join(KIT, 'fonts')))
    for rel in used:
        dst = os.path.join(root, 'HTML', '_assets', rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(KIT, rel), dst)
    extra = os.path.join(root, '_review'); os.makedirs(extra, exist_ok=True)
    for x in os.listdir(out):
        if x.startswith('_sheet_') or x == '_text.txt': shutil.copy(os.path.join(out, x), extra)
    if os.path.exists(SPEC_PATH): shutil.copy(SPEC_PATH, os.path.join(root, 'spec.json'))
    with open(os.path.join(root, 'README.txt'), 'w') as r:
        r.write(f'{name}\n\nPNG/   1920x1080 PNGs for the edit, grouped by section, named <timestamp>_<what it shows>.\n'
                'HTML/  the same frames as editable HTML, same names and folders. Open in Chrome; text can be edited and re-exported.\n'
                '       HTML/_assets holds the fonts, CSS and images the pages use (keep it next to the section folders).\n'
                '_review/  contact sheets and every on-screen string (for proofreading).\nspec.json  source; rebuild with the varsity-hindi-graphics skill.\n')
    z = os.path.join(out, name + '.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for d, _, fs in os.walk(root):
            for x in fs:
                fp = os.path.join(d, x); zf.write(fp, os.path.relpath(fp, out))
    print('package:', z)
    return z

SPEC_PATH = ''
def main():
    global SPEC_PATH
    a = sys.argv[1:]; out = 'out'; only = None; sheet = '--no-sheet' not in a
    if '--out' in a: out = a[a.index('--out') + 1]
    if '--only' in a: only = set(a[a.index('--only') + 1].split(','))
    SPEC_PATH = a[0]; spec = json.load(open(a[0])); frames = spec['frames']
    ids = [f['id'] for f in frames]
    if len(ids) != len(set(ids)): WARN.append('duplicate frame ids: ' + ', '.join(sorted({i for i in ids if ids.count(i) > 1})))
    todo = [f for f in frames if not only or f['id'] in only]
    for f in frames: palette_check(f)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, '_text.txt'), 'w') as tf:
        for f in frames:
            ss = list(strings({k: v for k, v in f.items() if k not in ('id', 'mode', 'plate')}))
            tf.write(f'[{f["id"]}] ' + ' | '.join(s.replace('\n', ' ') for s in ss) + '\n')
            for s in ss:
                bad = [w for w in re.findall(r"[A-Za-z]+", s) if w.lower() in HINGLISH]
                if bad: WARN.append(f'{f["id"]}: Hindi/Hinglish word on screen ({", ".join(bad)}): "{s[:60]}". All on-screen text must be English')
    asyncio.run(render(todo, out))
    if sheet: sheets(frames if not only else todo, out)
    if '--package' in a:
        if only: WARN.append('--package needs a full build (without --only) so every frame is included')
        else: package(frames, out, a[a.index('--package') + 1] if a.index('--package') + 1 < len(a) else 'graphics')
    for w in WARN: print('WARN', w)
    print(f'done: {len(todo)} frames -> {out}/  ({len(WARN)} warnings)')

if __name__ == '__main__': main()

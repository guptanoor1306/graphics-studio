#!/usr/bin/env python3
"""Build every frame of a video from ONE compact JSON spec, render PNGs, run layout checks,
and write a single contact sheet for visual QA.

Usage:  python3 scripts/build.py spec.json [--out out] [--only 0.47,1.19-Table1] [--no-sheet]

Spec format: see references/spec_format.md (and scenes/example_spec.json).
Writes: scenes/<id>.html, <out>/<id>.png, <out>/<id>_overlay.png (anchor frames only),
        <out>/_sheet.jpg (all frames, small), and prints WARN lines from automatic checks.
"""
import json, os, sys, html, asyncio
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = html.escape

# ----------------------------------------------------------------- item renderers
def title(i):
    col = i.get('color', 'white'); size = i.get('size', 'md' if len(i.get('key', '')) > 9 else '')
    key_cls = 't-key ' + ('' if col == 'white' else col) + ' ' + size
    lead = f'<div class="t-line {"b" if i.get("bold_lead") else ""}">{E(i["lead"])}</div>' if i.get('lead') else ''
    tail = f'<div class="t-line {"b" if i.get("bold_lead") else ""}">{E(i["tail"])}</div>' if i.get('tail') else ''
    return f'<div>{lead}<div class="{key_cls}">{E(i["key"])}</div>{tail}</div>'

def pill(i):   return f'<div><span class="pill-title">{E(i["text"])}</span></div>'
def htab(i):   return f'<div style="text-align:center"><span class="htab {i.get("color","")} {"sm" if i.get("small") else ""}">{E(i["text"])}</span></div>'
def num(i):    return f'<div class="num"><i>{E(str(i["n"]))}</i>{E(i["text"])}</div>'
def label(i):  return f'<div style="font-weight:{i.get("weight",700)};font-size:{i.get("size",34)}px;text-align:{i.get("align","left")}">{E(i["text"])}</div>'
def text(i):   return f'<div style="font-size:{i.get("size",34)}px;line-height:1.3;font-weight:{i.get("weight",400)}">{E(i["text"])}</div>'
def definition(i): return f'<div class="def"><div class="tag">{E(i["title"])}</div><div class="body">{E(i["text"])}</div></div>'
def defcard(i):
    lines = ''.join(f'<div class="t-key {"amber" if n == i.get("accent",1) else ""}">{E(w)}</div>' for n, w in enumerate(i['lines']))
    return f'<div class="defcard">{lines}<p>{E(i["text"])}</p></div>'

def _row(cells, tag='td'):
    return '<tr>' + ''.join(f'<{tag}>{E(str(c))}</{tag}>' for c in cells) + '</tr>'

def glass_table(i):
    head = f'<thead><tr>{"".join(f"<th>{E(h)}</th>" for h in i["head"])}</tr></thead>' if i.get('head') else ''
    rows = ''
    for n, r in enumerate(i['rows']):
        cls = 'result' if (i.get('result', True) and n == len(i['rows']) - 1) else ''
        rows += f'<tr class="{cls}">' + ''.join(f'<td>{E(str(c))}</td>' for c in r) + '</tr>'
    w = i.get('w', 680); fs = i.get('size', 24)
    return f'<div class="glass {"dark" if i.get("dark") else ""}" style="width:{w}px"><table class="gt" style="font-size:{fs}px">{head}{rows}</table></div>'

def calc_table(i):
    widths = i.get('widths') or []
    th = ''.join(f'<th style="{f"width:{widths[n]}" if n < len(widths) else ""}">{E(h)}</th>' for n, h in enumerate(i['head']))
    less, hl = set(i.get('less', [])), set(i.get('hl', []))
    rows = ''
    for n, r in enumerate(i['rows']):
        cls = ' '.join(c for c, on in [('less', n in less), ('hl', n in hl),
                                       ('total', i.get('total', True) and n == len(i['rows']) - 1)] if on)
        cells = ''
        for c in r:
            c = str(c)
            cells += '<td>' + ('<ul>' + ''.join(f'<li>{E(x.strip())}</li>' for x in c.split('•') if x.strip()) + '</ul>' if '•' in c else E(c)) + '</td>'
        rows += f'<tr class="{cls}">{cells}</tr>'
    w = i.get('w', 1000); fs = i.get('size', 24 if len(i['rows']) > 5 else 30)
    return f'<div class="card" style="width:{w}px"><table class="ct {i.get("color","")}" style="font-size:{fs}px"><tr>{th}</tr>{rows}</table></div>'

def popup(i):
    ul = '<ul>' + ''.join(f'<li>{E(b)}</li>' for b in i.get('bullets', [])) + '</ul>' if i.get('bullets') else ''
    return f'<div style="padding-bottom:40px"><div class="popup"><div class="bar">{E(i["title"])}</div><div class="v">{E(i["value"])}</div>{ul}<div class="popup-base"></div></div></div>'

def callout(i): return f'<div><span class="callout {"white" if i.get("white") else ""}">{E(i["text"])}</span></div>'
def hpill(i):   return f'<div><span class="hpill"><span>{E(i["label"])}</span><b>{E(i["value"])}</b></span></div>'
def result_pill(i): return f'<div style="text-align:center"><span class="result-pill">{E(i["text"])}</span></div>'
def nlist(i):
    a = i.get('active', 0)
    lis = ''.join(f'<li class="{"" if n == a or a == "all" else "off"}"><b>{n+1}.</b>{E(t)}</li>' for n, t in enumerate(i['items']))
    return f'<ol class="nlist" style="width:{i.get("w",1020)}px">{lis}</ol>'
def folder(i):
    a = i.get('active', 0)
    lis = ''.join(f'<li class="{"" if n == a else "off"}">{n+1}. {E(t)}</li>' for n, t in enumerate(i['items']))
    return f'<div class="folder"><ol class="paper">{lis}</ol><div class="front"></div></div>'
def cards(i):
    a = i.get('active')
    out = ''
    for n, c in enumerate(i['items']):
        st = '' if a is None else ('on' if n == a else 'off')
        img = f'<img src="../assets/{c["img"]}">' if c.get('img') else (c.get('svg') or '')
        out += f'<div class="icard {st}">{img}<b>{E(c["label"])}</b><span>{E(c.get("sub",""))}</span></div>'
    return f'<div style="display:flex;gap:28px;justify-content:center">{out}</div>'
def bars(i):
    # bar chart in house style: boxed y-axis with labels, baseline, blue bars (amber = highlight), dashed target (review rule 7)
    W, H = i.get('w', 1200), i.get('h', 600); vals = i['values']; mx = i.get('max', max(vals + [i.get('target', 0)]) * 1.2)
    n = len(vals); AX = 130; L = AX + 40; base = H - 70; top = 40
    bw = min(170, (W - L - 30) / n * 0.55); gap = (W - L - 30) / n
    fmt = i.get('unit_fmt', '{}')
    svg = [f'<svg width="{W}" height="{H}">',
           f'<rect x="4" y="{top-20}" width="{AX-14}" height="{base-top+40}" fill="#fff" stroke="#1d1d1d" stroke-width="3"/>']
    for k in range(6):
        y = base - (base - top) * k / 5; v = mx * k / 5
        lab = fmt.format(int(v) if v >= 10 or float(v).is_integer() else round(v, 1))
        svg.append(f'<text x="{AX-26}" y="{y+8}" text-anchor="end" font-size="24" font-weight="800">{E(lab)}</text>')
    svg.append(f'<line x1="{L-10}" y1="{base}" x2="{W-10}" y2="{base}" stroke="#111" stroke-width="3"/>')
    for k, v in enumerate(vals):
        x = L + gap * k + (gap - bw) / 2; h = (base - top) * v / mx
        col = '#F2B233' if k in i.get('highlight', []) else '#248EF7'
        svg.append(f'<rect x="{x}" y="{base-h}" width="{bw}" height="{h}" fill="{col}" stroke="#1d1d1d" stroke-width="2"/>')
        ty = base - h - 14
        if i.get('target') and abs((base - (base - top) * i['target'] / mx) - ty) < 40: ty = base - h + 40   # keep clear of the target line: label inside the bar
        svg.append(f'<text x="{x+bw/2}" y="{ty}" text-anchor="middle" font-size="28" font-weight="700">{E(str(i.get("value_labels", vals)[k]))}</text>')
        svg.append(f'<text x="{x+bw/2}" y="{base+40}" text-anchor="middle" font-size="27" font-weight="700">{E(i["labels"][k])}</text>')
    if i.get('target'):
        y = base - (base - top) * i['target'] / mx
        svg.append(f'<line x1="{L-10}" y1="{y}" x2="{W-10}" y2="{y}" stroke="#111" stroke-width="2.5" stroke-dasharray="10 7"/>')
        svg.append(f'<text x="{L+4}" y="{y-12}" text-anchor="start" font-size="26" font-weight="700">{E(i.get("target_label",""))}</text>')
    svg.append('</svg>')
    return f'<div class="chartcard" style="padding:30px 40px 20px 30px">{"".join(svg)}</div>'
def points(i):
    # body points under a heading: plain text, small numbered discs, no box (review rule 2/3)
    lis = ''.join(f'<div class="pt"><i>{n+1}</i><span>{E(t)}</span></div>' for n, t in enumerate(i['items']))
    return f'<div class="points" style="width:{i.get("w",740)}px">{lis}</div>'
def raw(i): return f'<div>{i["html"]}</div>'

R = dict(title=title, pill=pill, htab=htab, num=num, label=label, text=text, definition=definition, defcard=defcard,
         glass_table=glass_table, calc_table=calc_table, popup=popup, callout=callout, hpill=hpill,
         result_pill=result_pill, nlist=nlist, folder=folder, cards=cards, bars=bars, points=points, html=raw)

FLOOR = {'anchor': 1035, 'fss': 1040}           # review rule 4: visible bottoms sit on this line
ROLE_H = [(('building', 'bank', 'tower'), 560), (('house',), 360), (('character', 'person', 'friend'), 315),
          (('coin',), 100), (('calculator',), 150), (('jar',), 230), (('cash_stack',), 300)]   # rule 5: buildings >> characters
_bbox_cache = {}
def visible_box(src):
    if src not in _bbox_cache:
        from PIL import Image as _I
        im = _I.open(os.path.join(KIT, 'assets', src)).convert('RGBA')
        _bbox_cache[src] = (im.size, im.getchannel('A').getbbox() or (0, 0) + im.size)
    return _bbox_cache[src]
def floor_asset(src, mode, x, h=None, w=None, z=None, floor=None):
    """Return V.asset() options that stand the asset's VISIBLE bottom on the floor line, sized by visible height."""
    (iw, ih), (bx0, by0, bx1, by1) = visible_box(src)
    if h is None and w is None:
        h = next((hh for keys, hh in ROLE_H if any(k in src.lower() for k in keys)), 300)
    scale = (h / (by1 - by0)) if h else (w / iw)
    y = (floor or FLOOR[mode]) - by1 * scale
    o = {'x': x, 'y': round(y), 'w': round(iw * scale)}
    if z is not None: o['z'] = z
    return o

PLATES = {'right': 'anchor_right_setA_clean', 'left': 'anchor_left_setB'}
PROPS = {'coins': [('setA/coins_stack.png', 100)], 'tax': [('setC/calculator.png', 130), ('setA/coins_stack.png', 90)],
         'jar': [('setB/jar_cash_coins.png', 200)], 'house': [('setC/house_home_loan_small.png', 230)],
         'bank': [('setC/bank_building_classic.png', 240)], 'broker': [('setA/building_company_3d.png', 200)],
         'document': [('setA/document_clipped_note_rule.png', 160)],
         'chart': [('setA/icon_browser_donut.png', 180)], 'magnifier': [('setA/magnifying_glass.png', 140)],
         'none': []}   # (asset, visible height) for corner props

def topic_prop_assets(look):
    """One topic prop per video (skill rule): first entry in look.props / look.prop only."""
    props = look.get('props')
    if props is None:
        p = look.get('prop', 'coins')
        props = [] if p in (None, '', 'none') else [p]
    else:
        props = [p for p in props if p not in (None, '', 'none')][:1]
    out, seen = [], set()
    for p in props:
        if p in (None, '', 'none'):
            continue
        for src, h in PROPS.get(p, []):
            if src not in seen:
                seen.add(src)
                out.append((src, h))
    return out

def frame_html(f, look, edit=False):
    mode = f.get('mode', 'anchor'); side = f.get('anchor', look.get('anchor', 'right'))
    fss = mode == 'fss'; warm = look.get('fss', 'blue') == 'warm'
    plate = f.get('plate') or (('fss_sky_warm' if warm else 'fss_sky_blue') if fss else look.get('plate') or PLATES[side])
    body_cls = ('fss ' + ('warm' if warm else '')) if fss else ''
    if edit:
        body_cls = (body_cls + ' studio-edit-mode').strip()
    flow, absol, js = [], [], []
    has_head = False
    for idx, it in enumerate(f['items']):
        t = it['t']
        layer = f' data-spec-idx="{idx}" class="studio-editable"' if edit else ''
        if t == 'htab' and not fss and 'x' not in it and 'y' not in it:
            hx = 140 if side == 'right' else 1040
            absol.append(f'<div class="abs z"{layer} style="left:{hx}px;top:26px">{R[t](it)}</div>'); has_head = True
            continue
        if t in ('person', 'asset'):
            if t == 'person':
                h = it.get('h', 315)
                x = it.get('x', 110 if (fss or side == 'right') else 1500); y = it.get('y', FLOOR['fss' if fss else 'anchor'] - round(h * 0.985))
                o = {k: v for k, v in it.items() if k != 't'}; o.update(x=x, y=y, h=h)
                if not fss: o.setdefault('nameClass', 'name dark')     # rule 6: big dark name pill over the anchor
                if edit: o['specIdx'] = idx
                js.append(f'V.person({json.dumps(o)});')
            else:
                if 'y' in it:      # pinned by hand
                    o = {k: v for k, v in it.items() if k not in ('t', 'src')}
                else:              # stand it on the floor, sized by role
                    o = floor_asset(it['src'], 'fss' if fss else 'anchor', it.get('x', 140), it.get('h'), it.get('w'), it.get('z'))
                if edit: o['specIdx'] = idx
                js.append(f'V.asset("../assets/{it["src"]}",{json.dumps(o)});')
            continue
        h = R[t](it)
        if 'x' in it or 'y' in it:
            absol.append(f'<div class="abs z"{layer} style="left:{it.get("x",0)}px;top:{it.get("y",0)}px">{h}</div>')
        else:
            flow.append(f'<div{layer}>{h}</div>' if edit else h)
    # flow container = the safe content zone
    if fss:
        zone = 'left:{}px;top:40px;width:{}px;align-items:center'.format(*( (480, 1340) if f.get('person_left') else (160, 1600)))
    else:
        top = f.get('top', 200 if has_head else 110)
        zone = 'left:{}px;top:{}px;width:{}px;align-items:flex-start'.format(140 if side == 'right' else 1020, top, f.get('zone_w', 760))
    gap = f.get('gap', 30)
    flow_html = f'<div class="abs z flow" style="{zone};display:flex;flex-direction:column;gap:{gap}px">{"".join(flow)}</div>'
    # dressing + topic prop
    js.insert(0, f"V.decor({{theme:'{'warm' if warm else 'blue'}'}});" if fss else f"V.anchorDecor({{side:'{side}'}});")
    types = {it['t'] for it in f['items']}
    title_only = types <= {'title'} or (types <= {'title', 'pill', 'hpill'})
    # topic prop only on frames without their own illustrations (review rule 9: declutter)
    if not title_only and f.get('prop', not any(it['t'] in ('asset', 'person') for it in f['items'])):
        xcur = 1880 if fss else (880 if side == 'right' else 1050)
        for k, (src, h) in enumerate(topic_prop_assets(look)):
            o = floor_asset(src, 'fss' if fss else 'anchor', 0, h=h, z=6)
            if fss or side == 'right': xcur -= o['w']; o['x'] = xcur; xcur -= 12
            else: o['x'] = xcur; xcur += o['w'] + 12
            js.append(f'V.asset("../assets/{src}",{json.dumps(o)});')
    return f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../templates/varsity.css">
<script src="../templates/components.js"></script></head><body class="{body_cls}" data-mode="{mode}" data-side="{side}">
<img class="plate" src="../assets/plates/{plate}.png">
{flow_html}
{"".join(absol)}
<script>{"".join(js)}</script></body></html>'''

CHECK_JS = r'''() => {
 const TOK=[[36,142,247],[100,176,252],[242,178,51],[165,204,101],[242,107,91],[63,163,77],[224,70,58],[255,244,214],[253,225,221],[227,244,214],[217,233,255],[255,246,221]];
 const W=[], mode=document.body.dataset.mode, side=document.body.dataset.side;
 const els=[...document.querySelectorAll('.z, .z *')].filter(e=>e.children.length===0 || e.matches('.card,.glass,.popup,.nlist,.icard,.def,.htab,.pill-title'));
 for(const e of els){ const r=e.getBoundingClientRect(); if(!r.width||!r.height) continue;
   const t=(e.innerText||e.className||'').toString().slice(0,40).replace(/\n/g,' ');
   if(r.left<0||r.top<0||r.right>1920||r.bottom>1080) W.push(`off-frame: "${t}" (${r.left|0},${r.top|0},${r.right|0},${r.bottom|0})`);
   if(mode!=='fss'){ const lim = r.top>330 ? 900 : 1120;
     if(side==='right' && r.right>lim) W.push(`covers anchor: "${t}" right edge ${r.right|0} > ${lim}`);
     if(side==='left' && r.left<1920-lim) W.push(`covers anchor: "${t}" left edge ${r.left|0} < ${1920-lim}`);}
   if(e.scrollWidth>e.clientWidth+2 && getComputedStyle(e).overflow!=='visible') W.push(`text clipped: "${t}"`);
   const cs=getComputedStyle(e);
   for(const c of [cs.color, cs.backgroundColor]){ const m=c.match(/rgba?\(([\d.]+), ([\d.]+), ([\d.]+)(?:, ([\d.]+))?/); if(!m) continue;
     const [r,g,b,a]=[+m[1],+m[2],+m[3],m[4]===undefined?1:+m[4]]; if(a<0.9) continue;
     if(Math.max(r,g,b)-Math.min(r,g,b)<24) continue;      // greys, white, ink, black are fine
     const ok=TOK.some(([R,G,B])=>Math.abs(R-r)+Math.abs(G-g)+Math.abs(B-b)<40);
     if(!ok) W.push(`off-palette colour rgb(${r},${g},${b}) on "${t}"`); }
 }
 return [...new Set(W)].slice(0,12);
}'''

async def render(ids, out):
    from playwright.async_api import async_playwright
    exe = os.environ.get('CHROMIUM_PATH') or next((c for c in ['/opt/pw-browsers/chromium', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome'] if os.path.isfile(c)), None)
    async with async_playwright() as p:
        try: b = await p.chromium.launch()
        except Exception:
            if not exe: raise
            b = await p.chromium.launch(executable_path=exe)
        pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
        for fid in ids:
            await pg.goto('file://' + os.path.join(KIT, 'scenes', fid + '.html')); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(150)
            await pg.screenshot(path=f'{out}/{fid}.png')
            for w in await pg.evaluate(CHECK_JS): print(f'WARN {fid}: {w}')
            if not await pg.evaluate("document.body.classList.contains('fss')"):
                await pg.evaluate("document.body.classList.add('overlay');document.querySelectorAll('.plate').forEach(e=>e.style.display='none')")
                await pg.screenshot(path=f'{out}/{fid}_overlay.png', omit_background=True)
        await b.close()

def sheet(ids, out):
    # QA sheets: 6 frames per sheet, 2 columns at 960px, so table text stays legible
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
    a = sys.argv[1:]; spec = json.load(open(a[0]))
    out = a[a.index('--out') + 1] if '--out' in a else 'out'; os.makedirs(out, exist_ok=True)
    only = set(a[a.index('--only') + 1].split(',')) if '--only' in a else None
    look = spec.get('look', {}); ids = []
    # review rules 1 & 3: one heading system per video; no glass text boxes over the anchor
    head_types = {it['t'] for f in spec['frames'] for it in f['items'] if it['t'] in ('htab', 'pill', 'definition', 'defcard')}
    if len(head_types) > 1: print(f'WARN spec: mixed heading systems {sorted(head_types)}; use htab everywhere (title stack only for the opening title)')
    for f in spec['frames']:
        if f.get('mode', 'anchor') != 'fss':
            for it in f['items']:
                if it['t'] in ('pill', 'defcard', 'definition'): print(f"WARN {f['id']}: '{it['t']}' over the anchor; use htab + points/text instead")
        n_assets = sum(it['t'] in ('asset', 'person') for it in f['items'])
        if n_assets > 3: print(f"WARN {f['id']}: {n_assets} illustrations; declutter to the 1-3 that carry the idea")
    for f in spec['frames']:
        if only and f['id'] not in only: continue
        open(os.path.join(KIT, 'scenes', f['id'] + '.html'), 'w').write(frame_html(f, look)); ids.append(f['id'])
    asyncio.run(render(ids, out))
    print(f'rendered {len(ids)} frames -> {out}/')
    if '--no-sheet' not in a: sheet([f['id'] for f in spec['frames'] if os.path.exists(f"{out}/{f['id']}.png")], out)

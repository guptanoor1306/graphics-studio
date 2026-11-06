"""Flat SVG props in the Varsity Hindi line style: 4px black outline, white / amber / blue / grey fills.
prop(name, **opts) -> (svg_html, w, h). Every prop stands on its bottom edge (snap it to the floor).
Fill colours stay in the house palette; green/red are never used here (they belong to candles only).
"""
import html
INK, W_, AMB, YEL, BLU, GRY, LG = '#141414', '#FFFFFF', '#F0B32A', '#FFBE30', '#278BED', '#6E6E6E', '#D8D8D8'
E = html.escape
def T(x, y, s, size=28, wt=700, col=INK, anchor='middle'):
    return f'<text x="{x}" y="{y}" font-family="Inter" font-size="{size}" font-weight="{wt}" fill="{col}" stroke="none" text-anchor="{anchor}">{E(str(s))}</text>'
def S(w, h, inner, out_w=None):
    ow = out_w or w; oh = round(h * ow / w)
    return f'<svg width="{ow}" height="{oh}" viewBox="0 0 {w} {h}" overflow="visible">{inner}</svg>', ow, oh
st = f'stroke="{INK}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"'

def price_tag_svg(x, y, text, w=None):
    w = w or max(130, 22 * len(text) + 40)
    return (f'<g><path d="M{x} {y} L{x+w} {y} L{x+w} {y+64} L{x} {y+64} L{x-26} {y+32} Z" fill="{YEL}" {st}/>'
            f'<circle cx="{x-6}" cy="{y+32}" r="7" fill="#fff" {st}/>' + T(x + w / 2, y + 43, text, 30) + '</g>')

def wheat_field(w=None, label=None):
    g = []
    import random; rnd = random.Random(7)
    for k in range(34):
        x = 20 + k * 26 + rnd.randint(-6, 6); top = 40 + rnd.randint(0, 50)
        g.append(f'<path d="M{x} 260 C{x+4} 200 {x-4} 140 {x+2} {top+60}" fill="none" stroke="{INK}" stroke-width="3"/>')
        for j in range(5):
            yy = top + j * 13
            g.append(f'<ellipse cx="{x-7}" cy="{yy+8}" rx="6" ry="10" transform="rotate(-25 {x-7} {yy+8})" fill="{AMB}" stroke="{INK}" stroke-width="2"/>'
                     f'<ellipse cx="{x+9}" cy="{yy+8}" rx="6" ry="10" transform="rotate(25 {x+9} {yy+8})" fill="{AMB}" stroke="{INK}" stroke-width="2"/>')
        g.append(f'<path d="M{x+1} {top+2} L{x+1} {top-18}" stroke="{INK}" stroke-width="2"/>')
    g.append(f'<rect x="0" y="246" width="920" height="16" rx="8" fill="#EFB32E" {st}/>')
    if label: g.append(T(460, 236, label, 34))
    return S(920, 264, ''.join(g), w)

def wheat_sack(w=None, label='WHEAT', price=None):
    g = [f'<path d="M50 70 C30 140 26 240 44 290 L196 290 C214 240 210 140 190 70 Z" fill="#fff" {st}/>',
         f'<path d="M50 70 C70 40 90 52 98 30 C110 46 130 46 142 30 C150 52 170 40 190 70 C160 84 80 84 50 70 Z" fill="#fff" {st}/>',
         f'<path d="M62 80 C100 96 140 96 178 80" fill="none" stroke="{INK}" stroke-width="5"/>',
         f'<rect x="64" y="150" width="112" height="70" rx="10" fill="{AMB}" {st}/>', T(120, 196, label, 26)]
    for k in range(4):
        x = 92 + k * 18
        g.append(f'<ellipse cx="{x}" cy="40" rx="6" ry="12" fill="{AMB}" stroke="{INK}" stroke-width="2"/>')
    if price: g.append(price_tag_svg(176, 110, price))
    return S(380 if price else 240, 296, ''.join(g), w)

def flour_mill(w=None, label='Flour Mill'):
    g = [f'<rect x="40" y="150" width="420" height="270" fill="#fff" {st}/>',
         f'<path d="M20 160 L250 40 L480 160 Z" fill="{BLU}" {st}/>',
         f'<rect x="360" y="40" width="44" height="80" fill="{LG}" {st}/>',
         f'<rect x="100" y="182" width="300" height="70" rx="10" fill="{AMB}" {st}/>', T(250, 230, label, 36),
         f'<rect x="200" y="290" width="100" height="130" fill="{LG}" {st}/>',
         f'<rect x="70" y="290" width="90" height="74" fill="#fff" {st}/><path d="M115 290 L115 364 M70 327 L160 327" stroke="{INK}" stroke-width="3"/>',
         f'<circle cx="390" cy="340" r="44" fill="{LG}" {st}/><circle cx="390" cy="340" r="12" fill="#fff" {st}/>',
         f'<path d="M390 296 L390 384 M346 340 L434 340" stroke="{INK}" stroke-width="2" opacity=".5"/>']
    return S(500, 424, ''.join(g), w)

def market_stall(w=None, label=None, price=None, goods='wheat'):
    g = [f'<path d="M30 120 L40 400 M450 120 L440 400" stroke="{INK}" stroke-width="6"/>']
    for k in range(6):
        x = 20 + k * 77
        g.append(f'<path d="M{x} 60 L{x+77} 60 L{x+77} 130 C{x+58} 150 {x+19} 150 {x} 130 Z" fill="{BLU if k % 2 == 0 else "#fff"}" {st}/>')
    g.append(f'<path d="M10 60 L40 10 L440 10 L482 60 Z" fill="#fff" {st}/>')
    if label: g.append(T(246, 48, label, 30))
    g.append(f'<rect x="40" y="290" width="400" height="110" fill="#fff" {st}/><path d="M40 320 L440 320" stroke="{INK}" stroke-width="3"/>')
    for k in range(3):
        x = 90 + k * 130
        g.append(f'<path d="M{x-46} 290 C{x-40} 236 {x+40} 236 {x+46} 290 Z" fill="{AMB if goods=="wheat" else LG}" {st}/>')
    if price: g.append(price_tag_svg(170, 168, price))
    return S(492, 404, ''.join(g), w)

def scale(w=None, left='', right='', tilt=0, left_caption=None, right_caption=None):
    """Balance. Each price box hangs level under its pan; its caption sits right above the box."""
    def box(cx, val, fill, cap):
        c = T(cx, 320, cap, 28, 700) if cap else ''
        return (f'<g transform="rotate({tilt} {cx} 250)">{c}<rect x="{cx-90}" y="168" width="180" height="66" rx="14" fill="{fill}" stroke="{INK}" stroke-width="3"/>'
                f'{T(cx,213,val,32)}</g>')
    g = (f'<g {st} fill="none"><path d="M380 120 L380 392"/><path d="M290 396 L470 396"/>'
         f'<g transform="rotate({-tilt} 380 120)"><path d="M90 120 L670 120"/><path d="M90 120 L40 250 M90 120 L140 250 M670 120 L620 250 M670 120 L720 250"/>'
         f'<path d="M26 250 Q90 304 154 250 Z" fill="#fff"/><path d="M606 250 Q670 304 734 250 Z" fill="#fff"/>'
         f'{box(90, left, "#fff", left_caption)}{box(670, right, YEL, right_caption)}</g>'
         f'<circle cx="380" cy="120" r="13" fill="{INK}"/></g>')
    return S(760, 400, g, w)

def lock(w=None, label=None, open_=False):
    sh = 'M40 92 V56 a40 40 0 0 1 80 0 V' + ('40' if open_ else '92')
    g = f'<path d="{sh}" fill="none" stroke="{INK}" stroke-width="12" stroke-linecap="round"/><rect x="14" y="88" width="132" height="104" rx="18" fill="{YEL}" {st}/><circle cx="80" cy="130" r="12" fill="{INK}"/><path d="M80 136 L80 164" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
    if label: g += T(80, 232, label, 26)
    return S(160, 240 if label else 196, g, w)

def building(w=None, label='BANK'):
    g = [f'<path d="M20 120 L230 20 L440 120 Z" fill="{BLU}" {st}/>', f'<rect x="30" y="120" width="400" height="44" fill="#fff" {st}/>',
         T(230, 152, label, 30)]
    for k in range(5):
        x = 60 + k * 82
        g.append(f'<rect x="{x}" y="164" width="40" height="190" fill="#fff" {st}/>')
    g.append(f'<rect x="20" y="354" width="420" height="30" fill="{LG}" {st}/><rect x="0" y="384" width="460" height="26" fill="#fff" {st}/>')
    return S(460, 412, ''.join(g), w)

def house(w=None, label=None):
    g = (f'<rect x="50" y="150" width="300" height="200" fill="#fff" {st}/><path d="M20 160 L200 30 L380 160 Z" fill="{AMB}" {st}/>'
         f'<rect x="160" y="240" width="80" height="110" fill="{BLU}" {st}/><rect x="80" y="200" width="60" height="56" fill="{LG}" {st}/><rect x="260" y="200" width="60" height="56" fill="{LG}" {st}/>')
    if label: g += T(200, 130, label, 28)
    return S(400, 354, g, w)

def factory(w=None, label=None):
    g = (f'<path d="M30 380 L30 170 L130 230 L130 170 L230 230 L230 170 L330 230 L330 90 L390 90 L390 380 Z" fill="#fff" {st}/>'
         f'<rect x="70" y="290" width="60" height="50" fill="{BLU}" {st}/><rect x="180" y="290" width="60" height="50" fill="{BLU}" {st}/><rect x="290" y="290" width="60" height="90" fill="{LG}" {st}/>')
    if label: g += T(210, 160, label, 28)
    return S(420, 384, g, w)

def money_bag(w=None):
    g = (f'<path d="M70 70 C20 130 10 230 50 260 L170 260 C210 230 200 130 150 70 Z" fill="{AMB}" {st}/>'
         f'<path d="M70 70 L60 34 C90 46 130 46 160 34 L150 70 Z" fill="{AMB}" {st}/><path d="M64 76 C96 86 124 86 156 76" stroke="{INK}" stroke-width="6" fill="none"/>'
         + T(110, 200, '₹', 84, 700))
    return S(220, 264, g, w)

def coins(w=None, n=4):
    g = ''.join(f'<ellipse cx="90" cy="{150-k*24}" rx="72" ry="20" fill="{AMB}" {st}/><path d="M18 {150-k*24} v14 a72 20 0 0 0 144 0 v-14" fill="{AMB}" {st}/>' for k in range(n))
    return S(180, 180, g + T(90, 150 - (n - 1) * 24 + 10, '₹', 28), w)

def calendar(w=None, big='3', small='Months'):
    g = (f'<rect x="10" y="30" width="220" height="220" rx="20" fill="#fff" {st}/><path d="M10 50 a20 20 0 0 1 20 -20 h180 a20 20 0 0 1 20 20 v40 h-220 Z" fill="{BLU}" {st}/>'
         f'<path d="M64 10 v40 M176 10 v40" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>' + T(120, 190, big, 92) + T(120, 232, small, 26, 600))
    return S(240, 256, g, w)

def document(w=None, title='Contract', lines=5):
    g = f'<path d="M20 10 H180 L230 60 V300 H20 Z" fill="#fff" {st}/><path d="M180 10 V60 H230" fill="none" {st}/>' + T(110, 104, title, 28)
    g += ''.join(f'<path d="M50 {150+k*30} H{200 if k % 2 else 180}" stroke="{LG}" stroke-width="10" stroke-linecap="round"/>' for k in range(lines))
    return S(250, 310, g, w)

def phone(w=None, text=None):
    g = f'<rect x="10" y="10" width="200" height="380" rx="30" fill="#fff" {st}/><rect x="28" y="50" width="164" height="300" rx="10" fill="{LG}" stroke="{INK}" stroke-width="2"/><circle cx="110" cy="372" r="8" fill="{INK}"/>'
    if text: g += T(110, 200, text, 26)
    return S(220, 400, g, w)

def milk_can(w=None, label='MILK'):
    g = (f'<path d="M50 70 L150 70 L170 120 L170 290 C170 304 30 304 30 290 L30 120 Z" fill="#fff" {st}/><rect x="60" y="40" width="80" height="34" rx="8" fill="{LG}" {st}/>'
         f'<rect x="30" y="170" width="140" height="56" fill="{BLU}" {st}/>' + T(100, 208, label, 26, 700, '#fff'))
    return S(200, 304, g, w)

def cup(w=None, label=None):
    g = (f'<path d="M30 60 L170 60 L156 200 C154 214 46 214 44 200 Z" fill="#fff" {st}/><path d="M168 90 C210 90 210 160 160 160" fill="none" {st}/>'
         f'<path d="M36 80 L164 80" stroke="{AMB}" stroke-width="14"/><path d="M80 10 C70 30 96 36 84 54 M120 10 C110 30 136 36 124 54" fill="none" stroke="{GRY}" stroke-width="4" stroke-linecap="round"/>')
    if label: g += T(100, 150, label, 24)
    return S(210, 214, g, w)

def handshake(w=None):
    g = (f'<path d="M10 100 L70 70 L120 90 L190 60 L250 90" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
         f'<path d="M60 80 C90 50 130 50 150 70 L190 104 C200 116 186 130 172 120 L150 104 C160 120 146 134 132 122 C136 138 118 146 108 134 C108 150 88 150 82 138 L60 116 Z" fill="#fff" {st}/>'
         f'<path d="M150 70 C170 54 196 60 210 74 L236 104 L214 126 L190 104" fill="{YEL}" {st}/>')
    return S(260, 160, g, w)

def arrow(w=None, dir='up', label=None):
    if dir in ('same', 'equal', 'flat'):
        g = f'<rect x="10" y="50" width="100" height="26" rx="8" fill="#fff" {st}/><rect x="10" y="104" width="100" height="26" rx="8" fill="#fff" {st}/>'
        if label: g += T(60, 210, label, 28)
        return S(120, 220 if label else 180, g, w)
    p = 'M60 10 L110 80 L80 80 L80 170 L40 170 L40 80 L10 80 Z' if dir == 'up' else 'M60 170 L110 100 L80 100 L80 10 L40 10 L40 100 L10 100 Z'
    g = f'<path d="{p}" fill="#fff" {st}/>'
    if label: g += T(60, 210, label, 28)
    return S(120, 220 if label else 180, g, w)

def tea_glass(w=None, label=None):
    g = (f'<path d="M40 40 L160 40 L146 230 C144 244 56 244 54 230 Z" fill="#fff" {st}/>'
         f'<path d="M48 90 L152 90 L146 228 C144 240 56 240 54 228 Z" fill="{AMB}" {st}/>'
         f'<path d="M60 110 L140 110" stroke="#fff" stroke-width="4" opacity=".7"/>'
         f'<path d="M84 4 C74 20 98 26 86 36 M118 4 C108 20 132 26 120 36" fill="none" stroke="{GRY}" stroke-width="4" stroke-linecap="round"/>')
    if label: g += T(100, 290, label, 30)
    return S(200, 300 if label else 248, g, w)

def mug(w=None, label=None):
    g = (f'<path d="M30 50 L170 50 L170 220 C170 240 30 240 30 220 Z" fill="#fff" {st}/>'
         f'<path d="M170 90 C226 90 226 190 170 190" fill="none" stroke="{INK}" stroke-width="10"/>'
         f'<ellipse cx="100" cy="60" rx="66" ry="14" fill="#333333" stroke="{INK}" stroke-width="3"/>'
         f'<path d="M80 6 C70 22 94 28 82 42 M122 6 C112 22 136 28 124 42" fill="none" stroke="{GRY}" stroke-width="4" stroke-linecap="round"/>')
    if label: g += T(110, 290, label, 30)
    return S(230, 300 if label else 248, g, w)

def shaker(w=None, label=None):
    g = (f'<rect x="56" y="10" width="88" height="40" rx="10" fill="{BLU}" {st}/><rect x="86" y="0" width="28" height="18" rx="6" fill="{BLU}" {st}/>'
         f'<path d="M46 50 L154 50 L146 240 C146 252 54 252 54 240 Z" fill="#fff" {st}/>'
         f'<path d="M50 120 L150 120 L146 240 C146 250 54 250 54 240 Z" fill="#FFF8E8" {st}/>'
         f'<path d="M60 90 L140 90 M60 150 L84 150 M60 180 L84 180 M60 210 L84 210" stroke="{INK}" stroke-width="3"/>')
    if label: g += T(100, 290, label, 30)
    return S(200, 300 if label else 256, g, w)

PROPS = dict(tea_glass=tea_glass, mug=mug, shaker=shaker, wheat_field=wheat_field, wheat_sack=wheat_sack, flour_mill=flour_mill, market_stall=market_stall, scale=scale,
             lock=lock, building=building, bank=building, house=house, factory=factory, money_bag=money_bag, coins=coins,
             calendar=calendar, document=document, phone=phone, milk_can=milk_can, cup=cup, handshake=handshake, arrow=arrow)
FLOATING = {'handshake', 'lock', 'arrow', 'document', 'phone', 'calendar'}   # may hover (held / pinned); others stand on the floor

def prop(name, **o):
    if name not in PROPS: raise KeyError(name)
    if name == 'lock' and 'open' in o: o['open_'] = o.pop('open')
    return PROPS[name](**o)

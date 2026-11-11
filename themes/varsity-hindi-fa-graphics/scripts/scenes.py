"""Drawn scene library: backdrops and story props as SVG, one consistent flat illustrated style.

Style rules (keep any new drawing inside them):
- Backdrops: flat fills + soft vertical gradients, NO outlines, muted colours, light sky.
- Props: flat fills, 3px dark outline #1d1d1d (same line as the Varsity characters), rounded joins,
  one highlight tone per fill, no gradients except a soft shadow ellipse under objects on the ground.
- Palette: sky #CFE6F7→#EEF6FC, grass #9CCB6B/#7DB356, wheat #E9C25A/#D9A93E, soil #C9A27A,
  wood #B9804F, house walls #F3E3C8, roofs #E07A5F, blues #2F7CF6/#5AA0FF, white #FFFFFF.
"""
import html, math, random

OL = 'stroke="#1d1d1d" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"'

def esc(s): return html.escape(str(s))

# ------------------------------------------------------------------ backdrops (1920x1080)
def _sky(top="#CFE6F7", bot="#F2F8FC", sun=True):
    s = (f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
         f'<stop offset="1" stop-color="{bot}"/></linearGradient></defs><rect width="1920" height="1080" fill="url(#sky)"/>')
    if sun:
        s += ('<circle cx="1520" cy="170" r="70" fill="#FFD45C"/><circle cx="1520" cy="170" r="110" fill="#FFD45C" opacity=".18"/>')
    for (cx, cy, k) in ((330, 190, 1), (1100, 120, .8), (1750, 330, .7)):
        s += (f'<g opacity=".9" transform="translate({cx},{cy}) scale({k})"><ellipse cx="0" cy="0" rx="90" ry="34" fill="#fff"/>'
              f'<ellipse cx="-50" cy="8" rx="60" ry="26" fill="#fff"/><ellipse cx="55" cy="10" rx="64" ry="24" fill="#fff"/></g>')
    return s

def bd_farm(seed=1, house=True, tractor=True):
    rnd = random.Random(seed)
    s = _sky()
    s += '<path d="M0,560 C300,470 560,520 820,500 C1120,470 1400,540 1920,480 L1920,700 L0,700Z" fill="#B7D88F"/>'
    s += '<path d="M0,610 C380,560 700,600 1000,585 C1300,570 1600,610 1920,590 L1920,760 L0,760Z" fill="#9CCB6B"/>'
    for i in range(9):  # distant trees
        x = 120 + i * 210 + rnd.randint(-40, 40); y = 585 + rnd.randint(-15, 15)
        s += f'<rect x="{x-5}" y="{y}" width="10" height="34" fill="#8a6a4a"/><circle cx="{x}" cy="{y-10}" r="{rnd.randint(26,36)}" fill="#6FAE4F"/>'
    if house:
        s += ('<g transform="translate(1190,520)"><rect x="0" y="40" width="190" height="110" fill="#F3E3C8"/>'
              '<path d="M-20,45 L95,-25 L210,45Z" fill="#E07A5F"/><rect x="78" y="85" width="36" height="65" fill="#B9804F"/>'
              '<rect x="22" y="70" width="38" height="32" fill="#9fd0f0"/><rect x="132" y="70" width="38" height="32" fill="#9fd0f0"/></g>')
    s += '<path d="M0,690 L1920,650 L1920,1080 L0,1080Z" fill="#E9C25A"/>'
    s += '<path d="M860,1080 C900,900 1000,780 1180,680 L1240,680 C1080,790 1010,920 1000,1080Z" fill="#D7B48A"/>'
    for r in range(14):  # wheat rows
        y = 700 + r * 28 + r * r * 1.1
        col = "#D9A93E" if r % 2 else "#E3B84B"
        s += f'<path d="M0,{y:.0f} L1920,{y-30:.0f}" stroke="{col}" stroke-width="{6 + r*0.9:.1f}" opacity=".8"/>'
    for i in range(160):  # wheat ears near front
        x = rnd.randint(0, 1920); y = rnd.randint(860, 1080); h = rnd.randint(30, 60)
        if 860 < x < 1060 and y < 1000: continue
        s += f'<path d="M{x},{y} l{rnd.randint(-6,6)},-{h}" stroke="#C99A2E" stroke-width="3"/><ellipse cx="{x}" cy="{y-h}" rx="5" ry="12" fill="#E8B947"/>'
    if tractor:
        s += _tractor(560, 640, .55)
    return s

def bd_market(seed=2):
    rnd = random.Random(seed)
    s = _sky(sun=False)
    cols = ["#F3E3C8", "#F7D6C3", "#DDEAF3", "#F6E7A9", "#E6D9F2", "#D8EFD9"]
    x = -20
    while x < 1940:  # building row
        w = rnd.randint(150, 240); h = rnd.randint(260, 420); c = rnd.choice(cols)
        s += f'<rect x="{x}" y="{700-h}" width="{w}" height="{h}" fill="{c}"/>'
        s += f'<rect x="{x}" y="{700-h}" width="{w}" height="16" fill="#00000010"/>'
        for wy in range(700 - h + 40, 640, 70):
            for wx in range(x + 22, x + w - 40, 56):
                s += f'<rect x="{wx}" y="{wy}" width="28" height="36" rx="3" fill="#9fc6e6"/>'
        x += w + 6
    s += '<path d="M0,250 Q480,330 960,250 T1920,250" fill="none" stroke="#777" stroke-width="2"/>'
    for i in range(24):  # bunting
        bx = 40 + i * 80; by = 255 + 30 * math.sin(i / 3.8 * math.pi) * 0 + (20 if i % 2 else 26)
        s += f'<path d="M{bx},{by-14} l26,0 l-13,28Z" fill="{["#EF5143","#F6C21C","#2F7CF6","#86BD65"][i%4]}"/>'
    s += '<rect x="0" y="700" width="1920" height="380" fill="#E8D3B4"/>'
    s += '<rect x="0" y="700" width="1920" height="14" fill="#d2b893"/>'
    return s

def bd_city(seed=3):
    rnd = random.Random(seed)
    s = _sky(sun=False)
    x = -10
    while x < 1940:
        w = rnd.randint(110, 200); h = rnd.randint(300, 620)
        c = rnd.choice(["#BFD8EE", "#A9CBEA", "#D2E3F2"])
        s += f'<rect x="{x}" y="{760-h}" width="{w}" height="{h}" fill="{c}"/>'
        for wy in range(760 - h + 30, 720, 46):
            for wx in range(x + 16, x + w - 24, 34):
                s += f'<rect x="{wx}" y="{wy}" width="16" height="24" fill="#ffffff" opacity=".55"/>'
        x += w + 10
    s += '<rect x="0" y="760" width="1920" height="320" fill="#DDE6EE"/><rect x="0" y="860" width="1920" height="120" fill="#B9C6D2"/>'
    for i in range(12):
        s += f'<rect x="{i*170+40}" y="914" width="90" height="10" fill="#fff"/>'
    return s

def bd_interior(seed=4, wall="#F3E9DA"):
    s = f'<rect width="1920" height="1080" fill="{wall}"/>'
    s += '<rect x="0" y="0" width="1920" height="40" fill="#00000008"/>'
    for (x, w) in ((240, 360), (1320, 360)):
        s += f'<rect x="{x}" y="160" width="{w}" height="300" rx="8" fill="#BFE0F5"/><rect x="{x+w/2-4}" y="160" width="8" height="300" fill="#fff"/><rect x="{x}" y="306" width="{w}" height="8" fill="#fff"/>'
    s += '<rect x="0" y="760" width="1920" height="320" fill="#D9C2A2"/>'
    for i in range(0, 1920, 160):
        s += f'<line x1="{i}" y1="760" x2="{i - 300 + (i/1920)*600:.0f}" y2="1080" stroke="#c7ad89" stroke-width="3"/>'
    return s

BACKDROPS = {"farm": bd_farm, "market": bd_market, "city": bd_city, "interior": bd_interior}

def backdrop_svg(name, seed=None):
    fn = BACKDROPS[name]
    inner = fn(seed) if seed is not None else fn()
    return f'<svg class="backdrop-svg" viewBox="0 0 1920 1080" width="1920" height="1080" preserveAspectRatio="none">{inner}</svg>'

# ------------------------------------------------------------------ props (local SVG, sized by caller)
def _tractor(x, y, k=1):
    return (f'<g transform="translate({x},{y}) scale({k})"><rect x="0" y="40" width="150" height="60" rx="8" fill="#EF5143" {OL}/>'
            f'<rect x="90" y="0" width="70" height="60" rx="6" fill="#EF5143" {OL}/><rect x="102" y="10" width="44" height="30" fill="#BFE0F5" {OL}/>'
            f'<circle cx="40" cy="105" r="30" fill="#333" {OL}/><circle cx="40" cy="105" r="11" fill="#bbb"/>'
            f'<circle cx="140" cy="112" r="22" fill="#333" {OL}/><circle cx="140" cy="112" r="8" fill="#bbb"/></g>')

def p_sack(label="", price=""):
    """wheat/grain sack, optional label on it and a price tag hanging off it. box 220x240"""
    s = (f'<svg viewBox="0 0 {290 if price else 220} 240"><ellipse cx="104" cy="228" rx="88" ry="10" fill="#00000018"/>'
         f'<path d="M40,60 C20,120 18,190 30,222 L178,222 C190,190 188,120 168,60 Z" fill="#D9B07A" {OL}/>'
         f'<path d="M52,60 C70,40 140,40 156,60 Z" fill="#C49660" {OL}/>'
         f'<path d="M60,40 C70,10 140,10 150,40" fill="#F2D27A" {OL}/>'
         + "".join(f'<ellipse cx="{70+i*18}" cy="{30-abs(i-2)*5}" rx="7" ry="12" fill="#E8B947" stroke="#1d1d1d" stroke-width="2"/>' for i in range(5))
         + f'<path d="M58,64 Q104,78 150,64" fill="none" {OL}/>')
    if label:
        s += f'<rect x="58" y="120" width="92" height="44" rx="6" fill="#fff" {OL}/><text x="104" y="150" text-anchor="middle" font-family="Inter" font-weight="800" font-size="22">{esc(label)}</text>'
    if price:
        s += (f'<line x1="168" y1="90" x2="196" y2="120" stroke="#1d1d1d" stroke-width="2"/>'
              f'<g transform="rotate(12 200 140)"><path d="M184,120 L268,120 L268,166 L184,166 L170,143Z" fill="#fff" {OL}/>'
              f'<circle cx="182" cy="143" r="4" fill="#1d1d1d"/><text x="226" y="151" text-anchor="middle" font-family="Inter" font-weight="800" font-size="19">{esc(price)}</text></g>')
    return s + "</svg>"

def p_stall(awning="#2F7CF6", goods="sacks", sign="", price=""):
    """market stall with striped awning. box 420x380"""
    stripes = "".join(f'<path d="M{20+i*48},70 l48,0 l0,40 q-24,22 -48,0Z" fill="{awning if i%2==0 else "#fff"}" {OL}/>' for i in range(8))
    g = ""
    if goods == "sacks":
        for i in range(3):
            g += (f'<g transform="translate({70+i*100},210)"><path d="M0,20 C-10,60 -8,90 0,100 L80,100 C88,90 90,60 80,20Z" fill="#D9B07A" {OL}/>'
                  f'<ellipse cx="40" cy="20" rx="40" ry="14" fill="#E8B947" {OL}/></g>')
    elif goods == "boxes":
        for i in range(3):
            g += f'<rect x="{60+i*100}" y="240" width="86" height="70" fill="#C9935C" {OL}/><path d="M{60+i*100},262 h86" stroke="#1d1d1d" stroke-width="2"/>'
    s = (f'<svg viewBox="0 0 420 380"><ellipse cx="210" cy="372" rx="200" ry="10" fill="#00000016"/>'
         f'<rect x="34" y="100" width="12" height="270" fill="#B9804F" {OL}/><rect x="374" y="100" width="12" height="270" fill="#B9804F" {OL}/>'
         f'<rect x="10" y="40" width="400" height="34" rx="6" fill="{awning}" {OL}/>{stripes}'
         f'<rect x="30" y="300" width="360" height="72" fill="#C98B55" {OL}/><path d="M30,330 h360" stroke="#1d1d1d" stroke-width="2"/>{g}')
    if sign:
        s += f'<rect x="130" y="0" width="160" height="40" rx="6" fill="#fff" {OL}/><text x="210" y="28" text-anchor="middle" font-family="Inter" font-weight="800" font-size="20">{esc(sign)}</text>'
    if price:
        s += f'<rect x="150" y="318" width="120" height="40" rx="6" fill="#fff" {OL}/><text x="210" y="345" text-anchor="middle" font-family="Inter" font-weight="800" font-size="22">{esc(price)}</text>'
    return s + "</svg>"

def p_shop(sign="Shop", inside="mill", color="#2F7CF6"):
    """shop front with signboard; inside = mill (grinding machine + bags) | goods | counter. box 520x440"""
    ins = ""
    if inside == "mill":
        ins = (f'<rect x="200" y="200" width="120" height="150" rx="10" fill="#C9D4DE" {OL}/><path d="M220,200 L300,200 L280,150 L240,150Z" fill="#E5ECF2" {OL}/>'
               f'<rect x="236" y="250" width="48" height="40" rx="6" fill="#8A97A3" {OL}/><circle cx="260" cy="320" r="10" fill="#555"/>'
               + "".join(f'<g transform="translate({90+i*34 if i<2 else 360+(i-2)*36},300)"><rect x="0" y="0" width="30" height="48" rx="6" fill="#E3C894" {OL}/></g>' for i in range(4)))
    elif inside == "goods":
        ins = "".join(f'<rect x="{90+(i%5)*70}" y="{180+(i//5)*60}" width="50" height="40" rx="5" fill="{["#F6C21C","#86BD65","#EF5143","#5AA0FF","#E3C894"][i%5]}" {OL}/>' for i in range(10))
    elif inside == "counter":
        ins = f'<rect x="80" y="280" width="360" height="70" fill="#C98B55" {OL}/>'
    s = (f'<svg viewBox="0 0 520 440"><ellipse cx="260" cy="430" rx="250" ry="10" fill="#00000016"/>'
         f'<rect x="30" y="90" width="460" height="330" fill="{color}" {OL}/><rect x="60" y="140" width="400" height="230" fill="#4A5563" {OL}/>'
         f'{ins}<rect x="30" y="370" width="460" height="50" fill="#E8EEF3" {OL}/>'
         f'<rect x="20" y="70" width="480" height="30" fill="{color}" {OL}/>'
         f'<rect x="150" y="10" width="220" height="56" rx="8" fill="#fff" {OL}/>'
         f'<text x="260" y="48" text-anchor="middle" font-family="Inter" font-weight="800" font-size="26" fill="{color}">{esc(sign)}</text></svg>')
    return s

def p_calendar(month="December", mark=None):
    days = "".join(
        f'<rect x="{30+(d%7)*46}" y="{120+(d//7)*40}" width="36" height="30" rx="4" fill="{"#EF5143" if mark==d+1 else "#EEF2F6"}"/>'
        f'<text x="{48+(d%7)*46}" y="{141+(d//7)*40}" text-anchor="middle" font-family="Inter" font-weight="700" font-size="15" fill="{"#fff" if mark==d+1 else "#333"}">{d+1}</text>'
        for d in range(31))
    return (f'<svg viewBox="0 0 380 360"><rect x="10" y="40" width="360" height="310" rx="18" fill="#fff" {OL}/>'
            f'<path d="M10,58 a18,18 0 0 1 18,-18 h324 a18,18 0 0 1 18,18 v40 h-360Z" fill="#2F7CF6" {OL}/>'
            + "".join(f'<rect x="{60+i*60}" y="20" width="12" height="40" rx="6" fill="#555" {OL}/>' for i in range(5))
            + f'<text x="190" y="88" text-anchor="middle" font-family="Inter" font-weight="800" font-size="26" fill="#fff">{esc(month)}</text>{days}</svg>')

def p_document(title="Contract", lines=3, stamp=None, signed=True):
    s = (f'<svg viewBox="0 0 300 380"><rect x="20" y="20" width="260" height="340" rx="12" fill="#fff" {OL}/>'
         f'<text x="150" y="70" text-anchor="middle" font-family="Inter" font-weight="800" font-size="24">{esc(title)}</text>'
         + "".join(f'<rect x="50" y="{100+i*30}" width="{200 - (i%2)*40}" height="10" rx="5" fill="#D5DDE5"/>' for i in range(lines + 3)))
    if signed:
        s += '<path d="M60,320 c20,-30 30,10 50,-10 s20,-20 40,0" fill="none" stroke="#2F7CF6" stroke-width="3"/>'
    if stamp:
        s += (f'<g transform="rotate(-14 210 300)"><rect x="150" y="275" width="124" height="46" rx="6" fill="none" stroke="#EF5143" stroke-width="4"/>'
              f'<text x="212" y="306" text-anchor="middle" font-family="Inter" font-weight="800" font-size="20" fill="#EF5143">{esc(stamp)}</text></g>')
    return s + "</svg>"

def p_timeline(left="Today", right="In 3 Months", pos=0.0, w=900):
    x = 40 + (w - 80) * pos
    return (f'<svg viewBox="0 0 {w} 110"><rect x="40" y="40" width="{w-80}" height="18" rx="9" fill="#F3D98A" {OL}/>'
            f'<rect x="40" y="40" width="{max(18,(w-80)*pos)}" height="18" rx="9" fill="#EF5143"/>'
            f'<circle cx="40" cy="49" r="14" fill="#fff" {OL}/><circle cx="{w-40}" cy="49" r="14" fill="#fff" {OL}/>'
            f'<circle cx="{x}" cy="49" r="16" fill="#EF5143" {OL}/>'
            f'<text x="26" y="100" text-anchor="start" font-family="Inter" font-weight="700" font-size="22">{esc(left)}</text>'
            f'<text x="{w-26}" y="100" text-anchor="end" font-family="Inter" font-weight="700" font-size="22">{esc(right)}</text></svg>')

def p_handshake():
    return (f'<svg viewBox="0 0 200 120"><path d="M10,60 L60,40 L100,58 L140,40 L190,60" fill="none" {OL}/>'
            f'<path d="M60,40 C80,70 110,80 130,62 L100,58" fill="#F3D2B3" {OL}/><path d="M140,40 C120,80 90,90 70,70" fill="#E9BE97" {OL}/></svg>')

def p_lock(locked=True):
    shackle = '<path d="M30,50 V35 a25,25 0 0 1 50,0 V50" fill="none" stroke="#1d1d1d" stroke-width="7"/>' if locked else \
              '<path d="M30,50 V35 a25,25 0 0 1 50,0 V20" fill="none" stroke="#1d1d1d" stroke-width="7"/>'
    return (f'<svg viewBox="0 0 110 120">{shackle}<rect x="15" y="50" width="80" height="62" rx="10" fill="#F6C21C" {OL}/>'
            f'<circle cx="55" cy="78" r="8" fill="#1d1d1d"/><rect x="51" y="80" width="8" height="18" fill="#1d1d1d"/></svg>')

def p_price_tag(text="₹25/kg", strike=None, arrow=None):
    s = (f'<svg viewBox="0 0 240 100"><path d="M40,14 L226,14 L226,86 L40,86 L12,50Z" fill="#fff" {OL}/><circle cx="34" cy="50" r="6" fill="#1d1d1d"/>')
    if strike:
        s += f'<text x="134" y="40" text-anchor="middle" font-family="Inter" font-weight="600" font-size="18" fill="#EF5143" text-decoration="line-through">{esc(strike)}</text>'
        s += f'<text x="134" y="74" text-anchor="middle" font-family="Inter" font-weight="800" font-size="30">{esc(text)}</text>'
    else:
        s += f'<text x="134" y="62" text-anchor="middle" font-family="Inter" font-weight="800" font-size="32">{esc(text)}</text>'
    return s + "</svg>"

def p_arrow(direction="up", color="green"):
    c = {"green": "#86BD65", "coral": "#EF5143", "blue": "#2F7CF6"}[color]
    rot = {"up": 0, "down": 180, "right": 90, "left": -90}[direction]
    return (f'<svg viewBox="0 0 80 110"><g transform="rotate({rot} 40 55)"><path d="M40,6 L74,48 L52,48 L52,104 L28,104 L28,48 L6,48Z" '
            f'fill="{c}" {OL}/></g></svg>')

def p_truck(label=""):
    s = (f'<svg viewBox="0 0 360 200"><ellipse cx="180" cy="192" rx="170" ry="8" fill="#00000016"/>'
         f'<rect x="10" y="30" width="220" height="120" rx="8" fill="#fff" {OL}/><path d="M230,70 L300,70 L340,110 L340,150 L230,150Z" fill="#2F7CF6" {OL}/>'
         f'<rect x="250" y="82" width="44" height="30" fill="#BFE0F5" {OL}/>'
         f'<circle cx="70" cy="158" r="26" fill="#333" {OL}/><circle cx="280" cy="158" r="26" fill="#333" {OL}/>')
    if label:
        s += f'<text x="120" y="100" text-anchor="middle" font-family="Inter" font-weight="800" font-size="26">{esc(label)}</text>'
    return s + "</svg>"

def p_money(amount=""):
    s = (f'<svg viewBox="0 0 220 140"><g transform="rotate(-8 110 70)"><rect x="20" y="40" width="180" height="80" rx="8" fill="#9ED17B" {OL}/>'
         f'<rect x="10" y="28" width="180" height="80" rx="8" fill="#B5E08F" {OL}/><circle cx="100" cy="68" r="22" fill="#8CC56A" {OL}/>'
         f'<text x="100" y="77" text-anchor="middle" font-family="Inter" font-weight="800" font-size="24">₹</text></g>')
    if amount:
        s += f'<text x="110" y="136" text-anchor="middle" font-family="Inter" font-weight="800" font-size="22">{esc(amount)}</text>'
    return s + "</svg>"

PROPS = {"sack": p_sack, "stall": p_stall, "shop": p_shop, "calendar": p_calendar, "document": p_document,
         "timeline": p_timeline, "handshake": p_handshake, "lock": p_lock, "price_tag": p_price_tag,
         "arrow": p_arrow, "truck": p_truck, "money": p_money}

# ------------------------------------------------------------------ bubbles
def bubble_svg(kind, w, h, tail):
    """cloud (thought) or rounded (speech) bubble, tail towards (tx,ty) given in the bubble's local box"""
    tx, ty = tail
    if kind == "thought":
        r = min(w, h)
        bumps = []
        n = max(8, int((w + h) / 70))
        for i in range(n):
            a = 2 * math.pi * i / n
            bx = w / 2 + (w / 2 - r * .16) * math.cos(a); by = h / 2 + (h / 2 - r * .16) * math.sin(a)
            bumps.append(f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="{r*.2:.0f}"/>')
        body = (f'<g fill="#fff" stroke="#1d1d1d" stroke-width="3">{"".join(bumps)}</g>'
                f'<g fill="#fff">{"".join(b.replace("/>", " />") for b in bumps)}<ellipse cx="{w/2}" cy="{h/2}" rx="{w/2-r*.16}" ry="{h/2-r*.16}"/></g>')
        # trailing dots towards the tail
        dots = ""
        sx, sy = w / 2 + (tx - w / 2) * .55, h / 2 + (ty - h / 2) * .55
        for k, f in enumerate((0.70, 0.85, 1.0)):
            px, py = w / 2 + (tx - w / 2) * f, h / 2 + (ty - h / 2) * f
            dots += f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{14 - k*4}" fill="#fff" stroke="#1d1d1d" stroke-width="3"/>'
        return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" overflow="visible">{body}{dots}</svg>'
    # speech
    bx, by = w / 2, h / 2
    ang = math.atan2(ty - by, tx - bx)
    p1 = (bx + 40 * math.cos(ang + 1.6), by + 40 * math.sin(ang + 1.6))
    p2 = (bx + 40 * math.cos(ang - 1.6), by + 40 * math.sin(ang - 1.6))
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" overflow="visible">'
            f'<path d="M{p1[0]:.0f},{p1[1]:.0f} L{tx},{ty} L{p2[0]:.0f},{p2[1]:.0f}Z" fill="#fff" stroke="#1d1d1d" stroke-width="3" stroke-linejoin="round"/>'
            f'<rect x="3" y="3" width="{w-6}" height="{h-6}" rx="{min(40,h/3)}" fill="#fff" stroke="#1d1d1d" stroke-width="3"/>'
            f'<path d="M{p1[0]:.0f},{p1[1]:.0f} L{tx},{ty} L{p2[0]:.0f},{p2[1]:.0f}" fill="#fff" stroke="none"/></svg>')

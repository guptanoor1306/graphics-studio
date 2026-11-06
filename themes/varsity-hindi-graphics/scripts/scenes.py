"""Full-frame scene backdrops in the house line style (1920x1080), for storyboard lines such as
"standing on a wheat field", "atta chakki nearby", "Indian marketplace".
backdrop(name, clip=None, **o) -> (back_svg, front_svg or '', floor_y). `clip` = [x0, x1] keeps one half for split screens.
Palette only: amber/yellow wheat, white, greys, blue accents. No green/red (candles only).
"""
import random, props
INK, AMB, YEL, BLU, LG, CREAM = '#141414', '#EFB32E', '#FFBE30', '#278BED', '#D8D8D8', '#FFF8E8'

def _ear(x, y, s, rnd):
    """One wheat stalk with a grain head, scale s."""
    h = 70 * s; lean = rnd.uniform(-6, 6) * s
    g = f'<path d="M{x:.0f} {y:.0f} Q{x+lean/2:.0f} {y-h/2:.0f} {x+lean:.0f} {y-h:.0f}" fill="none" stroke="{INK}" stroke-width="{max(1.2,2.2*s):.1f}"/>'
    for j in range(4):
        yy = y - h + j * 9 * s; xx = x + lean
        rx, ry = 4.5 * s, 8 * s
        g += (f'<ellipse cx="{xx-5*s:.1f}" cy="{yy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" transform="rotate(-25 {xx-5*s:.1f} {yy:.1f})" fill="{YEL}" stroke="{INK}" stroke-width="{max(.8,1.4*s):.1f}"/>'
              f'<ellipse cx="{xx+5*s:.1f}" cy="{yy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" transform="rotate(25 {xx+5*s:.1f} {yy:.1f})" fill="{YEL}" stroke="{INK}" stroke-width="{max(.8,1.4*s):.1f}"/>')
    g += f'<path d="M{x+lean:.0f} {y-h-4*s:.0f} L{x+lean:.0f} {y-h-18*s:.0f}" stroke="{INK}" stroke-width="{max(.8,1.4*s):.1f}"/>'
    return g

def wheat_field(horizon=600, seed=4):
    rnd = random.Random(seed)
    g = [f'<circle cx="1540" cy="250" r="86" fill="{CREAM}" stroke="{INK}" stroke-width="3"/>',
         f'<path d="M0 {horizon} C260 {horizon-90} 520 {horizon-70} 760 {horizon-20} C1000 {horizon-110} 1340 {horizon-120} 1600 {horizon-40} C1720 {horizon-70} 1840 {horizon-60} 1920 {horizon-30} L1920 {horizon} Z" fill="{LG}" opacity=".55" stroke="{INK}" stroke-width="2"/>',
         f'<defs><linearGradient id="fld" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{YEL}"/><stop offset="1" stop-color="{AMB}"/></linearGradient></defs>',
         f'<rect x="0" y="{horizon}" width="1920" height="{1080-horizon}" fill="url(#fld)"/>',
         f'<path d="M0 {horizon} L1920 {horizon}" stroke="{INK}" stroke-width="3"/>']
    rows = [(horizon + 26, .38, 18), (horizon + 70, .5, 24), (horizon + 130, .66, 32), (horizon + 210, .85, 42), (horizon + 300, 1.05, 52)]
    for y, s, step in rows:
        x = rnd.uniform(0, step)
        while x < 1940:
            g.append(_ear(x, y + rnd.uniform(-6, 6), s, rnd)); x += step * rnd.uniform(.7, 1.2)
    front = []
    x = 10
    while x < 1940:
        front.append(_ear(x, 1090 + rnd.uniform(0, 20), 1.6, rnd)); x += 74 * rnd.uniform(.7, 1.2)
    return ''.join(g), ''.join(front), 980

def flour_mill(horizon=860):
    g = [f'<rect x="0" y="{horizon}" width="1920" height="{1080-horizon}" fill="{CREAM}"/><path d="M0 {horizon} L1920 {horizon}" stroke="{INK}" stroke-width="3"/>']
    mill, w, h = props.flour_mill(w=540, label='Atta Chakki')
    g.append(f'<g transform="translate(1320 {horizon-h+6})">{mill}</g>')
    for k, (x, sc) in enumerate([(1660, 210), (1760, 190), (1710, 170)]):
        sk, sw, sh = props.wheat_sack(w=sc, label='WHEAT')
        g.append(f'<g transform="translate({x} {horizon-sh+8 - (40 if k==2 else 0)})">{sk}</g>')
    return ''.join(g), '', horizon + 80

def grain_market(horizon=760, banner='Grain Market'):
    g = [f'<rect x="0" y="{horizon}" width="1920" height="{1080-horizon}" fill="{CREAM}"/><path d="M0 {horizon} L1920 {horizon}" stroke="{INK}" stroke-width="3"/>']
    for k, x in enumerate((-40, 440, 960, 1440)):
        st_, w, h = props.market_stall(w=520, goods='wheat')
        g.append(f'<g transform="translate({x} {horizon-h+4})" opacity=".9">{st_}</g>')
    bw = 640
    g.append(f'<rect x="{960-bw//2}" y="190" width="{bw}" height="96" rx="12" fill="#fff" stroke="{INK}" stroke-width="5"/>'
             f'<path d="M{960-bw//2+40} 190 L{960-bw//2+40} 150 M{960+bw//2-40} 190 L{960+bw//2-40} 150" stroke="{INK}" stroke-width="5"/>'
             + props.T(960, 256, banner, 54, 800))
    return ''.join(g), '', horizon + 220

SCENES = dict(wheat_field=wheat_field, flour_mill=flour_mill, atta_chakki=flour_mill, grain_market=grain_market, mandi=grain_market)

def backdrop(name, **o):
    if name not in SCENES: raise KeyError(name)
    return SCENES[name](**o)

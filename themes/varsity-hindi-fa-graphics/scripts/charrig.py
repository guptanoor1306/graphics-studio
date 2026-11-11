"""Pose + expression rig for the team's six Varsity characters.

Head, hair, face, eyes, body, legs and shoes are the team's artwork, untouched (assets/chars6/c1..c6.png,
arms removed). Only the stick arms are drawn (same stroke as the PSDs, the team's mitten hand) and,
for expressions, the mouth is redrawn.
"""
import json, math
from pathlib import Path

RIG_DIR = Path(__file__).resolve().parent.parent / "assets" / "chars6"
RIG = json.loads((RIG_DIR / "rig.json").read_text())

# wrist (and optional elbow) offsets from the shoulder, in units of arm length L (+x right, +y down)
# bend: sideways bow of a curved arm. "abs": target is a point on the head ("chin", "head_l", "head_r")
POSES = {
    "idle":        {"a": {"w": (-0.42, 0.88), "bend": 0.22},  "b": {"w": (0.30, 0.92), "bend": -0.2}},
    "point_left":  {"a": {"w": (-1.02, -0.12), "bend": 0.06}, "b": {"w": (0.30, 0.92), "bend": -0.2}},
    "point_right": {"a": {"w": (-0.42, 0.88), "bend": 0.22},  "b": {"w": (1.02, -0.12), "bend": -0.06}},
    "point_up":    {"a": {"w": (-0.42, 0.88), "bend": 0.22},  "b": {"w": (0.62, -0.92), "bend": -0.12}},
    "happy":       {"a": {"w": (-0.62, -0.80), "bend": -0.18}, "b": {"w": (0.62, -0.80), "bend": 0.18}},
    "hips":        {"a": {"e": (-0.50, 0.38), "w": (-0.08, 0.66)}, "b": {"e": (0.52, 0.38), "w": (0.10, 0.66)}},
    "think":       {"a": {"e": (-0.30, 0.62), "abs": "chin"}, "b": {"w": (0.30, 0.92), "bend": -0.2}},
    "worried":     {"a": {"e": (-0.48, 0.30), "abs": "cheek_l"}, "b": {"e": (0.50, 0.30), "abs": "cheek_r"}},
    "hold":        {"a": {"w": (-0.66, 0.42), "bend": 0.32},  "b": {"w": (0.30, 0.92), "bend": -0.2}},
    "give":        {"a": {"w": (-0.98, 0.12), "bend": 0.12},  "b": {"w": (0.30, 0.92), "bend": -0.2}},
    "shrug":       {"a": {"w": (-0.78, 0.10), "bend": -0.32}, "b": {"w": (0.78, 0.10), "bend": 0.32}},
    "explain":     {"a": {"w": (-0.80, 0.30), "bend": 0.25},  "b": {"w": (0.55, 0.45), "bend": -0.25}},
    "original":    None,
}
EXPRESSIONS = ("neutral", "smile", "happy", "worried", "surprised", "talk")

# team mitten hand, traced from the PSD hand; wrist at (0,0), arm leaves towards -33 degrees
HAND = ("M0,0 C-2,-1 -3,-7 -5,-13 C-7,-20 -16,-20 -19,-14 C-21,-9 -19,-4 -18,-1 "
        "C-26,2 -34,8 -34.5,17 C-35,26 -29,33 -20,33.5 C-12,34 -5,31 -1.3,21")
HAND_ANG = -33.0

def _hand(wx, wy, px, py, sw):
    ang = math.degrees(math.atan2(py - wy, px - wx))     # wrist -> towards shoulder/elbow
    flip = math.cos(math.radians(ang)) < 0               # arm reaching to the right: mirror the mitten
    if flip:
        rot = ang - (180 - HAND_ANG)
        tr = f"translate({wx:.1f},{wy:.1f}) rotate({rot:.1f}) scale(-1,1)"
    else:
        tr = f"translate({wx:.1f},{wy:.1f}) rotate({ang - HAND_ANG:.1f})"
    return f'<path d="{HAND}" transform="{tr}" fill="none" stroke="#111" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'

def _abs_point(r, key):
    hx, hy = r["head"]["c"]; rad = r["head"]["r"]
    if key == "chin": return (hx - rad * 0.10, hy + rad * 0.95)
    if key == "head_l": return (hx - rad * 0.98, hy + rad * 0.05)
    if key == "head_r": return (hx + rad * 0.98, hy + rad * 0.05)
    if key == "cheek_l": return (hx - rad * 0.80, hy + rad * 0.45)
    if key == "cheek_r": return (hx + rad * 0.80, hy + rad * 0.45)
    raise KeyError(key)

def _arm(r, side, spec, sw):
    sx, sy = r[side]; L = r["L"]
    if spec.get("abs"):
        wx, wy = _abs_point(r, spec["abs"])
    else:
        wx, wy = sx + spec["w"][0] * L, sy + spec["w"][1] * L
    if spec.get("e"):
        ex, ey = sx + spec["e"][0] * L, sy + spec["e"][1] * L
        d = f"M{sx},{sy} L{ex:.1f},{ey:.1f} L{wx:.1f},{wy:.1f}"
        prev = (ex, ey)
    else:
        mx, my = (sx + wx) / 2, (sy + wy) / 2
        dx, dy = wx - sx, wy - sy
        b = spec.get("bend", 0.2)
        cx, cy = mx - dy * b, my + dx * b
        d = f"M{sx},{sy} Q{cx:.1f},{cy:.1f} {wx:.1f},{wy:.1f}"
        prev = (cx, cy)
    arm = f'<path d="{d}" fill="none" stroke="#111" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
    return arm + _hand(wx, wy, prev[0], prev[1], sw), (wx, wy)

def _mouth(r, expr):
    if expr in (None, "neutral"): return ""
    m = r["mouth"]; cx, cy = m["c"]; k = max(m["rx"], 18) / 24
    patch = f'<ellipse cx="{cx}" cy="{cy}" rx="{m["rx"]}" ry="{m["ry"]}" fill="#fff"/>'
    s = 'stroke="#111" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"'
    t = f"translate({cx},{cy}) scale({k:.2f})"
    shapes = {
        "smile": f'<path d="M-15,-4 Q0,11 15,-4" fill="none" {s}/>',
        "happy": f'<path d="M-17,-6 Q0,20 17,-6 Q0,0 -17,-6 Z" fill="#3a1d1d" {s}/><path d="M-7,6 Q0,2 7,6 Q0,10 -7,6Z" fill="#ef7f7f"/>',
        "worried": f'<path d="M-14,6 Q-7,-3 0,2 Q7,-3 14,6" fill="none" {s}/>',
        "surprised": f'<ellipse cx="0" cy="2" rx="6.5" ry="8.5" fill="#3a1d1d" {s}/>',
        "talk": f'<path d="M-12,-3 Q0,13 12,-3 Z" fill="#3a1d1d" {s}/>',
    }
    return patch + f'<g transform="{t}">{shapes[expr]}</g>'

def char_svg(cid, pose="idle", expr="neutral", data_uri=None):
    """Returns (svg_markup, info). viewBox is the base PNG's local box padded for arms; info has the
    hand points (local) and the base box so callers can scale/position."""
    r = RIG[cid]
    import base64
    from PIL import Image
    p = RIG_DIR / f"{cid}.png"
    w, h = Image.open(p).size
    uri = data_uri or "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
    sw = RIG.get("stroke", 4)
    pad_x, pad_t = 260, 120
    back, front, hands = [], [], {}
    spec = POSES.get(pose, POSES["idle"])
    if pose == "original":
        uri_orig = RIG_DIR / f"{cid}_orig.png"
    if spec:
        for side in ("a", "b"):
            svg, hp = _arm(r, side, spec[side], sw)
            hands[side] = hp
            (back if side in r["behind"] else front).append(svg)
    body = f'<image href="{uri}" x="0" y="0" width="{w}" height="{h}"/>'
    vb = f"{-pad_x} {-pad_t} {w + 2 * pad_x} {h + pad_t}"
    svg = (f'<svg viewBox="{vb}" width="{w + 2 * pad_x}" height="{h + pad_t}" overflow="visible">'
           f'{"".join(back)}{body}{_mouth(r, expr)}{"".join(front)}</svg>')
    return svg, {"w": w, "h": h, "pad_x": pad_x, "pad_t": pad_t, "hands": hands}

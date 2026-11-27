"""Item ids: a fixed, short id on each piece of a frame that can be animated on its own (each point of a list, each card,
coin, date, bar, notification), so LA Studio can find "point 3" by its id instead of guessing from layer names.

The export (exporter.py) runs ITEM_JS on every rendered frame and writes data-item="point-3" on those pieces. The
storyboard CSV (storyboard_csv.py) names the same ids in its `actions` column. Both sides take the noun from NOUN_RULES
below, so "reveal 3" in the storyboard and the third point in the frame agree.
"""
from __future__ import annotations

import json
import re

# the first rule whose word appears in a block's type / class names gives its pieces' noun
NOUN_RULES: list[tuple[str, str]] = [
    ("coin", "coin"), ("card", "card"), ("people", "card"), ("catgrid", "card"), ("episode", "card"),
    ("calendar", "date"), ("date", "date"), ("month", "date"),
    ("notif", "notice"), ("notice", "notice"), ("alert", "notice"), ("toast", "notice"),
    ("table", "row"), ("rows", "row"),
    ("bar", "bar"), ("chart", "bar"), ("updown", "bar"),
    ("pie", "slice"), ("donut", "slice"), ("slice", "slice"),
    ("pill", "pill"), ("tab", "pill"),
    ("timeline", "step"), ("step", "step"),
    ("acronym", "word"),
    ("list", "point"), ("recap", "point"), ("check", "point"), ("point", "point"), ("bullet", "point"),
    ("option", "point"), ("takeaway", "point"), ("quiz", "point"), ("item", "point"),
]


def noun_for(words: str) -> str:
    w = (words or "").lower()
    for k, n in NOUN_RULES:
        if k in w:
            return n
    return "item"


# what a piece of a frame is called in the storyboard text ("5 points", "twelve coins", "the 3rd card")
SB_NOUNS = {"point": "point", "points": "point", "item": "point", "items": "point", "line": "point", "lines": "point",
            "coin": "coin", "coins": "coin", "card": "card", "cards": "card", "date": "date", "dates": "date",
            "notification": "notice", "notifications": "notice", "notice": "notice", "bar": "bar", "bars": "bar",
            "row": "row", "rows": "row", "step": "step", "steps": "step", "pill": "pill", "pills": "pill",
            "option": "point", "options": "point", "reason": "point", "reasons": "point", "decision": "point",
            "decisions": "point", "tip": "point", "tips": "point", "box": "card", "boxes": "card"}

_TEXT_KEYS = ("text", "label", "title", "name", "value", "word", "caption", "lead")


def _txt(x) -> str:
    if isinstance(x, str):
        return re.sub(r"(\+\+|__|\*\*|\{o:|\})", "", x).replace("|", " ").strip()
    if isinstance(x, dict):
        for k in _TEXT_KEYS:
            if isinstance(x.get(k), str) and x[k].strip():
                return _txt(x[k])
    return ""


def frame_items(frame: dict | None) -> dict:
    """The repeated pieces of a frame from its spec (what ITEM_JS finds in the picture, in the same order):
    {"noun": "point", "texts": [...]} or {} when the frame has none."""
    if not isinstance(frame, dict):
        return {}

    def walk(node, typ):
        if isinstance(node, dict):
            t = str(node.get("t") or node.get("type") or "")
            for k, v in node.items():
                if isinstance(v, list) and len(v) >= 2 and all(isinstance(x, (str, dict)) for x in v):
                    texts = [_txt(x) for x in v]
                    if sum(1 for x in texts if x) >= 2 and k not in ("frames",):
                        return {"noun": noun_for(t or typ or k), "texts": texts}   # the block's type first, as ITEM_JS does
                r = walk(v, t or typ)
                if r:
                    return r
        elif isinstance(node, list):
            for x in node:
                r = walk(x, typ)
                if r:
                    return r
        return {}

    top = frame.get("items") or frame.get("els") or frame.get("elements") or []
    if isinstance(top, list):
        for blk in top:      # a block's own list (a recap's points), not the frame's list of blocks
            r = walk(blk, "")
            if r:
                return r
    return {}


# runs in the rendered frame (before the export flattens it): data-item on each repeated piece and on the heading
ITEM_JS = r"""(rules) => {
  const noun = w => { w = String(w || '').toLowerCase(); for (const [k, n] of rules) if (w.includes(k)) return n; return 'item'; };
  const skip = el => el.closest('.plate, .decor, .deco, [data-decor], [aria-hidden="true"]') || el.ownerSVGElement;
  const vis = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el); return r.width >= 6 && r.height >= 6 && s.display !== 'none' && s.visibility !== 'hidden'; };
  const real = el => (el.innerText || '').trim() || [...el.querySelectorAll('img, svg, canvas')].concat(el.matches('img, svg, canvas') ? [el] : []).some(x => { const r = x.getBoundingClientRect(); return r.width >= 30 && r.height >= 30; });
  const sig = el => el.tagName + '.' + (el.classList[0] || '');   // (its colour / state classes differ: blue, orange, active)
  const typeOf = el => { const t = el.closest('[data-zo-t], [data-layer-type], [data-type], [data-t]');
    return t ? (t.dataset.zoT || t.dataset.layerType || t.dataset.type || t.dataset.t || '') : ''; };
  const used = {};
  const tagSet = (set) => {
    const p = set[0].parentElement, t = typeOf(p), cls = e => e.className && e.className.baseVal === undefined ? e.className : '';
    let n = t ? noun(t) : noun(cls(p) + ' ' + cls(set[0]));   // the block's type first (the storyboard CSV reads the same type from the spec) used[n] = (used[n] || 0) + 1; if (used[n] > 1) n = n + used[n];
    set.forEach((el, i) => { el.dataset.item = n + '-' + (i + 1); });
  };
  const sets = [];
  const look = (el) => {
    const kids = [...el.children].filter(k => !skip(k) && vis(k));
    const by = {}; kids.forEach(k => { (by[sig(k)] = by[sig(k)] || []).push(k); });
    const best = Object.values(by).filter(s => s.length >= 2 && s.filter(real).length >= 2).sort((a, b) => b.length - a.length)[0];
    if (best && best.length >= Math.max(2, kids.length * 0.5)) { sets.push(best); return; }   // the outermost repeated pieces: their insides stay theirs
    kids.forEach(look);
  };
  const root = document.querySelector('#stage') || document.body;
  [...root.children].filter(k => !skip(k)).forEach(look);
  sets.forEach(tagSet);
  const h = [...root.querySelectorAll('.heading, .title, h1, h2, [data-zo-t="heading"], [data-layer-type="heading"]')].find(e => !skip(e) && vis(e) && !e.closest('[data-item]') && (e.innerText || '').trim());
  if (h) h.dataset.item = 'heading';
  return document.querySelectorAll('[data-item]').length;
}"""


def item_js_args() -> str:
    return json.dumps(NOUN_RULES)

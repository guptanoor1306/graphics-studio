"""Parse project storyboard text into a timestamp-ordered CSV for downstream tools."""
from __future__ import annotations

import csv
import io
import re
from typing import Any

_SKIP = re.compile(
    r"^(SB\s|Look:|Totals:|#|\*\*|---+|\s*$)",
    re.I,
)
_TS_LINE = re.compile(
    r"^(?P<approx>~?)\s*"
    r"(?P<time>\d+:\d+(?:\.\d+)?|\d+\.\d+(?:_[a-z0-9]+)?)\s*"
    r"[–\-]\s*"
    r"(?P<body>.+)$",
    re.I,
)
_FRAME_ID = re.compile(r"(?:→|->)\s*([^\s·]+)\s*(?:·|$)")
_SPLIT = re.compile(r"\s[–\-]\s")


def _time_to_seconds(raw: str) -> int | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    base = raw.split("_", 1)[0]
    if ":" in base:
        m, s = base.split(":", 1)
        try:
            return int(m) * 60 + int(float(s))
        except ValueError:
            return None
    if "." in base:
        m, s = base.split(".", 1)
        try:
            return int(m) * 60 + int(s)
        except ValueError:
            return None
    return None


_REUSE = re.compile(r"\b(?:reuse[sd]?|re-use|bring\s+back|back\s+to|same\s+as|repeat(?:s|ed)?)\s+(?:frame\s+)?(\d+\.\d+(?:_[a-z0-9]+)?)", re.I)


def _frame_id_from_body(body: str) -> str:
    m = _FRAME_ID.search(body or "")
    if m:
        return m.group(1).strip()
    m = _REUSE.search(body or "")          # "reuse 0.20, reveal 3": the frame that comes back
    return m.group(1).strip() if m else ""


def _beat_and_instruction(body: str) -> tuple[str, str]:
    parts = _SPLIT.split(body.strip(), maxsplit=1)
    if len(parts) == 1:
        return "", parts[0].strip()
    return parts[0].strip(), parts[1].strip()


def parse_storyboard_lines(storyboard: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, line in enumerate((storyboard or "").splitlines(), start=1):
        text = line.strip()
        if not text or _SKIP.match(text):
            continue
        m = _TS_LINE.match(text)
        if not m:
            rows.append(
                {
                    "line_no": i,
                    "timestamp": "",
                    "timestamp_seconds": "",
                    "approximate": "",
                    "beat_type": "",
                    "instruction": text,
                    "frame_id": "",
                    "raw_line": text,
                }
            )
            continue
        body = m.group("body")
        beat, instruction = _beat_and_instruction(body)
        fid = _frame_id_from_body(body)
        ts = m.group("time")
        sec = _time_to_seconds(ts)
        rows.append(
            {
                "line_no": i,
                "timestamp": ts,
                "timestamp_seconds": "" if sec is None else sec,
                "approximate": "yes" if m.group("approx").startswith("~") else "no",
                "beat_type": beat,
                "instruction": instruction,
                "frame_id": fid,
                "raw_line": text,
            }
        )
    return rows


# ---------------------------------------------------------------- actions: what happens to which item (item_ids.py ids)
_NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
         "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "last": -1}
_COLOURS = ("red", "green", "blue", "orange", "yellow", "purple", "grey", "gray", "black", "white")
_STOP = set("the a an and or of to in on for is are be your you it its this that with as at by from will can".split())


def _num(w: str) -> int | None:
    w = (w or "").lower().strip()
    if w.isdigit():
        return int(w)
    return _NUMW.get(w)


def _words(t: str) -> list[str]:
    return re.findall(r"[a-z0-9₹%]+", (t or "").lower())


def _said_at(item_text: str, vo: str, others: list[str] | None = None) -> str:
    """The script words where an item is said ("saving for your financial goal"), or '' when they can't be found.
    Words every item shares ("Automate" in each point) don't count; words are compared by their first 5 letters."""
    st = lambda w: w[:5]
    common = {}
    for o in others or []:
        for w in set(map(st, _words(o))):
            common[w] = common.get(w, 0) + 1
    many = {w for w, n in common.items() if len(others or []) >= 3 and n > len(others) / 2}
    want = list(dict.fromkeys(st(w) for w in _words(item_text) if w not in _STOP and len(w) > 2 and st(w) not in many))
    vo_raw = re.findall(r"\S+", vo or "")
    vo_w = [st((_words(x) or [""])[0]) for x in vo_raw]
    if len(want) < 1 or not vo_w:
        return ""
    best, at = 0, None
    span = max(len(want) + 4, 5)
    for i in range(len(vo_w)):
        hit = [j for j in range(i, min(len(vo_w), i + span)) if vo_w[j] in want]
        n = len({vo_w[j] for j in hit})
        if n > best:
            best, at = n, (hit[0], hit[-1])
    if not at or best < max(1, -(-len(want) // 2)) or (len(want) >= 3 and best < 2):
        return ""
    a, b = at
    return " ".join(vo_raw[a:b + 1]).strip(" ,.;:!?\"'“”")[:80]


def _ids(noun: str, nums: list[int]) -> str:
    nums = sorted(dict.fromkeys(nums))
    if len(nums) >= 3 and nums == list(range(nums[0], nums[-1] + 1)):
        return f"{noun}-{nums[0]}..{noun}-{nums[-1]}"
    return ", ".join(f"{noun}-{n}" for n in nums)


def row_actions(instruction: str, frame_id: str, items: dict | None, vo: str, state: dict) -> str:
    """The `actions` column for one storyboard row: a short, fixed vocabulary (reveal, show, blur, tick, cross, highlight,
    swap A → B, zoom to) on the frame's item ids, each "on VO" or @ "the script words" it belongs to. '' when the row
    says nothing LA Studio can act on (it then times the frame as before)."""
    import item_ids
    text = instruction or ""
    m = re.search(r"\[actions?:\s*([^\]]+)\]", text, re.I) or re.search(r"(?:^|\s)actions?:\s*(.+)$", text, re.I)
    if m:
        return m.group(1).strip()
    low = text.lower()
    items = items or {}
    texts = items.get("texts") or []
    noun = items.get("noun") or ""
    count = None
    for mm in re.finditer(r"\b(\d+|" + "|".join(k for k in _NUMW if k not in ("last",)) + r")\s+([a-z]+)(?:\s+([a-z]+))?\b", low):
        nn = _num(mm.group(1))
        w = mm.group(2) if mm.group(2) in item_ids.SB_NOUNS else (mm.group(3) or "")   # "5 points", "5 money decisions"
        if nn and w in item_ids.SB_NOUNS:
            count = nn
            noun = noun or item_ids.SB_NOUNS[w]
            break
    if not noun:
        w = next((w for w in _words(low) if w in item_ids.SB_NOUNS), "")
        noun = item_ids.SB_NOUNS.get(w, "point")
    k = count or len(texts)
    seen = state.setdefault(frame_id or "?", set())

    def on(n: int) -> str:
        said = _said_at(texts[n - 1], vo, texts) if 0 < n <= len(texts) else ""
        return f'@ "{said}"' if said else "on VO"

    def targets(after: str) -> list[int]:
        out = []
        for mm in re.finditer(after + r"\s+((?:(?:\d+|[a-z]+)(?:st|nd|rd|th)?\s*(?:,|&|and|…|\.\.\.)?\s*){1,8})", low):
            for w in re.findall(r"\d+|[a-z]+", mm.group(1)):
                n = _num(re.sub(r"(st|nd|rd|th)$", "", w) if w[0].isdigit() else w)
                if n == -1 and k:
                    n = k
                if n:
                    out.append(n)
                elif w not in ("and", "point", "points", "item", "items", noun):
                    break
        return [n for n in out if not k or n <= k]

    acts: list[str] = []
    ordinals = [int(x) for x in re.findall(r"\b(\d+)(?:st|nd|rd|th)\b", low)] + [v for w, v in _NUMW.items() if v > 0 and re.search(r"\b" + w + r"\b", low) and w in ("first", "second", "third", "fourth", "fifth", "sixth", "last")]
    rev = targets(r"\breveal(?:s|ed)?")
    if re.search(r"\bblur", low) and k:
        acts.append(f"blur {_ids(noun, list(range(1, k + 1)))}")
    if rev:
        before = sorted(n for n in seen if n not in rev) or ([n for n in range(1, min(rev)) ] if _REUSE.search(text) else [])
        if before:
            acts.append(f"show {_ids(noun, before)}")
        for n in rev:
            acts.append(f"reveal {noun}-{n} {on(n)}")
        seen.update(before + rev)
    elif k and re.search(r"one by one|one after|as per vo|\bappear|\bpop|\bbuild|\breveal|comes? in|stagger", low) and not re.search(r"\b(tick|cross)", low):
        acts.append(f"reveal {_ids(noun, list(range(1, k + 1)))} each on VO" if not texts else "; ".join(f"reveal {noun}-{n} {on(n)}" for n in range(1, k + 1)))
        seen.update(range(1, k + 1))
    for word, act in (("tick", "tick"), ("✓", "tick"), ("check ?mark", "tick"), ("cross", "cross"), ("✗", "cross"), ("✕", "cross")):
        if re.search(word, low):
            tg = targets(act + r"(?:s|ed)?") or (ordinals if ordinals else [])
            if tg:
                acts += [f"{act} {noun}-{n} {on(n)}" for n in tg]
            elif k and texts:
                acts += [f"{act} {noun}-{n} {on(n)}" for n in range(1, k + 1)]
            elif k:
                acts.append(f"{act} each {_ids(noun, list(range(1, k + 1)))} on VO")
            break
    if re.search(r"highlight|turns? (?:" + "|".join(_COLOURS) + r")|glow|circled?|\bmark", low):
        col = next((c for c in _COLOURS if re.search(r"\b" + c + r"\b", low)), "")
        tg = targets(r"highlight(?:s|ed)?") or ordinals
        if tg:
            acts.append(f"highlight {_ids(noun, tg)}{' ' + col if col else ''} on VO")
    q = re.findall(r"[\"“]([^\"”]{1,60})[\"”]", text)
    if len(q) >= 2 and re.search(r"→|->|\bto\b|becomes|replaced|swap|changes", text):
        def idof(t):
            for i, x in enumerate(texts, 1):
                if x and (x.lower() in t.lower() or t.lower() in x.lower()):
                    return f"{noun}-{i}"
            return f'"{t}"'
        acts.append(f"swap {idof(q[-2])} → {idof(q[-1])} on VO")
    if re.search(r"zoom|push(?:es)? in", low):
        tg = ordinals or targets(r"zoom(?:s)? (?:in )?(?:to|on)")
        acts.append(f"zoom to {noun}-{tg[0]} on VO" if tg else "zoom to frame on VO")
    return "; ".join(acts)


def enrich_rows_with_spec(rows: list[dict[str, Any]], spec: dict | None) -> list[dict[str, Any]]:
    frame_ids = {
        str(f.get("id"))
        for f in (spec or {}).get("frames") or []
        if isinstance(f, dict) and f.get("id")
    }
    mode_by_id = {
        str(f.get("id")): f.get("mode") or f.get("type") or ""
        for f in (spec or {}).get("frames") or []
        if isinstance(f, dict) and f.get("id")
    }
    out: list[dict[str, Any]] = []
    for r in rows:
        row = dict(r)
        fid = row.get("frame_id") or ""
        row["has_spec_frame"] = "yes" if fid and fid in frame_ids else ("no" if fid else "")
        row["spec_mode"] = mode_by_id.get(fid, "") if fid else ""
        out.append(row)
    return out


def _spec_frames(spec: dict | None) -> dict:
    return {str(f.get("id")): f for f in (spec or {}).get("frames") or [] if isinstance(f, dict) and f.get("id")}


def _frame_lookup(by_id: dict, fid: str):
    return by_id.get(fid) or by_id.get(fid.split("_", 1)[0]) or next((f for k, f in by_id.items() if k.split("_", 1)[0] == fid), None)


def storyboard_csv_text(storyboard: str, spec: dict | None = None, *, project_name: str = "", vo_by_frame: dict | None = None) -> str:
    import item_ids
    rows = enrich_rows_with_spec(parse_storyboard_lines(storyboard), spec)
    by_id, state, vo_by_frame = _spec_frames(spec), {}, vo_by_frame or {}
    for r in rows:
        fid = r.get("frame_id") or ""
        r["actions"] = row_actions(r.get("instruction") or "", fid, item_ids.frame_items(_frame_lookup(by_id, fid)) if fid else {},
                                   vo_by_frame.get(fid) or r.get("instruction") or "", state) if r.get("timestamp") else ""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(
        [
            "project",
            "line_no",
            "timestamp",
            "timestamp_seconds",
            "approximate",
            "beat_type",
            "instruction",
            "frame_id",
            "has_spec_frame",
            "spec_mode",
            "raw_line",
            "actions",
        ]
    )
    name = project_name or ""
    for r in rows:
        w.writerow(
            [
                name,
                r.get("line_no", ""),
                r.get("timestamp", ""),
                r.get("timestamp_seconds", ""),
                r.get("approximate", ""),
                r.get("beat_type", ""),
                r.get("instruction", ""),
                r.get("frame_id", ""),
                r.get("has_spec_frame", ""),
                r.get("spec_mode", ""),
                r.get("raw_line", ""),
                r.get("actions", ""),
            ]
        )
    return buf.getvalue()


def frames_csv_text(frames: list[dict], *, project_name: str = "", spec: dict | None = None) -> str:
    """The same CSV for a video with no storyboard text (frames picked from the toolkit or made from the script): one row per
    frame, in time order, from what the page knows: {frame_id, t (seconds), mode, text (its script lines)}."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["project", "line_no", "timestamp", "timestamp_seconds", "approximate", "beat_type", "instruction",
                "frame_id", "has_spec_frame", "spec_mode", "raw_line", "actions"])
    import item_ids
    by_id, state = _spec_frames(spec), {}
    rows = []
    for f in frames or []:
        if not isinstance(f, dict) or not str(f.get("frame_id") or "").strip():
            continue
        try:
            t = float(f.get("t"))
        except (TypeError, ValueError):
            t = None
        rows.append((t if t is not None else 1e9, f, t))
    rows.sort(key=lambda r: r[0])
    for n, (_, f, t) in enumerate(rows, 1):
        ts = f"{int(t // 60)}.{int(t % 60):02d}" if t is not None else ""
        mode = str(f.get("mode") or "")[:40]
        text = " ".join(str(f.get("text") or "").split())[:2000]
        beat = {"fss": "FSS", "osa": "OSA"}.get(mode.lower(), mode.upper() or "FRAME")
        fid = str(f["frame_id"])[:80]
        sbi = " ".join(str(f.get("instruction") or "").split())[:500]     # the frame's own storyboard note, when the page has one
        act = row_actions(sbi, fid, item_ids.frame_items(_frame_lookup(by_id, fid)), text, state) if sbi else ""
        w.writerow([project_name or "", n, ts, f"{t:.2f}" if t is not None else "", "yes" if f.get("approx") and t is not None else "", beat, text, fid, "yes", mode,
                    f"{ts} – {beat} – {text} → {fid}".strip(" –"), act])
    return buf.getvalue()

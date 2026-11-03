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


def _frame_id_from_body(body: str) -> str:
    m = _FRAME_ID.search(body or "")
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


def storyboard_csv_text(storyboard: str, spec: dict | None = None, *, project_name: str = "") -> str:
    rows = enrich_rows_with_spec(parse_storyboard_lines(storyboard), spec)
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
            ]
        )
    return buf.getvalue()

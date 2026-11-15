"""LA Studio link: which Graphics Studio project is step 1 ("Graphics") of which LA Studio project.

LA Studio is a local app (each computer keeps its projects under ~/LA Studio Projects); Graphics Studio is the
shared web app. The link lives here, on the shared side, so LA Studio's engine never changes:
  la_links(la_project TEXT PRIMARY KEY, project_id INTEGER, la_name TEXT, linked_at)
One LA project ↔ one Graphics Studio project. The channel → kit hierarchy LA Studio reads is CHANNELS below
(the same list the Graphics Studio page shows).
"""
from __future__ import annotations

import json
import re
import time

_SCHEMA = """CREATE TABLE IF NOT EXISTS la_links (
    la_project TEXT PRIMARY KEY, project_id INTEGER, la_name TEXT, linked_at DOUBLE PRECISION)"""
LA_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# channel → kits; form: lf = long form 16:9, sf = short form 9:16 (LA Studio's project format)
CHANNELS = [
    {"id": "varsity", "name": "Varsity", "colour": "#5B55E6", "kits": [
        {"theme": "varsity-mf-graphics", "label": "Varsity Mutual Fund", "form": "lf"},
        {"theme": "varsity-english", "label": "Varsity English", "form": "lf"},
        {"theme": "varsity-hindi-graphics", "label": "Varsity Hindi – Charts", "form": "lf"},
        {"theme": "varsity-hindi-fa-graphics", "label": "Varsity Hindi – Elements", "form": "lf"},
    ]},
    {"id": "zo", "name": "ZO", "colour": "#387ED1", "kits": [
        {"theme": "zo-product-graphics", "label": "ZO Product", "form": "lf"},
    ]},
    {"id": "zero1", "name": "Zero1", "colour": "#C96442", "kits": [
        {"theme": "zero1-hindi-graphics", "label": "Zero1 Hindi", "form": "lf"},
        {"theme": "zero1-reel-graphics", "label": "Zero1 Reels", "form": "sf"},
    ]},
]


def hierarchy(available_themes: list[str]) -> dict:
    have = set(available_themes)
    chans = [{**c, "kits": [k for k in c["kits"] if k["theme"] in have]} for c in CHANNELS]
    return {"channels": [c for c in chans if c["kits"]]}


def channel_of(theme: str) -> str:
    return next((c["id"] for c in CHANNELS for k in c["kits"] if k["theme"] == theme), "")


def _db():
    from db_store import connect
    return connect()


def _ensure(c) -> None:
    c.execute(_SCHEMA)
    c.commit()


def link(la_project: str, project_id: int, la_name: str = "") -> None:
    if not LA_ID.match(str(la_project or "")):
        raise ValueError("bad LA project id")
    with _db() as c:
        _ensure(c)
        c.execute("delete from la_links where la_project=? or project_id=?", (la_project, int(project_id)))
        c.execute("insert into la_links(la_project,project_id,la_name,linked_at) values(?,?,?,?)",
                  (la_project, int(project_id), (la_name or "")[:120], time.time()))
        c.commit()


def unlink(la_project: str) -> None:
    with _db() as c:
        _ensure(c)
        c.execute("delete from la_links where la_project=?", (la_project,))
        c.commit()


def links() -> list[dict]:
    """Every linked project with what LA Studio shows on its step: frames made, kit, last change."""
    with _db() as c:
        _ensure(c)
        rows = c.execute(
            "select l.la_project, l.project_id, l.la_name, p.name, p.theme, p.spec, p.updated_at "
            "from la_links l join projects p on p.id = l.project_id"
        ).fetchall()
    out = []
    for r in rows:
        r = dict(r)
        try:
            frames = len((json.loads(r.pop("spec") or "null") or {}).get("frames") or [])
        except ValueError:
            frames = 0
        out.append({**r, "frames": frames, "channel": channel_of(r.get("theme") or "")})
    return out


def project_for(la_project: str) -> int | None:
    with _db() as c:
        _ensure(c)
        r = c.execute("select project_id from la_links where la_project=?", (la_project,)).fetchone()
    return int(r["project_id"]) if r else None

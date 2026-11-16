"""SQLite locally; Postgres on Render via DATABASE_URL."""
from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).parent
SQLITE_PATH = ROOT / "data" / "studio.db"

_SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    theme TEXT NOT NULL,
    script TEXT DEFAULT '',
    look TEXT DEFAULT '{}',
    storyboard TEXT DEFAULT '',
    spec TEXT,
    updated_by TEXT,
    updated_at DOUBLE PRECISION
);
CREATE TABLE IF NOT EXISTS versions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    spec TEXT,
    storyboard TEXT,
    author TEXT,
    note TEXT,
    ts DOUBLE PRECISION
);
"""

_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS projects(
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, theme TEXT, script TEXT,
    look TEXT, storyboard TEXT, spec TEXT, updated_by TEXT, updated_at REAL);
CREATE TABLE IF NOT EXISTS versions(
    id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INT, spec TEXT, storyboard TEXT,
    author TEXT, note TEXT, ts REAL);
"""


def database_url() -> str | None:
    raw = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("DATABASE_PRIVATE_URL")
        or os.environ.get("DATABASE_PUBLIC_URL")
        or os.environ.get("POSTGRES_URL")
        or ""
    ).strip()
    if not raw:
        return None
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql://", 1)
    return raw


def backend() -> str:
    return "postgres" if database_url() else "sqlite"


def _row_dict(row: Any) -> dict:
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    return dict(row)


class _Cursor:
    def __init__(self, cur, pg: bool):
        self._cur = cur
        self._pg = pg
        self.lastrowid: int | None = None

    def execute(self, sql: str, params: tuple = ()):
        if self._pg:
            sql = sql.replace("?", "%s")
        self._cur.execute(sql, params)
        if self._pg and "returning" in sql.lower():
            row = self._cur.fetchone()
            if row:
                self.lastrowid = row["id"] if isinstance(row, dict) else row[0]
        elif not self._pg:
            self.lastrowid = self._cur.lastrowid
        return self

    def fetchone(self):
        return _row_dict(self._cur.fetchone())

    def fetchall(self) -> list[dict]:
        return [_row_dict(r) for r in self._cur.fetchall()]


class _Conn:
    def __init__(self, raw, pg: bool):
        self._raw = raw
        self._pg = pg

    def execute(self, sql: str, params: tuple = ()) -> _Cursor:
        c = _Cursor(self._raw.cursor(), self._pg)
        c.execute(sql, params)
        return c

    def commit(self):
        self._raw.commit()

    def close(self):
        self._raw.close()


_SCHEMA_LOCK = threading.Lock()
_SCHEMA_DONE: set[str] = set()


def once(key: str, conn, fn) -> None:
    """Run a schema statement (CREATE TABLE IF NOT EXISTS …) once per process and database, not on every query:
    per-query DDL cost a round trip each time and could queue behind other sessions' locks."""
    k = f"{database_url() or SQLITE_PATH}:{key}"
    if k in _SCHEMA_DONE:
        return
    with _SCHEMA_LOCK:
        if k in _SCHEMA_DONE:
            return
        fn(conn)
        _SCHEMA_DONE.add(k)


def init_schema(conn: _Conn) -> None:
    if conn._pg:
        conn._raw.cursor().execute(_SCHEMA_PG)
        conn._raw.commit()
    else:
        conn._raw.executescript(_SCHEMA_SQLITE)


_POOL = None
_POOL_LOCK = threading.Lock()


def _pool(url: str):
    """A small pool of open Postgres connections shared by every request (STUDIO_DB_POOL, default 12).
    Opening a fresh TLS connection per query was slow, and many requests at once (a page of frame previews,
    several people) could pile up waiting for connections. None when psycopg_pool is not installed."""
    global _POOL
    if _POOL is None:
        with _POOL_LOCK:
            if _POOL is None:
                try:
                    from psycopg.rows import dict_row
                    from psycopg_pool import ConnectionPool
                except ImportError:
                    return None
                kwargs = {"row_factory": dict_row}
                if "sslmode=" not in url:
                    kwargs["connect_timeout"] = 30
                _POOL = ConnectionPool(url, min_size=1, max_size=int(os.environ.get("STUDIO_DB_POOL", "12")),
                                       kwargs=kwargs, timeout=60, max_idle=300,
                                       check=ConnectionPool.check_connection, open=True)
    return _POOL


@contextmanager
def connect() -> Iterator[_Conn]:
    url = database_url()
    if url:
        pool = _pool(url)
        if pool is not None:
            with pool.connection() as raw:        # commits on success, rolls back on error, returns it to the pool
                conn = _Conn(raw, True)
                once("core", conn, init_schema)
                yield conn
            return
        import psycopg
        from psycopg.rows import dict_row

        kwargs = {"row_factory": dict_row}
        if "sslmode=" not in url:
            kwargs["connect_timeout"] = 30
        raw = psycopg.connect(url, **kwargs)
        conn = _Conn(raw, True)
        once("core", conn, init_schema)
        try:
            yield conn
        finally:
            conn.close()
    else:
        SQLITE_PATH.parent.mkdir(exist_ok=True)
        raw = sqlite3.connect(SQLITE_PATH, timeout=30)
        raw.row_factory = sqlite3.Row
        raw.execute("pragma journal_mode=WAL")
        raw.execute("pragma busy_timeout=30000")
        conn = _Conn(raw, False)
        once("core", conn, init_schema)
        try:
            yield conn
        finally:
            conn.close()


def insert_project(name: str, theme: str, script: str, look_json: str, updated_by: str, updated_at: float) -> int:
    with connect() as c:
        if c._pg:
            cur = c.execute(
                "insert into projects(name,theme,script,look,updated_by,updated_at) "
                "values(?,?,?,?,?,?) returning id",
                (name, theme, script, look_json, updated_by, updated_at),
            )
        else:
            cur = c.execute(
                "insert into projects(name,theme,script,look,updated_by,updated_at) values(?,?,?,?,?,?)",
                (name, theme, script, look_json, updated_by, updated_at),
            )
        c.commit()
        if cur.lastrowid is None:
            raise RuntimeError("insert project failed: no id returned")
        return int(cur.lastrowid)

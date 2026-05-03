"""Surf — module-level SQLite connection + schema bootstrap.

`connect()` is decorated with `@st.cache_resource` (Plan 02-01 Task 8,
RESEARCH §11 Q8): under Streamlit's script-runner, every rerun of every
view returns the SAME `sqlite3.Connection` object instead of opening a
new file handle each time. The cache key is the function arguments —
the no-arg call (production path) shares one connection across the
session; tests passing `db_file=tmp_path/'…'` get their own.

Outside Streamlit's runtime (pytest), `@st.cache_resource` still
returns the same object on repeat calls (it just warns about the
missing ScriptRunContext). The identity check in
`tests/test_db_connection_cache_resource.py` confirms this.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import streamlit as st

DB_FILE = Path("~/.surf/user.sqlite").expanduser()
_SCHEMA_PATH = Path(__file__).with_name("schema") / "schema.sql"


@st.cache_resource
def connect(db_file: Path | None = None) -> sqlite3.Connection:
    """Open (or create) the user's SQLite DB, run schema, enable FK pragma.

    Cached singleton per Streamlit session: repeat calls with the same
    `db_file` return the same `sqlite3.Connection`. To swap the DB at
    runtime (e.g. tests rebinding to a tmp path), call
    `connect.clear()` first to evict the previous cache entry.
    """
    target = db_file or DB_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    return conn


# Module-level connection (per D-3.4). Tests should pass `db_file=tmp/'t.sqlite'`
# to `connect()` and rebind this DB symbol on the module before importing
# query wrappers, so the real ~/.surf/user.sqlite stays untouched.
DB: sqlite3.Connection = connect()

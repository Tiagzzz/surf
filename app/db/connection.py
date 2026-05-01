"""Surf — module-level SQLite connection + schema bootstrap."""
from __future__ import annotations

from pathlib import Path
import sqlite3

DB_FILE = Path("~/.surf/user.sqlite").expanduser()
_SCHEMA_PATH = Path(__file__).with_name("schema") / "schema.sql"


def connect(db_file: Path | None = None) -> sqlite3.Connection:
    """Open (or create) the user's SQLite DB, run schema, enable FK pragma."""
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

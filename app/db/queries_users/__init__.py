"""Surf — users query wrappers.

All helpers return ``dict | None`` or ``list[dict]``. Pandas is
deliberately not imported here — query helpers stay at the SQL boundary
and pandas only enters at preview/chart/ML layers if at all.

The new ``get_active_user()`` / ``has_saved_user()`` helpers are the
data source for ``app.brain.session.is_authenticated()``.
Neither helper logs or returns the API-key column to anywhere it would
be printed; callers must format only the fields they actually need.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This module talks to the `users` table. It imports the shared lazy `DB`
# proxy from `app.db.connection` and the connection module itself (so the
# `get_local_db_path()` helper can read the current path setting).
#
# Important code pieces:
# - `DB`: the lazy SQLite connection used for every read/write below.
# - `conn_mod`: the connection module, kept so display-only helpers can read
#   `DB_FILE` without taking a snapshot at import time.
from typing import Any

import app.db.connection as conn_mod
from app.db.connection import DB


# --------------------------------------------------------------------------- #
# ROW-TO-DICT HELPERS — KEEP QUERY OUTPUT PANDAS-FREE
# --------------------------------------------------------------------------- #
# Simple explanation:
# Two tiny converters that turn a `sqlite3` cursor result into plain Python
# `dict` (single row) or `list[dict]` (many rows). Per Surf's locked rule,
# pandas is intentionally NOT imported inside `queries_*`; charts and ML
# layers may convert to DataFrames if needed, but query helpers stay simple.
#
# Key detail:
# - `cur.description` lists `(name, ...)` tuples for each column; the helpers
#   pick the column names and `zip` them with the row values.
def _row_to_dict(cur) -> dict | None:
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def _rows_to_dicts(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# --------------------------------------------------------------------------- #
# USER CRUD — INSERT, UPSERT, READ, UPDATE, RESET-PATH HELPERS
# --------------------------------------------------------------------------- #
# Simple explanation:
# These functions are the only way Surf reads and writes the `users` table.
# Surf V1 is single-user, so most helpers expect 0 or 1 row to exist.
#
# Important code pieces:
# - `insert_user(...)`: low-level INSERT used by tests and `upsert_user_setup`.
#   The `with DB:` block opens a SQLite transaction and commits on exit.
# - `upsert_user_setup(...)`: P1 signup helper. Creates the single row, or if
#   one already exists, updates its username and saved key.
# - `get_user_by_id(...)`, `get_user_by_username(...)`, `list_users(...)`:
#   plain SELECT reads returned as `dict` / `list[dict]`.
# - `get_saved_anthropic_api_key(...)`: returns just the saved key column or
#   `None`; never used for printing or logging.
# - `get_active_user(...)`: returns the lowest-id user row; the session/auth
#   gate uses this to detect a saved user.
# - `update_display_name(...)`, `replace_anthropic_api_key(...)`: P7 settings
#   updates that touch one column each.
# - `get_local_db_path()`: returns the live DB path as a string for display
#   only; never returns or logs the saved API key.
# - `has_saved_user_with_key()`: cheap EXISTS-style probe used by the
#   authentication gate to decide whether the user is signed in.
#
# Key detail:
# - All SQL uses parameter placeholders (`?`), never string interpolation, so
#   user-typed usernames and keys can never inject SQL.
def insert_user(username: str, anthropic_api_key: str) -> int:
    with DB:
        cur = DB.execute(
            "INSERT INTO users (username, anthropic_api_key) VALUES (?, ?)",
            (username, anthropic_api_key),
        )
        return cur.lastrowid


def upsert_user_setup(username: str, anthropic_api_key: str) -> int:
    """Create the single Surf user or update the existing one.

    P1 setup is 0→1 in V1. If the row already exists, repeated setup updates
    that same lowest-id row instead of creating another user.
    """
    with DB:
        existing = DB.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
        if existing is None:
            cur = DB.execute(
                "INSERT INTO users (username, anthropic_api_key) VALUES (?, ?)",
                (username, anthropic_api_key),
            )
            return cur.lastrowid

        user_id = existing[0]
        DB.execute(
            "UPDATE users SET username = ?, anthropic_api_key = ? WHERE id = ?",
            (username, anthropic_api_key, user_id),
        )
        return user_id


def get_user_by_id(user_id: int) -> dict | None:
    return _row_to_dict(DB.execute("SELECT * FROM users WHERE id = ?", (user_id,)))


def get_saved_anthropic_api_key(user_id: int) -> str | None:
    """Return the saved key for exactly ``user_id`` or ``None`` on a miss."""
    row = DB.execute(
        "SELECT anthropic_api_key FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return row[0]


def get_user_by_username(username: str) -> dict | None:
    return _row_to_dict(
        DB.execute("SELECT * FROM users WHERE username = ?", (username,))
    )


def list_users() -> list[dict[str, Any]]:
    """Return all user rows ordered by id. Single-user app, so 0 or 1 row."""
    return _rows_to_dicts(DB.execute("SELECT * FROM users ORDER BY id"))


def get_active_user() -> dict | None:
    """Return the saved user row (or ``None``) for the session/auth gate.

    Surf V1 is single-user; ``users`` holds at most one row. This helper
    returns the lowest-id row to give a stable pick if the table ever has
    more than one entry. Caller must not log the ``anthropic_api_key`` field.
    """
    return _row_to_dict(DB.execute("SELECT * FROM users ORDER BY id LIMIT 1"))


def update_display_name(user_id: int, display_name: str) -> bool:
    """Update the V1 display-name field, stored as ``users.username``."""
    with DB:
        cur = DB.execute(
            "UPDATE users SET username = ? WHERE id = ?",
            (display_name, user_id),
        )
        return cur.rowcount > 0


def replace_anthropic_api_key(user_id: int, anthropic_api_key: str) -> bool:
    """Replace only the saved key for ``user_id`` after caller validation."""
    with DB:
        cur = DB.execute(
            "UPDATE users SET anthropic_api_key = ? WHERE id = ?",
            (anthropic_api_key, user_id),
        )
        return cur.rowcount > 0


def get_local_db_path() -> str:
    """Return the local DB path for display; never includes secret values."""
    return str(conn_mod.DB_FILE)


def has_saved_user_with_key() -> bool:
    """True iff at least one user row carries a non-blank Anthropic key.

    Used by ``app.brain.session.is_authenticated`` to gate authenticated
    pages on real saved-user/key state instead of DB-file existence
   . ``LENGTH(TRIM(...)) > 0`` excludes both NULL and whitespace.
    """
    cur = DB.execute(
        "SELECT 1 FROM users "
        "WHERE anthropic_api_key IS NOT NULL "
        "AND LENGTH(TRIM(anthropic_api_key)) > 0 "
        "LIMIT 1"
    )
    return cur.fetchone() is not None

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

from typing import Any

import app.db.connection as conn_mod
from app.db.connection import DB


def _row_to_dict(cur) -> dict | None:
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def _rows_to_dicts(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


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

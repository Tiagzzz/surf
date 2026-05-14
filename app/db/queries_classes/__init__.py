"""Surf — classes query wrappers (Phase 02-03 dict/list contract).

Pandas is deliberately NOT imported here. Helpers return
``dict | None`` (single-row) or ``list[dict]`` (lists). The factsheet JSON
column is decoded back to a Python dict in single-row reads; list reads
leave it as the raw JSON string so callers can decode lazily.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This module manages the `classes` table. It uses `json` because the
# `factsheet_json` column stores a Python dict serialized as JSON text.
#
# Important code pieces:
# - `json`: used to encode a dict on write and decode it back on a single-row
#   read.
# - `DB`: shared lazy SQLite connection. Some helpers also accept a `conn`
#   argument so unit tests can pass an explicit in-memory connection.
import json
from typing import Any

from app.db.connection import DB

__all__ = [
    "insert_class",
    "get_class_by_id",
    "list_classes_for_user",
    "get_class_pass_threshold",
    "delete_class_for_user",
]


# --------------------------------------------------------------------------- #
# ROW-TO-DICT HELPERS AND CONNECTION RESOLVER
# --------------------------------------------------------------------------- #
# Simple explanation:
# The two converters keep results as plain `dict`/`list[dict]` (no pandas).
# `_resolve_conn` lets callers pass an explicit connection or fall back to
# the shared `DB` lazy proxy.
def _row_to_dict(cur) -> dict | None:
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def _rows_to_dicts(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _resolve_conn(conn: Any | None):
    """Return the connection to use (caller-provided or the lazy default)."""
    return conn if conn is not None else DB


# --------------------------------------------------------------------------- #
# CLASS CRUD — INSERT, READ, LIST, PASS-THRESHOLD, OWNED DELETE
# --------------------------------------------------------------------------- #
# Simple explanation:
# These helpers create classes (P2 setup), read them back for P3/P6, expose
# the pass threshold the Swiss-grade formula needs, and own the class-delete
# path with ownership enforcement.
#
# Important code pieces:
# - `insert_class(...)`: serializes `factsheet_json` if it is a dict and
#   stores the new row. Returns the new SQLite row id.
# - `get_class_by_id(...)`: single-row read that also decodes the
#   `factsheet_json` text back into a Python dict.
# - `list_classes_for_user(...)`: lists all classes for one user; leaves the
#   factsheet JSON as raw text so callers decode only when needed.
# - `get_class_pass_threshold(...)`: returns the integer pass threshold
#   percent used by `compute_swiss_grade`.
# - `delete_class_for_user(...)`: DELETE that requires both the class id and
#   the owning user id to match. Cascading FKs clean up lectures, slide
#   pages, learning objectives, attempts, and answers.
def insert_class(
    user_id: int,
    name: str,
    factsheet_json: dict[str, Any] | str,
    pass_threshold_pct: int = 50,
) -> int:
    payload = factsheet_json if isinstance(factsheet_json, str) else json.dumps(factsheet_json)
    with DB:
        cur = DB.execute(
            "INSERT INTO classes (user_id, name, factsheet_json, pass_threshold_pct) "
            "VALUES (?, ?, ?, ?)",
            (user_id, name, payload, pass_threshold_pct),
        )
        return cur.lastrowid


def get_class_by_id(class_id: int) -> dict | None:
    cur = DB.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
    out = _row_to_dict(cur)
    if out is None:
        return None
    out["factsheet_json"] = json.loads(out["factsheet_json"])
    return out


def list_classes_for_user(user_id: int) -> list[dict]:
    cur = DB.execute(
        "SELECT * FROM classes WHERE user_id = ? ORDER BY id",
        (user_id,),
    )
    return _rows_to_dicts(cur)


def get_class_pass_threshold(
    class_id: int,
    *,
    conn: Any | None = None,
) -> int | None:
    """Return classes.pass_threshold_pct for one class, or None if missing/NULL."""
    db = _resolve_conn(conn)
    cur = db.execute(
        "SELECT pass_threshold_pct FROM classes WHERE id = ?",
        (class_id,),
    )
    row = cur.fetchone()
    if row is None or row[0] is None:
        return None
    return int(row[0])


def delete_class_for_user(user_id: int, class_id: int) -> dict[str, Any]:
    """Delete one owned class and its FK-cascaded graph.

    The page must collect confirmation first; this helper only enforces DB
    ownership so one user cannot delete another user's class.
    """
    with DB:
        cur = DB.execute(
            "DELETE FROM classes WHERE id = ? AND user_id = ?",
            (class_id, user_id),
        )
        return {"deleted": cur.rowcount > 0, "class_id": class_id}

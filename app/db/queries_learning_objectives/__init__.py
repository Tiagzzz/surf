"""Surf — learning_objectives query wrappers (Phase 02-03 dict/list contract).

Pandas is deliberately NOT imported here. Helpers return
``dict | None`` (single-row) or ``list[dict]`` (lists).
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Only the shared lazy `DB` is needed; learning-objective rows are plain
# columns with no JSON or external dependencies.
from app.db.connection import DB

__all__ = [
    "insert_learning_objective",
    "get_learning_objective_by_id",
    "list_learning_objectives_for_lecture",
]


def _row_to_dict(cur) -> dict | None:
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def _rows_to_dicts(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# --------------------------------------------------------------------------- #
# LEARNING-OBJECTIVE CRUD
# --------------------------------------------------------------------------- #
# Simple explanation:
# Learning objectives group slide pages into topics. These helpers create
# new LO rows during ingestion and read them back for ordered display.
#
# Important code pieces:
# - `insert_learning_objective(...)`: INSERT one row with the page range it
#   covers, returning the new SQLite row id.
# - `get_learning_objective_by_id(...)`: single-row read.
# - `list_learning_objectives_for_lecture(...)`: returns LOs ordered by
#   `page_start` so the UI shows them in lecture order.
def insert_learning_objective(
    lecture_id: int,
    title: str,
    page_start: int,
    page_end: int,
) -> int:
    with DB:
        cur = DB.execute(
            "INSERT INTO learning_objectives (lecture_id, title, page_start, page_end) "
            "VALUES (?, ?, ?, ?)",
            (lecture_id, title, page_start, page_end),
        )
        return cur.lastrowid


def get_learning_objective_by_id(lo_id: int) -> dict | None:
    cur = DB.execute("SELECT * FROM learning_objectives WHERE id = ?", (lo_id,))
    return _row_to_dict(cur)


def list_learning_objectives_for_lecture(lecture_id: int) -> list[dict]:
    cur = DB.execute(
        "SELECT * FROM learning_objectives WHERE lecture_id = ? ORDER BY page_start",
        (lecture_id,),
    )
    return _rows_to_dicts(cur)

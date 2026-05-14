"""Surf — slide_pages query wrappers (Phase 02-03 dict/list contract).

Pandas is deliberately NOT imported here. Helpers return
``dict | None`` (single-row) or ``list[dict]`` (lists).
"""
from __future__ import annotations

from app.db.connection import DB

__all__ = [
    "insert_slide_page",
    "get_slide_page_by_id",
    "list_slide_pages_for_lecture",
    "set_slide_page_status",
    "set_slide_page_learning_objective",
]


def _row_to_dict(cur) -> dict | None:
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def _rows_to_dicts(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def insert_slide_page(
    lecture_id: int,
    page_number: int,
    raw_md: str,
    status: str = "kept",
    learning_objective_id: int | None = None,
) -> int:
    with DB:
        cur = DB.execute(
            "INSERT INTO slide_pages "
            "(lecture_id, page_number, raw_md, status, learning_objective_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (lecture_id, page_number, raw_md, status, learning_objective_id),
        )
        return cur.lastrowid


def get_slide_page_by_id(slide_page_id: int) -> dict | None:
    cur = DB.execute("SELECT * FROM slide_pages WHERE id = ?", (slide_page_id,))
    return _row_to_dict(cur)


def list_slide_pages_for_lecture(lecture_id: int) -> list[dict]:
    cur = DB.execute(
        "SELECT * FROM slide_pages WHERE lecture_id = ? ORDER BY page_number",
        (lecture_id,),
    )
    return _rows_to_dicts(cur)


def set_slide_page_status(
    slide_page_id: int,
    status: str,
    learning_objective_id: int | None = None,
) -> None:
    with DB:
        DB.execute(
            "UPDATE slide_pages SET status = ?, learning_objective_id = ? WHERE id = ?",
            (status, learning_objective_id, slide_page_id),
        )


def set_slide_page_learning_objective(slide_page_id: int, learning_objective_id: int) -> None:
    with DB:
        DB.execute(
            "UPDATE slide_pages SET learning_objective_id = ? WHERE id = ?",
            (learning_objective_id, slide_page_id),
        )

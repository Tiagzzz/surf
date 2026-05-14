"""Surf — slide_pages query wrappers (Phase 02-03 dict/list contract).

Pandas is deliberately NOT imported here. Helpers return
``dict | None`` (single-row) or ``list[dict]`` (lists).
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Only the shared lazy `DB` is needed; slide-page rows store one Markdown
# blob per page and reference an optional learning objective.
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


# --------------------------------------------------------------------------- #
# SLIDE-PAGE CRUD AND STATUS UPDATES
# --------------------------------------------------------------------------- #
# Simple explanation:
# Slide pages are one row per slide of an uploaded lecture, with the
# extracted Markdown stored in `raw_md`. These helpers create rows during
# ingestion, read them back for question generation, and flip their status
# or LO assignment when needed.
#
# Important code pieces:
# - `insert_slide_page(...)`: INSERT one row with the extracted Markdown
#   and an optional learning-objective id.
# - `get_slide_page_by_id(...)`, `list_slide_pages_for_lecture(...)`: reads;
#   the list version is ordered by `page_number` so the UI keeps slides in
#   lecture order.
# - `set_slide_page_status(...)`: UPDATE both the status (`kept`, `skipped`,
#   etc.) and the LO assignment in one statement.
# - `set_slide_page_learning_objective(...)`: UPDATE only the LO column.
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

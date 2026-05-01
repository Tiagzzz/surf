"""Surf — slide_pages query wrappers."""
from __future__ import annotations

import pandas as pd

from app.db.connection import DB


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
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def list_slide_pages_for_lecture(lecture_id: int) -> "pd.DataFrame":
    return pd.read_sql(
        "SELECT * FROM slide_pages WHERE lecture_id = ? ORDER BY page_number",
        DB,
        params=(lecture_id,),
    )


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

"""Surf — learning_objectives query wrappers."""
from __future__ import annotations

import pandas as pd

from app.db.connection import DB


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
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def list_learning_objectives_for_lecture(lecture_id: int) -> "pd.DataFrame":
    return pd.read_sql(
        "SELECT * FROM learning_objectives WHERE lecture_id = ? ORDER BY page_start",
        DB,
        params=(lecture_id,),
    )

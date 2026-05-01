"""Surf — lectures query wrappers."""
from __future__ import annotations

import pandas as pd

from app.db.connection import DB


def insert_lecture(
    class_id: int,
    title: str,
    source_pdf_path: str,
    total_pages: int,
    status: str = "pending",
) -> int:
    with DB:
        cur = DB.execute(
            "INSERT INTO lectures (class_id, title, source_pdf_path, total_pages, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (class_id, title, source_pdf_path, total_pages, status),
        )
        return cur.lastrowid


def get_lecture_by_id(lecture_id: int) -> dict | None:
    cur = DB.execute("SELECT * FROM lectures WHERE id = ?", (lecture_id,))
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def list_lectures_for_class(class_id: int) -> "pd.DataFrame":
    return pd.read_sql(
        "SELECT * FROM lectures WHERE class_id = ? ORDER BY id",
        DB,
        params=(class_id,),
    )


def set_lecture_status(lecture_id: int, status: str) -> None:
    with DB:
        DB.execute("UPDATE lectures SET status = ? WHERE id = ?", (status, lecture_id))

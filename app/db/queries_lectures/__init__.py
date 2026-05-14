"""Surf — lectures query wrappers (Phase 02-03 dict/list contract).

Pandas is deliberately NOT imported here. Helpers return
``dict | None`` (single-row) or ``list[dict]`` (lists).
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Only the shared `DB` lazy proxy is needed; lectures are stored in plain
# columns (no JSON), so the standard library alone is enough.
from app.db.connection import DB

__all__ = [
    "insert_lecture",
    "get_lecture_by_id",
    "list_lectures_for_class",
    "set_lecture_status",
    "get_lecture_delete_summary",
    "delete_lecture_for_user",
]


# --------------------------------------------------------------------------- #
# ROW-TO-DICT HELPERS — PANDAS-FREE QUERY OUTPUT
# --------------------------------------------------------------------------- #
# Simple explanation:
# Convert raw SQLite cursor results into plain dicts / lists of dicts so the
# rest of the app never has to know cursor mechanics.
def _row_to_dict(cur) -> dict | None:
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def _rows_to_dicts(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# --------------------------------------------------------------------------- #
# LECTURE CRUD AND SAFE DELETE
# --------------------------------------------------------------------------- #
# Simple explanation:
# These helpers create lecture rows during PDF upload, read them back for
# P3/P6 dropdowns, flip lecture status during processing, and run the safety
# checks behind the P3/P6 lecture-delete dialog.
#
# Important code pieces:
# - `insert_lecture(...)`: INSERT a new lecture row with status (default
#   `'pending'`). Returns the new id used by ingestion.
# - `get_lecture_by_id(...)`, `list_lectures_for_class(...)`: simple reads.
# - `set_lecture_status(...)`: UPDATE the `status` column (`pending`,
#   `ready`, `failed`).
# - `get_lecture_delete_summary(...)`: JOIN-heavy SELECT that counts
#   questions and any attempt-answer rows referencing this lecture. The
#   `can_delete` flag is `True` only when there is zero attempt history.
# - `delete_lecture_for_user(...)`: refuses to delete when the summary says
#   the lecture is in use, then runs a DELETE that also checks user
#   ownership via the subquery on `classes`.
#
# Key detail:
# - The lecture delete intentionally blocks when attempts reference its
#   questions, matching the locked P3/P6 affordance.
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
    return _row_to_dict(cur)


def list_lectures_for_class(class_id: int) -> list[dict]:
    cur = DB.execute(
        "SELECT * FROM lectures WHERE class_id = ? ORDER BY id",
        (class_id,),
    )
    return _rows_to_dicts(cur)


def set_lecture_status(lecture_id: int, status: str) -> None:
    with DB:
        DB.execute("UPDATE lectures SET status = ? WHERE id = ?", (status, lecture_id))


def get_lecture_delete_summary(user_id: int, class_id: int, lecture_id: int) -> dict:
    cur = DB.execute(
        "SELECT "
        "l.id AS lecture_id, l.class_id, l.title, l.status, "
        "COUNT(DISTINCT q.id) AS question_count, "
        "COUNT(aa.id) AS used_answer_count, "
        "COUNT(DISTINCT aa.attempt_id) AS distinct_used_attempt_count "
        "FROM lectures l "
        "JOIN classes c ON l.class_id = c.id "
        "LEFT JOIN slide_pages sp ON sp.lecture_id = l.id "
        "LEFT JOIN questions q ON q.slide_page_id = sp.id "
        "LEFT JOIN attempt_answers aa ON aa.question_id = q.id "
        "WHERE c.user_id = ? AND c.id = ? AND l.id = ? "
        "GROUP BY l.id, l.class_id, l.title, l.status",
        (user_id, class_id, lecture_id),
    )
    row = _row_to_dict(cur)
    if row is None:
        return {
            "ownership": False,
            "lecture_id": lecture_id,
            "class_id": class_id,
            "title": None,
            "status": None,
            "question_count": 0,
            "used_answer_count": 0,
            "distinct_used_attempt_count": 0,
            "can_delete": False,
            "blocker_reason": "not_owned",
        }

    used_answer_count = int(row["used_answer_count"] or 0)
    can_delete = used_answer_count == 0
    return {
        "ownership": True,
        "lecture_id": row["lecture_id"],
        "class_id": row["class_id"],
        "title": row["title"],
        "status": row["status"],
        "question_count": int(row["question_count"] or 0),
        "used_answer_count": used_answer_count,
        "distinct_used_attempt_count": int(row["distinct_used_attempt_count"] or 0),
        "can_delete": can_delete,
        "blocker_reason": None if can_delete else "attempt_history_exists",
    }


def delete_lecture_for_user(user_id: int, class_id: int, lecture_id: int) -> dict:
    summary = get_lecture_delete_summary(user_id, class_id, lecture_id)
    if not summary["ownership"]:
        return {
            "deleted": False,
            "lecture_id": lecture_id,
            "class_id": class_id,
            "reason": "not_owned",
        }
    if not summary["can_delete"]:
        return {
            "deleted": False,
            "lecture_id": lecture_id,
            "class_id": class_id,
            "reason": summary["blocker_reason"],
        }

    with DB:
        cur = DB.execute(
            "DELETE FROM lectures "
            "WHERE id = ? "
            "AND class_id = (SELECT id FROM classes WHERE id = ? AND user_id = ?)",
            (lecture_id, class_id, user_id),
        )
    return {
        "deleted": cur.rowcount == 1,
        "lecture_id": lecture_id,
        "class_id": class_id,
        "reason": None if cur.rowcount == 1 else "not_owned",
    }

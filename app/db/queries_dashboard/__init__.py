"""Surf — dashboard aggregate query helpers.

Real-data aggregates for P6 dashboard / Study Next, computed from the
stored `attempts`, `attempt_answers`, `questions`, `slide_pages`,
`learning_objectives`, and `lectures` rows. NO direct UI entrypoint calls,
NO table-only helper libraries, NO chart rendering, NO fake/sample analytics —
this module returns plain Python dicts and ``list[dict]`` only. Production
dashboard code imports these helpers and renders them; demo fixtures live outside
the app package, and helpers never trigger application initialization.

Dashboard formulas:

* ``get_mock_grade_metrics(class_id, *, limit=4)`` — last completed mock
  grade, average Swiss grade over the last ``limit`` completed mock
  attempts (newest first), and ``mock_count`` for the
  "Based on N of 4 mocks" copy. Practice attempts and unfinished mocks
  are deliberately excluded.
* ``get_coverage_summary(class_id)`` — generated-question coverage
  buckets across finished mock + practice attempts; skipped counts as
  wrong. Unfinished attempt rows are ignored.
* ``get_completion_donut_summary(class_id)`` — denominator is all
  generated questions for the class; slices are latest correct, latest
  wrong/skipped, and not covered (denominator includes untouched questions).
* ``list_lectures_for_class(class_id)`` — all uploaded lectures for class
  dropdowns/history, ordered by upload order.
* ``list_lecture_performance_series(class_id, *, limit=4)`` — per-lecture
  performance points from the last completed mock attempts only, including
  lecture-level percent correct and Swiss grade conversion.
* ``get_weakest_learning_objectives(class_id, *, limit=5)`` — LO ranking
  by error rate using the latest answer per generated question (mock or
  practice), with skipped counted wrong.
* ``get_lecture_mock_averages(class_id, *, limit=4)`` — per-lecture
  question-weighted average Swiss grade across the last ``limit``
  completed mock attempts the lecture's questions appeared in. If a mock
  includes more questions from a lecture, that mock weighs more for that
  lecture.
* ``get_question_type_performance_for_class(class_id)`` — real attempted
  and correct counts grouped by stored ``question_type``. No fake rows
  are returned when there are no finished answers.
"""
# Compute dashboard metrics from submitted attempts without rendering charts.
from __future__ import annotations

from typing import Any

from app.brain.grading_formula import compute_swiss_grade
from app.db.connection import DB

__all__ = [
    "get_mock_grade_metrics",
    "get_coverage_summary",
    "get_weakest_learning_objectives",
    "get_lecture_mock_averages",
    "get_question_type_performance_for_class",
    "get_completion_donut_summary",
    "list_lectures_for_class",
    "list_lecture_performance_series",
]


def _resolve_conn(conn: Any | None):
    return conn if conn is not None else DB


# ---------------------------------------------------------------------------
# get_mock_grade_metrics
# ---------------------------------------------------------------------------

def get_mock_grade_metrics(
    class_id: int,
    *,
    limit: int = 4,
    conn: Any | None = None,
) -> dict:
    """Last completed mock grade + average over last ``limit`` completed mocks.

    Returns a dict with keys ``mock_count``, ``last_grade``,
    ``class_average``. ``mock_count`` is the total number of completed
    mock attempts for the class (used by the
    "Based on N of 4 mocks" partial-count copy). When no completed mock
    attempts exist, ``last_grade`` and ``class_average`` are ``None``.
    """
    # Use completed mock attempts only; practice answers do not affect grade cards.
    db = _resolve_conn(conn)

    # mock_count: total completed mock attempts (regardless of limit window).
    total_row = db.execute(
        "SELECT COUNT(*) FROM attempts "
        "WHERE class_id = ? AND mock_kind = 'mock' "
        "AND finished_at IS NOT NULL AND swiss_grade IS NOT NULL",
        (class_id,),
    ).fetchone()
    mock_count = int(total_row[0]) if total_row else 0

    if mock_count == 0:
        return {
            "mock_count": 0,
            "last_grade": None,
            "class_average": None,
        }

    # Last `limit` completed mock attempts, newest first (finished_at DESC, id DESC).
    cur = db.execute(
        "SELECT swiss_grade FROM attempts "
        "WHERE class_id = ? AND mock_kind = 'mock' "
        "AND finished_at IS NOT NULL AND swiss_grade IS NOT NULL "
        "ORDER BY finished_at DESC, id DESC "
        "LIMIT ?",
        (class_id, int(limit)),
    )
    grades = [float(r[0]) for r in cur.fetchall()]
    last_grade = grades[0] if grades else None
    class_average = (sum(grades) / len(grades)) if grades else None

    return {
        "mock_count": mock_count,
        "last_grade": last_grade,
        "class_average": class_average,
    }


# ---------------------------------------------------------------------------
# get_coverage_summary
# ---------------------------------------------------------------------------

def get_coverage_summary(class_id: int, conn: Any | None = None) -> dict:
    """Generated-question coverage buckets for the class.

    Buckets (denominator = generated questions for the class):
      * ``correct_at_least_once`` — at least one finished answer (mock or
        practice) had ``is_correct = 1``.
      * ``attempted_never_correct`` — at least one finished answer
        exists but none correct. Skipped rows count as attempted (and
        wrong).
      * ``never_attempted`` — no answer rows in any finished attempt.

    Any orphan/unfinished attempt rows are ignored even if an
    ``attempt_answers`` row exists, because V1 coverage is only based on
    submitted attempts.
    """
    # Count every generated question into exactly one coverage bucket.
    db = _resolve_conn(conn)
    sql = (
        "SELECT q.id AS question_id, "
        "       MAX(CASE WHEN t.id IS NOT NULL THEN 1 ELSE 0 END) AS attempted, "
        "       MAX(CASE WHEN t.id IS NOT NULL THEN COALESCE(a.is_correct, 0) "
        "                ELSE 0 END) AS ever_correct "
        "FROM questions q "
        "JOIN slide_pages sp ON sp.id = q.slide_page_id "
        "JOIN lectures l     ON l.id  = sp.lecture_id "
        "LEFT JOIN attempt_answers a ON a.question_id = q.id "
        "LEFT JOIN attempts t        ON t.id = a.attempt_id "
        "                             AND t.class_id = ? "
        "                             AND t.finished_at IS NOT NULL "
        "WHERE l.class_id = ? "
        "GROUP BY q.id"
    )
    rows = db.execute(sql, (class_id, class_id)).fetchall()

    total = len(rows)
    correct_at_least_once = 0
    attempted_never_correct = 0
    never_attempted = 0
    for _qid, attempted, ever_correct in rows:
        if ever_correct == 1:
            correct_at_least_once += 1
        elif attempted == 1:
            attempted_never_correct += 1
        else:
            never_attempted += 1

    return {
        "total_questions": total,
        "correct_at_least_once": correct_at_least_once,
        "attempted_never_correct": attempted_never_correct,
        "never_attempted": never_attempted,
    }


# ---------------------------------------------------------------------------
# get_completion_donut_summary
# ---------------------------------------------------------------------------


def get_completion_donut_summary(class_id: int, conn: Any | None = None) -> dict:
    """Return the latest-answer coverage donut buckets for `class_id`.

    Buckets (latest-answer semantics):
      * ``latest_correct`` — latest finished answer for the question is correct.
      * ``latest_wrong_or_skipped`` — latest finished answer exists but is
        wrong (skipped answers are already encoded as wrong).
      * ``not_covered`` — no finished mock/practice answer exists.

    Denominator for all buckets is all generated questions for the class, not
    just answered questions.
    """
    # Classify each generated question by its latest finished answer.
    db = _resolve_conn(conn)

    # latest finished answer row per generated question (mock + practice).
    sql = (
        "WITH latest AS ("
        "    SELECT a.question_id, a.is_correct "
        "    FROM attempt_answers a "
        "    JOIN attempts t ON t.id = a.attempt_id "
        "    WHERE t.class_id = ? "
        "      AND t.finished_at IS NOT NULL "
        "      AND a.id IN ("
        "          SELECT MAX(a2.id)"
        "          FROM attempt_answers a2 "
        "          JOIN attempts t2 ON t2.id = a2.attempt_id "
        "          WHERE t2.class_id = ? AND t2.finished_at IS NOT NULL "
        "          GROUP BY a2.question_id"
        "      )"
        ")"
        "SELECT q.id AS question_id, "
        "       MAX(CASE WHEN latest.question_id IS NOT NULL THEN 1 ELSE 0 END) AS covered,"
        "       MAX(CASE WHEN latest.is_correct = 1 THEN 1 ELSE 0 END) AS latest_correct "
        "FROM questions q "
        "JOIN slide_pages sp ON sp.id = q.slide_page_id "
        "JOIN lectures l     ON l.id = sp.lecture_id "
        "LEFT JOIN latest ON latest.question_id = q.id "
        "WHERE l.class_id = ? "
        "GROUP BY q.id"
    )
    rows = db.execute(sql, (class_id, class_id, class_id)).fetchall()

    total_questions = len(rows)
    latest_correct = 0
    latest_wrong_or_skipped = 0
    for _qid, covered, was_correct in rows:
        if covered:
            if was_correct:
                latest_correct += 1
            else:
                latest_wrong_or_skipped += 1

    return {
        "total_questions": total_questions,
        "latest_correct": latest_correct,
        "latest_wrong_or_skipped": latest_wrong_or_skipped,
        "not_covered": max(total_questions - latest_correct - latest_wrong_or_skipped, 0),
    }


# ---------------------------------------------------------------------------
# list_lectures_for_class
# ---------------------------------------------------------------------------

def list_lectures_for_class(class_id: int, conn: Any | None = None) -> list[dict]:
    """Return all uploaded lectures for the class, ordered by id.

    This helper is intentionally narrow: it is the source for the P6 lecture
    dropdown and must include every uploaded lecture so the user can launch a
    new attempt even when no analytics exist yet.
    """
    # Return all class lectures, including those with no finished analytics yet.
    db = _resolve_conn(conn)
    rows = db.execute(
        "SELECT id, title, source_pdf_path, total_pages, status "
        "FROM lectures WHERE class_id = ? ORDER BY id ASC",
        (class_id,),
    ).fetchall()

    return [
        {
            "lecture_id": int(row[0]),
            "title": row[1],
            "source_pdf_path": row[2],
            "total_pages": int(row[3]),
            "status": row[4],
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# list_lecture_performance_series
# ---------------------------------------------------------------------------


def _resolve_pass_threshold(db, class_id: int) -> int:
    """Resolve class pass threshold with safe default on unknown classes."""
    threshold_row = db.execute(
        "SELECT pass_threshold_pct FROM classes WHERE id = ?",
        (class_id,),
    ).fetchone()
    if threshold_row is None:
        return 50
    return int(threshold_row[0])


def list_lecture_performance_series(
    class_id: int,
    *,
    limit: int = 4,
    conn: Any | None = None,
) -> list[dict]:
    """Return per-lecture mock performance series for the class.

    For each lecture the series contains only performance points from the last
    ``limit`` completed mock attempts. Each point stores the lecture-local
    percent correct and Swiss grade. Attempts with no question from the lecture
    are skipped.

    Returns:
    [
        {
            "lecture_id": int,
            "title": str,
            "performance": [
                {
                    "attempt_id": int,
                    "attempt_position": int,
                    "correct_count": int,
                    "attempted_count": int,
                    "percent_correct": float,
                    "swiss_grade": float,
                },
                ...,
            ],
        },
        ...
    ]
    """
    # Build lecture-local chart points from the last completed mock attempts.
    db = _resolve_conn(conn)

    # Limit to the last `limit` completed mock attempts only.
    last_attempts = db.execute(
        "SELECT id, finished_at FROM attempts "
        "WHERE class_id = ? AND mock_kind = 'mock' "
        "AND finished_at IS NOT NULL AND swiss_grade IS NOT NULL "
        "ORDER BY finished_at DESC, id DESC LIMIT ?",
        (class_id, int(limit)),
    ).fetchall()
    if not last_attempts:
        return []

    attempt_ids = [int(row[0]) for row in last_attempts]
    attempt_position = {
        attempt_id: idx + 1 for idx, attempt_id in enumerate(attempt_ids)
    }

    placeholders = ",".join("?" for _ in attempt_ids)
    rows = db.execute(
        "SELECT l.id AS lecture_id, l.title AS title, "
        "       t.id AS attempt_id, "
        "       COUNT(a.id) AS attempted_count, "
        "       SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) AS correct_count "
        "FROM lectures l "
        "JOIN slide_pages sp ON sp.lecture_id = l.id "
        "JOIN questions q ON q.slide_page_id = sp.id "
        "JOIN attempt_answers a ON a.question_id = q.id "
        "JOIN attempts t ON t.id = a.attempt_id "
        f"WHERE l.class_id = ? AND t.id IN ({placeholders}) "
        "GROUP BY l.id, l.title, t.id "
        "ORDER BY l.id ASC, t.finished_at DESC, t.id DESC",
        (class_id, *attempt_ids),
    ).fetchall()

    lecture_map: dict[int, list[dict]] = {}
    for lecture_id, title, attempt_id, attempted_count, correct_count in rows:
        attempted = int(attempted_count or 0)
        if attempted == 0:
            continue
        correct = int(correct_count or 0)
        percent = (correct / attempted) * 100.0
        grade = compute_swiss_grade(
            correct,
            attempted,
            _resolve_pass_threshold(db, class_id),
        )
        lecture_row = lecture_map.setdefault(
            int(lecture_id),
            {
                "lecture_id": int(lecture_id),
                "title": title,
                "performance": [],
            },
        )
        lecture_row["performance"].append(
            {
                "attempt_id": int(attempt_id),
                "attempt_position": int(attempt_position[int(attempt_id)]),
                "correct_count": correct,
                "attempted_count": attempted,
                "percent_correct": percent,
                "swiss_grade": grade,
            }
        )

    # Preserve deterministic order (as seen by dropdown and chart renderers).
    return [
        lecture_map[lecture_id]
        for lecture_id in sorted(lecture_map.keys())
        if lecture_map[lecture_id]["performance"]
    ]


# ---------------------------------------------------------------------------
# get_weakest_learning_objectives
# ---------------------------------------------------------------------------

def get_weakest_learning_objectives(
    class_id: int,
    *,
    limit: int = 5,
    conn: Any | None = None,
) -> list[dict]:
    """Return LOs ranked by error rate (worst first).

    Uses the latest finished answer per generated question across mock
    AND practice (practice affects Study Next per the V1 lock). Skipped
    answers count as wrong because their stored ``is_correct`` is
    already ``0``. LO is determined via
    ``slide_pages.learning_objective_id`` for the question's parent
    slide.

    Each row: ``{lo_id, lo_title, lecture_id, answered_count,
    wrong_count, error_rate}``. ``error_rate`` is in ``[0.0, 1.0]``.
    """
    # Rank learning objectives by latest-answer error rate for Study Next.
    db = _resolve_conn(conn)
    # latest_answers picks one answer row per question_id (the one with
    # the largest attempt_answers.id, breaking ties on the underlying
    # auto-increment id). The outer query joins back to slide_pages and
    # learning_objectives to attribute each question to its LO.
    sql = (
        "WITH latest AS ( "
        "  SELECT a.question_id, a.is_correct "
        "  FROM attempt_answers a "
        "  JOIN attempts t ON t.id = a.attempt_id "
        "  WHERE t.class_id = ? AND t.finished_at IS NOT NULL "
        "  AND a.id IN ( "
        "    SELECT MAX(a2.id) FROM attempt_answers a2 "
        "    JOIN attempts t2 ON t2.id = a2.attempt_id "
        "    WHERE t2.class_id = ? AND t2.finished_at IS NOT NULL "
        "    GROUP BY a2.question_id "
        "  ) "
        ") "
        "SELECT lo.id AS lo_id, lo.title AS lo_title, lo.lecture_id AS lecture_id, "
        "       COUNT(latest.question_id) AS answered_count, "
        "       SUM(CASE WHEN latest.is_correct = 0 THEN 1 ELSE 0 END) AS wrong_count "
        "FROM learning_objectives lo "
        "JOIN lectures l ON l.id = lo.lecture_id "
        "JOIN slide_pages sp ON sp.learning_objective_id = lo.id "
        "JOIN questions q ON q.slide_page_id = sp.id "
        "JOIN latest ON latest.question_id = q.id "
        "WHERE l.class_id = ? "
        "GROUP BY lo.id, lo.title, lo.lecture_id "
        "ORDER BY (CAST(SUM(CASE WHEN latest.is_correct = 0 THEN 1 ELSE 0 END) AS REAL) "
        "          / NULLIF(COUNT(latest.question_id), 0)) DESC, lo.id ASC "
        "LIMIT ?"
    )
    rows = db.execute(sql, (class_id, class_id, class_id, int(limit))).fetchall()
    out: list[dict] = []
    for lo_id, lo_title, lecture_id, answered_count, wrong_count in rows:
        answered = int(answered_count)
        wrong = int(wrong_count or 0)
        error_rate = (wrong / answered) if answered > 0 else 0.0
        out.append(
            {
                "lo_id": int(lo_id),
                "lo_title": lo_title,
                "lecture_id": int(lecture_id),
                "answered_count": answered,
                "wrong_count": wrong,
                "error_rate": error_rate,
            }
        )
    return out


# ---------------------------------------------------------------------------
# get_lecture_mock_averages
# ---------------------------------------------------------------------------

def get_lecture_mock_averages(
    class_id: int,
    *,
    limit: int = 4,
    conn: Any | None = None,
) -> list[dict]:
    """Question-weighted per-lecture grade average across last ``limit`` mocks.

    Picks the last ``limit`` completed mock attempts (newest first),
    then for each lecture whose questions appeared in any of those
    attempts, averages the attempt-level ``swiss_grade`` once per
    question-answer row. This is intentionally question-weighted: if a
    mock had more questions from a lecture, that mock has more influence
    on that lecture's average. ``mock_count`` remains the number of
    distinct attempts that touched the lecture.

    Returns a list of dicts ``{lecture_id, lecture_title, mock_count,
    avg_swiss_grade}`` ordered by lecture_id ASC.
    """
    # Average grades per lecture using the last completed mock window.
    db = _resolve_conn(conn)
    # Materialize the last `limit` mock attempts (newest first).
    last_mocks = db.execute(
        "SELECT id, swiss_grade FROM attempts "
        "WHERE class_id = ? AND mock_kind = 'mock' "
        "AND finished_at IS NOT NULL AND swiss_grade IS NOT NULL "
        "ORDER BY finished_at DESC, id DESC "
        "LIMIT ?",
        (class_id, int(limit)),
    ).fetchall()
    if not last_mocks:
        return []

    attempt_ids = [int(r[0]) for r in last_mocks]
    placeholders = ",".join("?" for _ in attempt_ids)
    sql = (
        "SELECT l.id AS lecture_id, l.title AS lecture_title, "
        "       COUNT(DISTINCT t.id) AS mock_count, "
        "       AVG(t.swiss_grade) AS avg_swiss_grade "
        "FROM lectures l "
        "JOIN slide_pages sp ON sp.lecture_id = l.id "
        "JOIN questions q ON q.slide_page_id = sp.id "
        "JOIN attempt_answers a ON a.question_id = q.id "
        "JOIN attempts t ON t.id = a.attempt_id "
        f"WHERE l.class_id = ? AND t.id IN ({placeholders}) "
        "GROUP BY l.id, l.title "
        "ORDER BY l.id ASC"
    )
    rows = db.execute(sql, (class_id, *attempt_ids)).fetchall()
    out: list[dict] = []
    for lecture_id, lecture_title, mock_count, avg in rows:
        out.append(
            {
                "lecture_id": int(lecture_id),
                "lecture_title": lecture_title,
                "mock_count": int(mock_count),
                "avg_swiss_grade": float(avg) if avg is not None else None,
            }
        )
    return out


# ---------------------------------------------------------------------------
# get_question_type_performance_for_class
# ---------------------------------------------------------------------------

def get_question_type_performance_for_class(
    class_id: int,
    conn: Any | None = None,
) -> list[dict]:
    """Real finished-answer counts grouped by stored question type.

    This narrow P6 handoff can be computed from
    existing rows without any ML, difficulty profile, or fake/sample
    analytics. Both completed mock and practice attempts count. Unfinished
    attempts are ignored.
    """
    # Group real finished answers by canonical stored question type.
    db = _resolve_conn(conn)
    sql = (
        "SELECT q.question_type, "
        "       COUNT(a.id) AS attempted_count, "
        "       SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) AS correct_count "
        "FROM attempt_answers a "
        "JOIN attempts t ON t.id = a.attempt_id "
        "JOIN questions q ON q.id = a.question_id "
        "WHERE t.class_id = ? AND t.finished_at IS NOT NULL "
        "GROUP BY q.question_type "
        "ORDER BY q.question_type ASC"
    )
    rows = db.execute(sql, (class_id,)).fetchall()
    out: list[dict] = []
    for question_type, attempted_count, correct_count in rows:
        attempted = int(attempted_count or 0)
        correct = int(correct_count or 0)
        out.append(
            {
                "question_type": question_type,
                "attempted_count": attempted,
                "correct_count": correct,
                "accuracy": (correct / attempted) if attempted else None,
            }
        )
    return out

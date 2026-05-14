"""Surf — final-submit-only attempt persistence and review query helpers.

Public surface:
    - ``finalize_attempt(...)``      — atomic all-or-nothing write of one
      attempt row plus one ``attempt_answers`` row per frozen question.
    - ``get_attempt_summary(...)``   — single-row dict for P5 review header.
    - ``get_attempt_review_rows(...)`` — answer rows in original `position`
      order for P5 review.
    - ``list_completed_attempts_for_class(...)`` — P6 dashboard helper.
    - ``latest_answer_per_question_for_class(...)`` — Study Next helper:
      latest answer per generated question (mock OR practice).

Rules enforced (no `start_attempt`, no `record_answer`):
    - Exact-match grading via ``app.brain.grading_formula``; skipped
      questions are wrong with empty selected_indices.
    - NO durable draft attempt persistence. Answering stays in
      session state until ``finalize_attempt(...)`` writes once.
    - One explicit SQLite transaction (BEGIN -> INSERT attempt ->
      INSERT all answers -> UPDATE summary -> COMMIT). On any failure, the
      whole transaction rolls back so partial rows cannot exist.
    - 1-based ``position`` on every answer row preserves the order the
      user actually saw the questions; canonical ``selected_indices`` JSON.
    - Rejects duplicate selected_indices before write.

Pandas is deliberately NOT imported here. Helpers return
``dict | None`` or ``list[dict]``.
"""
# Persist attempts only at final submit and read them back as plain dicts.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This module owns the `attempts` and `attempt_answers` tables. It uses
# `json` because `selected_indices` is stored as JSON text per the V1 lock,
# `sqlite3` directly to take manual control of one explicit transaction, and
# the shared grading helpers to compute correctness and the Swiss grade.
#
# Important code pieces:
# - `compute_swiss_grade`: maps `(correct, total, pass_threshold_pct)` to a
#   Swiss grade in the 1.00–6.00 range.
# - `is_exact_match`: True only when the user's selection equals the stored
#   correct set; skipped answers grade as wrong by contract.
import json
import sqlite3
from typing import Any, Iterable

from app.brain.grading_formula import compute_swiss_grade, is_exact_match
from app.db.connection import DB

__all__ = [
    "finalize_attempt",
    "get_attempt_summary",
    "get_attempt_review_rows",
    "list_completed_attempts_for_class",
    "latest_answer_per_question_for_class",
    "list_personal_difficulty_examples_for_class",
]

_VALID_MOCK_KINDS = ("mock", "practice")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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


def _all_unique(seq: Iterable[int]) -> bool:
    items = list(seq)
    return len(set(items)) == len(items)


# --------------------------------------------------------------------------- #
# PRE-WRITE VALIDATION FOR FINAL SUBMIT
# --------------------------------------------------------------------------- #
# Simple explanation:
# Before any attempt row touches SQLite, this helper checks the shape of the
# user's submitted answers. Every contract break raises `ValueError` with a
# specific message so the page can show what went wrong.
#
# Key detail:
# - Selected indices must be `int` (booleans explicitly excluded), unique,
#   and inside `0..3` since every MCQ has exactly four options.
def _validate_finalize_inputs(
    *,
    class_id: int,
    mock_kind: str,
    question_ids: list[int],
    answers_by_question_id: dict[int, list[int]],
    skipped_question_ids: set[int],
) -> None:
    """Pre-write validation; raises ``ValueError`` on contract violations."""
    if mock_kind not in _VALID_MOCK_KINDS:
        raise ValueError(
            f"mock_kind must be one of {_VALID_MOCK_KINDS}, got {mock_kind!r}"
        )
    if not isinstance(class_id, int) or class_id <= 0:
        raise ValueError("class_id must be a positive integer")
    if not question_ids:
        raise ValueError("question_ids must contain at least one question id")
    if len(set(question_ids)) != len(question_ids):
        raise ValueError("question_ids must not contain duplicates")

    # Every non-skipped question must have an answer entry; selected indices
    # must be unique and within 0..3 (4-option MCQ shape).
    for qid in question_ids:
        if qid in skipped_question_ids:
            continue
        if qid not in answers_by_question_id:
            raise ValueError(f"missing answer for question_id={qid}")
        sel = answers_by_question_id[qid]
        if not isinstance(sel, list):
            raise ValueError(f"selected_indices for q{qid} must be a list")
        if not all(isinstance(i, int) and not isinstance(i, bool) for i in sel):
            raise ValueError(f"selected_indices for q{qid} must be ints")
        if any(i < 0 or i >= 4 for i in sel):
            raise ValueError(f"selected_indices for q{qid} out of 0..3")
        if not _all_unique(sel):  # stored selections must not contain duplicates
            raise ValueError(
                f"selected_indices for q{qid} must be unique (got {sel})"
            )


# ---------------------------------------------------------------------------
# finalize_attempt — atomic write
# ---------------------------------------------------------------------------

# --------------------------------------------------------------------------- #
# FINAL SUBMIT — `finalize_attempt`
# --------------------------------------------------------------------------- #
# Simple explanation:
# The one moment Surf actually persists an attempt. Everything before this
# call lives only in Streamlit session state. On final submit, this function
# runs a single SQLite transaction that:
#   1. INSERTs one row into `attempts`,
#   2. INSERTs one row into `attempt_answers` per question (in their
#      original 1-based `position`),
#   3. UPDATEs the attempt summary with totals, percent, and Swiss grade.
# If any step fails, the whole transaction rolls back so the database can
# never contain a half-written attempt.
#
# Important code pieces:
# - `raw_conn.isolation_level = None`: switches SQLite into manual
#   transaction mode so we can issue explicit `BEGIN` / `COMMIT` /
#   `ROLLBACK` statements.
# - `is_exact_match(...)`: grades each answer; skipped questions store an
#   empty list and grade as wrong.
# - `compute_swiss_grade(...)`: turns correct/total + the class threshold
#   into the Swiss grade saved alongside the percent.
# - The `try` / `except` / `finally` block restores the prior isolation
#   level no matter what.
#
# App connection:
# P4 calls this exactly once when the user presses the final submit. P5
# review and P6 dashboard then read what this function persisted.
def finalize_attempt(
    *,
    class_id: int,
    mock_kind: str,
    question_ids: list[int],
    answers_by_question_id: dict[int, list[int]],
    skipped_question_ids: set[int] | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    submit_token: str | None = None,  # reserved; no idempotency table in V1
    conn: Any | None = None,
) -> dict:
    """Persist one attempt + all answer rows atomically.

    Returns a dict containing at least ``attempt_id``, ``class_id``,
    ``mock_kind``, ``correct_count``, ``total_count``, ``score_pct``,
    ``swiss_grade``, ``skipped_count``, ``finished_at``.

    Raises ``ValueError`` for contract violations and propagates DB errors
    after a full rollback.
    """
    # Validate, grade, insert answers, and update the attempt summary in one transaction.
    skipped = set(skipped_question_ids) if skipped_question_ids else set()
    _validate_finalize_inputs(
        class_id=class_id,
        mock_kind=mock_kind,
        question_ids=question_ids,
        answers_by_question_id=answers_by_question_id,
        skipped_question_ids=skipped,
    )

    db = _resolve_conn(conn)

    # Resolve class pass threshold (Swiss-grade boundary input).
    threshold_row = db.execute(
        "SELECT pass_threshold_pct FROM classes WHERE id = ?",
        (class_id,),
    ).fetchone()
    if threshold_row is None:
        raise ValueError(f"class_id {class_id} not found")
    pass_threshold_pct = int(threshold_row[0])

    # Pre-load each question's correct_indices in one batch so grading runs
    # inside the transaction window with no extra DB round-trips per row.
    placeholders = ",".join("?" for _ in question_ids)
    cur = db.execute(
        f"SELECT id, correct_indices FROM questions WHERE id IN ({placeholders})",
        tuple(question_ids),
    )
    correct_by_qid: dict[int, list[int]] = {}
    for qid, ci_json in cur.fetchall():
        correct_by_qid[int(qid)] = json.loads(ci_json)
    missing = [qid for qid in question_ids if qid not in correct_by_qid]
    if missing:
        raise ValueError(f"unknown question_ids: {missing}")

    # Single explicit transaction: BEGIN -> INSERT attempt -> INSERT answers
    # -> UPDATE attempt summary -> COMMIT. On any failure: ROLLBACK and
    # re-raise so callers see the original error.
    raw_conn = _underlying_sqlite(db)
    prior_isolation = raw_conn.isolation_level
    raw_conn.isolation_level = None
    try:
        raw_conn.execute("BEGIN")

        # 1) attempt row
        attempt_cur = raw_conn.execute(
            "INSERT INTO attempts (class_id, mock_kind, started_at, finished_at) "
            "VALUES (?, ?, COALESCE(?, datetime('now')), ?)",
            (class_id, mock_kind, started_at, finished_at),
        )
        attempt_id = attempt_cur.lastrowid

        # 2) answer rows
        correct_count = 0
        total_count = len(question_ids)
        skipped_count = 0
        for position, qid in enumerate(question_ids, start=1):
            was_skipped = qid in skipped
            if was_skipped:
                selected: list[int] = []
                skipped_count += 1
            else:
                selected = list(answers_by_question_id[qid])
            correct = correct_by_qid[qid]
            is_correct = is_exact_match(selected, correct, was_skipped=was_skipped)
            if is_correct:
                correct_count += 1
            raw_conn.execute(
                "INSERT INTO attempt_answers "
                "(attempt_id, question_id, position, selected_indices, "
                "was_skipped, is_correct) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    attempt_id,
                    qid,
                    position,
                    json.dumps(selected),
                    1 if was_skipped else 0,
                    1 if is_correct else 0,
                ),
            )

        # 3) attempt summary update (raw_score_pct, swiss_grade, counts)
        score_pct = (correct_count / total_count) * 100.0
        swiss_grade = compute_swiss_grade(correct_count, total_count, pass_threshold_pct)
        raw_conn.execute(
            "UPDATE attempts SET correct_count=?, total_count=?, "
            "raw_score_pct=?, swiss_grade=?, "
            "finished_at=COALESCE(?, datetime('now')) "
            "WHERE id = ?",
            (correct_count, total_count, score_pct, swiss_grade,
             finished_at, attempt_id),
        )

        raw_conn.execute("COMMIT")
    except Exception:
        try:
            raw_conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        raw_conn.isolation_level = prior_isolation

    finished_row = raw_conn.execute(
        "SELECT finished_at FROM attempts WHERE id = ?", (attempt_id,)
    ).fetchone()

    return {
        "attempt_id": attempt_id,
        "class_id": class_id,
        "mock_kind": mock_kind,
        "correct_count": correct_count,
        "total_count": total_count,
        "score_pct": score_pct,
        "swiss_grade": swiss_grade,
        "skipped_count": skipped_count,
        "finished_at": finished_row[0] if finished_row else None,
    }


def _underlying_sqlite(db: Any):
    """Return the real ``sqlite3.Connection`` behind ``db``.

    The production DB symbol is a ``_LazyConnection`` proxy. Tests rebind
    ``conn.DB`` to a real ``sqlite3.Connection``. Either works for normal
    forwarded calls; explicit BEGIN/COMMIT/ROLLBACK + ``isolation_level``
    needs the real connection. This helper unwraps the lazy proxy via the
    ``_ensure()`` hook when present.
    """
    # Unwrap the lazy DB proxy when transaction control needs the real connection.
    if isinstance(db, sqlite3.Connection):
        return db
    ensure = getattr(db, "_ensure", None)
    if callable(ensure):
        return ensure()
    return db  # last-ditch: assume Connection-compatible


# ---------------------------------------------------------------------------
# Read helpers (P5 review + P6 dashboard + Study Next)
# ---------------------------------------------------------------------------

# --------------------------------------------------------------------------- #
# READ HELPERS — P5 REVIEW, P6 DASHBOARD, STUDY NEXT
# --------------------------------------------------------------------------- #
# Simple explanation:
# These helpers read the persisted attempts back for the review page, the
# dashboard, Study Next ranking, and the optional Phase 7 personal
# difficulty inputs.
#
# Important code pieces:
# - `get_attempt_summary(...)`: one-row read for the P5 header. The optional
#   `class_id` lets a caller assert the attempt belongs to the expected
#   class.
# - `get_attempt_review_rows(...)`: answer rows joined with question text,
#   options JSON, correct indices, type, and LO context, returned in
#   `position ASC` order so P5 shows the exact sequence the user saw.
# - `list_completed_attempts_for_class(...)`: lists finished attempts newest
#   first; supports an optional `mock_kind` filter and `limit`.
# - `list_personal_difficulty_examples_for_class(...)`: finished
#   attempt-answer rows joined with question content for the Phase 7
#   personal-difficulty model. The scoring core lives elsewhere; this
#   helper only returns evidence rows.
# - `latest_answer_per_question_for_class(...)`: collapses all finished
#   answers down to one latest row per generated question. Study Next uses
#   this to rank weak topics, counting practice and mock together (per the
#   V1 lock).
def get_attempt_summary(
    attempt_id: int,
    class_id: int | None = None,
    conn: Any | None = None,
) -> dict | None:
    """Return one attempt row as a dict (or ``None`` if not found)."""
    db = _resolve_conn(conn)
    if class_id is None:
        cur = db.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,))
    else:
        cur = db.execute(
            "SELECT * FROM attempts WHERE id = ? AND class_id = ?",
            (attempt_id, class_id),
        )
    return _row_to_dict(cur)


def get_attempt_review_rows(
    attempt_id: int,
    conn: Any | None = None,
) -> list[dict]:
    """Return review rows in original `position` order."""
    # Preserve the exact question order the user saw during the submitted attempt.
    db = _resolve_conn(conn)
    cur = db.execute(
        "SELECT a.id AS answer_id, a.attempt_id, a.question_id, a.position, "
        "a.selected_indices, a.was_skipped, a.is_correct, a.answered_at, "
        "q.question_text, q.options_json, q.correct_indices, q.question_type, "
        "q.rationales_per_option_json, q.source_page, q.language, "
        "q.difficulty_word_count AS difficulty_word_count, "
        "q.difficulty_readability AS difficulty_readability, "
        "q.difficulty_distractor_similarity AS difficulty_distractor_similarity, "
        "q.difficulty_conceptual_density AS difficulty_conceptual_density, "
        "q.difficulty_distractor_derivation AS difficulty_distractor_derivation, "
        "q.difficulty_reasoning_steps AS difficulty_reasoning_steps, "
        "q.difficulty_wording_complexity AS difficulty_wording_complexity, "
        "q.difficulty_wording_clarity_issue AS difficulty_wording_clarity_issue, "
        "sp.lecture_id AS lecture_id, "
        "sp.learning_objective_id AS learning_objective_id, "
        "lo.title AS learning_objective_title "
        "FROM attempt_answers a "
        "JOIN questions q ON q.id = a.question_id "
        "JOIN slide_pages sp ON q.slide_page_id = sp.id "
        "LEFT JOIN learning_objectives lo ON sp.learning_objective_id = lo.id "
        "WHERE a.attempt_id = ? "
        "ORDER BY a.position ASC",
        (attempt_id,),
    )
    return _rows_to_dicts(cur)


def list_completed_attempts_for_class(
    class_id: int,
    mock_kind: str | None = None,
    limit: int | None = None,
    conn: Any | None = None,
) -> list[dict]:
    """List completed attempts for a class, newest first.

    ``mock_kind`` filters on 'mock' or 'practice'; ``limit`` is optional.
    Only rows with non-NULL ``finished_at`` are returned (the final-submit
    contract guarantees finished_at is set on commit).
    """
    db = _resolve_conn(conn)
    sql = (
        "SELECT * FROM attempts "
        "WHERE class_id = ? AND finished_at IS NOT NULL"
    )
    params: list[Any] = [class_id]
    if mock_kind is not None:
        if mock_kind not in _VALID_MOCK_KINDS:
            raise ValueError(f"mock_kind must be in {_VALID_MOCK_KINDS}")
        sql += " AND mock_kind = ?"
        params.append(mock_kind)
    sql += " ORDER BY finished_at DESC, id DESC"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))
    return _rows_to_dicts(db.execute(sql, tuple(params)))


def list_personal_difficulty_examples_for_class(
    class_id: int,
    conn: Any | None = None,
) -> list[dict]:
    """Return completed-answer rows for a class for personal-difficulty scoring.

    Used by Phase 7 personal difficulty: each row pairs the student's answer
    outcome (`is_correct`, `is_skipped`) with the question text/options/type
    fields needed to fit a small local model. Only finished attempts are
    included; draft/unsubmitted attempts and unfinished rows are excluded.

    No labels are fabricated. Wrong/skipped vs correct mapping happens in
    `app.ml.personal_difficulty`, not here.
    """
    # Read finished attempt-answer rows only; finalize_attempt sets finished_at.
    db = _resolve_conn(conn)
    cur = db.execute(
        "SELECT a.id AS answer_id, a.attempt_id AS attempt_id, "
        "a.question_id AS question_id, a.selected_indices AS selected_indices, "
        "a.was_skipped AS was_skipped, a.is_correct AS is_correct, "
        "a.answered_at AS answered_at, t.mock_kind AS mock_kind, "
        "t.finished_at AS finished_at, "
        "q.question_text AS question_text, q.options_json AS options_json, "
        "q.correct_indices AS correct_indices, "
        "q.question_type AS question_type, q.source_page AS source_page, "
        "q.language AS language, "
        "q.difficulty_word_count AS difficulty_word_count, "
        "q.difficulty_readability AS difficulty_readability, "
        "q.difficulty_distractor_similarity AS difficulty_distractor_similarity, "
        "q.difficulty_conceptual_density AS difficulty_conceptual_density, "
        "q.difficulty_distractor_derivation AS difficulty_distractor_derivation, "
        "q.difficulty_reasoning_steps AS difficulty_reasoning_steps, "
        "q.difficulty_wording_complexity AS difficulty_wording_complexity, "
        "q.difficulty_wording_clarity_issue AS difficulty_wording_clarity_issue, "
        "sp.lecture_id AS lecture_id, "
        "sp.learning_objective_id AS learning_objective_id, "
        "lo.title AS learning_objective_title "
        "FROM attempt_answers a "
        "JOIN attempts t ON t.id = a.attempt_id "
        "JOIN questions q ON q.id = a.question_id "
        "JOIN slide_pages sp ON q.slide_page_id = sp.id "
        "LEFT JOIN learning_objectives lo ON sp.learning_objective_id = lo.id "
        "WHERE t.class_id = ? AND t.finished_at IS NOT NULL "
        "ORDER BY a.answered_at ASC, a.id ASC",
        (class_id,),
    )
    rows = _rows_to_dicts(cur)
    # Project SQLite integers/text into shapes the scoring core expects without
    # fabricating any new fields. Keep `question_type` exactly as stored.
    for row in rows:
        row["is_correct"] = bool(row.get("is_correct"))
        row["is_skipped"] = bool(row.get("was_skipped"))
    return rows


def latest_answer_per_question_for_class(
    class_id: int,
    conn: Any | None = None,
) -> list[dict]:
    """Return the most recent answer row per generated question id for a class.

    Used by Study Next / weakness ranking. Both 'mock' and 'practice' attempts
    are considered (practice affects Study Next per the V1 lock).
    """
    # Collapse finished answers to one latest row per generated question.
    db = _resolve_conn(conn)
    sql = (
        "SELECT a.question_id, a.attempt_id, a.position, a.selected_indices, "
        "a.was_skipped, a.is_correct, a.answered_at, t.mock_kind "
        "FROM attempt_answers a "
        "JOIN attempts t ON t.id = a.attempt_id "
        "WHERE t.class_id = ? "
        "AND a.id IN ( "
        "  SELECT MAX(a2.id) FROM attempt_answers a2 "
        "  JOIN attempts t2 ON t2.id = a2.attempt_id "
        "  WHERE t2.class_id = ? "
        "  GROUP BY a2.question_id "
        ") "
        "ORDER BY a.question_id ASC"
    )
    return _rows_to_dicts(db.execute(sql, (class_id, class_id)))

"""Surf — questions query wrappers.

Dict/list return contract + storage-boundary MCQ validation.

Pandas is deliberately NOT imported here. Helpers return
``dict | None`` (single-row) or ``list[dict]`` (lists).

Storage-boundary MCQ validation mirrors the generated-boundary guard in
``app.class_.lecture_ingest._validate_mcq``:
``insert_question(...)`` rejects, with ``ValueError``, any payload whose:

  * ``options`` is not a list of length 4,
  * ``rationales_per_option`` is not a list of length 4,
  * ``correct_indices`` is missing/not a list,
  * ``correct_indices`` is empty (1..4 unique correct answers required),
  * ``correct_indices`` has more than 4 entries,
  * ``correct_indices`` contains non-integer values (booleans included),
  * ``correct_indices`` contains values outside ``0..3``,
  * ``correct_indices`` contains duplicates (e.g. ``[0, 0]``).

The two boundary guards (generated and storage) are deliberately
redundant: invalid MCQs cannot reach `attempt_answers` matching at
grading time even if a future caller bypasses lecture_ingest.
"""
# Validate and store generated questions while keeping query returns pandas-free.
from __future__ import annotations

import json
from typing import Any, Sequence

from app.brain.question_type import is_valid_question_type, normalize_question_type
from app.db.connection import DB

__all__ = [
    "insert_question",
    "list_questions_for_slide_page",
    "list_questions_for_lecture",
    "ready_question_count_for_lecture",
    "list_ready_questions_for_lecture",
    "list_ready_questions_for_class",
    "list_questions_for_learning_objective",
    "get_question_display_context",
]


def _resolve_conn(conn: Any | None):
    """Return the connection to use (caller-provided or the lazy default)."""
    return conn if conn is not None else DB


def _row_to_dict(cur) -> dict | None:
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def _rows_to_dicts(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _validate_mcq_payload(
    options: Sequence[str],
    correct_indices: Sequence[int],
    rationales_per_option: Sequence[str],
) -> None:
    """Storage-boundary mirror of the generated-boundary MCQ guard.

    Raises ``ValueError`` with a precise message on every contract break.
    """
    # Reject invalid MCQ payloads before any insert can reach SQLite.
    if not isinstance(options, list) or len(options) != 4:
        raise ValueError("options must be a list of exactly 4 entries")
    if not isinstance(rationales_per_option, list) or len(rationales_per_option) != 4:
        raise ValueError("rationales_per_option must be a list of exactly 4 entries")
    if not isinstance(correct_indices, list):
        raise ValueError("correct_indices must be a list of unique integers in 0..3")
    if not correct_indices:
        raise ValueError("correct_indices must be non-empty (1..4 unique values)")
    if len(correct_indices) > 4:
        raise ValueError("correct_indices must have at most 4 entries")
    for i in correct_indices:
        # ``bool`` is a subclass of ``int`` — exclude it explicitly.
        if isinstance(i, bool) or not isinstance(i, int):
            raise ValueError(
                f"correct_indices must be integers in 0..3 (got {i!r})"
            )
        if i < 0 or i > 3:
            raise ValueError(
                f"correct_indices values must be in 0..3 (got {i!r}, out of range)"
            )
    if len(set(correct_indices)) != len(correct_indices):
        raise ValueError(
            f"correct_indices must be unique (got duplicates: {list(correct_indices)})"
        )


def _validated_question_type(question_type: object) -> str:
    normalized = normalize_question_type(question_type)
    if not is_valid_question_type(normalized):
        raise ValueError(f"question_type must be one of the Surf V1 slugs (got {question_type!r})")
    return normalized


def insert_question(
    slide_page_id: int,
    question_text: str,
    options: list[str],
    correct_indices: list[int],
    rationales_per_option: list[str],
    source_page: int,
    language: str,
    *,
    question_type: str,
    difficulty_word_count: int | None = None,
    difficulty_readability: float | None = None,
    difficulty_distractor_similarity: float | None = None,
    difficulty_conceptual_density: int | None = None,
    difficulty_distractor_derivation: int | None = None,
    difficulty_reasoning_steps: int | None = None,
    difficulty_wording_complexity: int | None = None,
    difficulty_wording_clarity_issue: int = 0,
    difficulty_score: float | None = None,
) -> int:
    """Insert one MCQ.

    Ingestion normally passes word count plus optional Claude-computed
    intrinsic metadata fields. The optional ``difficulty_score`` is legacy
    compatibility storage; Phase 7/7.1 compute personal difficulty on demand.

    Storage-boundary validation raises ``ValueError`` before any DB write if
    the payload violates the MCQ contract (see module docstring).
    """
    # Normalize question type and store MCQ JSON only after validation passes.
    _validate_mcq_payload(options, correct_indices, rationales_per_option)
    normalized_question_type = _validated_question_type(question_type)
    with DB:
        cur = DB.execute(
            "INSERT INTO questions ("
            "slide_page_id, question_text, options_json, correct_indices, "
            "rationales_per_option_json, question_type, source_page, language, "
            "difficulty_word_count, difficulty_readability, difficulty_distractor_similarity, "
            "difficulty_conceptual_density, difficulty_distractor_derivation, "
            "difficulty_reasoning_steps, difficulty_wording_complexity, "
            "difficulty_wording_clarity_issue, difficulty_score"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                slide_page_id,
                question_text,
                json.dumps(options),
                json.dumps(correct_indices),
                json.dumps(rationales_per_option),
                normalized_question_type,
                source_page,
                language,
                difficulty_word_count,
                difficulty_readability,
                difficulty_distractor_similarity,
                difficulty_conceptual_density,
                difficulty_distractor_derivation,
                difficulty_reasoning_steps,
                difficulty_wording_complexity,
                difficulty_wording_clarity_issue,
                difficulty_score,
            ),
        )
        return cur.lastrowid


def list_questions_for_slide_page(slide_page_id: int) -> list[dict]:
    cur = DB.execute(
        "SELECT * FROM questions WHERE slide_page_id = ? ORDER BY id",
        (slide_page_id,),
    )
    return _rows_to_dicts(cur)


def list_questions_for_lecture(lecture_id: int) -> list[dict]:
    cur = DB.execute(
        "SELECT q.* FROM questions q "
        "JOIN slide_pages sp ON q.slide_page_id = sp.id "
        "WHERE sp.lecture_id = ? ORDER BY q.id",
        (lecture_id,),
    )
    return _rows_to_dicts(cur)


def ready_question_count_for_lecture(lecture_id: int) -> int:
    cur = DB.execute(
        "SELECT COUNT(q.id) "
        "FROM questions q "
        "JOIN slide_pages sp ON q.slide_page_id = sp.id "
        "JOIN lectures l ON sp.lecture_id = l.id "
        "WHERE sp.lecture_id = ? AND sp.status = 'kept' AND l.status = 'ready'",
        (lecture_id,),
    )
    return int(cur.fetchone()[0])


def list_ready_questions_for_lecture(lecture_id: int) -> list[dict]:
    cur = DB.execute(
        "SELECT q.*, sp.learning_objective_id AS learning_objective_id, "
        "lo.title AS learning_objective_title "
        "FROM questions q "
        "JOIN slide_pages sp ON q.slide_page_id = sp.id "
        "JOIN lectures l ON sp.lecture_id = l.id "
        "LEFT JOIN learning_objectives lo ON sp.learning_objective_id = lo.id "
        "WHERE sp.lecture_id = ? AND sp.status = 'kept' AND l.status = 'ready' "
        "ORDER BY q.id",
        (lecture_id,),
    )
    return _rows_to_dicts(cur)


def list_questions_for_learning_objective(learning_objective_id: int) -> list[dict]:
    cur = DB.execute(
        "SELECT q.*, sp.learning_objective_id AS learning_objective_id, "
        "lo.title AS learning_objective_title "
        "FROM questions q "
        "JOIN slide_pages sp ON q.slide_page_id = sp.id "
        "JOIN lectures l ON sp.lecture_id = l.id "
        "LEFT JOIN learning_objectives lo ON sp.learning_objective_id = lo.id "
        "WHERE sp.learning_objective_id = ? "
        "AND sp.status = 'kept' AND l.status = 'ready' "
        "ORDER BY q.id",
        (learning_objective_id,),
    )
    return _rows_to_dicts(cur)


def get_question_display_context(question_id: int) -> dict | None:
    cur = DB.execute(
        "SELECT q.id, q.question_type, sp.lecture_id, "
        "sp.learning_objective_id AS learning_objective_id, "
        "lo.title AS learning_objective_title "
        "FROM questions q "
        "JOIN slide_pages sp ON q.slide_page_id = sp.id "
        "LEFT JOIN learning_objectives lo ON sp.learning_objective_id = lo.id "
        "WHERE q.id = ?",
        (question_id,),
    )
    return _row_to_dict(cur)


def list_ready_questions_for_class(
    class_id: int,
    conn: Any | None = None,
) -> list[dict]:
    """Return every ready MCQ row for a class, joined with lecture and LO context.

    Used by the Phase 7 Custom Mock selector. SELECT-only; never mutates rows.
    The returned dicts include the stored Claude `question_type` value as-is.
    """
    # Reads questions whose slide page is kept and whose lecture is ready.
    db = _resolve_conn(conn)
    cur = db.execute(
        "SELECT q.id AS id, q.slide_page_id AS slide_page_id, "
        "q.question_text AS question_text, q.options_json AS options_json, "
        "q.correct_indices AS correct_indices, "
        "q.rationales_per_option_json AS rationales_per_option_json, "
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
        "q.difficulty_score AS difficulty_score, "
        "sp.lecture_id AS lecture_id, "
        "sp.learning_objective_id AS learning_objective_id, "
        "l.title AS lecture_title, "
        "lo.title AS learning_objective_title "
        "FROM questions q "
        "JOIN slide_pages sp ON q.slide_page_id = sp.id "
        "JOIN lectures l ON sp.lecture_id = l.id "
        "LEFT JOIN learning_objectives lo ON sp.learning_objective_id = lo.id "
        "WHERE l.class_id = ? AND sp.status = 'kept' AND l.status = 'ready' "
        "ORDER BY q.id",
        (class_id,),
    )
    return _rows_to_dicts(cur)

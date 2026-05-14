"""Phase 7 Custom Mock selector — top-N ready questions by personal difficulty.

This module is the ranking seam used by the red `CUSTOM MOCK >` button on
the Class page. It joins ready question rows for a class with the
student's completed answer examples, asks
``app.ml.personal_difficulty.score_questions`` for a personal wrong-risk
score per question, and returns the highest-risk questions in descending
score order (with a deterministic tie-break by question id).

It does **not** call standard mock launch helpers, Study Next helpers,
the Claude client, NotebookLM, or the network. The selector is pure
ranking; the actual session-state launch lives in
``app.class_.mock_custom_launch`` (Plan 07-03).
"""
# Custom Mock ranking. Separate from standard mock and Study Next.
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from app.db.queries_attempts import list_personal_difficulty_examples_for_class
from app.db.queries_questions import list_ready_questions_for_class
from app.ml.personal_difficulty import score_questions

DEFAULT_CUSTOM_MOCK_LIMIT = 10
_DIFFICULTY_FEATURE_KEYS = (
    "difficulty_word_count",
    "difficulty_readability",
    "difficulty_distractor_similarity",
    "difficulty_conceptual_density",
    "difficulty_distractor_derivation",
    "difficulty_reasoning_steps",
    "difficulty_wording_complexity",
    "difficulty_wording_clarity_issue",
)

__all__ = [
    "DEFAULT_CUSTOM_MOCK_LIMIT",
    "select_custom_mock_questions",
]


def _decode_json_list(value: object) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
        except ValueError:
            return []
        if isinstance(parsed, list):
            return parsed
    return []


def _question_id(row: Mapping[str, Any]) -> Any:
    return row.get("question_id", row.get("id"))


def _scoring_view(row: Mapping[str, Any]) -> dict[str, Any]:
    """Build the plain-dict view passed to the scoring core."""
    qid = _question_id(row)
    view = {
        "id": qid,
        "question_id": qid,
        "stem": row.get("question_text"),
        "question_text": row.get("question_text"),
        "options": _decode_json_list(row.get("options_json", row.get("options"))),
        "correct_indices": _decode_json_list(row.get("correct_indices")),
        "question_type": row.get("question_type"),
        "lo_title": (
            row.get("learning_objective_title")
            or row.get("learning_objective")
            or row.get("lo_title")
        ),
    }
    for key in _DIFFICULTY_FEATURE_KEYS:
        view[key] = row.get(key)
    return view


def _example_view(row: Mapping[str, Any]) -> dict[str, Any]:
    """Build the plain-dict example view passed to the scoring core."""
    view = _scoring_view(row)
    view["selected_indices"] = _decode_json_list(row.get("selected_indices"))
    view["is_correct"] = bool(row.get("is_correct"))
    view["is_skipped"] = bool(row.get("is_skipped") or row.get("was_skipped"))
    return view


def select_custom_mock_questions(
    class_id: int,
    limit: int = DEFAULT_CUSTOM_MOCK_LIMIT,
    conn: Any | None = None,
    *,
    ready_questions_fn=list_ready_questions_for_class,
    examples_fn=list_personal_difficulty_examples_for_class,
    score_questions_fn=score_questions,
) -> list[dict[str, Any]]:
    """Return up to ``limit`` ready question rows ranked by personal difficulty.

    Each returned dict is a shallow copy of the underlying ready-question
    row, plus ``personal_difficulty_score`` (int 0..100) and
    ``personal_difficulty_source`` (``"rule"`` or ``"ml"``). Highest scores
    come first; ties break by question id ascending so output is
    deterministic.

    The default helpers come from `app.db.queries_questions` and
    `app.db.queries_attempts` (real SQLite) and from
    `app.ml.personal_difficulty.score_questions`. Tests inject fakes via the
    keyword-only parameters; they are not used by production callers.
    """
    if isinstance(class_id, bool) or not isinstance(class_id, int) or class_id <= 0:
        raise ValueError("class_id must be a positive integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")

    ready_rows = list(ready_questions_fn(class_id, conn=conn) or [])
    if not ready_rows:
        return []

    examples = list(examples_fn(class_id, conn=conn) or [])

    scoring_inputs = [_scoring_view(row) for row in ready_rows]
    scoring_examples = [_example_view(row) for row in examples]

    results = score_questions_fn(scoring_inputs, examples=scoring_examples)
    if len(results) != len(ready_rows):
        # Defensive: fall back to a flat rule score per row so Custom Mock
        # still launches deterministically.
        from app.ml.personal_difficulty import score_rule_based

        results = [score_rule_based(row) for row in scoring_inputs]

    scored: list[dict[str, Any]] = []
    for row, result in zip(ready_rows, results):
        annotated = dict(row)
        annotated["personal_difficulty_score"] = int(result.score)
        annotated["personal_difficulty_source"] = str(result.source)
        scored.append(annotated)

    scored.sort(
        key=lambda r: (
            -int(r["personal_difficulty_score"]),
            int(r["id"]),
        )
    )
    return scored[:limit]

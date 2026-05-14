"""P4 final-submit service for one-shot attempt persistence."""
# Validates the session draft before one database transaction saves it.
from __future__ import annotations

from typing import Any, Callable

from app.db.queries_attempts import finalize_attempt as _default_finalize

__all__ = ["submit_attempt"]

FinalizeFn = Callable[..., dict[str, Any]]


def _positive_int(value: Any, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _question_ids_from_launch(launch_state: dict[str, Any]) -> list[int]:
    raw = launch_state.get("frozen_question_ids")
    if not isinstance(raw, list) or not raw:
        raise ValueError("launch_state must include frozen_question_ids")
    qids = [_positive_int(qid, name="question_id") for qid in raw]
    if len(set(qids)) != len(qids):
        raise ValueError("frozen_question_ids must not contain duplicates")
    return qids


def _selected_answers(
    *,
    question_ids: list[int],
    selected_indices_by_qid: Any,
    skipped_qids: set[int],
) -> dict[int, list[int]]:
    if not isinstance(selected_indices_by_qid, dict):
        raise ValueError("selected_indices_by_qid must be a dict")
    answers: dict[int, list[int]] = {}
    for qid in question_ids:
        if qid in skipped_qids:
            continue
        raw_selected = selected_indices_by_qid.get(qid, [])
        if not isinstance(raw_selected, list):
            raise ValueError(f"selected indices for question {qid} must be a list")
        if not all(isinstance(idx, int) and not isinstance(idx, bool) for idx in raw_selected):
            raise ValueError(f"selected indices for question {qid} must be ints")
        if not all(0 <= idx <= 3 for idx in raw_selected):
            raise ValueError(f"selected indices for question {qid} must be 0..3")
        if len(set(raw_selected)) != len(raw_selected):
            raise ValueError(f"selected indices for question {qid} must not contain duplicates")
        clean = sorted(raw_selected)
        if not clean:
            raise ValueError(f"question {qid} must be answered or skipped")
        answers[qid] = clean
    return answers


def submit_attempt(
    *,
    launch_state: dict[str, Any],
    attempt_state: dict[str, Any],
    finalize_fn: FinalizeFn = _default_finalize,
) -> dict[str, Any]:
    """Validate and persist the final P4 attempt exactly once.

    Returns one of these status dicts:
    ``in_flight``, ``already_submitted``, ``submitted``,
    ``validation_error``, or ``error``.
    """
    # Turns session-only answers into the single persisted attempt.
    if attempt_state.get("submit_in_flight") is True:
        return {"status": "in_flight"}

    submitted_attempt_id = attempt_state.get("submitted_attempt_id")
    if submitted_attempt_id is not None:
        return {
            "status": "already_submitted",
            "attempt_id": submitted_attempt_id,
        }

    attempt_state["submit_in_flight"] = True
    try:
        class_id = _positive_int(launch_state.get("class_id"), name="class_id")
        mock_kind = launch_state.get("mock_kind")
        if mock_kind not in {"mock", "practice"}:
            raise ValueError("mock_kind must be 'mock' or 'practice'")
        question_ids = _question_ids_from_launch(launch_state)
        raw_skipped = attempt_state.get("skipped_qids", set())
        if not isinstance(raw_skipped, set | list | tuple):
            raise ValueError("skipped_qids must be a set")
        skipped_question_ids = {
            _positive_int(qid, name="skipped question_id") for qid in raw_skipped
        }
        unknown_skips = skipped_question_ids - set(question_ids)
        if unknown_skips:
            raise ValueError(f"skipped_qids contains unknown questions: {sorted(unknown_skips)}")

        answers_by_question_id = _selected_answers(
            question_ids=question_ids,
            selected_indices_by_qid=attempt_state.get("selected_indices_by_qid", {}),
            skipped_qids=skipped_question_ids,
        )
        result = finalize_fn(
            class_id=class_id,
            mock_kind=mock_kind,
            question_ids=question_ids,
            answers_by_question_id=answers_by_question_id,
            skipped_question_ids={int(qid) for qid in skipped_question_ids},
            started_at=attempt_state.get("started_at"),
        )
    except ValueError as exc:
        attempt_state["submit_in_flight"] = False
        return {"status": "validation_error", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - UI service maps unexpected failures.
        attempt_state["submit_in_flight"] = False
        return {"status": "error", "error": str(exc)}

    attempt_id = result.get("attempt_id")
    attempt_state["submitted_attempt_id"] = attempt_id
    attempt_state["submit_in_flight"] = False
    return {"status": "submitted", "attempt_id": attempt_id, "result": result}

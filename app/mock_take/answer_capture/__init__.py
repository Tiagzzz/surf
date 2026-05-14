"""Session-only answer capture helpers for P4 take-mock flow.

No database writes happen here. These helpers only shape the in-memory
``st.session_state`` attempt payload that P4 later hands to
``app.mock_take.attempt_save.submit_attempt`` on final submit.
"""
# Keeps P4 answer edits in memory until final submit.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Standard-library imports only. This pipeline owns the in-memory P4 answer
# draft and must not import Streamlit, the database, or the Claude client.
# The `datetime` helpers stamp when the user began the attempt so the final
# submit can record `started_at` without persisting a draft attempt row.
from datetime import UTC, datetime
from typing import Any

# --------------------------------------------------------------------------- #
# SESSION-STATE CONTRACT KEYS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Two locked string constants. The renderer in `app/mock_take/question_render`
# imports both and must use these exact spellings — they are part of the
# session-state contract between the answer-capture helpers and the page.
#
# Important code pieces:
# - `P4_IN_PROGRESS_KEY`: the `st.session_state` key under which the draft
#   attempt dict lives while the user works through the questions.
# - `SUBMIT_DIALOG_SENTINEL`: the marker returned by `advance(...)` when
#   the user reaches the last question, telling the page to open the final
#   submit confirmation dialog.
P4_IN_PROGRESS_KEY = "p4_attempt_in_progress"
SUBMIT_DIALOG_SENTINEL = "open_submit_dialog"

__all__ = [
    "P4_IN_PROGRESS_KEY",
    "SUBMIT_DIALOG_SENTINEL",
    "advance",
    "can_advance",
    "init_attempt_state",
    "mark_skipped",
    "toggle_option",
]


def init_attempt_state(
    launch_state: dict[str, Any] | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return the fresh session-only P4 attempt state.

    ``launch_state`` is accepted for renderer compatibility but does not alter
    the state shape. ``started_at`` is ISO UTC so the eventual DB write can
    preserve when the user began the mock/practice without creating a draft
    attempt row.
    """
    # Builds the draft state shape without writing an attempt row.
    _ = launch_state
    started = now if now is not None else datetime.now(UTC)
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    else:
        started = started.astimezone(UTC)
    return {
        "selected_indices_by_qid": {},
        "skipped_qids": set(),
        "current_index": 0,
        "started_at": started.isoformat(),
        "submit_in_flight": False,
        "submitted_attempt_id": None,
    }


def _qid(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("question_id must be a positive integer")
    return int(value)


def _option_index(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 3:
        raise ValueError("option_index must be an integer from 0 to 3")
    return int(value)


def _selected_map(attempt_state: dict[str, Any]) -> dict[int, list[int]]:
    selected = attempt_state.setdefault("selected_indices_by_qid", {})
    if not isinstance(selected, dict):
        raise ValueError("attempt_state selected_indices_by_qid must be a dict")
    return selected


def _skipped_set(attempt_state: dict[str, Any]) -> set[int]:
    skipped = attempt_state.setdefault("skipped_qids", set())
    if isinstance(skipped, set):
        return skipped
    if isinstance(skipped, list | tuple):
        normalized = {int(qid) for qid in skipped}
        attempt_state["skipped_qids"] = normalized
        return normalized
    raise ValueError("attempt_state skipped_qids must be a set")


# --------------------------------------------------------------------------- #
# OPTION TOGGLE — `toggle_option`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Surf MCQs are multi-select with 1..4 correct answers. This helper flips
# whether one option is currently picked for a question. The stored list is
# kept sorted and de-duplicated so the final-submit `correct_indices` /
# `selected_indices` shape always matches the schema contract. Picking any
# option also clears any previous skip — answered beats skipped.
def toggle_option(
    attempt_state: dict[str, Any],
    question_id: int,
    option_index: int,
) -> dict[str, Any]:
    """Toggle one MCQ option for a question.

    The stored list is always sorted and unique. Choosing an option also
    removes that question from the skipped set, because answered beats skipped.
    """
    # Stores one clean multi-select answer and clears skipped state.
    qid = _qid(question_id)
    idx = _option_index(option_index)
    selected = _selected_map(attempt_state)
    current = {int(i) for i in selected.get(qid, [])}
    if idx in current:
        current.remove(idx)
    else:
        current.add(idx)
    if current:
        selected[qid] = sorted(current)
    else:
        selected.pop(qid, None)
    _skipped_set(attempt_state).discard(qid)
    return attempt_state


def mark_skipped(attempt_state: dict[str, Any], question_id: int) -> dict[str, Any]:
    """Mark a question as skipped and clear any selected options."""
    qid = _qid(question_id)
    _selected_map(attempt_state)[qid] = []
    _skipped_set(attempt_state).add(qid)
    return attempt_state


# --------------------------------------------------------------------------- #
# ADVANCE GATE — `can_advance`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Implements the P4 rule that `NEXT` is disabled until the user has picked
# at least one option OR explicitly pressed `SKIP`. `SKIP` itself stays
# enabled at all times; that asymmetry is intentional so a careful student
# is forced to make an explicit choice.
def can_advance(attempt_state: dict[str, Any], question_id: int) -> bool:
    """Return True only when the current question has an answer or skip."""
    qid = _qid(question_id)
    selected = _selected_map(attempt_state).get(qid, [])
    return bool(selected) or qid in _skipped_set(attempt_state)


def advance(attempt_state: dict[str, Any], total_questions: int) -> str | None:
    """Advance the pointer or request the submit dialog at the end."""
    if (
        isinstance(total_questions, bool)
        or not isinstance(total_questions, int)
        or total_questions <= 0
    ):
        raise ValueError("total_questions must be a positive integer")
    current = attempt_state.get("current_index", 0)
    if isinstance(current, bool) or not isinstance(current, int) or current < 0:
        raise ValueError("current_index must be a non-negative integer")
    current += 1
    attempt_state["current_index"] = current
    if current >= total_questions:
        return SUBMIT_DIALOG_SENTINEL
    return None

"""Study Next practice launch helpers for P3 → P4.

Practice launch mirrors the standard mock launch contract, but scopes
the frozen questions to one weak learning objective. It writes session
state only and creates no ``attempts`` row.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS AND PRACTICE-LAUNCH CONSTANTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Study Next surfaces the weakest learning objective for a class and
# lets the student practice it. The launch step mirrors the standard
# mock launch contract but scopes the frozen questions to one LO. Like
# the other launchers, no DB row is created here — P4 owns the final
# write.
#
# Important code pieces:
# - `PRACTICE_KIND = "practice"`: discriminator stored alongside the
#   frozen questions so P4 can distinguish practice from a mock attempt.
# - `SELECTED_LEARNING_OBJECTIVE_ID_KEY`: extra session-state key the
#   mock launch does not need; lets P4 highlight the LO being practiced.
from collections.abc import MutableMapping
from typing import Any

from app.class_.mock_standard_launch import (
    FROZEN_QUESTION_IDS_KEY,
    MOCK_KIND_KEY,
    P4_LAUNCH_STATE_KEY,
    QUESTION_PAYLOADS_KEY,
    build_question_payload,
)
from app.db.queries_questions import list_questions_for_learning_objective

PRACTICE_KIND = "practice"
SELECTED_LEARNING_OBJECTIVE_ID_KEY = "selected_learning_objective_id"

__all__ = [
    "PRACTICE_KIND",
    "SELECTED_LEARNING_OBJECTIVE_ID_KEY",
    "launch_study_next_practice",
]


def _default_session_state() -> MutableMapping[str, Any]:
    import streamlit as st

    return st.session_state


def _positive_int(value: int, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _write_launch_state(
    session_state: MutableMapping[str, Any],
    *,
    state: dict[str, Any],
) -> None:
    session_state[P4_LAUNCH_STATE_KEY] = state
    session_state[FROZEN_QUESTION_IDS_KEY] = list(state["frozen_question_ids"])
    session_state[QUESTION_PAYLOADS_KEY] = list(state["question_payloads"])
    session_state[MOCK_KIND_KEY] = state["mock_kind"]
    session_state[SELECTED_LEARNING_OBJECTIVE_ID_KEY] = state[
        "learning_objective_id"
    ]


# --------------------------------------------------------------------------- #
# LAUNCH_STUDY_NEXT_PRACTICE — FREEZE ONE LO'S QUESTIONS FOR PRACTICE
# --------------------------------------------------------------------------- #
# Simple explanation:
# Pulls every ready question tagged with the given learning objective,
# projects them into the same payload shape mock attempts use, and
# writes them into session state with `mock_kind == "practice"`. Raises
# a clear error when the LO has no ready questions so the caller can
# show an honest empty-state message.
def launch_study_next_practice(
    *,
    class_id: int,
    learning_objective_id: int,
    class_name: str | None = None,
    session_state: MutableMapping[str, Any] | None = None,
    questions_for_learning_objective_fn=list_questions_for_learning_objective,
) -> dict[str, Any]:
    """Freeze a Study Next practice launch in session state only."""
    clean_class_id = _positive_int(class_id, name="class_id")
    clean_lo_id = _positive_int(
        learning_objective_id,
        name="learning_objective_id",
    )
    rows = list(questions_for_learning_objective_fn(clean_lo_id) or [])
    if not rows:
        raise ValueError("learning objective has no ready questions")

    payloads = [
        build_question_payload(row, learning_objective_id=clean_lo_id)
        for row in rows
    ]
    frozen_question_ids = [int(row["id"]) for row in payloads]
    lecture_ids = sorted(
        {
            int(row["lecture_id"])
            for row in payloads
            if row.get("lecture_id") is not None
        }
    )

    state = {
        "ok": True,
        "class_id": clean_class_id,
        "class_name": (
            class_name.strip()
            if isinstance(class_name, str) and class_name.strip()
            else None
        ),
        "mock_kind": PRACTICE_KIND,
        "learning_objective_id": clean_lo_id,
        "selected_lecture_ids": lecture_ids,
        "frozen_question_ids": frozen_question_ids,
        "question_payloads": payloads,
        "target_question_count": len(payloads),
        "available_question_count": len(payloads),
        "honest_short_copy": None,
    }
    target_session = session_state if session_state is not None else _default_session_state()
    _write_launch_state(target_session, state=state)
    return state

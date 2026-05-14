"""Phase 7 Custom Mock launch helper.

The red `CUSTOM MOCK >` button on the Class page calls
``launch_mock_custom(...)``. This helper consumes the top-10 ranked
questions from ``app.class_.custom_mock_selection`` and writes the same
P4 session-state contract that the standard mock launch uses. It does
**not** create an ``attempts`` row — P4 final submit owns the
all-or-nothing DB write via ``app.db.queries_attempts.finalize_attempt``.

This module is intentionally separate from ``mock_standard_launch`` and
``study_next_launch``; their behavior in Phase 7 is unchanged.
"""
# Custom Mock launch — writes P4 session keys, never touches the DB.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS AND LOCKED COPY CONSTANTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This module powers the red `CUSTOM MOCK >` button on the Class Hub. It
# reuses the same session-state keys as the standard mock launch (so P4
# does not care which entry point started the attempt), but uses the
# ranking helper from `custom_mock_selection` to pick the highest-risk
# questions instead of letting the student pick lectures.
#
# Important code pieces:
# - `MutableMapping[str, Any]`: a generic type hint that lets tests pass
#   a plain `dict` while production passes `st.session_state`.
# - `CUSTOM_MOCK_HONEST_SHORT_COPY_TEMPLATE`: the partial-mock message
#   shown when fewer than 10 ready questions exist.
# - `CUSTOM_MOCK_EMPTY_COPY`: the empty-state copy when no ready
#   questions exist anywhere in the class.
from collections.abc import MutableMapping
from typing import Any

from app.class_.custom_mock_selection import (
    DEFAULT_CUSTOM_MOCK_LIMIT,
    select_custom_mock_questions,
)
from app.class_.mock_standard_launch import (
    FROZEN_QUESTION_IDS_KEY,
    MOCK_KIND,
    MOCK_KIND_KEY,
    P4_LAUNCH_STATE_KEY,
    QUESTION_PAYLOADS_KEY,
    SELECTED_LECTURE_IDS_KEY,
    build_question_payload,
)

CUSTOM_MOCK_TARGET_QUESTION_COUNT = DEFAULT_CUSTOM_MOCK_LIMIT
CUSTOM_MOCK_HONEST_SHORT_COPY_TEMPLATE = (
    "Only {ready} ready questions in this class — Surf will build a "
    "shorter Custom Mock with whatever's ready."
)
CUSTOM_MOCK_EMPTY_COPY = (
    "No ready questions for Custom Mock yet. Generate or import questions "
    "first."
)

__all__ = [
    "CUSTOM_MOCK_TARGET_QUESTION_COUNT",
    "CUSTOM_MOCK_HONEST_SHORT_COPY_TEMPLATE",
    "CUSTOM_MOCK_EMPTY_COPY",
    "launch_mock_custom",
]


def _default_session_state() -> MutableMapping[str, Any]:
    import streamlit as st

    return st.session_state


def _write_launch_state(
    session_state: MutableMapping[str, Any],
    *,
    state: dict[str, Any],
) -> None:
    session_state[P4_LAUNCH_STATE_KEY] = state
    session_state[FROZEN_QUESTION_IDS_KEY] = list(state["frozen_question_ids"])
    session_state[QUESTION_PAYLOADS_KEY] = list(state["question_payloads"])
    session_state[MOCK_KIND_KEY] = state["mock_kind"]
    session_state[SELECTED_LECTURE_IDS_KEY] = list(state["selected_lecture_ids"])


def _validate_class_id(class_id: int) -> None:
    if isinstance(class_id, bool) or not isinstance(class_id, int) or class_id <= 0:
        raise ValueError("class_id must be a positive integer")


# --------------------------------------------------------------------------- #
# LAUNCH_MOCK_CUSTOM — RANK + FREEZE THE TOP-N HARDEST QUESTIONS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Calls the ranking helper to get up to 10 ready questions ordered by
# personal difficulty, projects them through the standard
# `build_question_payload(...)`, and writes the same P4 session-state
# keys as the standard mock launch. Returns a dict the renderer uses to
# show success/empty/partial toasts.
def launch_mock_custom(
    *,
    class_id: int,
    class_name: str | None = None,
    session_state: MutableMapping[str, Any] | None = None,
    selector_fn=select_custom_mock_questions,
    target_question_count: int = CUSTOM_MOCK_TARGET_QUESTION_COUNT,
) -> dict[str, Any]:
    """Freeze a Custom Mock launch in session state.

    Reads up to ``target_question_count`` ready class questions from the
    selector, projects them into the P4 launch payload using
    ``build_question_payload(...)``, and writes the same set of session
    keys that standard mock launch uses (``p4_launch_state``,
    ``frozen_question_ids``, ``p4_question_payloads``, ``mock_kind``,
    ``selected_lecture_ids``). No DB write occurs here.
    """
    _validate_class_id(class_id)
    if (
        isinstance(target_question_count, bool)
        or not isinstance(target_question_count, int)
        or target_question_count <= 0
    ):
        raise ValueError("target_question_count must be a positive integer")

    ranked_rows = list(
        selector_fn(class_id=class_id, limit=target_question_count) or []
    )

    payloads: list[dict[str, Any]] = []
    selected_lecture_ids: list[int] = []
    seen_lecture_ids: set[int] = set()
    for row in ranked_rows:
        payload = build_question_payload(row)
        payloads.append(payload)
        lecture_id = payload.get("lecture_id")
        if isinstance(lecture_id, int) and lecture_id not in seen_lecture_ids:
            seen_lecture_ids.add(lecture_id)
            selected_lecture_ids.append(lecture_id)
    selected_lecture_ids.sort()

    available = len(payloads)
    honest_short_copy: str | None = None
    if available == 0:
        honest_short_copy = CUSTOM_MOCK_EMPTY_COPY
    elif available < target_question_count:
        honest_short_copy = CUSTOM_MOCK_HONEST_SHORT_COPY_TEMPLATE.format(
            ready=available,
        )

    state: dict[str, Any] = {
        "ok": available > 0,
        "class_id": int(class_id),
        "class_name": (
            class_name.strip()
            if isinstance(class_name, str) and class_name.strip()
            else None
        ),
        "mock_kind": MOCK_KIND,
        "selected_lecture_ids": selected_lecture_ids,
        "frozen_question_ids": [int(p["id"]) for p in payloads],
        "question_payloads": payloads,
        "target_question_count": int(target_question_count),
        "available_question_count": available,
        "honest_short_copy": honest_short_copy,
        "launch_kind": "custom",
    }

    target_session = (
        session_state if session_state is not None else _default_session_state()
    )
    if available > 0:
        _write_launch_state(target_session, state=state)
    return state

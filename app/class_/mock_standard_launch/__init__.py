"""Selected-lecture mock launch helpers for P3 → P4.

The launch step is deliberately session-only. It freezes the selected
question ids and a small display payload for P4, but it does **not**
create an ``attempts`` row. P4 final submit owns the all-or-nothing DB
write via ``app.db.queries_attempts.finalize_attempt``.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS, KIND LABEL, AND SESSION-STATE KEYS
# --------------------------------------------------------------------------- #
# Simple explanation:
# When a student clicks `TAKE MOCK >`, this module "freezes" the picked
# lectures into a small bundle in `st.session_state` so the P4 take-mock
# page can render the same questions even if the user navigates away and
# back. No DB row is created here — the final submit transaction on P4
# owns the all-or-nothing DB write.
#
# Important code pieces:
# - `MOCK_KIND`: discriminator stored in session state so P4/P5 know if
#   the attempt is a mock or a practice round.
# - `P4_LAUNCH_STATE_KEY` / `FROZEN_QUESTION_IDS_KEY` /
#   `QUESTION_PAYLOADS_KEY` / `MOCK_KIND_KEY` / `SELECTED_LECTURE_IDS_KEY`:
#   the locked Streamlit session-state keys shared with P4 and P5.
# - `TARGET_PER_LECTURE = 5`: how many ready questions Surf aims to pull
#   from each picked lecture; honest shorter-mock copy fires below that.
import json
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any

from app.db.queries_questions import list_ready_questions_for_lecture

MOCK_KIND = "mock"
P4_LAUNCH_STATE_KEY = "p4_launch_state"
FROZEN_QUESTION_IDS_KEY = "frozen_question_ids"
QUESTION_PAYLOADS_KEY = "p4_question_payloads"
MOCK_KIND_KEY = "mock_kind"
SELECTED_LECTURE_IDS_KEY = "selected_lecture_ids"
TARGET_PER_LECTURE = 5

HONEST_SHORT_COPY_TEMPLATE = (
    "Only {ready} ready questions across the picked lectures — Surf will "
    "build a shorter mock with whatever's ready."
)

__all__ = [
    "MOCK_KIND",
    "P4_LAUNCH_STATE_KEY",
    "FROZEN_QUESTION_IDS_KEY",
    "QUESTION_PAYLOADS_KEY",
    "MOCK_KIND_KEY",
    "SELECTED_LECTURE_IDS_KEY",
    "TARGET_PER_LECTURE",
    "build_question_payload",
    "launch_mock_standard",
]


def _default_session_state() -> MutableMapping[str, Any]:
    import streamlit as st

    return st.session_state


def _unique_sorted_positive_ints(values: Iterable[int], *, name: str) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must contain positive integer ids")
        if value not in seen:
            seen.add(value)
            out.append(value)
    out.sort()
    if not out:
        raise ValueError(f"{name} must contain at least one id")
    return out


def _json_list(value: object, *, fallback: list[Any] | None = None) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    if fallback is not None:
        return fallback
    raise ValueError(f"expected JSON list, got {value!r}")


# --------------------------------------------------------------------------- #
# BUILD_QUESTION_PAYLOAD — PROJECT A DB ROW INTO A SAFE FRONTEND PAYLOAD
# --------------------------------------------------------------------------- #
# Simple explanation:
# Reads one question row from SQLite and returns a smaller dict that is
# safe to drop into `st.session_state` for P4/P5. Correct answers,
# rationales, and difficulty-looking columns are intentionally dropped
# here — they are pulled back on review/submit so the student cannot see
# them via the browser dev tools during a live attempt.
def build_question_payload(
    question_row: Mapping[str, Any],
    *,
    lecture_id: int | None = None,
    learning_objective_id: int | None = None,
) -> dict[str, Any]:
    """Return the minimal P4/P5 question payload.

    The payload intentionally preserves ``question_type`` and intentionally
    drops correct answers, rationales, and difficulty-looking fields. Later
    analytics compute type performance from real submitted answers.
    """
    return {
        "id": int(question_row["id"]),
        "lecture_id": (
            int(lecture_id)
            if lecture_id is not None
            else _optional_int(question_row.get("lecture_id"))
        ),
        "learning_objective_id": (
            int(learning_objective_id)
            if learning_objective_id is not None
            else _optional_int(question_row.get("learning_objective_id"))
        ),
        "question_text": str(question_row.get("question_text") or ""),
        "options": _json_list(question_row.get("options_json"), fallback=[]),
        "question_type": question_row.get("question_type"),
        "learning_objective_title": question_row.get("learning_objective_title"),
        "learning_objective_label": question_row.get("learning_objective_label"),
        "source_page": question_row.get("source_page"),
        "language": question_row.get("language"),
    }


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


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


# --------------------------------------------------------------------------- #
# LAUNCH_MOCK_STANDARD — FREEZE THE PICKED LECTURES INTO SESSION STATE
# --------------------------------------------------------------------------- #
# Simple explanation:
# Called by the P3 Class Hub when the student clicks `TAKE MOCK >`. It
# pulls up to `target_per_lecture` ready questions per selected lecture,
# wraps each in a safe payload, and writes the locked session-state keys
# that P4 reads. Honest shorter-mock copy is included when fewer ready
# questions exist than the target.
#
# Important code pieces:
# - `questions_for_lecture_fn`: injection seam; tests pass a fake, the
#   real call hits `list_ready_questions_for_lecture` against SQLite.
# - `_unique_sorted_positive_ints(...)`: validates and de-duplicates the
#   picked lecture ids.
# - `target_per_lecture * len(selected)`: the desired total — the
#   shorter-mock copy fires when actual ready questions are fewer.
def launch_mock_standard(
    *,
    class_id: int,
    selected_lecture_ids: Iterable[int],
    class_name: str | None = None,
    session_state: MutableMapping[str, Any] | None = None,
    questions_for_lecture_fn=list_ready_questions_for_lecture,
    target_per_lecture: int = TARGET_PER_LECTURE,
) -> dict[str, Any]:
    """Freeze a standard mock launch in session state.

    ``target_per_lecture`` defaults to 5, so a mock with N selected
    ready lectures targets ``5 × N`` questions. When a selected lecture
    has fewer ready questions, Surf uses what exists and returns honest
    shorter-mock copy. No DB write occurs here.
    """
    if isinstance(class_id, bool) or not isinstance(class_id, int) or class_id <= 0:
        raise ValueError("class_id must be a positive integer")
    if (
        isinstance(target_per_lecture, bool)
        or not isinstance(target_per_lecture, int)
        or target_per_lecture <= 0
    ):
        raise ValueError("target_per_lecture must be a positive integer")

    selected = _unique_sorted_positive_ints(
        selected_lecture_ids,
        name="selected_lecture_ids",
    )
    selected_rows: list[dict[str, Any]] = []
    for lecture_id in selected:
        rows = list(questions_for_lecture_fn(lecture_id) or [])
        for row in rows[:target_per_lecture]:
            selected_rows.append(
                build_question_payload(row, lecture_id=lecture_id)
            )

    if not selected_rows:
        raise ValueError("selected lectures have no ready questions")

    target_question_count = target_per_lecture * len(selected)
    frozen_question_ids = [int(row["id"]) for row in selected_rows]
    honest_short_copy = None
    if len(selected_rows) < target_question_count:
        honest_short_copy = HONEST_SHORT_COPY_TEMPLATE.format(
            ready=len(selected_rows)
        )

    state = {
        "ok": True,
        "class_id": int(class_id),
        "class_name": (
            class_name.strip()
            if isinstance(class_name, str) and class_name.strip()
            else None
        ),
        "mock_kind": MOCK_KIND,
        "selected_lecture_ids": selected,
        "frozen_question_ids": frozen_question_ids,
        "question_payloads": selected_rows,
        "target_question_count": target_question_count,
        "available_question_count": len(selected_rows),
        "honest_short_copy": honest_short_copy,
    }
    target_session = session_state if session_state is not None else _default_session_state()
    _write_launch_state(target_session, state=state)
    return state

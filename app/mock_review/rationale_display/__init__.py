"""Pure helpers for P5 mock/practice review rationale display.

This module intentionally has no Streamlit, DB, pandas, or model API imports.
It converts raw review-query rows into small Python values that a renderer can
style later without duplicating correctness/rationale rules.
"""
# Converts saved answer rows into safe review display values.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Pure helpers — no Streamlit, no database, no Anthropic client. Only
# `json` for decoding the persisted list fields and the canonical
# question_type lookups so chip labels never invent values that are not in
# the locked taxonomy.
import json
from typing import Any

from app.brain.question_type import QUESTION_TYPE_LABELS, normalize_question_type

__all__ = [
    "classify_option_state",
    "result_stamp_for_attempt",
    "format_question_type_chip_label",
    "format_rationale_text",
    "parse_review_row",
]

_OPTION_STATE_CORRECT = "correct"
_OPTION_STATE_WRONG = "wrong"
_OPTION_STATE_MISSED = "missed"
_OPTION_STATE_NEUTRAL = "neutral"
_OPTION_STATE_SKIPPED = "skipped"


def _coerce_indices(value: object) -> list[int]:
    """Return only integer indices from an already-decoded iterable."""
    if not isinstance(value, (list, tuple, set)):
        return []
    return [item for item in value if isinstance(item, int) and not isinstance(item, bool)]


def _loads_list(value: object) -> list[Any]:
    """Safely decode a JSON list field, returning [] on bad or non-list input."""
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    try:
        decoded = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return []
    return decoded if isinstance(decoded, list) else []


# --------------------------------------------------------------------------- #
# OPTION STATE CLASSIFIER — `classify_option_state`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Looks at one option's index alongside the user's saved answer and the
# question's correct answer set, and returns a small state string that the
# P5 renderer uses to paint the option. Skipped attempts still mark the
# correct option(s) as `missed` so the review can show the user what they
# should have picked, while non-correct options stay in the neutral skipped
# styling.
#
# Important code pieces:
# - `option_index: int`: which of the up-to-4 options this is.
# - The keyword-only `selected_indices`, `correct_indices`, and
#   `was_skipped` parameters: keyword-only (the `*,` argument) so callers
#   cannot accidentally swap them by position.
def classify_option_state(
    option_index: int,
    *,
    selected_indices: object,
    correct_indices: object,
    was_skipped: bool,
) -> str:
    """Classify one option for P5 review styling.

    Returned states are: ``correct``, ``wrong``, ``missed``, ``neutral``, or
    ``skipped``. A skipped answer still marks correct options as ``missed`` so
    the review page can show what the user should have selected, while
    non-correct options receive the global skipped styling.
    """
    # Applies P5 option styling without changing saved answers.
    selected = set(_coerce_indices(selected_indices))
    correct = set(_coerce_indices(correct_indices))

    if was_skipped:
        if option_index in correct:
            return _OPTION_STATE_MISSED
        return _OPTION_STATE_SKIPPED

    if option_index in selected and option_index in correct:
        return _OPTION_STATE_CORRECT
    if option_index in selected and option_index not in correct:
        return _OPTION_STATE_WRONG
    if option_index not in selected and option_index in correct:
        return _OPTION_STATE_MISSED
    return _OPTION_STATE_NEUTRAL


def result_stamp_for_attempt(*, was_skipped: bool, is_correct: bool) -> str:
    """Return the compact attempt result stamp for a review row."""
    if was_skipped:
        return "SKIPPED"
    return "CORRECT" if is_correct else "WRONG"


def format_question_type_chip_label(question_type: object) -> str:
    """Return a human label for a stored question_type slug.

    Unknown, missing, or future values stay honest with ``Type unavailable``
    instead of inventing a label.
    """
    # Shows only labels backed by the stored taxonomy.
    slug = normalize_question_type(question_type)
    return QUESTION_TYPE_LABELS.get(slug, "Type unavailable")


def format_rationale_text(rationale: object) -> str:
    """Return display-safe rationale text with a stable empty fallback."""
    text = "" if rationale is None else str(rationale).strip()
    return text or "Rationale unavailable."


def parse_review_row(row: dict[str, Any]) -> dict[str, Any]:
    """Decode JSON list fields from a raw ``get_attempt_review_rows`` row.

    Bad JSON, missing fields, or non-list JSON values decode to ``[]`` so the
    P5 renderer can continue with honest fallbacks rather than crashing.
    """
    # Decodes list fields while keeping broken rows recoverable.
    parsed = dict(row)
    parsed["selected_indices"] = _coerce_indices(_loads_list(row.get("selected_indices")))
    parsed["options_json"] = _loads_list(row.get("options_json"))
    parsed["correct_indices"] = _coerce_indices(_loads_list(row.get("correct_indices")))
    parsed["rationales_per_option_json"] = _loads_list(
        row.get("rationales_per_option_json")
    )
    return parsed

"""Central Surf V1 question type taxonomy.

Surf stores and displays question types, but does not classify questions with
ML. The provisional slug list stays in Python instead of a SQLite CHECK so a
later taxonomy rename or reduction does not require an immediate schema
migration.
"""
# Central slug list and normalization helpers for question-type display.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# QUESTION-TYPE TAXONOMY — SLUGS, LABELS, AND ALIASES
# --------------------------------------------------------------------------- #
# Simple explanation:
# Surf classifies each generated MCQ by Bloom-style cognitive level
# (knowledge, comprehension, application, ...). The lowercase "slug" is
# what is stored in SQLite and used in prompts; the label is the
# Title-Cased version shown in the UI. The alias map fixes one known
# typo (`analysi` → `analysis`) Claude has occasionally produced.
#
# Important code pieces:
# - `QUESTION_TYPE_SLUGS`: a `tuple[str, ...]` of accepted slugs. Tuples
#   are immutable, which signals "don't mutate this list at runtime".
# - `QUESTION_TYPE_LABELS`: a `dict[str, str]` mapping slug → label.
# - `_QUESTION_TYPE_ALIASES`: a `dict` of typo → canonical slug, used by
#   `normalize_question_type` so a known typo does not silently become an
#   unsupported value.
#
# App connection:
# P4 (Take Mock) and P5 (Review) display the question type per question.
# P6 (Dashboard) aggregates real performance by type. ML wiring is the
# Phase 7 readiness gate; until then, the slug is metadata only.
QUESTION_TYPE_SLUGS: tuple[str, ...] = (
    "evaluation",
    "synthesis",
    "analysis",
    "application",
    "comprehension",
    "knowledge",
)

QUESTION_TYPE_LABELS: dict[str, str] = {
    "evaluation": "Evaluation",
    "synthesis": "Synthesis",
    "analysis": "Analysis",
    "application": "Application",
    "comprehension": "Comprehension",
    "knowledge": "Knowledge",
}

_QUESTION_TYPE_ALIASES: dict[str, str] = {
    "analysi": "analysis",
}


def normalize_question_type(value: object) -> str:
    """Return a stripped lowercase question_type slug or alias target.

    Unsupported values are not rejected here; callers should use
    ``is_valid_question_type(...)`` after normalization. This keeps the helper
    simple at generation/storage boundaries where clear validation errors are
    owned by the caller.
    """
    # --------------------------------------------------------------------- #
    # NORMALIZE_QUESTION_TYPE — STRIP, LOWERCASE, AND ALIAS-MAP
    # --------------------------------------------------------------------- #
    # Simple explanation:
    # Cleans up a raw question-type value so callers can compare against
    # the canonical slug set. It does NOT decide whether the value is
    # valid — that is `is_valid_question_type`'s job — so an unsupported
    # value comes back visibly wrong rather than being silently dropped.
    # Normalize known typo aliases while leaving unsupported values visible.
    normalized = "" if value is None else str(value).strip().lower()
    return _QUESTION_TYPE_ALIASES.get(normalized, normalized)


# --------------------------------------------------------------------------- #
# IS_VALID_QUESTION_TYPE — STRICT CHECK AGAINST THE LOCKED SLUG SET
# --------------------------------------------------------------------------- #
# Simple explanation:
# Returns True only when the (already-normalized) value is one of the
# six accepted slugs. Used by the ingestion validator to reject MCQs
# Claude tagged with an unknown question type.
def is_valid_question_type(value: object) -> bool:
    """Return True when value normalizes to one provisional Surf V1 slug."""
    return normalize_question_type(value) in QUESTION_TYPE_SLUGS

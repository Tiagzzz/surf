"""Central Surf V1 question type taxonomy.

Surf stores and displays question types, but does not classify questions with
ML. The provisional slug list stays in Python instead of a SQLite CHECK so a
later taxonomy rename or reduction does not require an immediate schema
migration.
"""
# Central slug list and normalization helpers for question-type display.
from __future__ import annotations

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
    # Normalize known typo aliases while leaving unsupported values visible.
    normalized = "" if value is None else str(value).strip().lower()
    return _QUESTION_TYPE_ALIASES.get(normalized, normalized)


def is_valid_question_type(value: object) -> bool:
    """Return True when value normalizes to one provisional Surf V1 slug."""
    return normalize_question_type(value) in QUESTION_TYPE_SLUGS

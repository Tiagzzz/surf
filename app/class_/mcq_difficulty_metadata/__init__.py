"""Claude metadata critic for generated Surf MCQs.

This package is intentionally outside ``app/ml`` because it calls Claude. The
pure scoring package consumes only the normalized metadata rows produced here.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS AND MODULE CONSTANTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This package is the Claude-based "critic" that scores generated MCQs on
# five difficulty rubrics plus a wording-clarity flag. It is intentionally
# outside `app/ml/` because it calls Claude; the pure scoring code in
# `app.ml.personal_difficulty` reads only the normalized metadata rows
# this module produces.
#
# Important code pieces:
# - `_SYSTEM_PROMPT_PATH`: sibling `.md` system prompt used in the
#   Surf "~10-line specialist" pattern.
# - `log`: module-level logger so soft failures stay visible.
# - `_SCORE_FIELDS`: maps the rubric names Claude returns ("conceptual
#   density" etc.) to the SQLite column names Surf actually stores.
import json
import logging
from pathlib import Path
from typing import Any

from app.brain.claude_client import call_claude

_SYSTEM_PROMPT_PATH = Path(__file__).with_name("mcq_difficulty_metadata_system_prompt.md")
log = logging.getLogger(__name__)

_SCORE_FIELDS = {
    "distractor_similarity": "difficulty_distractor_similarity",
    "conceptual_density": "difficulty_conceptual_density",
    "distractor_derivation": "difficulty_distractor_derivation",
    "reasoning_steps": "difficulty_reasoning_steps",
    "wording_complexity": "difficulty_wording_complexity",
}


# --------------------------------------------------------------------------- #
# EMPTY_METADATA_FOR_LOCAL_ID — SAFE NULL ROW WHEN CRITIC IS MISSING
# --------------------------------------------------------------------------- #
# Simple explanation:
# Returns the placeholder storage row used when Claude either skips a
# question or fails to score it. Numeric fields stay `None` (NULL in
# SQLite) while the clarity flag falls back to `0` because that column
# is non-nullable.
def empty_metadata_for_local_id(local_id: str) -> dict[str, int | str | None]:
    """Return the null-safe storage row for one generated MCQ local id."""
    # Numeric rubric values stay NULL when Claude omits or corrupts metadata;
    # the clarity flag defaults to 0 because the DB column is non-nullable.
    return {
        "local_id": str(local_id),
        "difficulty_distractor_similarity": None,
        "difficulty_conceptual_density": None,
        "difficulty_distractor_derivation": None,
        "difficulty_reasoning_steps": None,
        "difficulty_wording_complexity": None,
        "difficulty_wording_clarity_issue": 0,
    }


# --------------------------------------------------------------------------- #
# BUILD_METADATA_REQUEST — PACK THE TWO INPUT PIECES THE CRITIC NEEDS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Builds the JSON payload sent to Claude: the original slide markdown
# (so Claude has context) and the generator's per-slide MCQs (so Claude
# can score each `local_id`).
def build_metadata_request(
    slides_batch: list[dict[str, Any]], by_slide: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build the JSON-serializable critic request sent to Claude."""
    return {"slides": slides_batch, "by_slide": by_slide}


# --------------------------------------------------------------------------- #
# SCORE_MCQ_DIFFICULTY_METADATA — PUBLIC ENTRY POINT FOR THE CRITIC
# --------------------------------------------------------------------------- #
# Simple explanation:
# Public function used by the ingestion orchestrator. It calls Claude
# once per batch and turns the response into one storage-shaped row per
# generated `local_id`. The function is soft-failing — when the second
# Claude call fails, every expected id falls back to a null metadata
# row so generated MCQs are still saved without metadata.
def score_mcq_difficulty_metadata(
    slides_batch: list[dict[str, Any]],
    by_slide: list[dict[str, Any]],
    *,
    api_key: str | None = None,
) -> list[dict[str, int | str | None]]:
    """Ask Claude to score generated MCQs, then return normalized metadata rows.

    The function soft-fails: if the second Claude call fails, generated MCQs are
    still usable and each expected ``local_id`` receives null metadata.
    """
    expected_local_ids = _expected_local_ids(by_slide)
    if not expected_local_ids:
        return []

    try:
        response = call_claude(
            system_prompt=_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
            user_message=json.dumps(
                build_metadata_request(slides_batch, by_slide), ensure_ascii=False
            ),
            expect_json=True,
            api_key=api_key,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Claude difficulty metadata call failed: %s", exc)
        return [empty_metadata_for_local_id(local_id) for local_id in expected_local_ids]

    return validate_difficulty_metadata_response(response, expected_local_ids)


# --------------------------------------------------------------------------- #
# VALIDATE_DIFFICULTY_METADATA_RESPONSE — TRUSTED PROJECTION OF RAW JSON
# --------------------------------------------------------------------------- #
# Simple explanation:
# Takes whatever shape Claude returns and rebuilds it into exactly one
# normalized row per expected `local_id`. Rows Claude did not produce
# fall back to the null-safe shape; rows Claude invented (unknown ids)
# are dropped so they can never sneak into SQLite.
def validate_difficulty_metadata_response(
    response: dict[str, Any] | Any,
    expected_local_ids: list[str],
) -> list[dict[str, int | str | None]]:
    """Normalize untrusted Claude metadata into one row per expected local id."""
    # Build by-id rows from trusted local ids only. Unknown ids are ignored so
    # Claude cannot inject extra question metadata into downstream storage.
    expected = [str(local_id) for local_id in expected_local_ids]
    expected_set = set(expected)
    normalized_by_id: dict[str, dict[str, int | str | None]] = {}

    for raw_item in _iter_raw_metadata_items(response):
        if not isinstance(raw_item, dict):
            continue
        local_id = raw_item.get("local_id")
        if local_id is None:
            continue
        local_id = str(local_id)
        if local_id not in expected_set:
            continue
        normalized_by_id[local_id] = _normalize_item(local_id, raw_item)

    return [
        normalized_by_id.get(local_id, empty_metadata_for_local_id(local_id))
        for local_id in expected
    ]


# --------------------------------------------------------------------------- #
# INTERNAL HELPERS — EXTRACT IDS, ITERATE RAW ITEMS, NORMALIZE FIELDS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Small private helpers used by the two public functions above. They
# walk Claude's nested response shape, accept only rubric scores in the
# 1..5 range, and coerce the clarity flag into the SQLite-safe 0/1 int.
#
# Important code pieces:
# - `_coerce_score`: ints, digit strings, and only 1..5 survive; booleans
#   are rejected because `True`/`False` are technically `int` in Python.
# - `_coerce_clarity_issue`: accepts a wider range of truthy/falsy
#   strings ("yes"/"no") in addition to bools/ints because Claude
#   occasionally returns the clarity hint as plain text.
def _expected_local_ids(by_slide: list[dict[str, Any]]) -> list[str]:
    """Extract generated-MCQ local ids in stable batch order."""
    ids: list[str] = []
    for slide_entry in by_slide or []:
        if not isinstance(slide_entry, dict):
            continue
        for mcq in slide_entry.get("mcqs", []) or []:
            if isinstance(mcq, dict) and mcq.get("local_id") is not None:
                ids.append(str(mcq["local_id"]))
    return ids


def _iter_raw_metadata_items(response: dict[str, Any] | Any) -> list[Any]:
    """Return raw difficulty metadata records from Claude's by-slide shape."""
    if not isinstance(response, dict):
        return []
    items: list[Any] = []
    for slide_entry in response.get("by_slide", []) or []:
        if not isinstance(slide_entry, dict):
            continue
        raw_items = slide_entry.get("difficulty_metadata", []) or []
        if isinstance(raw_items, list):
            items.extend(raw_items)
    return items


def _normalize_item(local_id: str, raw_item: dict[str, Any]) -> dict[str, int | str | None]:
    """Normalize one Claude metadata item to Surf storage field names."""
    row = empty_metadata_for_local_id(local_id)
    features = raw_item.get("difficulty_features")
    if not isinstance(features, dict):
        features = raw_item
    for raw_field, storage_field in _SCORE_FIELDS.items():
        row[storage_field] = _coerce_score(features.get(raw_field))
    row["difficulty_wording_clarity_issue"] = _coerce_clarity_issue(
        raw_item.get("wording_clarity_issue")
    )
    return row


def _coerce_score(value: Any) -> int | None:
    """Accept only rubric scores in 1..5; malformed values become None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.strip().isdigit():
        number = int(value.strip())
    else:
        return None
    return number if 1 <= number <= 5 else None


def _coerce_clarity_issue(value: Any) -> int:
    """Convert Claude's clarity flag to SQLite-friendly 0 or 1."""
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int) and not isinstance(value, bool):
        return 1 if value == 1 else 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return 1
        if lowered in {"false", "no", "0"}:
            return 0
    return 0

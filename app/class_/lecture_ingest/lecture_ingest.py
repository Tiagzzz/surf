"""Surf lecture ingestion orchestrator.

Runs the app pipeline:
    PDF -> Markdown -> split and batch -> LO extraction -> MCQ generation -> DB.

The pipeline supports partial success, stops MCQ generation when LO extraction
fails, retries each generation call twice, and treats empty MCQ arrays as
ignored slides.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Callable

from app.brain.claude_client import call_claude
from app.brain.ingestion.page_splitter import batch_slides, split_lecture_md
from app.brain.ingestion.pdf_to_md_v3 import extract_with_tables
from app.brain.question_type import is_valid_question_type, normalize_question_type
from app.class_.lo_extract import extract_los
from app.class_.mcq_difficulty_metadata import (
    empty_metadata_for_local_id,
    score_mcq_difficulty_metadata,
)
from app.class_.mcq_generate import MAX_BATCH_SIZE, generate_mcqs
from app.db.queries_classes import get_class_by_id
from app.db.queries_learning_objectives import insert_learning_objective
from app.db.queries_lectures import insert_lecture, set_lecture_status
from app.db.queries_pages import insert_slide_page, set_slide_page_status
from app.db.queries_questions import insert_question

log = logging.getLogger(__name__)
_SPARSE_EXTRACTION_NON_WS_CHARS = 150
_PAGE_MARKER_RE = re.compile(r"^---\s+PAGE\s+\d+\s+---\s*$", re.MULTILINE)
_LO_SYSTEM_PROMPT_PATH = Path(__file__).parents[1] / "lo_extract" / "lo_extractor_system_prompt.md"

# Only these factsheet keys are passed to the LO extractor.
_FACTSHEET_TOP_KEYS = ("surf_extraction_notes", "FSLO")
_FACTSHEET_CCC_KEYS = (
    "narrative_summary",
    "main_topics",
    "important_concepts_models_methods",
    "skills_students_are_expected_to_develop",
)
_FACTSHEET_ASSESS_KEYS = ("exam_relevant_content",)
_METADATA_STORAGE_FIELDS = (
    "difficulty_distractor_similarity",
    "difficulty_conceptual_density",
    "difficulty_distractor_derivation",
    "difficulty_reasoning_steps",
    "difficulty_wording_complexity",
)


def _build_factsheet_subset(factsheet: dict[str, Any]) -> dict[str, Any]:
    """Curate the 7-key factsheet subset for the LO prompt.

    Missing keys default to None so the system prompt always sees a complete shape.
    """
    ccc = factsheet.get("core_course_content", {}) or {}
    assess = factsheet.get("assessment_and_grading", {}) or {}
    subset: dict[str, Any] = {k: factsheet.get(k) for k in _FACTSHEET_TOP_KEYS}
    subset["core_course_content"] = {k: ccc.get(k) for k in _FACTSHEET_CCC_KEYS}
    subset["assessment_and_grading"] = {k: assess.get(k) for k in _FACTSHEET_ASSESS_KEYS}
    return subset


def _call_with_retry(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Call a generation helper up to two times, without backoff."""
    last_exc: BaseException | None = None
    for attempt in (1, 2):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            log.warning("Claude call attempt %d failed: %s", attempt, exc)
    assert last_exc is not None
    raise last_exc


def _default_extract_los(
    lecture_md: str,
    factsheet_subset: dict[str, Any],
    *,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Call the standard LO extractor, preserving per-call key routing."""
    if api_key is None:
        return extract_los(lecture_md, factsheet_subset)

    user_message = json.dumps(
        {"lecture_md": lecture_md, "factsheet_subset": factsheet_subset},
        ensure_ascii=False,
    )
    return call_claude(
        system_prompt=_LO_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
        user_message=user_message,
        expect_json=True,
        api_key=api_key,
    )


def _find_lo_id(page_number: int, lo_records: list[tuple[int, int, int]]) -> int | None:
    """Return the first LO covering a page, or None for a pending slide."""
    for lo_id, start, end in lo_records:
        if start <= page_number <= end:
            return lo_id
    return None


def _validate_mcq(mcq: dict[str, Any]) -> bool:
    """Validate generated MCQ shape before storage.

    Rejects MCQs whose ``correct_indices``:
      - is missing or not a list,
      - is empty (no correct answer is invalid for a generated multi-select),
      - contains non-integer values,
      - contains duplicates (for example ``[0, 0]``),
      - or contains values outside ``0..3`` (the 4-option MCQ shape).

    This guard runs before DB/query handoff so invalid generated rows never
    reach `attempt_answers` matching at grading time. The query layer keeps a
    second defensive check for the same invariant.
    """
    try:
        opts = mcq["options"]
        idx = mcq["correct_indices"]
        rats = mcq["rationales_per_option"]
        question_type = normalize_question_type(mcq["question_type"])
    except (KeyError, TypeError):
        return False
    if not is_valid_question_type(question_type):
        return False
    mcq["question_type"] = question_type
    if not (isinstance(opts, list) and len(opts) == 4):
        return False
    if not (isinstance(rats, list) and len(rats) == 4):
        return False
    if not isinstance(idx, list) or not idx:
        return False
    if not all(isinstance(i, int) and not isinstance(i, bool) for i in idx):
        return False
    if not all(0 <= i < 4 for i in idx):
        return False
    if len(set(idx)) != len(idx):  # Reject duplicates like [0, 0].
        return False
    if len(idx) > 4:
        return False
    return True


def _local_id_for_mcq(mcq: dict[str, Any], fallback_page: int, index: int) -> str:
    """Return the deterministic ingestion-only metadata id for one valid MCQ."""
    # Prefer the MCQ's source page; fall back to the batch page if Claude mangles it.
    try:
        source_page = int(mcq.get("source_page", fallback_page))
    except (TypeError, ValueError):
        source_page = fallback_page
    return f"{source_page}-{index}"


def _coerce_metadata_score(value: Any) -> int | None:
    """Keep only the 1..5 rubric scores ingestion knows how to store."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and 1 <= value <= 5:
        return value
    return None


def _coerce_metadata_clarity_issue(value: Any) -> int:
    """Return the SQLite 0/1 clarity flag; malformed values use the safe 0 fallback."""
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int) and not isinstance(value, bool):
        return 1 if value == 1 else 0
    return 0


def _metadata_rows_by_local_id(
    rows: Any,
    expected_local_ids: list[str],
) -> dict[str, dict[str, int | str | None]]:
    """Normalize metadata rows from the critic seam into storage rows by local id."""
    if not isinstance(rows, list):
        if expected_local_ids:
            log.warning(
                "Claude difficulty metadata returned malformed rows; storing null metadata"
            )
        return {}

    expected = set(expected_local_ids)
    normalized: dict[str, dict[str, int | str | None]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        local_id = row.get("local_id")
        if local_id is None:
            continue
        local_id = str(local_id)
        if local_id not in expected:
            continue
        storage_row = empty_metadata_for_local_id(local_id)
        for field in _METADATA_STORAGE_FIELDS:
            storage_row[field] = _coerce_metadata_score(row.get(field))
        storage_row["difficulty_wording_clarity_issue"] = _coerce_metadata_clarity_issue(
            row.get("difficulty_wording_clarity_issue")
        )
        normalized[local_id] = storage_row
    return normalized


def _score_metadata_for_batch(
    metadata_fn: Callable[..., Any] | None,
    slides_batch: list[dict[str, Any]],
    by_slide: list[dict[str, Any]],
    api_key_kwargs: dict[str, str],
) -> dict[str, dict[str, int | str | None]]:
    """Call the optional metadata critic once and return rows keyed by local id."""
    expected_local_ids = [
        str(mcq["local_id"])
        for slide_entry in by_slide
        for mcq in slide_entry.get("mcqs", [])
        if isinstance(mcq, dict) and mcq.get("local_id") is not None
    ]
    if metadata_fn is None or not expected_local_ids:
        return {}
    try:
        rows = metadata_fn(slides_batch, by_slide, **api_key_kwargs)
    except Exception:  # noqa: BLE001
        log.warning(
            "Claude difficulty metadata call failed; storing null metadata for %d MCQs",
            len(expected_local_ids),
        )
        return {}
    return _metadata_rows_by_local_id(rows, expected_local_ids)


def ingest_lecture(
    class_id: int,
    pdf_path: Path,
    *,
    title: str | None = None,
    api_key: str | None = None,
    claude_call_lo: Callable[..., dict[str, Any]] | None = None,
    claude_call_mcq: Callable[..., dict[str, Any]] | None = None,
    claude_call_difficulty_metadata: Callable[..., Any] | None = None,
) -> int:
    """5-step ingestion. See module docstring for the policies honored."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    if title is None or not title.strip():
        raise ValueError("lecture title is required before uploading a lecture.")
    title = title.strip()

    lo_fn = claude_call_lo or _default_extract_los
    mcq_fn = claude_call_mcq or generate_mcqs
    metadata_fn = claude_call_difficulty_metadata
    if metadata_fn is None and claude_call_mcq is None:
        metadata_fn = score_mcq_difficulty_metadata

    # Step 1: PDF -> MD
    markdown, _tables, _chars = extract_with_tables(pdf_path)
    markerless_markdown = _PAGE_MARKER_RE.sub("", markdown)
    if len(re.sub(r"\s+", "", markerless_markdown)) < _SPARSE_EXTRACTION_NON_WS_CHARS:
        raise RuntimeError(
            "Surf could not read enough text from this PDF. Please re-upload a "
            "searchable/OCR PDF or export the lecture slides again before retrying."
        )
    slides = split_lecture_md(markdown)
    if not slides:
        raise ValueError(f"No slides parsed from {pdf_path} (no `--- PAGE N ---` markers).")
    total_pages = max(s["page_number"] for s in slides)

    # Create the lecture record in a pending state before generation starts.
    klass = get_class_by_id(class_id)
    if klass is None:
        raise ValueError(f"class_id {class_id} not found")
    factsheet_subset = _build_factsheet_subset(klass.get("factsheet_json") or {})
    lecture_id = insert_lecture(
        class_id=class_id,
        title=title,
        source_pdf_path=str(pdf_path),
        total_pages=total_pages,
        status='pending',
    )

    # Extract learning objectives with one retry; failed extraction marks the lecture failed.
    api_key_kwargs = {"api_key": api_key} if api_key is not None else {}
    try:
        lo_response = _call_with_retry(lo_fn, markdown, factsheet_subset, **api_key_kwargs)
    except Exception:
        log.exception(
            "LO extraction failed both attempts; marking lecture %d as 'failed'", lecture_id
        )
        set_lecture_status(lecture_id, 'failed')
        return lecture_id  # No MCQ generation runs after LO extraction fails.

    learning_objectives = lo_response.get("learning_objectives", []) or []
    ignored_pages = {p["page_number"] for p in lo_response.get("ignored_pages", []) or []}

    lo_records: list[tuple[int, int, int]] = []
    for lo in learning_objectives:
        page_range = lo.get("page_range") or [0, 0]
        lo_id = insert_learning_objective(
            lecture_id=lecture_id,
            title=lo.get("title", ""),
            page_start=int(page_range[0]),
            page_end=int(page_range[1]),
        )
        lo_records.append((lo_id, int(page_range[0]), int(page_range[1])))

    # Persist slide_pages: kept slides bound to LO; ignored slides flagged.
    slide_id_by_page: dict[int, int] = {}
    for s in slides:
        page = s["page_number"]
        if page in ignored_pages:
            sid = insert_slide_page(
                lecture_id, page, s["raw_md"],
                status='ignored', learning_objective_id=None,
            )
        else:
            lo_id = _find_lo_id(page, lo_records)
            status = 'kept' if lo_id is not None else 'pending'
            sid = insert_slide_page(
                lecture_id, page, s["raw_md"],
                status=status, learning_objective_id=lo_id,
            )
        slide_id_by_page[page] = sid

    # Step 4: generate MCQs per batch, keeping partial successes.
    kept_slides = [
        s for s in slides
        if s["page_number"] not in ignored_pages
        and _find_lo_id(s["page_number"], lo_records) is not None
    ]
    any_failure = False
    for batch in batch_slides(kept_slides, size=MAX_BATCH_SIZE):
        try:
            response = _call_with_retry(mcq_fn, batch, **api_key_kwargs)
        except Exception:
            log.exception(
                "MCQ batch failed both attempts; flipping %d slides to 'pending'", len(batch)
            )
            any_failure = True
            for s in batch:
                set_slide_page_status(slide_id_by_page[s["page_number"]], 'pending')
            continue

        by_slide = response.get("by_slide", []) or []
        valid_entries: list[tuple[int, dict[str, Any]]] = []
        metadata_by_slide: list[dict[str, Any]] = []
        for entry in by_slide:
            page = entry.get("page_number")
            mcqs = entry.get("mcqs", []) or []
            if page not in slide_id_by_page:
                continue  # Claude returned a page not in batch — skip
            sid = slide_id_by_page[page]
            if not mcqs:
                # Empty MCQ arrays mean the slide has no usable question content.
                set_slide_page_status(sid, 'ignored')
                continue
            valid_mcqs: list[dict[str, Any]] = []
            for index, mcq in enumerate(mcqs):
                if not _validate_mcq(mcq):
                    log.warning("Skipping invalid MCQ for page %d", page)
                    continue
                mcq["local_id"] = _local_id_for_mcq(mcq, int(page), index)
                valid_mcqs.append(mcq)
                valid_entries.append((sid, mcq))
            if valid_mcqs:
                metadata_by_slide.append({"page_number": page, "mcqs": valid_mcqs})

        metadata_by_id = _score_metadata_for_batch(
            metadata_fn,
            batch,
            metadata_by_slide,
            api_key_kwargs,
        )
        for sid, mcq in valid_entries:
            local_id = str(mcq["local_id"])
            metadata = metadata_by_id.get(local_id, empty_metadata_for_local_id(local_id))
            fallback_page = int(local_id.split("-", maxsplit=1)[0])
            try:
                source_page = int(mcq.get("source_page", fallback_page))
            except (TypeError, ValueError):
                source_page = fallback_page
            question_text = mcq.get("question", "")
            try:
                insert_question(
                    slide_page_id=sid,
                    question_text=question_text,
                    options=list(mcq["options"]),
                    correct_indices=list(mcq["correct_indices"]),
                    rationales_per_option=list(mcq["rationales_per_option"]),
                    question_type=mcq["question_type"],
                    source_page=source_page,
                    language=mcq.get("language", lo_response.get("language", "en")),
                    difficulty_word_count=len(question_text.split()),
                    difficulty_distractor_similarity=metadata[
                        "difficulty_distractor_similarity"
                    ],
                    difficulty_conceptual_density=metadata[
                        "difficulty_conceptual_density"
                    ],
                    difficulty_distractor_derivation=metadata[
                        "difficulty_distractor_derivation"
                    ],
                    difficulty_reasoning_steps=metadata["difficulty_reasoning_steps"],
                    difficulty_wording_complexity=metadata[
                        "difficulty_wording_complexity"
                    ],
                    difficulty_wording_clarity_issue=int(
                        metadata["difficulty_wording_clarity_issue"] or 0
                    ),
                )
            except ValueError as exc:
                log.warning("Skipping invalid MCQ for page %s: %s", source_page, exc)
                continue

    set_lecture_status(lecture_id, 'ready' if not any_failure else 'pending')
    return lecture_id

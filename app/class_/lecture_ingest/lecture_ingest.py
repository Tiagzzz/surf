"""Surf — lecture ingestion orchestrator.

Implements the 5-step pipeline from D-4.2:
    PDF -> MD -> split+batch -> LO-extract -> MCQ-generate -> DB.

Honors the partial-success policy (D-4.5), the LO-failure policy (D-4.7),
the 2-attempt retry policy (D-4.4), and the empty-MCQ-array rule (D-4.8).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from app.brain.ingestion.page_splitter import batch_slides, split_lecture_md
from app.brain.ingestion.pdf_to_md_v3 import extract_with_tables
from app.class_.lo_extract import extract_los
from app.class_.mcq_generate import MAX_BATCH_SIZE, generate_mcqs
from app.db.queries_classes import get_class_by_id
from app.db.queries_learning_objectives import insert_learning_objective
from app.db.queries_lectures import insert_lecture, set_lecture_status
from app.db.queries_pages import insert_slide_page, set_slide_page_status
from app.db.queries_questions import insert_question

log = logging.getLogger(__name__)

# D-1.2: the only factsheet keys that pass to the LO-extractor.
_FACTSHEET_TOP_KEYS = ("surf_extraction_notes", "FSLO")
_FACTSHEET_CCC_KEYS = (
    "narrative_summary",
    "main_topics",
    "important_concepts_models_methods",
    "skills_students_are_expected_to_develop",
)
_FACTSHEET_ASSESS_KEYS = ("exam_relevant_content",)


def _build_factsheet_subset(factsheet: dict[str, Any]) -> dict[str, Any]:
    """Curate the 7-key subset (D-1.2). Missing keys default to None so the
    system prompt always sees a complete shape."""
    ccc = factsheet.get("core_course_content", {}) or {}
    assess = factsheet.get("assessment_and_grading", {}) or {}
    subset: dict[str, Any] = {k: factsheet.get(k) for k in _FACTSHEET_TOP_KEYS}
    subset["core_course_content"] = {k: ccc.get(k) for k in _FACTSHEET_CCC_KEYS}
    subset["assessment_and_grading"] = {k: assess.get(k) for k in _FACTSHEET_ASSESS_KEYS}
    return subset


def _call_with_retry(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """D-4.4: 2 attempts, no backoff."""
    last_exc: BaseException | None = None
    for attempt in (1, 2):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — retry-all per D-4.4
            last_exc = exc
            log.warning("Claude call attempt %d failed: %s", attempt, exc)
    assert last_exc is not None
    raise last_exc


def _find_lo_id(page_number: int, lo_records: list[tuple[int, int, int]]) -> int | None:
    """lo_records is [(lo_id, page_start, page_end), ...]; return the first
    matching lo_id or None when no LO covers the page (D-1.5 violation —
    caller treats this slide as 'pending')."""
    for lo_id, start, end in lo_records:
        if start <= page_number <= end:
            return lo_id
    return None


def _validate_mcq(mcq: dict[str, Any]) -> bool:
    """Defensive: schema rules from D-2.4/D-2.5/D-2.6."""
    try:
        opts = mcq["options"]
        idx = mcq["correct_indices"]
        rats = mcq["rationales_per_option"]
        return (
            isinstance(opts, list) and len(opts) == 4
            and isinstance(rats, list) and len(rats) == 4
            and isinstance(idx, list) and 1 <= len(idx) <= 4
            and all(isinstance(i, int) and 0 <= i < 4 for i in idx)
        )
    except (KeyError, TypeError):
        return False


def ingest_lecture(
    class_id: int,
    pdf_path: Path,
    *,
    title: str | None = None,
    claude_call_lo: Callable[..., dict[str, Any]] | None = None,
    claude_call_mcq: Callable[..., dict[str, Any]] | None = None,
) -> int:
    """5-step ingestion. See module docstring for the policies honored."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    lo_fn = claude_call_lo or extract_los
    mcq_fn = claude_call_mcq or generate_mcqs

    # Step 1: PDF -> MD
    markdown, _tables, _chars = extract_with_tables(pdf_path)
    slides = split_lecture_md(markdown)
    if not slides:
        raise ValueError(f"No slides parsed from {pdf_path} (no `--- PAGE N ---` markers).")
    total_pages = max(s["page_number"] for s in slides)

    # Insert lectures row up front (status='pending' — D-4.7 default)
    klass = get_class_by_id(class_id)
    if klass is None:
        raise ValueError(f"class_id {class_id} not found")
    factsheet_subset = _build_factsheet_subset(klass.get("factsheet_json") or {})
    lecture_id = insert_lecture(
        class_id=class_id,
        title=title or pdf_path.stem,
        source_pdf_path=str(pdf_path),
        total_pages=total_pages,
        status='pending',
    )

    # Step 3: LO-extract once (D-4.4 retry, D-4.7 failure handling)
    try:
        lo_response = _call_with_retry(lo_fn, markdown, factsheet_subset)
    except Exception:
        log.exception(
            "LO extraction failed both attempts; lecture %d remains 'pending'", lecture_id
        )
        return lecture_id  # D-4.7: no MCQ runs

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
            status = 'kept' if lo_id is not None else 'pending'  # D-1.5 defensive
            sid = insert_slide_page(
                lecture_id, page, s["raw_md"],
                status=status, learning_objective_id=lo_id,
            )
        slide_id_by_page[page] = sid

    # Step 4: MCQ-generate per batch (D-4.3 size 10, D-4.4 retry, D-4.5 partial)
    kept_slides = [
        s for s in slides
        if s["page_number"] not in ignored_pages
        and _find_lo_id(s["page_number"], lo_records) is not None
    ]
    any_failure = False
    for batch in batch_slides(kept_slides, size=MAX_BATCH_SIZE):
        try:
            response = _call_with_retry(mcq_fn, batch)
        except Exception:
            log.exception(
                "MCQ batch failed both attempts; flipping %d slides to 'pending'", len(batch)
            )
            any_failure = True
            for s in batch:
                set_slide_page_status(slide_id_by_page[s["page_number"]], 'pending')
            continue

        by_slide = response.get("by_slide", []) or []
        for entry in by_slide:
            page = entry.get("page_number")
            mcqs = entry.get("mcqs", []) or []
            if page not in slide_id_by_page:
                continue  # Claude returned a page not in batch — skip
            sid = slide_id_by_page[page]
            if not mcqs:
                # D-4.8: empty array -> reclassify as ignored
                set_slide_page_status(sid, 'ignored')
                continue
            for mcq in mcqs:
                if not _validate_mcq(mcq):
                    log.warning("Skipping invalid MCQ for page %d", page)
                    continue
                question_text = mcq.get("question", "")
                insert_question(
                    slide_page_id=sid,
                    question_text=question_text,
                    options=list(mcq["options"]),
                    correct_indices=list(mcq["correct_indices"]),
                    rationales_per_option=list(mcq["rationales_per_option"]),
                    source_page=int(mcq.get("source_page", page)),
                    language=mcq.get("language", lo_response.get("language", "en")),
                    difficulty_word_count=len(question_text.split()),
                    # readability + distractor_similarity left None (Phase 4)
                )

    set_lecture_status(lecture_id, 'ready' if not any_failure else 'pending')
    return lecture_id

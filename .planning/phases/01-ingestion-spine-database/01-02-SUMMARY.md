---
phase: 01-ingestion-spine-database
plan: 02
subsystem: ingestion
tags: [pdf, markdown, regex, splitter, batcher, python311]

requires: []
provides:
  - "pdf_to_md_v3 now emits `--- PAGE N ---` markers (D-4.1) instead of `# Page N` headings, in both extraction paths (native + OCR)"
  - "app/brain/ingestion/page_splitter package: split_lecture_md(md) and batch_slides(slides, size=10)"
affects:
  - "01-03 (LO extractor): consumes the full lecture markdown directly; the new marker format gives it deterministic page-range citations"
  - "01-04 (MCQ generator): consumes one batch (≤10 slide records) per Claude call"
  - "01-05 (orchestrator): wires PDF → pdf_to_md_v3 → split_lecture_md → batch_slides → mcq_generate"

tech-stack:
  added: []
  patterns:
    - "Regex page splitter with multiline anchors: `^---\\s+PAGE\\s+(\\d+)\\s+---\\s*$`"
    - "Pure-stdlib splitter (no pandas/numpy here — those live in the DB layer only)"

key-files:
  created:
    - app/brain/ingestion/page_splitter/__init__.py
    - app/brain/ingestion/page_splitter/page_splitter.py
    - app/brain/ingestion/page_splitter/page_splitter.md
  modified:
    - app/brain/ingestion/pdf_to_md_v3.py (2 surgical edits — both marker emission sites)
    - app/brain/ingestion/pdf_to_md_v3.md (5 surgical edits — user-facing description + 3 code-block snippets + main-loop blurb)

key-decisions:
  - "D-4.1 honored: marker is `--- PAGE N ---` on its own line, replacing the old `# Page N` heading in BOTH extract_with_tables() and ocr_pdf()"
  - "D-4.3 honored: batch_slides default size = 10 (DEFAULT_BATCH_SIZE constant)"
  - "Sidecar pattern: surgical edit only (the 4 lines mentioning the marker contract). Did NOT rewrite the dense pre-existing pdf_to_md_v3.md — that's a deferred housekeeping item per the plan's instructions."

patterns-established:
  - "Per-slide record shape: {page_number: int, raw_md: str}. raw_md is .strip()-ed; preserves multi-line content within a slide."
  - "Splitter drops any preamble before the first `--- PAGE 1 ---` marker (intentional — pdf_to_md_v3 never emits preamble)."
  - "batch_slides raises ValueError on size<1 (defensive — the only invalid case)."

requirements-completed:
  - PIPE-01
  - "MECH-04 (partial — first segment of canonical data flow)"

duration: ~10min
completed: 2026-05-01
---

# Plan 01-02: PDF Marker Migration + page_splitter

**Lecture markdown now flows from `pdf_to_md_v3` through `page_splitter` as deterministic per-slide records, ready for batched MCQ generation.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-05-01
- **Tasks:** 2
- **Files modified:** 5 (2 modified + 3 created)

## Accomplishments

- Both PDF→MD code paths (`extract_with_tables` and `ocr_pdf`) now emit the locked `--- PAGE N ---` marker. The legacy `# Page N` heading is gone everywhere.
- A new `page_splitter` package exposes the two pure functions every downstream pipeline needs: `split_lecture_md(md)` and `batch_slides(slides, size=10)`.
- Round-trip on a synthetic 3-page markdown verified end-to-end: 3 records returned, page numbers captured, `raw_md` correctly stripped, preamble dropped, 11 slides correctly batched as `[10, 1]`.

## Task Commits

1. **Task 1: pdf_to_md_v3 marker migration + sidecar update** — `86228b2` (feat)
2. **Task 2: page_splitter package + sidecar** — `77394fa` (feat)

## Files Created

- `app/brain/ingestion/page_splitter/__init__.py` — re-exports `split_lecture_md`, `batch_slides`
- `app/brain/ingestion/page_splitter/page_splitter.py` (39L) — regex splitter + batcher
- `app/brain/ingestion/page_splitter/page_splitter.md` (36L) — sidecar

## Files Modified

- `app/brain/ingestion/pdf_to_md_v3.py` — 2 surgical edits at lines 22 and 103
- `app/brain/ingestion/pdf_to_md_v3.md` — 5 surgical edits to lines that mention the marker contract; the file as a whole stays "too dense" by C-22 — full rewrite is deferred housekeeping per the plan's explicit instruction

## Verification

- `pytest -q`: 2 passed, 2 skipped
- `ruff check app/brain/ingestion/page_splitter/`: all checks passed
- Behavioural verify: 3-page split + preamble drop + empty input + 11→10+1 batch all pass
- Acceptance grep checks: 5 `--- PAGE` references in the sidecar + 2 in the source; 0 `# Page ` left in either

## Self-Check: PASSED

All acceptance criteria met. No deviations from plan.

## Note for downstream

- **Plan 03 (LO extractor)** does NOT use `page_splitter` — it gets the full lecture markdown so Claude can reason across slide boundaries.
- **Plan 04 (MCQ generator)** is the consumer of `batch_slides`. Each Claude call receives one batch (≤10 slide records: `{"page_number": int, "raw_md": str}`).

## Pre-existing tech debt observed (not fixed per Surgical Changes rule)

`ruff check app/brain/ingestion/pdf_to_md_v3.py` reports 5 pre-existing issues (E501 line-too-long on lines 2/168/169/170; I001 import order on lines 3-9). None of these were introduced by this plan and none are in the lines I touched (22, 103). Flagging here for future housekeeping.

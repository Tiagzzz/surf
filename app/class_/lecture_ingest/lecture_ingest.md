# `lecture_ingest.py` — lecture ingestion orchestrator

This module turns one uploaded lecture PDF plus a required lecture title into stored lectures, slide pages, learning objectives, and generated questions.

## Inputs / outputs

- **Input:** `class_id`, `pdf_path`, required `title`, optional per-call `api_key`, and optional fake generation/metadata functions for tests.
- **Output:** the new `lecture_id`.
- **DB writes:** `lectures`, `slide_pages`, `learning_objectives`, and `questions` through query helpers only.
- **External calls:** PDF extraction through `app.brain.ingestion.pdf_to_md_v3.extract_with_tables`, then Anthropic calls through the LO, MCQ, and optional MCQ difficulty-metadata wrappers.

## Data flow

```text
ingest_lecture(class_id, pdf_path, title=..., api_key=...)
        │
        ├── validate file exists and title is non-blank
        ├── extract PDF to Markdown and reject sparse extraction
        ├── insert pending lecture row
        ├── build 7-key factsheet subset from the class factsheet
        ├── extract learning objectives and ignored pages
        ├── write LO rows and slide-page rows
        ├── generate MCQs in batches of up to 10 kept slides
        ├── validate each generated MCQ and assign ingestion-only local_id values
        ├── call the Phase 7.1 metadata critic once per valid MCQ batch
        ├── store valid questions with metadata or null-safe metadata fallback
        └── set lecture status to ready, pending, or failed
```

## Connected code and tools

- `app.class_.lo_extract.extract_los` and `app.class_.mcq_generate.generate_mcqs` call the shared Anthropic wrapper.
- `app.class_.mcq_difficulty_metadata.score_mcq_difficulty_metadata` is the second Claude call for intrinsic MCQ difficulty metadata; it stays outside `app/ml/**` because it can call Claude.
- `app.brain.question_type` normalizes and validates stored `question_type` slugs.
- `app.db.queries_*` helpers perform SQLite writes.
- `app.class_.class_hub.submit_add_lecture_form(...)` calls this function after validating UI inputs and fetching the saved key.

## Two-call MCQ + metadata flow

Lecture ingestion deliberately separates generation from enrichment:

1. **First Claude call:** `generate_mcqs(...)` creates candidate MCQs for a slide batch.
2. **Generated-boundary validation:** `_validate_mcq(...)` keeps only MCQs with four options, four rationales, 1..4 unique `correct_indices` in `0..3`, and one normalized Surf `question_type`.
3. **Local ID assignment:** each valid MCQ receives an ingestion-only ID such as `12-0`. The ID is not a product field and is not stored in SQLite; it only lets the second call match metadata to the already-validated MCQ.
4. **Second Claude call:** `score_mcq_difficulty_metadata(...)` reads the valid MCQs and source slides, then returns the five `1..5` rubric fields plus `wording_clarity_issue`.
5. **Storage handoff:** valid metadata is passed into `insert_question(...)`; missing, malformed, or failed metadata leaves the nullable rubric fields as `NULL` and uses `difficulty_wording_clarity_issue=0`.

The metadata call is soft enrichment. If it fails, valid generated MCQs are still inserted and can still be used for standard mocks, Custom Mock ranking, P5 review, and later scoring fallback logic.

## Code walkthrough

### Constants and factsheet subset helpers
`_FACTSHEET_TOP_KEYS`, `_FACTSHEET_CCC_KEYS`, and `_FACTSHEET_ASSESS_KEYS` define the seven factsheet fields sent to the LO prompt. `_build_factsheet_subset(...)` fills that exact shape with `None` for missing values.

### `_call_with_retry(...)`
Runs the passed generation function up to two times. It logs failed attempts and re-raises the last exception if both attempts fail.

### `_default_extract_los(...)`
Routes LO extraction through `extract_los(...)` normally, or directly through `call_claude(...)` when the Class Hub passes a saved per-user API key.

### `_find_lo_id(...)`
Finds the first learning objective whose stored page range covers a slide. Slides with no matching LO stay `pending`.

### `_validate_mcq(...)`
Validates generated MCQ shape before storage: four options, four rationales, 1–4 unique integer correct indices in range, and one valid normalized `question_type`. Invalid MCQs are skipped without failing the whole lecture.

### Metadata helper functions
`_local_id_for_mcq(...)` assigns deterministic batch-local IDs such as `1-0`
so the second Claude call can match metadata back to generated MCQs without
comparing question text. `_score_metadata_for_batch(...)` calls the injected
metadata fake or the production `score_mcq_difficulty_metadata(...)` wrapper
once per batch of valid MCQs. `_metadata_rows_by_local_id(...)` accepts only
rows for expected local IDs, coerces the five `1..5` rubric scores, and turns
malformed metadata into the same null-safe row shape used by
`empty_metadata_for_local_id(...)`.

### `ingest_lecture(...)`
Coordinates the full pipeline. It inserts the lecture only after PDF extraction passes the sparse-content check, marks LO-extraction failures as `failed`, stores ignored slides as `ignored`, keeps unmatched slides `pending`, stores only valid generated questions, and marks the lecture `ready` unless a whole MCQ batch failed. After MCQ generation succeeds, it validates the MCQs, calls the metadata critic for the valid rows, and passes the six storage fields into `insert_question(...)`: distractor similarity, conceptual density, distractor derivation, reasoning steps, wording complexity, and wording clarity issue. Metadata failure is soft: valid MCQs are still inserted with nullable rubric fields left `NULL` and `difficulty_wording_clarity_issue=0`; the lecture and slide statuses are not flipped solely because metadata failed or was malformed.

## Testing notes

```bash
python -m pytest -q tests/test_lecture_ingest_title_required.py tests/test_lecture_ingest_per_call_key.py tests/test_lecture_ingest_per_mcq_isolation.py tests/test_lecture_ingest_ocr_fail_fast.py tests/test_lecture_ingest_failed_status.py tests/test_question_type_generation_validation.py
python -m ruff check app/class_/lecture_ingest --no-cache
```

Phase 7.1 metadata tests inject fake MCQ and metadata functions. If a test injects a fake MCQ generator but no metadata fake, ingestion must not accidentally call live Claude; it stores null metadata instead. Normal production ingestion still uses the second metadata critic when the default MCQ generator is used.

## What could break if changed

- Allowing blank titles would make Class Hub cards ambiguous.
- Sending the full factsheet can waste tokens and drift from the prompt contract.
- Letting one malformed MCQ stop the whole lecture would discard valid questions.
- Storing invalid `correct_indices` would break multi-select grading.
- Treating a metadata-critic failure like MCQ-generation failure would discard
  valid questions and incorrectly leave slides/lectures pending.
- Running MCQ generation after LO extraction fails would create questions without a reliable slide-to-LO map.
- Reading environment keys here would bypass the saved-key UI flow.

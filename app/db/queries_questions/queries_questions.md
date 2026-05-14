# queries_questions.md

This file is the small set of helpers Surf uses to save and read
multiple-choice questions (MCQs) inside the local database. There is
one row per question, and each row carries the question text, its
four answer options, the index of every correct option, a short
explanation for each option, the canonical `question_type` slug, and optional
intrinsic difficulty metadata from the Phase 7.1 Claude critic.
Lists like the four options are stored as JSON text in a single column
to keep the table small. Before the row is saved, the helper runs a
strict safety check that rejects any malformed MCQ (wrong number of
options, duplicate correct answers, indices outside 0..3, etc.) so a
broken question can never reach grading. It also validates `question_type`
against the central taxonomy in `app/brain/question_type` and stores the
normalized slug, including `Analysi` -> `analysis`. The lecture-ingestion
pipeline writes these rows; the Take Mock page (P4), the Review page
(P5), and the Dashboard (P6) read them back. Helpers return plain
Python dictionaries (no pandas) so any caller can use the data
without an extra library.

## How to call

```python
from app.db.queries_questions import (
    insert_question,
    list_questions_for_slide_page,
    list_questions_for_lecture,
    ready_question_count_for_lecture,
    list_ready_questions_for_lecture,
    list_ready_questions_for_class,
    list_questions_for_learning_objective,
)

qid  = insert_question(
    slide_page_id=12,
    question_text="Which forecasting method assumes seasonality?",
    options=["Naive", "Holt-Winters", "Linear regression", "ARIMA(1,0,0)"],
    correct_indices=[1],            # always a list of unique ints in 0..3
    rationales_per_option=["...", "...", "...", "..."],
    source_page=8,
    language="en",
    question_type="application",     # required; normalized/validated
    difficulty_word_count=42,        # optional ingestion-flow feature
    difficulty_distractor_similarity=4,
    difficulty_conceptual_density=3,
    difficulty_distractor_derivation=4,
    difficulty_reasoning_steps=3,
    difficulty_wording_complexity=2,
    difficulty_wording_clarity_issue=0,
)
rows_for_slide    = list_questions_for_slide_page(slide_page_id=12)  # list[dict]
rows_for_lecture  = list_questions_for_lecture(lecture_id=1)          # list[dict]
ready_count       = ready_question_count_for_lecture(lecture_id=1)    # int
ready_questions   = list_ready_questions_for_lecture(lecture_id=1)    # list[dict]
all_class_ready    = list_ready_questions_for_class(class_id=1)        # list[dict] — Phase 7 Custom Mock
practice_questions = list_questions_for_learning_objective(learning_objective_id=3)
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `insert_question(...)` | see signature; `question_type` is a required keyword-only arg; rubric difficulty fields default `None`, while `difficulty_wording_clarity_issue` defaults `0` | `int` lastrowid |
| `list_questions_for_slide_page(slide_page_id)` | int | `list[dict]` |
| `list_questions_for_lecture(lecture_id)` | int — JOINs through slide_pages | `list[dict]` |
| `ready_question_count_for_lecture(lecture_id)` | int — JOINs through kept slide pages on a ready lecture | `int` |
| `list_ready_questions_for_lecture(lecture_id)` | int — ready lecture + kept pages only | `list[dict]` with `question_type`, `learning_objective_id`, and `learning_objective_title` |
| `list_ready_questions_for_class(class_id, conn=None)` | int — every ready MCQ in a class across all its lectures; SELECT-only | `list[dict]` with question + JSON columns, `question_type`, `lecture_id`, `lecture_title`, `learning_objective_id`, `learning_objective_title`, and all selected `difficulty_*` columns including Phase 7.1 wording fields |
| `list_questions_for_learning_objective(learning_objective_id)` | int — ready lecture + kept pages for one LO | `list[dict]` with `question_type`, `learning_objective_id`, and `learning_objective_title` |
| `get_question_display_context(question_id)` | int — one question id | `dict \| None` with only display metadata (`question_type`, lecture id, LO id/title) |

## Code walkthrough

- Module docstring states the pandas-free query-helper contract and lists the storage-boundary validation rules.
- `_row_to_dict` / `_rows_to_dicts` — small helpers that turn one cursor row (or all rows) into dicts using the cursor's `description` for column names.
- `_validate_mcq_payload(options, correct_indices, rationales_per_option)` — pure validator that raises `ValueError` BEFORE the DB write when the MCQ payload violates the contract:
  - `options` must be a list of length 4;
  - `rationales_per_option` must be a list of length 4;
  - `correct_indices` must be a list, non-empty, at most 4 entries;
  - every `correct_indices` value must be an `int` (booleans rejected explicitly via `isinstance(i, bool)`) in `0..3`;
  - duplicate values like `[0, 0]` are rejected (`len(set(...)) != len(...)`).
  This is the deliberate STORAGE-boundary mirror of the GENERATED-boundary guard in `app/class_/lecture_ingest/lecture_ingest.py::_validate_mcq` (MCQ-validation). Both guards must coexist.
- `_validated_question_type(question_type)` — normalizes the incoming value via the central taxonomy and raises `ValueError` if the result is not one of the provisional Surf V1 slugs.
- `insert_question(...)` — calls `_validate_mcq_payload(...)` first, then validates and normalizes the required keyword-only `question_type`; on success, JSON-encodes `options`, `correct_indices`, and `rationales_per_option` and INSERTs them along with `question_type` and the optional difficulty kwargs. Phase 7.1 adds `difficulty_wording_complexity` and the non-null `difficulty_wording_clarity_issue` flag; callers that have no metadata leave rubric numbers as `None` and pass/use the clarity fallback `0`. Wraps the INSERT in `with DB:` so the implicit transaction commits or rolls back together. Returns `cur.lastrowid`.
- `list_questions_for_slide_page(slide_page_id)` — list read ordered by `id`; returns `list[dict]`. JSON columns are returned as raw strings; consumers `json.loads(...)` when they need typed values.
- `list_questions_for_lecture(lecture_id)` — joins through `slide_pages` to filter by `lecture_id`; ordered by `q.id`. Same `list[dict]` contract.
- `ready_question_count_for_lecture(lecture_id)` — counts questions on `kept` slide pages for a lecture whose status is `ready`. Pending/failed lectures return `0` even if partial rows exist.
- `list_ready_questions_for_lecture(lecture_id)` — returns the selectable question rows for P3/P4 launch: ready lecture, kept pages, ordered by question id, preserving `question_type`, `learning_objective_id`, and `learning_objective_title` for the P4 display handoff.
- `list_ready_questions_for_class(class_id, conn=None)` — Phase 7 Custom Mock seam. Same kept-page + ready-lecture filter as `list_ready_questions_for_lecture`, but joins on `lectures.class_id` to return every ready question in that one class. SELECT-only — the helper has no `INSERT/UPDATE/DELETE/ALTER` keywords and is guarded by a regression test. Stored `question_type`, `options_json`, `correct_indices`, LO context, and all selected `difficulty_*` columns flow through unchanged, including `difficulty_wording_complexity` and `difficulty_wording_clarity_issue`; callers project these rows into the shared Phase 7.1 scoring view before calling `app.ml.personal_difficulty.score_questions(...)`. Normal `TAKE MOCK >` selection still uses `list_ready_questions_for_lecture`; this helper is only used by `app.class_.custom_mock_selection`.
- `list_questions_for_learning_objective(learning_objective_id)` — returns practice candidates for Study Next by joining through slide pages to one LO; it keeps the same ready/kept filters and preserves `question_type`, `learning_objective_id`, and `learning_objective_title`.
- `get_question_display_context(question_id)` — small read-only recovery helper for P4/P5 display metadata. It returns the stored question type, lecture id, LO id, and LO title for one question without exposing correct-answer/review data.

## Where it fits

The MCQ generator inside `app/class_/lecture_ingest` writes rows here. The class-hub ingestion flow
requires a `question_type` slug at the storage boundary and does not implement
ML. The legacy difficulty columns may still be present in the schema for older
older ingestion experiments, but new class-hub code must not add difficulty-score/profile
helpers or fake analytics.
- P4 mock-take reads the frozen launch payload first. For standard mocks that payload is built from `list_ready_questions_for_lecture`; for Study Next it is built from `list_questions_for_learning_objective`. The launch payload must drop `correct_indices` and `rationales_per_option` so attempts do not leak answers before submit. If an older/stale session payload lacks display metadata, P4 can recover the LO title and type via `get_question_display_context`, which returns only display metadata.
- P5 review reads question text/options through `queries_attempts.get_attempt_review_rows`, which JOINs through `questions` directly.
- P6 dashboard's `queries_dashboard` package reads `questions.id` and `slide_pages.lecture_id` when building coverage and per-lecture aggregates.

## Gotchas-if-real

- `correct_indices` is **always a list of unique ints in 0..3**, even when there is one correct answer. Decode with `json.loads(row["correct_indices"])`. The UI uses checkboxes when `len(correct_indices) >= 2`.
- `question_type` is required at insert time and validated in Python, not via a SQLite CHECK, because the taxonomy may be renamed or reduced later.
- Difficulty metadata is optional at insert time. A failed metadata critic must not block a valid MCQ: nullable rubric fields can stay `NULL`, and the clarity flag falls back to `0`.
- `difficulty_score` may still appear in the schema and ready-question rows for legacy compatibility, but it is not the visible personal-difficulty score source. Phase 7.1 scoring reads the metadata fields, exact-question history, and optional DecisionTree reliability branch instead.
- Storage validation does NOT run on the list helpers — they trust whatever `lecture_ingest._validate_mcq` (or this module's `_validate_mcq_payload`) already accepted. Tampering with rows directly via SQL bypasses both guards; treat the live DB as append-only from app code.
- This module must not import pandas. Re-introducing `import pandas` or `pd.read_sql` reverts the query-helper fix and fails `tests/test_query_return_shapes.py::test_no_pandas_import_in_query_modules`.
- Static check: `grep -n "import pandas\|pd.read_sql" app/db/queries_questions/__init__.py` must return zero matches.
- Verification: `python -m pytest tests/test_queries_questions_question_type.py tests/test_ready_question_count.py tests/test_list_ready_questions_for_lecture.py tests/test_list_questions_for_lo.py tests/test_no_streamlit_or_pandas_in_queries_questions.py -q`.

# `app/mock_review/rationale_display/__init__.py` — review row helper functions

This module prepares raw review-query rows for the read-only review renderer. It is pure Python: no Streamlit imports, no database calls, no pandas, and no model API calls.

## Purpose

- Decode JSON list fields from persisted review rows.
- Classify each option as selected-correct, selected-wrong, missed-correct, skipped, or neutral.
- Produce the compact result stamp for a question.
- Turn stored question-type slugs into honest display labels.
- Provide stable fallback text for missing rationales.

## Inputs and outputs

| Function | Input | Output |
|---|---|---|
| `parse_review_row(...)` | Raw `get_attempt_review_rows(...)` dict | Dict with decoded `selected_indices`, `options_json`, `correct_indices`, and `rationales_per_option_json`. |
| `classify_option_state(...)` | Option index plus selected/correct/skipped values | One CSS/state string: `correct`, `wrong`, `missed`, `neutral`, or `skipped`. |
| `result_stamp_for_attempt(...)` | `was_skipped` and `is_correct` booleans | `SKIPPED`, `CORRECT`, or `WRONG`. |
| `format_question_type_chip_label(...)` | Stored question-type slug | Human label or `Type unavailable`. |
| `format_rationale_text(...)` | Rationale value | Stripped text or `Rationale unavailable.` |

## Data flow

`results_render` reads persisted rows through `get_attempt_review_rows(...)`, sends each raw row to `parse_review_row(...)`, and then asks `classify_option_state(...)` for each of the four option slots. The returned values only drive display classes and copy; they do not change saved answers.

## Connected files, tables, and tools

- Called by `app/mock_review/results_render/__init__.py`.
- Receives rows built from `attempt_answers`, `questions`, learning objectives, and lecture metadata through query helpers.
- Uses `app.brain.question_type` for stored question-type labels.
- No direct SQLite connection, no Streamlit dependency, and no external service call.

## Code walkthrough

### Module docstring, imports, and exports

The file imports `json`, typing helpers, and question-type utilities. `__all__` exposes the small helper surface used by the renderer and tests.

### Option-state constants

Private constants hold the state strings consumed by CSS and feedback-copy logic. Keeping them centralized prevents spelling drift between parser tests and renderer markup.

### `_coerce_indices(...)`

Accepts an already decoded iterable and keeps only real integers. Booleans are excluded so `True` and `False` do not become option indices.

### `_loads_list(...)`

Safely decodes JSON list fields. Bad JSON, empty values, and non-list values return `[]`, allowing the review page to show honest fallbacks instead of crashing.

### `classify_option_state(...)`

Compares one option index against selected and correct sets. A skipped answer marks correct options as `missed` and other options as `skipped`, so the review can show what should have been selected without pretending the learner chose anything.

### `result_stamp_for_attempt(...)`

Returns the compact per-question result stamp: skipped takes priority, otherwise correct answers show `CORRECT` and all other non-skipped answers show `WRONG`.

### `format_question_type_chip_label(...)`

Normalizes the stored question-type slug and looks up its label. Unknown or missing values stay as `Type unavailable` rather than inventing a label.

### `format_rationale_text(...)`

Strips the rationale string and returns the stable fallback when the stored rationale is missing or blank.

### `parse_review_row(...)`

Copies the input row, decodes the JSON/list fields the renderer needs, and returns the normalized dict. The original row is not mutated.

## Constraints

- Helpers must remain read-only and deterministic.
- Classification must match exact-match grading: no extra score is calculated here.
- Unknown question types and missing rationales must use honest fallback copy.
- Bad stored JSON should degrade gracefully, not crash review.

## Tests and checks

- `tests/test_review_mock_render_contract.py`
- `tests/test_queries_attempts.py`
- `python -m ruff check app/mock_review/rationale_display --no-cache`

## What could break if changed

- Treating skipped non-correct options as neutral would hide the skipped state.
- Treating missed correct options as correct would mislead the learner.
- Raising on bad JSON would make one malformed row block the whole review page.
- Inferring new question-type labels here would make review drift from the stored taxonomy.

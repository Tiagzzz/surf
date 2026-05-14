# `app/mock_review/` — review mock and practice bucket

This bucket owns the read-only review surface for completed mock and practice attempts. It reads persisted attempt summaries and answer rows, then shows the saved grade or practice result, raw score, percentage, skipped count, threshold status, question-type chip, selected/correct/missed options, and rationales.

## Purpose

- Render a completed attempt without changing it.
- Explain each option using stored selections, stored correct indices, and stored rationales.
- Preserve the original question order from final submit.
- Show honest recovery copy when no attempt is selected or no rows are found.
- Route back to the class page or dashboard without changing saved answers.
- Display the **current** personal wrong-risk score (`Difficulty for you: X/100`) per review card using the existing Phase 7 badge. The score is recomputed on every render via `app.ml.personal_difficulty.score_questions(...)`; no frozen snapshot is stored.
- Provide a text-only `Understand your difficulty score` disclosure above the
  first review card so students can understand the badge without adding another
  scoring path.
- Keep hidden Phase 7.1 metadata/history/model inputs hidden. P5 does not add a six-feature breakdown, dashboard ML widget, or layout redesign.

## What lives here

| Path | Role |
|---|---|
| `__init__.py` | Bucket entry point that re-exports `render_review_mock_page`. |
| `rationale_display/` | Pure helpers for decoding review rows, classifying option states, result stamps, question-type labels, and rationale fallbacks. |
| `results_render/` | Streamlit renderer for the review hero, summary card, per-question cards, feedback rows, and bottom navigation. |

## Inputs and outputs

**Inputs**

- `attempt_id` from `st.session_state["current_attempt_id"]`.
- Selected class id from the page wrapper.
- `get_attempt_summary(...)` result for grade, score, counts, attempt kind, and finished timestamp.
- `get_attempt_review_rows(...)` rows for selected indices, correct indices, option text, rationales, question type, and ordering.
- Optional class threshold from `get_class_pass_threshold(...)`.
- Phase 7.1: metadata-rich review rows, completed answer history for the class from `list_personal_difficulty_examples_for_class(...)`, and per-question scores from `app.ml.personal_difficulty.score_questions(...)` — all consumed on each render to compute the existing `Difficulty for you: X/100` badge.

**Outputs**

- Read-only Streamlit UI.
- Optional navigation to class page or dashboard.
- `selected_class_id` refreshed before opening the dashboard.
- No database writes and no external model/API calls; the page may call the local pure-Python `score_questions(...)` helper to compute the badge.

## Data flow

```text
current_attempt_id
  -> get_attempt_summary(...)
  -> get_attempt_review_rows(...), including Phase 7.1 metadata columns
  -> list_personal_difficulty_examples_for_class(...)
  -> score_questions(...) using the same scoring shape as Custom Mock
  -> rationale_display parses JSON fields and classifies options
  -> results_render paints summary + difficulty explainer + ordered cards + optional existing badge
  -> bottom buttons route away without changing attempt data
```

P6 dashboard analytics depend on the same persisted rows, especially `selected_indices`, `was_skipped`, raw score fields, and stored `question_type` values. This review bucket displays those values; it does not recompute or rewrite them.

## Connected files, tables, and tools

| Connection | Why it matters |
|---|---|
| `app.db.queries_attempts` | Supplies persisted attempt summary and ordered review rows from `attempts` and `attempt_answers`. |
| `app.db.queries_classes` | Supplies class name and pass threshold for the header and summary. |
| `app.brain.question_type` | Converts stored question-type slugs into display labels. |
| `app.brain.topbar` | Renders the review breadcrumb. |
| `views/review_mock_exam.py` | Authenticates and passes the selected attempt to this bucket. |
| P6 dashboard | Reuses the same completed-attempt data model for analytics. |

## Code walkthrough

### `__init__.py`

The bucket entry imports and re-exports `render_review_mock_page`, giving the page wrapper one stable import path.

### `rationale_display/`

This pure helper package decodes JSON list fields, classifies each option as correct, wrong, missed, neutral, or skipped, formats the result stamp, formats stored question-type labels, and supplies fallback rationale text.

### `results_render/`

The renderer loads the persisted attempt summary and review rows, shows recovery copy when they are missing, renders the topbar, paints the summary card and text-only difficulty-score explainer, computes current personal-difficulty scores from the same metadata/history input shape used by Custom Mock, loops over review rows in stored order, and renders navigation buttons at the bottom. If example fetching or scoring fails, it safely omits the `Difficulty for you: X/100` badge and keeps the rest of P5 usable.

## Constraints

- Review is read-only.
- Stored `selected_indices` is the canonical answer; older single-choice fields are not used here.
- Skipped answers remain wrong and still show the missed correct options.
- The page shows the stored question type; it does not infer new analytics.
- No repeat-current-attempt shortcut, presentation preview, all-or-nothing grading change, model-generated difficulty panel, six-feature visible breakdown, dashboard ML widget, P5 layout redesign, or frozen per-attempt difficulty snapshot belongs in this bucket. The score explainer is static help copy only.

## Tests and checks

- `tests/test_review_mock_render_contract.py`
- `tests/test_review_mock_view_wrapper.py`
- `tests/test_queries_attempts.py`
- `tests/test_question_type_launch_handoff.py`
- `python -m ruff check app/mock_review views/review_mock_exam.py --no-cache`

## What could break if changed

- Re-grading in the renderer can make review disagree with saved attempt rows.
- Dropping `was_skipped` hides skipped-state feedback from the learner and dashboard.
- Reordering rows can break the promise that review follows the original question order.
- Showing invented difficulty or model-analysis output would make the page dishonest.
- Letting the static score explainer call scoring/query/write code would violate
  the read-only Review boundary.

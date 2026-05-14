# `app/mock_review/results_render/__init__.py` — P5 review renderer

This module renders the completed-attempt review page. It is a read-only Streamlit surface: query helpers fetch saved attempt data, pure helpers prepare option states, and scoped CSS/HTML paint the review cards.

## Purpose

- Show the saved mock grade or practice result.
- Show raw score, percentage, skipped count, and grade-4 threshold status.
- Render each question in the original saved order.
- Show selected, correct, missed, skipped, and neutral option states.
- Show per-option rationales with safe fallback copy.
- Provide navigation back to class or onward to the dashboard.

## Inputs and outputs

**Inputs**

- `user`: authenticated local user row from the wrapper.
- `class_id`: selected class id, if present.
- `attempt_id`: selected completed attempt id.
- `get_attempt_summary(...)`: attempt kind, grade, score, counts, and timestamp.
- `get_attempt_review_rows(...)`: one row per saved answer/question in review order, including the Phase 7.1 difficulty metadata columns needed by the shared scorer.
- `get_class_pass_threshold(...)`: threshold used for the mock summary card.
- `list_personal_difficulty_examples_for_class(...)`: completed-answer history for the same class, passed in as examples for exact-question history and the DecisionTree reliability blend.

**Outputs**

- Streamlit UI only.
- Optional navigation to `views/class_view.py` or `views/dashboard.py`.
- `st.session_state["selected_class_id"]` refreshed before opening dashboard.
- No saved attempt data is changed.

## Data flow

```text
attempt_id
  -> get_attempt_summary(attempt_id, class_id)
  -> get_attempt_review_rows(attempt_id)
  -> metadata-rich review rows + completed-answer examples
  -> app.ml.personal_difficulty.score_questions(...)
  -> parse_review_row(...) for each row
  -> classify_option_state(...) for each option
  -> summary card + ordered review cards with optional Difficulty for you: X/100 badge
  -> navigation buttons
```

The renderer trusts the database summary and answer rows. It does not recompute Swiss grades, does not call the finalizer, and does not write answer rows.

## Connected files, tables, and tools

| Connection | Role |
|---|---|
| `app.db.queries_attempts.get_attempt_summary` | Reads the saved attempt result from `attempts`. |
| `app.db.queries_attempts.get_attempt_review_rows` | Reads saved answer rows, question text, options, correct indices, rationales, learning objectives, and question type. |
| `app.db.queries_classes.get_class_by_id` | Fallback class-name lookup for the topbar. |
| `app.db.queries_classes.get_class_pass_threshold` | Supplies the summary threshold copy. |
| `app.mock_review.rationale_display` | Parses JSON fields and classifies option states. |
| `app.brain.topbar` | Renders the authenticated review breadcrumb. |

## Code walkthrough

### Module docstring, imports, and public export

The file imports Streamlit, local-font helpers, datetime tools, query helpers, topbar rendering, and rationale-display helpers. `__all__` exposes `render_review_mock_page`.

### Constants

Copy constants centralize fallback labels for unavailable type, unavailable rationale, missed markers, unavailable lecture, practice disclaimer, and the local display timezone.

### Font and style helpers

`_font_data_uri(...)`, `_font_face_block()`, and `_styles()` load local fonts and return scoped CSS for the review page, summary card, option rows, rationale feedback, actions, and reduced-motion behavior.

### Date and class helpers

`_format_finished_at(...)` accepts stored timestamp shapes, treats naive SQLite timestamps as UTC, and displays them in the local Europe/Zurich timezone. `_lookup_class_name(...)` and `_class_name(...)` resolve the breadcrumb label with safe fallbacks.

### Numeric and grade helpers

`_safe_int(...)`, `_safe_float(...)`, and `_grade_value(...)` format stored summary values without crashing on missing data. They do not calculate a new grade.

### Hero, threshold, and recovery helpers

`_hero_html(...)` builds the top review hero. `_threshold_status(...)` describes whether the saved percent reaches the class threshold. `_recovery_state()` shows `No attempt selected` and a back-to-class button when no attempt or rows are available.

### Summary-card helpers

`_summary_html(...)` renders the four summary metrics: result, score, percent, and skipped count. Practice attempts show practice disclaimer copy instead of a Swiss grade.

### Review-card helpers

`_result_state(...)`, `_review_card_header_html(...)`, `_option_html(...)`, and `_feedback_html(...)` build escaped card fragments. The header shows the stored question type, learning objective, and question text. `_review_card_header_html(...)` accepts an optional `difficulty_score` and emits an absolutely-positioned ribbon `<div class="surf-personal-difficulty-flag surf-personal-difficulty-flag--{tier}">` anchored to the top-right of the review card when a valid score (`0..100`) is supplied — otherwise the flag is omitted. The flag carries a stacked `DIFFICULTY FOR YOU` monospace label, the italic-serif score, and an `aria-label="Difficulty for you: {score}/100"` for screen readers. Out-of-range or non-integer scores are dropped silently rather than displayed as nonsense. Option rows show whether an option was selected. Feedback rows show the state label and stored rationale.

### Phase 7/7.1 — personal difficulty score helpers

- `_decode_json_list(value)` accepts an already-decoded list or a JSON string and returns a plain list. It is used only for the scoring contract; `parse_review_row(...)` still owns display parsing.
- `_scoring_view_from_review_row(row)` builds the same plain-dict feature view that Custom Mock ranking uses: coalesced `id`/`question_id`, `stem`, `question_text`, decoded `options`, decoded `correct_indices`, `question_type`, `lo_title`, word count/readability, and all Phase 7.1 Claude difficulty metadata fields. The function never mutates the underlying review row.
- `_example_view_from_review_row(row)` starts from `_scoring_view_from_review_row(row)`, then adds decoded `selected_indices` plus Python-bool `is_correct` and `is_skipped` for completed-answer examples.
- `_difficulty_score_map_for_review(class_id, review_rows, examples_fn=list_personal_difficulty_examples_for_class, score_questions_fn=score_questions)` reads the student's completed answer examples for the class, projects review questions and examples into the same metadata/history scoring-input contract used by Custom Mock, scores every review question on demand, and returns `{question_id: score}`. The underlying scorer may use the metadata-first rule score, exact-question Bayesian history, and the reliability-capped `DecisionTreeClassifier` blend; this renderer only consumes the final score. The map is recomputed on every render (D-16). Any failure path — missing `class_id`, broken example fetch, scoring exception, mismatched lengths — returns `{}` so P5 renders the existing card layout without a `Difficulty for you: X/100` badge instead of crashing.
- `_difficulty_flag_tier(score)` maps the clamped score to the tier class suffix used on the flag: `< 33 → "ok"` (green), `33..66 → "warn"` (yellow, paper5 text), `> 66 → "risk"` (red). The colors come straight from the design-system tokens (`--surf-status-ok`, `--surf-status-warn`, `--surf-accent-deep`) and never invent new colors.

No snapshot column or row is written. D-17 is preserved: there is no schema for frozen difficulty.

### `_render_review_row(...)`

Parses one saved review row, computes selected/correct/skipped sets, gets the result stamp, formats the stored question type, accepts an optional `difficulty_score` keyword from `render_review_mock_page`, forwards it to `_review_card_header_html(...)`, and renders up to four options with feedback under each option.

### `_render_actions(...)`

Renders the bottom navigation. `BACK TO CLASS` returns to class view. `OPEN DASHBOARD` refreshes `selected_class_id` when available and routes to dashboard.

### `render_review_mock_page(...)`

The public renderer checks for a selected attempt, fetches summary and rows, falls back to recovery copy if anything essential is missing, renders the topbar and styles, computes threshold/skipped count, calls `_difficulty_score_map_for_review(class_id, review_rows)` once, then paints the hero, summary card, review rows (with the per-question personal-difficulty score forwarded), and actions. The score recomputation is on render — there is no frozen snapshot.

## Visible elements

| Element | Source |
|---|---|
| Hero title and date | Attempt kind and `finished_at` from summary. |
| Grade value | Stored `swiss_grade` for mock attempts; practice shows no grade in the hero. |
| Result/score/percent/skipped | Stored summary fields and saved skipped rows. |
| Threshold copy | Class pass threshold plus stored percent. |
| Question-type chip | Stored `question_type` label. |
| Personal difficulty flag | Existing Phase 7 ribbon anchored to the top-right of each review card with a stacked `DIFFICULTY FOR YOU` label and the `Difficulty for you: X/100` screen-reader label. Tier color: green when score < 33, yellow (paper5 text) when 33 ≤ score ≤ 66, red when score > 66. Recomputed on every render via `app.ml.personal_difficulty.score_questions`; never frozen; omitted when the score is unavailable, out of range, or the scorer fails. |
| Option feedback | Stored selected indices, correct indices, skipped flag, and rationales. |

## Constraints

- The page is read-only.
- It must preserve saved row order.
- It must not invent analytics or difficulty panels. The Phase 7 `Difficulty for you: X/100` badge is the **only** ML-flavored UI element on P5 and it is recalculated on every render — no visible six-feature metadata breakdown, no dashboard ML widget, no P5 layout redesign, no frozen per-attempt difficulty snapshot, and no UPDATE/INSERT to `attempts` / `attempt_answers`.
- Practice attempts do not count toward class average and do not show a Swiss grade hero value.
- Missing attempt context must recover to class navigation instead of crashing.
- If the personal-difficulty scoring path fails for any reason, P5 must omit the badge rather than crash.

## Tests and checks

- `tests/test_review_mock_render_contract.py`
- `tests/test_review_mock_view_wrapper.py`
- `tests/test_queries_attempts.py`
- `python -m ruff check app/mock_review/results_render views/review_mock_exam.py --no-cache`

## What could break if changed

- Recomputing grades here can make P5 disagree with the saved attempt summary.
- Dropping skipped-state display can hide why a question was wrong.
- Changing the dashboard handoff can open P6 without the reviewed class selected.
- Rendering unescaped generated text would risk unsafe HTML in question/rationale copy.

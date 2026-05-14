# `app/mock_take/question_render/__init__.py` — P4 attempt renderer

This module renders the take-mock/practice page. It keeps answer behavior connected to real Streamlit buttons while using scoped CSS and escaped HTML for the stamped Surf card appearance.

## Purpose

- Recover safely when no attempt launch state is present.
- Render the authenticated topbar, question counter, question-type chip, learning objective, question text, and four option rows.
- Keep answer choices in session state until final submit.
- Keep `NEXT >` disabled until a selection exists, while `SKIP` remains available.
- Open a confirmation dialog before calling the final-submit service.

## Inputs and outputs

**Inputs**

- `user`: authenticated local user row, used as an ownership signal by the wrapper.
- `class_id`: selected class id from session state.
- `st.session_state["p4_launch_state"]`: launch payload containing `mock_kind`, class data, frozen question ids, and question payloads.
- Optional DB display context from `get_question_display_context(...)` when the launch payload lacks learning objective or question type.

**Outputs**

- Streamlit UI for the current question and attempt controls.
- Mutations to `p4_attempt_in_progress` through answer-capture helpers.
- `p4_show_submit_dialog` when final confirmation should render.
- `current_attempt_id` and navigation to `views/review_mock_exam.py` after successful save.

## Data flow

```text
p4_launch_state
  -> render_take_mock_page(...)
  -> _get_attempt_state(...)
  -> option/SKIP/NEXT handlers mutate session state
  -> final dialog calls submit_attempt(...)
  -> saved attempt id enters session state
  -> review page opens
```

The renderer reads from query helpers for display labels only. It does not write to the database until the learner clicks the final dialog action.

## Connected files, tables, and tools

- `app.mock_take.answer_capture`: option toggles, skip state, movement, and submit-dialog sentinel.
- `app.mock_take.attempt_save`: final validation and persistence call.
- `app.class_.mock_standard_launch` and `app.class_.study_next_launch`: launch/session keys.
- `app.db.queries_questions.get_question_display_context`: learning objective and stored question type fallback.
- `app.db.queries_classes.get_class_by_id`: class-name fallback for the topbar.
- `app.brain.question_type`: stored question-type slug normalization.
- `app.brain.topbar`: authenticated breadcrumb and navigation.
- Database tables indirectly affected only after submit: `attempts`, `attempt_answers`, and source `questions` rows.

## Code walkthrough

### Module docstring, imports, and public export

The module declares the page contract, imports Streamlit, shared helpers, query helpers, and the final-submit service, then exports `P4_SHOW_SUBMIT_DIALOG_KEY` and `render_take_mock_page`.

### Session-state constants

`P4_SHOW_SUBMIT_DIALOG_KEY` is the shared final-confirmation flag. Fallback constants keep old tests and session shapes readable. `_CHECKMARK_DATA_URI` provides the selected-option checkmark without loading an external image.

### Font and style helpers

`_font_data_uri(...)`, `_font_face_block()`, and `_styles()` load local fonts and return scoped CSS for the P4 page, question card, option overlays, action buttons, submit dialog, and reduced-motion behavior.

### Attempt-state helpers

`_attempt_state_key()`, `_new_attempt_state(...)`, `_get_attempt_state(...)`, `_selected_indices(...)`, `_toggle_option(...)`, `_mark_skipped(...)`, `_can_advance(...)`, and `_advance(...)` adapt the renderer to the answer-capture module. Their fallback code preserves importability, but normal behavior delegates to `answer_capture`.

### Small display helpers

`_question_type_label(...)`, `_mode_label(...)`, `_question_id(...)`, `_question_payloads(...)`, `_class_name_from_launch(...)`, and `_display_context_for_question(...)` normalize labels and recover missing display context without changing the saved question set.

### Topbar, recovery, and HTML builders

`_render_topbar(...)` renders the breadcrumb. `_recovery_html()` and `_render_recovery(...)` show the safe return path when no attempt is in progress. `_hero_html(...)`, `_question_html(...)`, and `_option_overlay_html(...)` build escaped decorative markup for the current card.

### Submit dialog helpers

`_render_submit_dialog_body(...)` counts answered and skipped questions, reminds the learner that skipped questions are wrong, and offers `KEEP ANSWERING` or the final finish action. The finish action calls `submit_attempt(...)`, clears launch state on success, stores `current_attempt_id`, and routes to review. Validation or finalizer errors keep the answers in session and show retry copy.

`_render_mock_submit_dialog(...)`, `_render_practice_submit_dialog(...)`, and `_render_submit_dialog(...)` choose the correct dialog title and finish label.

### `render_take_mock_page(...)`

The public renderer checks launch state, renders recovery if needed, applies the topbar and styles, clamps the current index, selects the current question, paints up to four option rows, and wires the controls. Option buttons toggle selected indices. `SKIP` marks the question skipped and advances. `NEXT >` and finish are disabled until `_can_advance(...)` is true.

## Visible controls

| Control | Behavior |
|---|---|
| Option row | Toggles one option in the current question's selected-index list. |
| `SKIP` | Clears selections, marks the question skipped, and moves forward. |
| `NEXT >` | Moves forward only after selection or skip. |
| `FINISH MOCK` / `FINISH PRACTICE` | Opens final confirmation on the last question. |
| `KEEP ANSWERING` | Closes the final confirmation. |
| Dialog finish action | Saves once and opens review on success. |

## Constraints

- The page must not show rationales or correct answers during the attempt.
- The launch question order is the order saved and later reviewed.
- Question-type chips are labels from stored question type, not live analysis.
- `SKIP` stays enabled even when `NEXT >` is disabled.
- Failed submit leaves answers in session so the learner can retry.

## Tests and checks

- `tests/test_take_mock_state_machine.py`
- `tests/test_take_mock_final_submit.py`
- `tests/test_take_mock_view_wrapper.py`
- `tests/test_question_type_launch_handoff.py`
- `python -m ruff check app/mock_take/question_render views/take_mock_exam.py --no-cache`

## What could break if changed

- Changing Streamlit keys can break tests and scoped styling.
- Removing the disabled gate from `NEXT >` can allow unanswered questions without explicit skip.
- Saving directly from the finish button would bypass confirmation and idempotency guards.
- Reordering questions here would make P5 review disagree with the launch payload.

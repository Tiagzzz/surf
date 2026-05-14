# `app/mock_take/` — take mock and practice bucket

This bucket owns the in-progress mock/practice attempt. It starts from the Class Hub or Study Next launch payload, keeps answers in Streamlit session state while the learner is working, and sends one normalized payload to the attempt-finalization service only after the learner confirms the final submit.

## Purpose

- Render the P4 attempt page and recovery state.
- Capture four-option multi-select MCQ choices in session state.
- Record explicit skips and keep skipped questions wrong at grading time.
- Preserve the frozen question order from launch through review.
- Keep all database writes behind the final-submit service.

## What lives here

| Path | Role |
|---|---|
| `__init__.py` | Bucket entry point that re-exports `render_take_mock_page`. |
| `answer_capture/` | Pure session-state helpers for toggling options, skipping, and moving to the next card. |
| `question_render/` | Streamlit renderer for the attempt card, buttons, recovery state, and final-submit dialog. |
| `attempt_save/` | Validation and one-shot persistence boundary for completed attempts. |

## Inputs and outputs

**Inputs**

- `st.session_state["p4_launch_state"]` from mock launch or Study Next practice launch.
- Frozen question ids and question payloads from the launch handoff.
- The selected class id from the page wrapper.

**Outputs**

- Session-only answer state under `p4_attempt_in_progress` while answering.
- `p4_show_submit_dialog` when the learner reaches the final confirmation.
- One call to `app.db.queries_attempts.finalize_attempt(...)` after final confirmation.
- `st.session_state["current_attempt_id"]` before navigating to review.

## Data flow

```text
Class Hub / Study Next launch
  -> p4_launch_state in Streamlit session
  -> question_render renders the card and controls
  -> answer_capture mutates selected_indices_by_qid and skipped_qids
  -> attempt_save validates coverage and duplicates
  -> queries_attempts.finalize_attempt writes attempts + attempt_answers atomically
  -> Review page reads the saved attempt
```

The bucket touches no private files, no live model API, and no local database until final submit. During answering, closing the browser or leaving the session loses unsaved choices by design.

## Connected files, tables, and tools

| Connection | Why it matters |
|---|---|
| `app.class_.mock_standard_launch` | Supplies the mock launch state, frozen question ids, and question payloads. |
| `app.class_.study_next_launch` | Supplies the same shape for practice attempts. |
| `app.brain.question_type` | Normalizes the stored question-type chip shown on the card. |
| `app.brain.topbar` | Renders the authenticated breadcrumb and Home/Settings actions. |
| `app.db.queries_attempts.finalize_attempt` | Writes `attempts` and `attempt_answers` in one transaction. |
| `views/take_mock_exam.py` | Authenticates the user and delegates to this bucket. |
| P5 review and P6 analytics | Depend on `selected_indices`, `was_skipped`, score fields, and question order stored here. |

## Code walkthrough

### `__init__.py`

The bucket entry imports `render_take_mock_page` from `question_render` and exposes it through `__all__`. Page wrappers can import from the bucket root instead of knowing the subfolder layout.

### `answer_capture/`

The state machine creates the attempt dict, validates question ids and option indices, toggles selected answers, clears selections on skip, and advances the current card index. It never writes SQLite rows.

### `question_render/`

The renderer reads launch state, shows a recovery message when launch state is missing, displays the topbar and current question, paints four clickable option rows, and keeps `NEXT >` disabled until the learner selects at least one option or presses `SKIP`. `SKIP` remains active, records explicit skipped state, and moves forward. The final action opens the confirmation dialog instead of saving immediately.

### `attempt_save/`

The save service validates `class_id`, `mock_kind`, frozen question ids, selected option lists, skipped ids, and answer coverage. It rejects duplicate or out-of-range selected indices before calling `finalize_attempt(...)`, then records the saved `attempt_id` in session state.

## Constraints

- Answering is session-only until final submit.
- MCQs use four option indices: `0`, `1`, `2`, and `3`.
- Grading is exact-match: the selected set must equal the correct set.
- Skipped questions are stored explicitly and count as wrong.
- The renderer must not show correct answers or rationales before submit.
- The final submit must stay one all-or-nothing database transaction.
- No attempt draft rows, no repeat-current-attempt shortcut, no presentation preview, and no model-generated analytics are added here.

## Tests and checks

- `tests/test_take_mock_state_machine.py`
- `tests/test_take_mock_final_submit.py`
- `tests/test_take_mock_view_wrapper.py`
- `tests/test_queries_attempts.py`
- `tests/test_question_type_launch_handoff.py`
- `python -m ruff check app/mock_take views/take_mock_exam.py --no-cache`

## What could break if changed

- Changing launch/session keys breaks the P3-to-P4 handoff.
- Moving writes into `answer_capture` or `question_render` creates draft persistence the app does not support.
- Allowing duplicate `selected_indices` can corrupt exact-match grading.
- Changing skip handling can make skipped answers disappear from review or analytics.
- Renaming keyed containers can break Streamlit tests and scoped visual styling.

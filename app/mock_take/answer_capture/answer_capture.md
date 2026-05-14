# `app/mock_take/answer_capture/__init__.py` — session answer state

This module is the pure state machine for the take-mock/practice page. It keeps the current attempt in a plain Python dict that can live in Streamlit session state. It does not import Streamlit, write SQLite rows, call pandas, or contact any model API.

## Purpose

- Start a new in-session attempt state.
- Toggle selected MCQ option indices for a question.
- Mark a question as skipped and clear its selected answers.
- Decide whether the learner can move forward.
- Advance the current question pointer and signal when the submit dialog should open.

## Inputs and outputs

| Function/value | Input | Output |
|---|---|---|
| `P4_IN_PROGRESS_KEY` | none | Session key `p4_attempt_in_progress`. |
| `SUBMIT_DIALOG_SENTINEL` | none | Signal string `open_submit_dialog`. |
| `init_attempt_state(...)` | Optional launch state and optional clock | Dict with selections, skipped ids, index, UTC start time, and submit guards. |
| `toggle_option(...)` | Attempt state, question id, option index | Same dict updated with a sorted unique selected list. |
| `mark_skipped(...)` | Attempt state and question id | Same dict with selections cleared and the id added to `skipped_qids`. |
| `can_advance(...)` | Attempt state and question id | `True` only after selection or explicit skip. |
| `advance(...)` | Attempt state and total question count | `None` for normal movement or `open_submit_dialog` after the last card. |

## Data flow

`question_render` owns the visible buttons. Each click calls one of these helpers, then Streamlit reruns and reads the same dict again. The dict is handed to `attempt_save.submit_attempt(...)` only after the final confirmation. Until then, the database has no attempt row and no answer rows for this in-progress work.

## Connected files, tables, and tools

- Called by `app/mock_take/question_render/__init__.py`.
- Consumed by `app/mock_take/attempt_save/__init__.py` at final submit.
- Final save writes to `attempts` and `attempt_answers` through `app.db.queries_attempts`.
- No direct database, file, pandas, Streamlit, or Anthropic dependency in this module.

## Code walkthrough

### Module constants and exports

`P4_IN_PROGRESS_KEY` names the session-state slot. `SUBMIT_DIALOG_SENTINEL` is the signal returned when the next movement should open final confirmation. `__all__` lists the public helpers used by the renderer and tests.

### `init_attempt_state(...)`

Builds the exact attempt-state shape: `selected_indices_by_qid`, `skipped_qids`, `current_index`, `started_at`, `submit_in_flight`, and `submitted_attempt_id`. `started_at` is normalized to UTC so the final attempt row can record when answering began without creating a draft row.

### Validation helpers

`_qid(...)` accepts only positive integer question ids. `_option_index(...)` accepts only integer options from `0` to `3`. Both reject booleans because `True` and `False` are integers in Python but not valid app ids.

### State container helpers

`_selected_map(...)` ensures selected answers live in a mutable dict. `_skipped_set(...)` ensures skipped ids live in a set and normalizes list/tuple shapes that may appear after a session-state round trip.

### `toggle_option(...)`

Reads the current selection, adds or removes the clicked option, stores a sorted unique list, removes empty lists, and clears the skipped marker because an answered question is no longer skipped.

### `mark_skipped(...)`

Stores an empty selected list for the question and adds the question id to `skipped_qids`. This makes skipped state explicit for final submit and review.

### `can_advance(...)`

Checks the page rule behind the disabled `NEXT >` button: movement is allowed only when the current question has a selected option or has been skipped.

### `advance(...)`

Validates the total question count and current index, increments the pointer, and returns the submit-dialog sentinel when the learner moves beyond the final question.

## Constraints

- Selected indices must stay unique and sorted.
- Empty selection alone is not an answer.
- Skip and answer cannot both be active for the same question.
- This module must remain session-only and side-effect-light.

## Tests and checks

- `tests/test_take_mock_state_machine.py`
- `tests/test_take_mock_final_submit.py`
- `python -m ruff check app/mock_take/answer_capture --no-cache`

## What could break if changed

- Accepting invalid option indices can write impossible answer rows later.
- Treating an empty list as answered would bypass the visible movement gate.
- Forgetting to clear skip state on answer can make a correct answer count as skipped.
- Writing to SQLite here would violate the final-submit boundary and make recovery confusing.

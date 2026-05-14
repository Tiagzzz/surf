# `app/mock_take/attempt_save/__init__.py` — final attempt submit service

This module is the only P4 service that turns the session-only answer state into durable attempt rows. It validates the launch payload and answer payload, then delegates to `app.db.queries_attempts.finalize_attempt(...)` for the atomic SQLite write.

## Purpose

- Guard against double-submit from the same browser session.
- Validate class id, attempt kind, frozen question ids, skipped ids, and selected indices.
- Reject malformed or duplicate selected-index payloads before the database boundary.
- Call the attempt finalizer exactly once for a new valid submit.
- Return a small status dict the renderer can turn into navigation or error copy.

## Inputs and outputs

**Input from launch state**

- `class_id`: positive integer class id.
- `mock_kind`: `mock` or `practice`.
- `frozen_question_ids`: non-empty list of unique question ids in display order.

**Input from attempt state**

- `selected_indices_by_qid`: mapping from question id to selected option-index list.
- `skipped_qids`: set/list/tuple of explicitly skipped question ids.
- `started_at`: session start timestamp.
- `submit_in_flight`: idempotency guard.
- `submitted_attempt_id`: saved id after success.

**Status outputs**

| Status | Meaning |
|---|---|
| `in_flight` | A submit is already running; no database call happens. |
| `already_submitted` | This browser session already has a saved attempt id. |
| `submitted` | The finalizer saved the attempt and answer rows. |
| `validation_error` | Launch or answer state is invalid. |
| `error` | The finalizer raised an unexpected exception. |

## Data flow

```text
question_render submit dialog
  -> submit_attempt(launch_state, attempt_state)
  -> _question_ids_from_launch(...)
  -> _selected_answers(...)
  -> queries_attempts.finalize_attempt(...)
  -> attempts + attempt_answers committed together
  -> renderer stores current_attempt_id and opens review
```

Skipped questions are not included in `answers_by_question_id`; they are passed separately as `skipped_question_ids`. The database helper then records them as explicit skipped rows and grades them wrong.

## Connected files, tables, and tools

- Called by `app/mock_take/question_render/__init__.py`.
- Receives state created by `app/mock_take/answer_capture/__init__.py`.
- Receives launch data from `app/class_/mock_standard_launch` or `app/class_/study_next_launch`.
- Calls `app.db.queries_attempts.finalize_attempt(...)`.
- Writes through the finalizer to `attempts` and `attempt_answers` only.
- Read later by P5 review and P6 analytics through query helpers.

## Code walkthrough

### Imports, export, and `FinalizeFn`

The module imports `finalize_attempt` as `_default_finalize` and exposes only `submit_attempt`. The injectable `finalize_fn` lets tests prove validation behavior without raw SQL in this file.

### `_positive_int(...)`

Rejects booleans, non-integers, zero, and negative ids for class ids, question ids, and skipped question ids.

### `_question_ids_from_launch(...)`

Reads `frozen_question_ids`, requires a non-empty list, normalizes each id, and rejects duplicate question ids so the saved answer order stays unambiguous.

### `_selected_answers(...)`

Loops through frozen question ids in order. Skipped questions are left out of `answers_by_question_id`. Answered questions must provide a list of integer indices, each from `0` to `3`, with no duplicates and at least one selected option. Valid lists are sorted for stable storage.

### `submit_attempt(...)`

Returns early for in-flight or already-submitted sessions. For a new submit, it sets the in-flight guard, validates launch and answer state, calls the finalizer once, and resets the guard on every failure path. On success it stores `submitted_attempt_id` and returns the finalizer result.

The broad exception branch keeps the `noqa: BLE001` directive because the UI service converts unexpected finalizer failures into user-facing retry copy without exposing internal details.

## Constraints

- No raw SQL in this file.
- No partial answer writes outside the finalizer transaction.
- No silent deduplication of corrupted selected-index payloads.
- No durable draft attempt persistence before this function succeeds.
- No change to exact-match grading; this module only normalizes payloads for the finalizer.

## Tests and checks

- `tests/test_take_mock_final_submit.py`
- `tests/test_queries_attempts.py`
- `tests/test_no_real_db.py`
- `python -m ruff check app/mock_take/attempt_save --no-cache`

## What could break if changed

- Calling the finalizer twice can duplicate attempts.
- Allowing duplicate selected indices can make grading and review disagree.
- Forgetting skipped ids can make skipped questions vanish from P5 and P6.
- Not resetting `submit_in_flight` on failure can trap the learner in the submit dialog.

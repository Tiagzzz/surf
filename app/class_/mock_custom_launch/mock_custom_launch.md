# `app/class_/mock_custom_launch/` — Phase 7 Custom Mock launch helper

The red `CUSTOM MOCK >` button on the Class Hub calls this helper. It reads the top-10 highest-personal-difficulty questions from `app/class_/custom_mock_selection/` (Plan 07-02) and writes the same P4 session-state contract that the standard mock launch uses, so P4 takes the Custom Mock through the **existing** attempt flow without changing P4 itself.

No `attempts` row is created here. P4 final submit owns the all-or-nothing DB write via `app.db.queries_attempts.finalize_attempt`.

## Files

| File | Purpose |
| --- | --- |
| `app/class_/mock_custom_launch/__init__.py` | `launch_mock_custom(...)` session-only launch helper. |
| `app/class_/mock_custom_launch/mock_custom_launch.md` | This sidecar. |

## How it fits

```text
Class Hub (P3)
   │  click "CUSTOM MOCK >"
   ▼
app.class_.mock_custom_launch.launch_mock_custom(class_id=...)
   │
   ├── select_custom_mock_questions(class_id, limit=10)
   │      ├── list_ready_questions_for_class(...)
   │      ├── list_personal_difficulty_examples_for_class(...)
   │      └── app.ml.personal_difficulty.score_questions(...)
   │
   └── writes P4 session keys (p4_launch_state, frozen_question_ids,
       p4_question_payloads, mock_kind="mock", selected_lecture_ids)
   │
   ▼
views/take_mock_exam.py reads session keys and renders the P4 mock
   │
   ▼
P4 final submit → app.db.queries_attempts.finalize_attempt(...)
```

## Inputs, outputs, and data flow

Inputs are a validated `class_id`, optional display `class_name`, optional injectable `session_state`, and the selector function that returns ranked ready-question rows. The output is a state dictionary with `ok`, frozen question ids, P4 payloads, selected lecture ids, count/copy fields, and `launch_kind="custom"`. The live side effect is limited to writing Streamlit session-state keys when at least one question is available; no database row is created until P4 final submit.

Data flow stays deliberately short: Class Hub button → selector reads/scoring → this helper builds P4-safe payloads through `build_question_payload(...)` → session-state handoff → existing P4 renderer. Correct answers and rationales are never copied into the pre-submit payload.

## Connected files, tables, and tools

- `app/class_/class_hub/` calls this helper for the red `CUSTOM MOCK >` action.
- `app/class_/custom_mock_selection/` supplies ranked ready-question rows and owns the DB/scoring reads.
- `app/class_/mock_standard_launch/build_question_payload(...)` owns the safe P4 payload shape reused here.
- P4 later persists to `attempts` and `attempt_answers` through `app.db.queries_attempts.finalize_attempt(...)`; this helper does not write those tables.

## Constants

- `CUSTOM_MOCK_TARGET_QUESTION_COUNT = 10` (matches D-12 — "up to 10 highest current scores").
- `CUSTOM_MOCK_HONEST_SHORT_COPY_TEMPLATE` — explanation copy when fewer than 10 ready questions exist.
- `CUSTOM_MOCK_EMPTY_COPY` — toast/help copy when the pool is empty.

## Code walkthrough

### `_default_session_state()`

Returns `st.session_state`. Local import of Streamlit so tests can inject a plain dict and skip Streamlit setup.

### `_write_launch_state(session_state, *, state)`

Mirrors the implementation in `mock_standard_launch`: writes the four standard P4 keys (`p4_launch_state`, `frozen_question_ids`, `p4_question_payloads`, `mock_kind`) plus `selected_lecture_ids`. P4 reads exactly these keys today, so reusing the standard contract means P4 needs no special-casing for Custom Mock.

### `_validate_class_id(class_id)`

Rejects non-positive ints and booleans with `ValueError`. Custom Mock is always launched for an authenticated, selected class — a bad value here means a wiring bug.

### `launch_mock_custom(*, class_id, class_name=None, session_state=None, selector_fn=select_custom_mock_questions, target_question_count=10)`

The public entry point. Steps:

1. Validate `class_id` and `target_question_count` (positive ints, no booleans).
2. Call the selector — defaults to `app.class_.custom_mock_selection.select_custom_mock_questions(class_id=..., limit=target_question_count)`. Tests inject a fake.
3. Project each selector row into the P4 launch payload via `build_question_payload(row)` from `mock_standard_launch`. The payload deliberately preserves `question_type` and drops `correct_indices` and `rationales_per_option_json` so the launch state cannot leak answers before submit.
4. Collect unique lecture ids touched by the picked questions, sorted ascending, into `selected_lecture_ids`.
5. Build a state dict with `ok`, `class_id`, `class_name` (whitespace-stripped or `None`), `mock_kind="mock"` (Custom Mock is a normal mock attempt by the V1 contract), `selected_lecture_ids`, `frozen_question_ids`, `question_payloads`, `target_question_count`, `available_question_count`, `honest_short_copy`, and `launch_kind="custom"` so callers can tell standard vs custom mocks apart in telemetry/logging without changing P4 behavior.
6. If the pool was empty (`available == 0`), set `honest_short_copy = CUSTOM_MOCK_EMPTY_COPY`, set `ok=False`, and **skip writing session keys** so the Class Hub can show its own toast instead of jumping to P4.
7. If the pool was non-empty but shorter than 10, set `honest_short_copy` to the templated short-pool message.
8. Write the session keys via `_write_launch_state(...)` and return the state dict.

The helper does not call the DB, the Claude client, NotebookLM, or the network. It does not import `app.db.*` directly; all SQL goes through the injected `selector_fn` (which uses the SELECT-only helpers from Plan 07-02).

## Safety boundaries

- No DB imports, no Claude/NotebookLM/network imports, no secret reads.
- `mock_kind` is `"mock"` — the V1 contract treats Custom Mock as a normal mock attempt.
- No attempt row is created; P4 final submit remains the only write boundary.

## What could break if changed carelessly

- Skipping `build_question_payload(...)` would let `correct_indices` / `rationales_per_option_json` leak into session state before submit and into P4 view models.
- Changing `mock_kind` to anything other than `"mock"` would violate the V1 `CHECK (mock_kind IN ('mock','practice'))` constraint on `attempts.mock_kind`.
- Removing the empty-pool toast path would land the user on a P4 page with no questions.
- Calling `list_ready_questions_for_class` or `list_personal_difficulty_examples_for_class` from this module directly would couple the launch helper to the DB layer — keep the dependency one level removed via the selector.

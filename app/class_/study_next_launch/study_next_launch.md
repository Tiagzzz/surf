# `study_next_launch` — Study Next practice launch

This module freezes the Class Hub Study Next `>` handoff for P4 practice mode. It scopes questions to one weak learning objective, writes session state, and creates no `attempts` row.

## Inputs / outputs

- **Input:** positive `class_id`, positive `learning_objective_id`, optional `class_name`, session state, and query function.
- **Output:** a dict with `mock_kind="practice"`, learning objective id, selected lecture ids, frozen question ids, and question payloads.
- **Session keys:** `p4_launch_state`, `frozen_question_ids`, `p4_question_payloads`, `mock_kind`, and `selected_learning_objective_id`.

## Data flow

```text
Study Next `>` click
        │
        └── launch_study_next_practice(...)
                ├── validate class and LO ids
                ├── load ready questions for that LO
                ├── build answer-safe payloads
                └── write P4 practice launch state to session only
```

## Code walkthrough

### Imports and constants
The module reuses `build_question_payload(...)` from `mock_standard_launch` so mock and practice launches keep the same answer-safe question shape. `PRACTICE_KIND` is the value P4 later passes to final submit.

### `_positive_int(...)`
Validates class and LO ids before query or session writes.

### `_write_launch_state(...)`
Writes the main launch dict plus compatibility keys that P4 can read directly. The state remains in session only.

### `launch_study_next_practice(...)`
Loads ready questions for one LO, rejects an empty LO, builds payloads that preserve `question_type` and learning-objective context without exposing answers, derives selected lecture ids from those payloads, stores optional class name, writes session state, and returns the state.

## Testing notes

```bash
python -m pytest -q tests/test_study_next_launch.py tests/test_question_type_launch_handoff.py
python -m ruff check app/class_/study_next_launch --no-cache
```

## What could break if changed

- Creating an `attempts` row here would break the practice submit flow.
- Dropping selected lecture ids would make P4/P5 context and dashboard coverage harder to compute.
- Including correct answers or rationales would leak review data before final submit.
- Diverging from `mock_standard_launch.build_question_payload(...)` would make mock and practice payloads inconsistent.

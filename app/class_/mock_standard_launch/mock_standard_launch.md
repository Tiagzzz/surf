# `mock_standard_launch` — selected-lecture mock launch

This module freezes the Class Hub `TAKE MOCK >` handoff for P4. It writes question ids and display payloads to Streamlit session state, but it does not create an `attempts` row.

## Inputs / outputs

- **Input:** positive `class_id`, selected ready lecture ids, optional `class_name`, session state, query function, and target count per lecture.
- **Output:** a dict with `mock_kind="mock"`, selected lecture ids, frozen question ids, question payloads, target/available counts, and optional honest shorter-mock copy.
- **Session keys:** `p4_launch_state`, `frozen_question_ids`, `p4_question_payloads`, `mock_kind`, and `selected_lecture_ids`.

## Data flow

```text
Class Hub `TAKE MOCK >`
        │
        └── launch_mock_standard(...)
                ├── validate selected lecture ids
                ├── load ready questions per lecture
                ├── build answer-safe question payloads
                └── write P4 launch state to session only
```

## Code walkthrough

### Constants
Constants define the launch-state key names, `mock` kind, and default target of five ready questions per selected lecture.

### `_unique_sorted_positive_ints(...)`
Validates selected lecture ids, removes duplicates, sorts ids for deterministic launches, and rejects empty selections before session writes.

### `_json_list(...)`
Parses stored JSON list fields, mainly `options_json`, into Python lists for the P4 display payload.

### `build_question_payload(...)`
Builds the answer-safe payload P4 can display. It keeps `question_type`, lecture/LO context, source page, language, and options. It omits `correct_indices` and rationales so answers are not exposed before final submit.

### `launch_mock_standard(...)`
Loads up to five ready questions from each selected lecture, builds payloads, returns honest copy when the available count is below target, writes launch state to session, and returns the same state for tests.

## Testing notes

```bash
python -m pytest -q tests/test_mock_standard_launch.py tests/test_question_type_launch_handoff.py
python -m ruff check app/class_/mock_standard_launch --no-cache
```

## What could break if changed

- Creating `attempts` here would break the all-or-nothing submit model.
- Including answers or rationales in session state would leak grading data during P4.
- Dropping `question_type` would break display labels and later real type analytics.
- Removing honest shorter-mock copy would hide why a selected mock has fewer questions than expected.

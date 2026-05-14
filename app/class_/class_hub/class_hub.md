# `class_hub` — Class Hub renderer

This module owns the P3 Class Hub screen. It renders the topbar, class title, `DASHBOARD >`, the red `CUSTOM MOCK >` button (Phase 7), the lecture chooser grid, the Add Lecture form, the Study Next card, the selected-lecture mock launch button, the narrow lecture-delete dialog, and the Attempt History section.

## How to call it

```python
from app.class_.class_hub import render_class_hub_page

render_class_hub_page(
    user={"id": user_id, "username": display_name},
    class_id=st.session_state.get("selected_class_id"),
)
```

Production uses the default query/render hooks. Tests and previews pass fakes through the same public entry point.

## Inputs / outputs

- **Input:** saved user mapping and `selected_class_id` from Streamlit session state.
- **Output:** Streamlit UI only; the function returns `None`.
- **Recovery:** if the class id is missing or invalid, the page renders `Class not found` and `BACK TO MY CLASSES`.
- **Launch output:** mock/practice helpers write `p4_launch_state`, `frozen_question_ids`, `p4_question_payloads`, and kind-specific session keys for P4.

## Data flow

```text
render_class_hub_page(...)
        │
        ├── get_class_by_id(class_id)
        ├── list_lectures_for_class(class_id)
        ├── ready_question_count_for_lecture(...) and ready-question queries
        ├── get_weakest_learning_objectives(class_id)
        ├── list_completed_attempts_for_class(class_id)
        ├── get_saved_anthropic_api_key(user_id) when Add Lecture submits
        ├── lecture_ingest.ingest_lecture(...) for title + PDF upload
        ├── launch_mock_standard(...) for `TAKE MOCK >`
        ├── launch_mock_custom(...) for `CUSTOM MOCK >` (Phase 7)
        ├── launch_study_next_practice(...) for Study Next `>`
        └── delete_lecture_after_confirmation(...) from the dialog confirm path
```

## Connected code and tools

- `views/class_view.py` resolves the saved user and selected class before calling this renderer.
- `app.brain.topbar`, `app.brain.page_header`, and `app.brain.page_layout` provide shared page chrome.
- `app.db.queries_*` helpers keep SQLite access out of the renderer.
- `app.class_.lecture_ingest` owns PDF processing, LO extraction, MCQ generation, and question storage.
- `app.class_.mock_standard_launch`, `app.class_.mock_custom_launch` (Phase 7), and `app.class_.study_next_launch` own session-only P4 handoff state.
- `app.class_.lecture_delete` owns the confirmation-gated delete service.

## Locked app behavior

- `TAKE MOCK >` is enabled only when at least one selected lecture has ready questions.
- Shorter mocks are allowed, but the helper copy says exactly how many ready questions exist.
- Add Lecture requires a non-empty lecture name and a PDF upload.
- Add Lecture fetches the saved Anthropic key from local SQLite; the renderer never reads environment keys and never displays the saved key.
- Attempt History stays hidden until the first completed mock or practice attempt exists.
- The dashboard button routes to `views/dashboard.py` while keeping `selected_class_id` in session state.
- The red `CUSTOM MOCK >` button (Phase 7) renders directly under `DASHBOARD >` with the same dimensions/layout and a red fill (`var(--surf-accent)`). Clicking launches up to 10 highest-personal-difficulty questions through the existing P4 attempt flow (`launch_mock_custom(...)`). If the class has no ready questions the button shows a toast and stays on the Class page; no DB write or attempt row is created here. Normal `TAKE MOCK >` and Study Next behavior are unchanged.
- Delete mode clears selected lecture ids, only lets deletable cells open the dialog, and blocks history-linked lectures through the DB helper.
- `question_type` is stored metadata passed forward for display and real analytics; this page does not compute difficulty profiles or classifier output.

## Code walkthrough

### Imports and constants
The imports define the renderer's boundaries: shared page chrome, class-bucket services, and database query helpers. Constants hold all visible copy, route strings, session-state keys, and grid sizing so contract tests can catch accidental copy or route drift.

### `build_lecture_grid_view_models(...)`
Builds the 3×4 lecture grid. It keeps lecture insertion order, labels real lectures as `L01`, `L02`, and so on, pads empty cells, marks only `ready` lectures selectable, and marks `failed`, `pending`, or never-attempted lectures deletable.

### `compute_take_mock_state(...)`
Reads selected lecture ids and ready-question counts. It disables `TAKE MOCK >` for empty selections and returns honest shorter-mock copy when the selected lectures have fewer ready questions than the target.

### `build_study_next_view_models(...)` and `render_study_next_section(...)`
Turn weak learning-objective rows into up to three Study Next rows and render the shared P3/P6 card. The render helper returns the clicked LO id only; callers decide whether to launch practice and navigate.

### `build_attempt_history_view_models(...)` and `attempt_history_is_visible(...)`
Convert completed attempt rows into display rows with kind, date, counts, lecture labels, and grade tier. The visibility helper hides the whole section until a completed attempt exists.

### `submit_add_lecture_form(...)`
Validates lecture title, PDF upload, and saved key. It writes uploaded bytes to a temporary `.pdf`, calls `ingest_lecture(...)` with `title=...` and `api_key=saved_key`, cleans up the temporary file when possible, and returns renderer-friendly status dictionaries.

### `handle_lecture_delete(...)`
Delegates confirmed deletion to `delete_lecture_after_confirmation(...)` and maps the result into page status. The renderer calls this only from the destructive dialog confirmation branch.

### Query defaults and CSS helpers
The `_default_*` query helpers are thin adapters around database functions. `_styles()` and related font/icon helpers scope Class Hub visuals to P3 keys so button, card, uploader, dialog, and Study Next styling do not leak across pages.

### Render helpers and `render_class_hub_page(...)`
Private render helpers draw the recovery state, lecture cells, dashboard button, Add Lecture form, Study Next, Attempt History, delete mode, and dialog. `render_class_hub_page(...)` gathers data, builds payloads, passes them to `_default_layout_renderer(...)`, and reacts to returned actions by launching mocks/practice or switching pages.

## Testing notes

```bash
python -m ruff check app/class_ views/class_view.py --no-cache
python -m pytest -q tests/test_class_hub_render_contract.py tests/test_class_hub_visual_rounds_4_10_contract.py tests/test_mock_standard_launch.py tests/test_study_next_launch.py tests/test_lecture_delete.py tests/test_lecture_delete_ui_contract.py tests/test_question_type_launch_handoff.py
```

## What could break if changed

- Changing session-state keys can break P4 launch recovery, P5 review routing, or dashboard ownership checks.
- Moving DB access into the renderer would make tests harder and increase live-data risk.
- Removing the saved-key lookup would make lecture upload fail or use the wrong key source.
- Removing the temporary-PDF cleanup can leave uploaded lecture files on disk.
- Expanding delete eligibility can break Attempt History and dashboard rows that still depend on lecture questions.
- Replacing honest empty states with generated placeholders would mislead users.

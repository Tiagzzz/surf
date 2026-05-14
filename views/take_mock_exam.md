# `views/take_mock_exam.py` — take mock/practice page wrapper

This file is the thin Streamlit page wrapper for the P4 attempt surface. It handles authentication routing, reads the selected class id from session state, and delegates the real page work to `app.mock_take.render_take_mock_page(...)`.

## Page overview

The wrapper is intentionally small so the attempt behavior stays in the `app/mock_take/` bucket. If no saved local user exists, it sends the browser to signup. If a user exists, it passes the saved user row and current class id to the attempt renderer.

## Inputs and outputs

**Inputs**

- `app.brain.session.get_saved_user()` result.
- `st.session_state["selected_class_id"]`, when a class is selected.
- Existing P4 launch/session state read later by the renderer.

**Outputs**

- `st.switch_page("views/signup.py")` for unauthenticated users.
- A call to `render_take_mock_page(user=_user, class_id=_class_id)` for authenticated users.
- No direct database write and no direct answer-state mutation in this wrapper.

## On-screen elements

The wrapper renders no visible UI itself. The delegated renderer owns the topbar, recovery message, question card, option rows, `SKIP`, `NEXT >`, finish buttons, and final confirmation dialog.

## User interactions

| Interaction | Handler |
|---|---|
| Unauthenticated page open | Wrapper routes to signup. |
| Authenticated page open | Wrapper delegates to the P4 renderer. |
| Answer/skip/navigation/final submit | `app.mock_take.question_render` and `app.mock_take.attempt_save`. |

## Data flow

```text
Streamlit page load
  -> get_saved_user()
  -> selected_class_id from session state
  -> render_take_mock_page(...)
  -> app/mock_take handles launch state, answers, and final submit
```

## Connected files, tables, and tools

- `app.brain.session`: saved-user lookup.
- `app.mock_take`: P4 bucket entry point.
- `streamlit_app.py`: page registry loads this wrapper.
- Final submit later writes `attempts` and `attempt_answers` through the P4 bucket, not through this wrapper.

## Code walkthrough

### Module docstring and imports

The module states that it is a thin P4 wrapper, imports Streamlit, imports `get_saved_user`, and imports the bucket-level `render_take_mock_page` function.

### Saved-user gate

`_user = get_saved_user()` asks the local session helper whether a user and key are saved. A missing user routes to `views/signup.py`.

### Authenticated delegation

For saved users, the wrapper reads `_class_id = st.session_state.get("selected_class_id")` and calls `render_take_mock_page(user=_user, class_id=_class_id)`. The renderer handles missing class/launch recovery.

## Tests and checks

- `tests/test_take_mock_view_wrapper.py`
- P4 state and submit tests listed in the bucket docs.
- `python -m ruff check views/take_mock_exam.py --no-cache`

## What could break if changed

- Removing the auth gate can expose attempt pages before local setup.
- Reading a different class-session key can break Class Hub launch handoff.
- Adding page logic here can duplicate P4 behavior and make tests harder to reason about.

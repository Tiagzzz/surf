# `views/review_mock_exam.py` — review mock/practice page wrapper

This file is the thin Streamlit page wrapper for the P5 review surface. It handles authentication routing, reads the selected class and attempt ids from session state, and delegates the read-only review UI to `app.mock_review.render_review_mock_page(...)`.

## Page overview

The wrapper does not fetch review rows or render cards. It only makes sure a saved local user exists and then passes the page context to the review bucket.

## Inputs and outputs

**Inputs**

- `app.brain.session.get_saved_user()` result.
- `st.session_state["selected_class_id"]`, when a class is selected.
- `st.session_state["current_attempt_id"]`, when a completed attempt was chosen or just submitted.

**Outputs**

- `st.switch_page("views/signup.py")` for unauthenticated users.
- A call to `render_review_mock_page(user=_user, class_id=_class_id, attempt_id=_attempt_id)` for authenticated users.
- No direct database write and no review-row parsing in this wrapper.

## On-screen elements

The wrapper renders no visible UI itself. The delegated renderer owns the topbar, recovery state, summary card, review cards, feedback rows, and bottom navigation buttons.

## User interactions

| Interaction | Handler |
|---|---|
| Unauthenticated page open | Wrapper routes to signup. |
| Authenticated page open | Wrapper delegates to the P5 renderer. |
| No selected attempt | P5 renderer shows recovery copy and a back-to-class button. |
| Review navigation | P5 renderer routes to class view or dashboard. |

## Data flow

```text
Streamlit page load
  -> get_saved_user()
  -> selected_class_id + current_attempt_id from session state
  -> render_review_mock_page(...)
  -> app/mock_review reads saved attempt data and renders review
```

## Connected files, tables, and tools

- `app.brain.session`: saved-user lookup.
- `app.mock_review`: P5 bucket entry point.
- `streamlit_app.py`: page registry loads this wrapper.
- `attempts` and `attempt_answers` are read by the review bucket's query helpers, not directly by this wrapper.

## Code walkthrough

### Module docstring and imports

The module identifies itself as the P5 wrapper, imports Streamlit, imports `get_saved_user`, and imports `render_review_mock_page` from the bucket root.

### Saved-user gate

`_user = get_saved_user()` checks local saved-user state. If it returns `None`, the wrapper routes to signup.

### Authenticated delegation

For saved users, the wrapper reads `_class_id` and `_attempt_id` from Streamlit session state, then calls `render_review_mock_page(...)`. The renderer owns missing-attempt recovery and all review display.

## Tests and checks

- `tests/test_review_mock_view_wrapper.py`
- `tests/test_review_mock_render_contract.py`
- `python -m ruff check views/review_mock_exam.py --no-cache`

## What could break if changed

- Removing the auth gate can expose review pages before local setup.
- Reading a different attempt-session key can break the submit-to-review handoff.
- Adding query or rendering logic here can duplicate the P5 bucket contract.

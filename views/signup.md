# `views/signup.py` — P1 signup page wrapper

This page wrapper is the Streamlit route for Surf's unauthenticated signup screen.

## What this page is for

`views/signup.py` keeps routing simple: it imports `render_signup_flow()` from the signup bucket and calls it. All page layout, validation, saving, and dialog behavior lives in `app/signup/signup_flow/__init__.py`.

## Actual wrapper code

```python
"""P1 — Sign Up. Thin Streamlit wrapper around ``render_signup_flow``."""

from app.signup.signup_flow import render_signup_flow

# Route-level wrapper: the signup bucket owns layout, validation, and save behavior.
render_signup_flow()
```

What this receives: the Streamlit runtime selects this file as the current page.  
What this generates: one call to the signup bucket renderer. It does not generate database rows, API calls, or page CSS itself.

## Route and session context

| Context | Detail |
|---|---|
| Router | `streamlit_app.py` selects this page when `app.brain.session.is_authenticated()` is false. |
| Session state | The wrapper does not read or write session state directly. Streamlit owns the current input widget state during the render. |
| Next page | Successful signup switches to `views/my_classes.py` inside the signup flow renderer. |
| Authenticated shell | P1 does not render the shared authenticated topbar. |

## External tools, libraries, and app functions used

| Name | Type | Where this wrapper touches it |
|---|---|---|
| Streamlit page router | External framework behavior | Chooses `views/signup.py` as the page file. |
| `render_signup_flow` | Surf app function | The only imported function; it renders and handles signup. |
| `app.brain.session.is_authenticated` | Surf app function | Used upstream by `streamlit_app.py` to decide whether this route is shown. |
| `views/my_classes.py` | Surf page route | The signup renderer switches there after successful local setup. |

## On-screen elements

The wrapper itself creates no visible elements. The called renderer creates these elements:

| Element | Source code |
|---|---|
| Left brand panel | `app.signup.signup_flow._render_left_panel()` |
| Welcome card | `app.signup.signup_flow._render_setup_card()` |
| Display-name field | `st.text_input(..., key="p1_display_name")` |
| Anthropic key field | `st.text_input(..., key="p1_anthropic_api_key", type="password")` |
| Console helper link | Signup flow constant `CONSOLE_URL` |
| `AI USE` button | `st.button(..., key="p1_ai_use")` |
| `START SURFING >` button | `st.button(..., key="p1_submit", type="primary")` |
| Privacy helper copy | Signup flow constant `HELPER_COPY` |

## User interactions

| User action | Handler/module | Navigation or data effect |
|---|---|---|
| Opens app without a saved local user | `streamlit_app.py` routes here | Signup page renders. |
| Clicks `AI USE` | `app.signup.signup_flow._show_ai_use_dialog` | Dialog opens; no validation, database write, or route change. |
| Clicks `START SURFING >` with missing fields | `_save_after_validation` | Inline error; no validation or save. |
| Clicks `START SURFING >` with invalid key | `_save_after_validation` and `validate_anthropic_key` | Invalid-key toast; no local save. |
| Clicks `START SURFING >` with valid key | `_save_after_validation` and `upsert_user_setup` | Local user setup is saved, then page switches to My Classes. |

## Data sources

- User-typed display name from the P1 display-name field.
- User-typed Anthropic API key from the P1 password field.
- Local Markdown copy from `app/signup/signup_flow/ai_use_copy.md` for the dialog.
- Local font files from `assets/fonts/` for the approved P1 visual style.
- No live database row is read by this wrapper directly.

## Connected bucket

| Bucket/module | Relationship |
|---|---|
| `app.signup.signup_flow` | Owns the full P1 render and submit behavior. |
| `app.brain.claude_client` | Validates the typed Anthropic key through the renderer callback. |
| `app.db.queries_users` | Saves the local user setup after validation. |
| `app.brain.session` | Decides whether the router should show signup before this wrapper runs. |

## Code walkthrough

### 1. Docstring

```python
"""P1 — Sign Up. Thin Streamlit wrapper around ``render_signup_flow``."""
```

The docstring tells future readers that this file is a route wrapper, not the implementation. The implementation lives in the signup bucket.

### 2. Import

```python
from app.signup.signup_flow import render_signup_flow
```

This imports exactly one function. The wrapper does not import database helpers, key validators, CSS helpers, or dialog helpers. That keeps the route easy to review.

### 3. Render call

```python
render_signup_flow()
```

When Streamlit runs this page file, this call generates the whole signup UI. The default callbacks inside `render_signup_flow` validate the typed key and save local setup only after validation succeeds.

## Testing notes

- `tests/test_signup_flow.py` covers the behavior owned by the called renderer.
- `tests/test_session_auth.py` covers the auth decision that sends users to this page.
- `tests/test_no_secrets_committed.py` and `tests/test_no_real_db.py` protect key and local database safety.

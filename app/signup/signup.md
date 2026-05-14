# `app/signup/` — P1 signup bucket

This bucket owns **P1 — Sign Up / local setup**, the first screen shown before Surf has a saved local user. It collects a display name and Anthropic API key, validates the typed key, saves both locally only after validation succeeds, and then opens My Classes.

## What this page is for

Surf is a local-first study app. It does not create a remote Surf account. The signup bucket gives the app one local user record so later pages know who is using the app and which Anthropic key to use for factsheet cleanup, lecture processing, and question generation.

For non-coders: this is like the key desk at the entrance. The user writes their name, proves their Anthropic key works, and then Surf stores that setup on this computer so the rest of the app can run.

## What lives in this folder

| File / folder | What it does | Used by |
|---|---|---|
| `__init__.py` | Empty package marker kept thin on purpose. | Python import system. |
| `api_key_validate/` | Legacy isolated key-validation helpers kept for reference until a future maintenance decision decides their role. | Not the main P1 page path. |
| `signup_flow/__init__.py` | Main renderer for the P1 split layout, input handling, key validation, local save, and route to My Classes. | `views/signup.py`. |
| `signup_flow/ai_use_copy.md` | Markdown shown inside the `AI USE` dialog. | P1 signup and the Settings page dialog. |
| `signup_flow/signup_flow.md` | Detailed file sidecar for the renderer, including code snippets. | Team documentation and future maintenance. |
| `signup.md` | This bucket sidecar. | Team documentation and code-impact review. |

## How signup fits Surf

```text
streamlit_app.py
      │ unauthenticated local user
      ▼
views/signup.py
      ▼
app.signup.signup_flow.render_signup_flow()
      ├─ validate typed key with app.brain.claude_client.validate_anthropic_key
      ├─ save display name + key with app.db.queries_users.upsert_user_setup
      └─ switch to views/my_classes.py after success
```

A user reaches this bucket only when the app has no authenticated saved user. After signup, the router can show the authenticated pages: My Classes, Class Hub, Take Mock, Review, Dashboard, and Settings.

## External tools, libraries, and app functions used

| Name | Type | Purpose in signup |
|---|---|---|
| Streamlit (`st`) | External UI library | Renders columns, inputs, buttons, dialogs, toasts, spinners, and page navigation. |
| Anthropic Console URL | External web service link | Helps the user find or create an Anthropic API key. |
| `app.brain.claude_client.validate_anthropic_key` | Surf app function | Validates the typed Anthropic key before saving. |
| `app.db.queries_users.upsert_user_setup` | Surf app function | Saves the display name and key in the local SQLite database after validation. |
| SQLite through `queries_users` | Local database storage | Stores the setup on this computer. This bucket does not call SQLite directly. |
| `Path`, `base64`, `escape`, `Callable` | Python standard library | Support local file reads, inline fonts, safe HTML text, and typed callback parameters. |
| `assets/fonts/*.woff2` | Local files | Supply the approved P1 fonts. |
| `signup_flow/ai_use_copy.md` | Local Markdown | Supplies reusable visible copy for the `AI USE` dialog. |

## Requirement coverage

| Requirement | How this bucket covers it |
|---|---|
| P1 signup entry | Shows display-name and Anthropic API-key fields. |
| Local-only key storage | Saves the key through the local user query helper after validation. |
| Key validation before save | Calls the Anthropic validation helper before `upsert_user_setup`. |
| Privacy copy | Shows helper text that the key is validated and saved on this computer. |
| AI-use explanation | Reuses `ai_use_copy.md` in the popup so the explanation has one source. |
| Unauthenticated routing | `streamlit_app.py` shows `views/signup.py` before authenticated pages. |

## User interactions

| Visible action | Code path | Result |
|---|---|---|
| Type display name | `st.text_input(..., key="p1_display_name")` in `_render_setup_card` | Streamlit gives the current text to `_save_after_validation` only when submit is clicked. |
| Type Anthropic API key | `st.text_input(..., key="p1_anthropic_api_key", type="password")` | Streamlit masks the key and passes it only to validation/save callbacks on submit. |
| Click Console link | HTML link using `CONSOLE_URL` | Browser opens Anthropic Console. |
| Click `AI USE` | `_show_ai_use_dialog()` | Opens Markdown explanation; no validation or save runs. |
| Click `START SURFING >` with blanks | `_save_after_validation()` missing-field guards | Shows an error and saves nothing. |
| Click `START SURFING >` with invalid key | `validate_key(clean_key)` branch | Shows invalid-key toast and saves nothing. |
| Click `START SURFING >` with valid key | `save_setup(clean_name, clean_key)` then `st.switch_page(...)` | Saves local setup and routes to My Classes. |

## Code walkthrough

### 1. Route entry

The route wrapper is intentionally tiny:

```python
from app.signup.signup_flow import render_signup_flow

render_signup_flow()
```

This means routing and rendering meet at one public function. The wrapper does not validate keys, write the database, or style the page itself.

### 2. Public renderer creates the page shell

```python
def render_signup_flow(
    *,
    validate_key: Callable[[str], bool] = validate_anthropic_key,
    save_setup: Callable[[str, str], int] = upsert_user_setup,
) -> None:
    _render_styles()
    left, right = st.columns([1, 1], gap="small")
    with left:
        _render_left_panel()
    with right:
        with st.container(key="p1_setup_panel"):
            _render_setup_card(validate_key=validate_key, save_setup=save_setup)
```

This block receives two callbacks. In production, they are the real Anthropic-key validator and local-save function. In tests, they can be fake functions. It generates the split page and passes those callbacks down to the setup card.

### 3. Setup card captures values and button choices

```python
display_name = st.text_input("DISPLAY NAME", key="p1_display_name", ...)
api_key = st.text_input("ANTHROPIC API KEY", key="p1_anthropic_api_key", type="password", ...)

ai_use_clicked = st.button(AI_USE_LABEL, key="p1_ai_use", ...)
submit_clicked = st.button(PRIMARY_LABEL, key="p1_submit", type="primary", ...)
```

This block generates the visible fields and buttons. The two buttons produce two separate booleans so the information popup and form submit stay separate.

### 4. Button branches keep help separate from save

```python
if ai_use_clicked:
    _show_ai_use_dialog()
    return

if submit_clicked:
    _save_after_validation(
        display_name,
        api_key,
        validate_key=validate_key,
        save_setup=save_setup,
    )
```

The early `return` is important: if `AI USE` is clicked, the function opens help and stops. It cannot also validate or save.

### 5. Validation and save gates

```python
clean_name = display_name.strip()
clean_key = api_key.strip()

if not clean_name:
    st.error(MISSING_NAME_ERROR)
    return False
if not clean_key:
    st.error(MISSING_KEY_ERROR)
    return False
```

Empty values stop before Anthropic validation or database save.

```python
with st.spinner(VALIDATING_COPY):
    key_is_valid = validate_key(clean_key)

if not key_is_valid:
    st.toast(INVALID_KEY_TOAST)
    return False
```

Only a non-empty typed key reaches the validator. A failed validation keeps the user on signup.

```python
save_setup(clean_name, clean_key)
st.toast(SUCCESS_TOAST)
st.switch_page(SWITCH_PAGE_PATH)
return True
```

Only a valid key reaches the local-save callback. After the save succeeds, the page switches to My Classes.

### 6. Dialog and copy files

```python
def _show_ai_use_dialog() -> None:
    @st.dialog(AI_USE_LABEL)
    def _dialog() -> None:
        st.markdown(_load_ai_use_copy())

    _dialog()
```

The dialog reads `signup_flow/ai_use_copy.md`. This keeps visible explanation text separate from validation/save code.

## What classmates should be able to explain

- Signup is local setup, not a remote account system.
- The Anthropic key is validated before it is saved.
- Failed validation keeps the user on signup and saves nothing.
- The key is stored in the local SQLite user table because Surf needs it for later Anthropic Claude calls.
- `AI USE` is information only; it does not submit the form.
- The page has no authenticated topbar because it appears before the user enters the app.
- The renderer accepts fake callbacks in tests, which is why signup can be tested without a real Anthropic key or live database.

## Testing notes

Run the focused signup checks after changes:

```bash
python -m pytest -q tests/test_signup_flow.py tests/test_session_auth.py tests/test_no_secrets_committed.py tests/test_no_real_db.py
python -m ruff check app/signup views/signup.py --no-cache
```

## What could break if changed

- A validation bypass could save a bad key.
- Showing or logging a key value could leak a credential.
- Changing `views/my_classes.py` routing could trap users on signup after success.
- Duplicating AI-use copy could make P1 and Settings disagree.
- Broad P1 CSS could affect authenticated pages.
- Replacing callback injection with direct hard-coded calls would make safe tests harder.

# `app/settings/` bucket — P7 Settings page and helpers

This bucket owns the P7 Settings surface: a three-card vertical stack (**Profile** → **Anthropic API key** → **Reset app data**). `app.settings.render_settings_page` draws the cards, opens `AI USE` from shared signup markdown, and gates local reset behind the exact typed `DELETE` token. The bucket is intentionally small: the page renderer owns Streamlit UI, and the service folders own the save/replace/reset rules.

## What lives in this bucket

| Folder / file | What it does |
|---|---|
| `__init__.py` | P7 page renderer, locked copy strings, scoped CSS, card/dialog renderers, and pure helpers such as `is_reset_confirmation_armed`. |
| `username_save/` | Validates a non-blank display name, then calls `app.db.queries_users.update_display_name`. |
| `api_key_save/` | Validates the typed Anthropic key before replacing the saved key. Blank/failed branches keep the old key unchanged. |
| `reset_account/` | Deletes the local account graph in one SQLite transaction after the page confirms the typed `DELETE` gate. No plaintext-key backup is created. |
| `backup_export/` | Reserved placeholder. It is not used by P7 reset and should stay inert unless a future approved backup flow is designed. |
| `settings.md` | This bucket sidecar. |

## How the pieces interact

```text
views/settings.py
        │
        └── app.settings.render_settings_page(user=...)
                ├── app.brain.topbar.render_topbar(current_page="settings")
                ├── app.brain.page_layout.page_rail("p7_settings_page")
                ├── app.brain.page_header.render_page_header(...)
                ├── _render_profile_card
                │       └── app.settings.username_save.save_display_name
                │               └── app.db.queries_users.update_display_name
                ├── _render_api_key_card
                │       ├── _render_ai_use_dialog
                │       │       └── app/signup/signup_flow/ai_use_copy.md
                │       └── app.settings.api_key_save.replace_api_key_after_validation
                │               ├── app.brain.claude_client.validate_anthropic_key
                │               └── app.db.queries_users.replace_anthropic_api_key
                └── _render_reset_card
                        └── _render_reset_dialog
                                └── app.settings.reset_account.reset_local_account_data
                                        └── SQLite `DELETE FROM users`
```

## Connected code, tools, and libraries

- **Streamlit:** `st.container`, `st.text_input`, `st.button`, `st.dialog`, `st.spinner`, `st.toast`, `st.rerun`, and `st.session_state.clear`.
- **Shared shell:** `render_topbar`, `page_rail`, and `render_page_header` give Settings the authenticated Surf shell.
- **Shared AI-use copy:** `app/signup/signup_flow/ai_use_copy.md` feeds both P1 and P7 so the explanation stays single-sourced.
- **Anthropic validation:** `app.brain.claude_client.validate_anthropic_key` validates the newly typed replacement key only.
- **SQLite helpers:** `update_display_name`, `replace_anthropic_api_key`, `get_local_db_path`, and `reset_local_account_data` are the only data-writing paths.
- **Standard library:** `html.escape` protects rendered copy; `pathlib.Path` resolves the shared markdown path.

## User interactions and data flow

1. **Profile card:** User types a new display name → `save_display_name(user_id, new_name)` strips and validates → DB helper updates the user row → page toasts success and reruns, or shows the returned error copy.
2. **Anthropic API key card:** User types a new key → `replace_api_key_after_validation(user_id, new_key)` strips it, validates with Anthropic, and only then persists it. Blank input, validation failure, validation exception, persist exception, or persist `False` keep the old key unchanged.
3. **AI USE dialog:** User presses `AI USE` → `_render_ai_use_dialog()` opens a modal and renders the shared markdown. No DB/API write happens.
4. **Reset card:** User presses `RESET APP DATA` → dialog asks for exact typed `DELETE` → confirmed reset calls `reset_local_account_data`, clears Streamlit session state, shows a toast, and reruns through the app router. Because the local user/key has been deleted, the router mounts only Sign Up.

## Constraints

- The saved Anthropic key value is never rendered, printed, logged, or copied into docs. The page only uses `bool(user.get("anthropic_api_key"))` to decide whether to show `API key saved`.
- Replacement validation must happen before persistence, and any non-success branch must preserve the old key.
- Reset uses the exact token `DELETE`; lowercase, trailing spaces, or extra characters keep the destructive button disabled.
- Reset creates no plaintext-key backup. `backup_export/` is reserved and not part of the current P7 reset.
- The shared AI-use markdown path must remain single-sourced with signup.
- Comment/doc cleanup must not change card order, Streamlit keys, CSS selectors, locked copy strings, validation branches, or route names.

## Code walkthrough

### 1. Module docstring and imports

`app/settings/__init__.py` starts by naming the three cards and the injected services. Imports stay narrow: Streamlit for rendering, `escape` for safe HTML copy, `Path` for the shared markdown location, and the specific Surf helpers that Settings calls.

```python
from html import escape
from pathlib import Path
from typing import Any, Callable

import streamlit as st
```

### 2. Locked constants

The next block defines every visible Settings label and helper string: page title, card titles, field labels, button labels, toast messages, reset dialog copy, and the signup route constant used by tests/docs.

```python
RESET_TYPED_TOKEN = "DELETE"
SIGNUP_VIEW_PATH = "views/signup.py"
```

These constants make tests and sidecars point at one source instead of repeating copy across card functions.

### 3. Shared AI-use path and pure helpers

`_AI_USE_COPY_PATH` resolves `app/signup/signup_flow/ai_use_copy.md`. `get_ai_use_copy_path()` exposes that path for tests, `load_ai_use_copy()` reads it for the dialog, and `is_reset_confirmation_armed()` is the exact typed-`DELETE` check.

```python
def is_reset_confirmation_armed(typed_value: str) -> bool:
    return typed_value == RESET_TYPED_TOKEN
```

### 4. `_settings_styles()`

This function returns the scoped CSS for the Settings page. It styles the page rail, hard-stamped cards, hidden text-input labels, full-width inputs, stamped buttons, dialog buttons, destructive reset button, card spacing, and reduced-motion fallback. The key idea: selectors stay under P7 keys (`p7_settings_page`, `p7_profile_save`, `p7_reset_confirm`, etc.) so Settings polish does not leak into other pages.

### 5. `_render_profile_card()`

The profile card receives `user_id`, current `display_name`, and an injectable `save_name_fn`. It renders the current-name line, text input, and `SAVE NAME` button. On click it renders only the status dict returned by `save_name_fn`.

```python
result = save_name_fn(user_id, new_name)
if result["status"] == "saved":
    st.toast(PROFILE_SAVE_SUCCESS_TOAST)
    st.rerun()
```

### 6. `_render_ai_use_dialog()` and `_render_api_key_card()`

The dialog reads the shared markdown. The API-key card shows only saved-key presence, never the key value. The replacement button wraps `replace_key_fn(user_id, new_key)` in a spinner and switches on the returned status dict.

### 7. `_render_reset_dialog()` and `_render_reset_card()`

The reset card shows the local DB path and warning copy. The dialog collects the typed confirmation, disables the destructive button until `is_reset_confirmation_armed(typed)` is true, then calls `reset_fn()`, clears session state, shows the success toast, and calls `st.rerun()`. The rerun lets `streamlit_app.py` recalculate auth from the now-empty local data and show Sign Up directly.

### 8. `render_settings_page()`

The public entry point renders topbar, Settings CSS, page rail, shared page header, and the three cards in order. It accepts injectable functions so tests and previews can run without real Anthropic calls, live SQLite writes, or live reset actions.

## Testing notes

```bash
python -m pytest -q tests/test_streamlit_app_router.py
ruff check app/settings views/settings.py tests/test_streamlit_app_router.py --no-cache
```

These checks prove the typed reset reruns through the router, the signed-in reload redirect is one-time only, unauthenticated routing still mounts Sign Up only, and the Settings lint contract remains clean.

## What could break if changed

- Rendering `user["anthropic_api_key"]` directly would leak the saved key.
- Calling persistence before validation would overwrite the old key with an invalid key.
- Removing the exact `DELETE` check would make reset too easy to trigger.
- Changing Streamlit keys would break scoped CSS and tests that look for safe button paths.
- Moving AI-use copy into a Settings-only file would let P1 and P7 explanations drift.
- Calling reset helpers outside injected tests can mutate the live local DB.

## Recent UI documentation notes

The shared authenticated header now wraps Settings through the same helper used by My Classes, Class Hub, and Dashboard. Settings passes an empty helper string because the approved page has no extra subtitle. Button-label selectors target both native Streamlit buttons and their child text wrappers so labels such as `SAVE NAME`, `REPLACE API KEY`, `AI USE`, `RESET APP DATA`, and reset-dialog buttons use the Surf button font reliably.

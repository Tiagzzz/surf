# `views/settings.py` — P7 Settings route wrapper

This page file is intentionally thin. Streamlit mounts it when the user chooses Settings from the authenticated app shell. The wrapper resolves the saved user and delegates all UI, copy, validation, and reset behavior to `app.settings.render_settings_page`.

## What this page is for

- Provide the Streamlit route for P7 Settings.
- Block rendering if the saved user disappears between routing and page render.
- Keep page logic in `app/settings/` instead of inside the `views/` file.

## Route and session context

```text
streamlit_app.py
    └── authenticated user chooses Settings
            └── views/settings.py
                    ├── app.brain.session.get_saved_user()
                    └── app.settings.render_settings_page(user=user)
```

The router normally sends only authenticated users here. The wrapper still checks `get_saved_user()` because local data can be reset or removed while the app is running.

## On-screen elements

The wrapper does not create page elements itself except for the defensive `Not signed in.` error. When a user exists, `app.settings.render_settings_page` renders:

- Shared authenticated topbar and page header.
- Profile card.
- Anthropic API key card with AI USE dialog.
- Reset app data card with typed `DELETE` confirmation.

## User interactions

- Save display name → `app.settings.username_save.save_display_name`.
- Replace Anthropic key → `app.settings.api_key_save.replace_api_key_after_validation`.
- Open AI USE info → shared markdown at `app/signup/signup_flow/ai_use_copy.md`.
- Reset local data → typed `DELETE` gate, then `app.settings.reset_account.reset_local_account_data`, then route to `views/signup.py`.

## Data sources and safety

- `get_saved_user()` reads the current local user row through the brain/session helper.
- The wrapper never prints or logs the saved key.
- If no user is returned, the wrapper displays a generic error and does not call the Settings renderer.

## Connected buckets

- `app/brain/session/` — saved-user lookup.
- `app/settings/` — all P7 Settings UI and behavior.
- `app/db/queries_users/` — reached by Settings services, not directly by this wrapper.
- `app/signup/signup_flow/` — shared AI-use copy and post-reset destination.

## Code walkthrough

### Imports

```python
from app.brain.session import get_saved_user
from app.settings import render_settings_page
```

The wrapper imports one auth/session helper and one page renderer.

### Saved-user guard

```python
user = get_saved_user()
if user is None:
    import streamlit as st
    st.error("Not signed in.")
```

This is a defensive fallthrough for a rare stale-session case. It avoids rendering Settings with a missing user dict.

### Render delegation

```python
else:
    render_settings_page(user=user)
```

All card layout, validation, key replacement, AI USE, and reset behavior lives in `app/settings/`.

## Testing notes

```bash
python -m pytest -q tests/test_settings_account.py tests/test_settings_reset.py tests/test_no_secrets_committed.py tests/test_no_real_db.py
ruff check app/settings views/settings.py --no-cache
```

## What could break if changed

- Calling `render_settings_page` with `user=None` would break Settings card assumptions.
- Moving service logic into this route wrapper would make the page harder to test and explain.
- Logging the user dict could expose the saved Anthropic key.
- Changing the post-reset destination in Settings without updating this page doc would make reset handoff confusing.

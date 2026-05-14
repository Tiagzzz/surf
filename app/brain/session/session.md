# `app/brain/session/__init__.py`

Saved-user session helper for the app shell. It answers whether Surf has a real
saved user row and whether that row has a non-blank Anthropic key. The router
uses these answers instead of guessing from the presence of a SQLite file.

## Purpose

- `is_authenticated()` decides whether the authenticated pages can be shown.
- `get_saved_user()` returns the active local user row for page renderers that
  need the username or saved key.
- `has_saved_user()` lets callers distinguish "no setup yet" from "setup exists
  but key is blank".

## Inputs / outputs

| Function | Input | Output |
|---|---|---|
| `is_authenticated()` | none | `True` when a user row exists with a non-blank `anthropic_api_key` |
| `get_saved_user()` | none | Saved user row as `dict`, or `None` |
| `has_saved_user()` | none | `True` when any saved user row exists |

## Data flow

Each function imports `app.db.queries_users` lazily inside the function body.
That keeps importing `app.brain.session` side-effect-free and avoids touching
`~/.surf/user.sqlite` until a page actually asks for user state.

## Connected code and tools

- `streamlit_app.py` calls `is_authenticated()` to choose unauthenticated or
  authenticated pages.
- Page wrappers and renderers call `get_saved_user()` when they need current
  user context.
- Query helpers under `app.db.queries_users` own the actual SQLite reads.
- No Anthropic call happens here.

## No-secret boundaries

`get_saved_user()` may return an `anthropic_api_key` field because generation
and Settings need it. UI code must not print or log the whole dict; display only
safe fields such as the username.

## Code walkthrough

### Module docstring

States the saved-user auth boundary and warns that imports must not create or
mutate the local database.

### `is_authenticated()`

Imports `has_saved_user_with_key` lazily and returns its boolean result. This is
the router's main authenticated/unauthenticated gate.

### `get_saved_user()`

Imports `get_active_user` lazily and returns the saved user row or `None`. The
function does not redact the dict, so callers are responsible for not rendering
or logging the saved key.

### `has_saved_user()`

Imports `get_active_user` lazily and checks whether any row exists. This helps
Settings/recovery copy avoid treating a blank-key setup like a first launch.

## Testing notes

```bash
python -m pytest -q tests/test_session_auth.py tests/test_no_secrets_committed.py
```

## What could break if changed

- Opening the database at import time can break tests and startup flows that
  monkeypatch `HOME`.
- Rendering the full user dict can leak the plaintext local key.
- Returning pandas objects or custom classes would make simple page contracts
  harder to reason about and test.

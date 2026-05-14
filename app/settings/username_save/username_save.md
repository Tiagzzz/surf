# `app/settings/username_save/` — display-name save service

A thin orchestrator around `app.db.queries_users.update_display_name`. The P7 page never touches the queries layer directly — it asks this module to save and renders the returned status dict.

## What lives in this folder

| File | What it does |
|---|---|
| `__init__.py` | Exports `save_display_name(user_id, display_name)` and three locked copy strings the service returns inside its status dict (`Add a display name to save.`, `Couldn't save name`, `Something went wrong. Try again.`). |
| `username_save.md` | This sidecar. |

## How it's used

```python
from app.settings.username_save import save_display_name

result = save_display_name(user_id, raw_input)
if result["status"] == "saved":
    st.toast("Saved.")
elif result.get("kind") == "missing_name":
    st.error(result["message"])
else:
    st.toast(f"{result['title']} — {result['body']}")
```

The persist function is **injectable** so tests and the P7 preview sandbox can supply a fake (no live SQLite write):

```python
fake_persist = lambda uid, name: True  # or False, or `raise`
result = save_display_name(1, "Student Name", persist_fn=fake_persist)
```

## Pages and tools this module connects to

- **P7 Profile card** (`app.settings.render_settings_page` → `_render_profile_card`) calls `save_display_name(user_id, new_name)` and renders the status dict.
- **Data layer:** `app.db.queries_users.update_display_name(user_id, display_name) -> bool` is the default persist target. Returns `True` on success, `False` if the row wasn't found.
- **Test suite:** `tests/test_settings_account.py` has four service-layer tests (blank input, success path, persist exception, persist returns False).

## Constraints

- **Strip whitespace before validating empty.** `"   "` is treated as blank; `"  Student Name  "` is persisted as `"Student Name"`.
- **Never log or display raw input.** The status dict carries the cleaned name back to the page only on success; failure branches surface generic copy.
- **Don't add session-state writes here.** This module is a pure-function orchestrator; the page owns Streamlit state.
- **Don't widen the return shape silently.** The page's `result["status"]` switch is what ships in production — adding a new branch needs a corresponding test + page handler.

## Code walkthrough

This walkthrough mirrors the order of declarations in `app/settings/username_save/__init__.py`.

### 1. Module docstring (lines 1–18)

States the contract: thin orchestrator, returns a status dict the page can render directly, persist function is injectable for tests/sandbox.

### 2. Locked copy constants (lines 26–28)

Three private strings that hold the exact user-facing copy. Live in this module (not in the page) so the service is the single source of truth for the strings it can return:

- `_MISSING_NAME_MESSAGE = "Add a display name to save."`
- `_SAVE_FAILURE_TITLE = "Couldn't save name"`
- `_SAVE_FAILURE_BODY = "Something went wrong. Try again."`

Underscored because they're implementation details — the page only sees them via the returned dict's `message` / `title` / `body` keys.

### 3. `save_display_name(user_id, display_name, *, persist_fn=update_display_name)` (lines 31–73)

The only public function. Three branches:

1. **Strip-and-blank check (lines 49–55).** `display_name.strip()` and reject empty. Status dict: `{"status": "error", "kind": "missing_name", "message": ...}`. The persist function is **not** called.
2. **Persist-with-exception-shield (lines 57–65).** `persist_fn(user_id, clean)` inside a `try/except`. Any exception (DB locked, schema mismatch, etc.) returns the save-failure dict.
3. **Persist-returned-False guard (lines 67–73).** `update_display_name` returns `False` when the row doesn't exist — that's also a save failure from the user's perspective.

On success, returns `{"status": "saved", "display_name": <stripped>}` so the page can update its `Current name: …` line inline without re-querying.

## What could break if changed

- Renaming `save_display_name` breaks both the P7 page import and the test suite.
- Removing the `try/except` around `persist_fn` lets a SQLite exception leak into the Streamlit script and produce an ugly traceback in the page.
- Adding a second persist call (e.g., to log the change) without a corresponding `try/except` reintroduces the leak risk.
- Returning a status dict the page doesn't recognize falls through the `else` branch and renders the generic save-failure toast. Tighten the test suite if you add new branches.

## Verification commands

```bash
python -m pytest tests/test_settings_account.py -k save_display_name -q
ruff check app/settings/username_save tests/test_settings_account.py
```

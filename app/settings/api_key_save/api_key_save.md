# `app/settings/api_key_save/` — Anthropic API-key replacement service

The locked Surf V1 safety rule: the saved key is **only** overwritten after a fresh validation against Anthropic succeeds. Every other branch — blank input, validation exception, validation `False`, persist exception, persist `False` — leaves the existing saved key untouched.

This module enforces that rule. The P7 API-key card calls `replace_api_key_after_validation(user_id, typed_key)` and renders the returned status dict.

## What lives in this folder

| File | What it does |
|---|---|
| `__init__.py` | Exports `replace_api_key_after_validation(user_id, new_api_key)` and the locked status copy strings the service returns. |
| `api_key_save.md` | This sidecar. |

## How it's used

```python
from app.settings.api_key_save import replace_api_key_after_validation

result = replace_api_key_after_validation(user_id, typed_key)
if result["status"] == "replaced":
    st.toast("Saved.")
elif result.get("kind") == "blank":
    st.error(result["message"])
else:
    st.toast(f"{result['title']} — {result['body']}")
```

Both the validate and persist functions are **injectable** so tests and the P7 preview sandbox can supply fakes (no real Anthropic call, no live SQLite write):

```python
result = replace_api_key_after_validation(
    user_id,
    "sk-ant-test",
    validate_fn=lambda k: True,         # or False, or raise
    persist_fn=lambda uid, k: True,     # or False, or raise
)
```

## Pages and tools this module connects to

- **P7 API-key card** (`app.settings.render_settings_page` → `_render_api_key_card`) wraps the call in `st.spinner("Checking your Anthropic key…")` and routes the status dict to either an inline error or a notification toast.
- **Validation:** `app.brain.claude_client.validate_anthropic_key(api_key) -> bool` — same path P1 uses.
- **Data layer:** `app.db.queries_users.replace_anthropic_api_key(user_id, api_key) -> bool` — single-column update, returns `False` if the user row is missing.
- **Test suite:** `tests/test_settings_account.py` has five service-layer tests covering every non-success branch + the success path. Each one checks BOTH the returned dict AND that the persist function was not called when validation failed (the locked safety guarantee).

## Constraints (non-negotiable)

- **Never call persist before validate succeeds.** A blank input, a validation exception, or a `False` validation must short-circuit before `persist_fn` runs. The test suite has explicit assertions on this — `validate_calls == []` for blank, `persist_calls == []` for invalid / exception.
- **Never log or display the typed key.** The status dict carries no key value (success or failure). The page only sees status copy.
- **Strip whitespace before validating.** `"   "` is treated as blank; `"  sk-ant-typed  "` is validated and persisted as `"sk-ant-typed"`.
- **Don't add session-state writes here.** Page owns Streamlit state.

## Code walkthrough

This walkthrough mirrors the order of declarations in `app/settings/api_key_save/__init__.py`.

### 1. Module docstring (lines 1–22)

States the locked safety rule, the injection pattern for tests/sandbox, and the status-dict shape.

### 2. Imports (lines 25–28)

`validate_anthropic_key` from `app.brain.claude_client` and `replace_anthropic_api_key` from `app.db.queries_users`. Both are the production defaults the page uses; tests pass fakes via the keyword arguments.

### 3. Locked copy constants (lines 32–39)

Five private strings — every status-dict text the page renders. Underscored because the page only sees them via the returned dict.

- `_BLANK_MESSAGE` — inline error below the field.
- `_INVALID_TITLE` / `_INVALID_BODY` — toast on validation failure or exception.
- `_SAVE_FAILURE_TITLE` / `_SAVE_FAILURE_BODY` — toast on persist failure or exception.

These strings are the service copy contract; keep the page and tests in sync if they change.

### 4. `replace_api_key_after_validation(user_id, new_api_key, *, validate_fn=…, persist_fn=…)` (lines 42–110)

The only public function. **Six branches**, each blocking every later branch:

1. **Strip-and-blank check (lines 67–73).** Empty input → blank-error dict. No validation. No persist.
2. **Validation exception shield (lines 75–82).** `validate_fn(clean)` inside `try/except`. Any exception (network down, SDK error, API timeout) → invalid-key dict. The page surfaces the same toast as a `False` return — distinguishing "the key is wrong" vs "we couldn't reach Anthropic" would leak network state to a UX that doesn't need it.
3. **Validation `False` (lines 84–90).** Anthropic rejected the key → invalid-key dict.
4. **Persist exception shield (lines 92–99).** `persist_fn(user_id, clean)` inside `try/except`. SQLite errors → save-failure dict.
5. **Persist `False` (lines 101–107).** User row doesn't exist (rare; usually a race with a reset) → save-failure dict.
6. **All four pass (lines 109).** `{"status": "replaced"}` — the page toasts `Saved.` and clears the input.

The page never sees the new or old key value in the returned dict — that's intentional. Status copy is what the page renders.

## What could break if changed

- Removing the validation `try/except` lets a network exception leak into the Streamlit script and break the P7 render.
- Reordering the branches (e.g., persist before validate) violates the locked safety rule and the tests will fail with `persist_calls == [...]` instead of `[]`.
- Adding a status dict the page doesn't recognize falls through the `else` branch and renders the generic save-failure toast. Tighten the test suite if you add new branches.
- Logging the cleaned key anywhere (debug print, telemetry, exception body) violates the "never display the typed key" rule.

## Verification commands

```bash
python -m pytest tests/test_settings_account.py -k replace_api_key -q
ruff check app/settings/api_key_save tests/test_settings_account.py
```

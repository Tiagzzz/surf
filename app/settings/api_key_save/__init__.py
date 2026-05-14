"""Surf P7 — Anthropic API-key replacement service.

The locked Surf V1 rule: the saved key is **only** overwritten after a
fresh validation against Anthropic succeeds. A blank
input, a failed validation call, an exception during validation, or a
persist failure all leave the existing saved key untouched.

Both the validate and persist functions are injectable so tests and the
P7 preview sandbox can supply fakes without making real Anthropic calls
or touching the live SQLite file.

Usage::

    from app.settings.api_key_save import replace_api_key_after_validation

    result = replace_api_key_after_validation(user_id, typed_key)
    if result["status"] == "replaced":
        st.toast("Saved.")
    else:
        # Render result["message"] (inline) or
        # (result["title"], result["body"]) as a toast.
        ...
"""
# Validates a replacement key before the saved account key is overwritten.
from __future__ import annotations

from typing import Any, Callable

from app.brain.claude_client import validate_anthropic_key
from app.db.queries_users import replace_anthropic_api_key

__all__ = ["replace_api_key_after_validation"]

_BLANK_MESSAGE = "Paste a new Anthropic key to replace."
_INVALID_TITLE = "Invalid Anthropic key"
_INVALID_BODY = (
    "That key didn't validate. "
    "Double-check it on console.anthropic.com and try again."
)
_SAVE_FAILURE_TITLE = "Couldn't replace your key"
_SAVE_FAILURE_BODY = "Something went wrong. Try again, or check your network."


def replace_api_key_after_validation(
    user_id: int,
    new_api_key: str,
    *,
    validate_fn: Callable[[str], bool] = validate_anthropic_key,
    persist_fn: Callable[[int, str], bool] = replace_anthropic_api_key,
) -> dict[str, Any]:
    """Validate then persist; on any non-success branch the old key remains.

    Branch order (each blocks every later branch):

    1. **Blank** stripped input → no validation, no persist.
    2. **Validation raises** (network / SDK error) → invalid-key dict.
    3. **Validation returns False** → invalid-key dict.
    4. **Persist raises** → save-failure dict.
    5. **Persist returns False** → save-failure dict (e.g., user row missing).
    6. **All four pass** → ``{"status": "replaced"}``.

    The page never sees the new or old key value in the returned dict —
    that's intentional. Status copy is what the page renders.
    """
    # Rejects every failed branch before any persisted key can change.
    clean = new_api_key.strip()
    if not clean:
        return {
            "status": "error",
            "kind": "blank",
            "message": _BLANK_MESSAGE,
        }

    try:
        valid = validate_fn(clean)
    except Exception:
        return {
            "status": "error",
            "kind": "invalid",
            "title": _INVALID_TITLE,
            "body": _INVALID_BODY,
        }

    if not valid:
        return {
            "status": "error",
            "kind": "invalid",
            "title": _INVALID_TITLE,
            "body": _INVALID_BODY,
        }

    try:
        ok = persist_fn(user_id, clean)
    except Exception:
        return {
            "status": "error",
            "kind": "save_failure",
            "title": _SAVE_FAILURE_TITLE,
            "body": _SAVE_FAILURE_BODY,
        }

    if not ok:
        return {
            "status": "error",
            "kind": "save_failure",
            "title": _SAVE_FAILURE_TITLE,
            "body": _SAVE_FAILURE_BODY,
        }

    return {"status": "replaced"}

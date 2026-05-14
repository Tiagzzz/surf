"""Surf P7 — display-name save service.

Thin orchestrator around :func:`app.db.queries_users.update_display_name`.
The page renders only the returned status dict; it never touches the
queries layer directly. This keeps the persistence call injectable for
tests and previews.

Usage::

    from app.settings.username_save import save_display_name

    result = save_display_name(user_id, raw_input)
    if result["status"] == "saved":
        st.toast("Saved.")
    else:
        st.error(result.get("message") or result.get("body"))
"""
# Saves a non-blank display name through the user query layer.
from __future__ import annotations

from typing import Any, Callable

from app.db.queries_users import update_display_name

__all__ = ["save_display_name"]

_MISSING_NAME_MESSAGE = "Add a display name to save."
_SAVE_FAILURE_TITLE = "Couldn't save name"
_SAVE_FAILURE_BODY = "Something went wrong. Try again."


def save_display_name(
    user_id: int,
    display_name: str,
    *,
    persist_fn: Callable[[int, str], bool] = update_display_name,
) -> dict[str, Any]:
    """Validate non-blank input then persist via ``persist_fn``.

    Returns a status dict the page can render directly. The persist
    function is injectable so tests and the preview sandbox can supply
    fakes without touching the live SQLite file.

    Status keys:
      * ``saved`` — ``{"status": "saved", "display_name": <stripped>}``
      * ``missing_name`` — blank input, no DB write attempted.
      * ``save_failure`` — persist raised or returned ``False``.
    """
    # Blocks blank names before the persistence function is called.
    clean = display_name.strip()
    if not clean:
        return {
            "status": "error",
            "kind": "missing_name",
            "message": _MISSING_NAME_MESSAGE,
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

    return {"status": "saved", "display_name": clean}

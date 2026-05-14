"""P3 confirmation-gated lecture delete service.

The Class Hub renderer owns the destructive confirmation UI. This service keeps
the safety rule testable: it never calls the DB helper unless the user has
explicitly confirmed the deletion.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS AND PUBLIC EXPORT
# --------------------------------------------------------------------------- #
# Simple explanation:
# This service module is the safety gate sitting between the P3 Class Hub
# destructive-confirm dialog and the SQLite delete helper. It refuses to
# call the DB unless the caller explicitly says `confirmed=True`, which
# keeps the rule unit-testable.
#
# Important code pieces:
# - `Callable[[int, int, int], dict[str, Any]]`: the type hint for the
#   injected delete function. Tests pass a fake; production passes
#   `delete_lecture_for_user`.
# - `delete_lecture_for_user`: real SQLite delete that also checks the
#   lecture belongs to this user and has no attempt history.
from typing import Any, Callable

from app.db.queries_lectures import delete_lecture_for_user

__all__ = [
    "delete_lecture_after_confirmation",
]


# --------------------------------------------------------------------------- #
# DELETE_LECTURE_AFTER_CONFIRMATION — CONFIRM-GATED DELETE SERVICE
# --------------------------------------------------------------------------- #
# Simple explanation:
# Returns a small dict describing what happened:
#   - `cancelled`: the user backed out before confirming.
#   - `deleted`: the row was successfully removed.
#   - `not_owned`: the lecture isn't on this account.
#   - `blocked`: the DB refused the delete (e.g. attempt history exists).
#   - `error`: an unexpected exception bubbled up from the DB layer.
#
# Important code pieces:
# - `if not confirmed: ...`: the explicit safety guard. The DB function
#   is never called without confirmation.
# - `try / except Exception`: any failure from the DB call becomes a
#   clean `"error"` status instead of a Streamlit traceback.
# - `result.get(...)`: defensive reads from the DB helper's return dict.
def delete_lecture_after_confirmation(
    *,
    user_id: int,
    class_id: int,
    lecture_id: int,
    confirmed: bool,
    delete_fn: Callable[[int, int, int], dict[str, Any]] = delete_lecture_for_user,
) -> dict[str, Any]:
    """Delete a lecture only after explicit user confirmation."""
    if not confirmed:
        return {"status": "cancelled", "class_id": class_id, "lecture_id": lecture_id}

    try:
        result = delete_fn(user_id, class_id, lecture_id)
    except Exception:
        return {"status": "error", "class_id": class_id, "lecture_id": lecture_id}

    if result.get("deleted"):
        return {"status": "deleted", "class_id": class_id, "lecture_id": lecture_id}

    reason = result.get("reason", "not_owned")
    if reason == "not_owned":
        return {"status": "not_owned", "class_id": class_id, "lecture_id": lecture_id}
    return {
        "status": "blocked",
        "class_id": class_id,
        "lecture_id": lecture_id,
        "reason": reason,
    }

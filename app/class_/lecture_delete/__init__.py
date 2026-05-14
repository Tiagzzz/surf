"""P3 confirmation-gated lecture delete service.

The Class Hub renderer owns the destructive confirmation UI. This service keeps
the safety rule testable: it never calls the DB helper unless the user has
explicitly confirmed the deletion.
"""
from __future__ import annotations

from typing import Any, Callable

from app.db.queries_lectures import delete_lecture_for_user

__all__ = [
    "delete_lecture_after_confirmation",
]


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

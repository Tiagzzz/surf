"""P2 confirmation-gated class delete service.

The renderer collects user confirmation through the destructive
:func:`st.dialog` and then asks this service to perform the deletion.
The service must never call the underlying DB helper unless the page
has confirmed the user pressed ``DELETE CLASS``.

The locked copy strings here mirror ``03-UI-SPEC.md`` §3.3 verbatim so
the page renderer and the preview sandbox share a single source of
truth.
"""
from __future__ import annotations

from typing import Any, Callable

from app.db.queries_classes import delete_class_for_user

__all__ = [
    "DIALOG_TITLE",
    "DIALOG_BODY_TEMPLATE",
    "KEEP_LABEL",
    "DELETE_LABEL",
    "DELETE_TRIGGER_LABEL",
    "DELETE_SUCCESS_TOAST",
    "format_dialog_body",
    "delete_class_after_confirmation",
]

#: Dialog title for the destructive class-delete confirmation.
DIALOG_TITLE = "Delete this class?"

#: Dialog body; the visible class name is interpolated verbatim.
DIALOG_BODY_TEMPLATE = (
    'Deleting "{class_name}" also deletes its lectures, generated '
    "questions, mock attempts, and answers from this computer. "
    "This cannot be undone."
)

#: Secondary CTA that leaves the class untouched.
KEEP_LABEL = "KEEP CLASS"

#: Destructive primary CTA inside the confirmation dialog.
DELETE_LABEL = "DELETE CLASS"

#: Locked card-level delete trigger label. Matches the destructive
#: dialog primary so the user sees the same copy from card → dialog
#: confirmation.
DELETE_TRIGGER_LABEL = "DELETE CLASS"

#: Success toast after the DB helper confirms deletion.
DELETE_SUCCESS_TOAST = "Class deleted."


def format_dialog_body(class_name: str) -> str:
    """Render the locked destructive body with the class name interpolated."""
    return DIALOG_BODY_TEMPLATE.format(class_name=class_name)


def delete_class_after_confirmation(
    *,
    user_id: int,
    class_id: int,
    confirmed: bool,
    delete_fn: Callable[[int, int], dict[str, Any]] = delete_class_for_user,
) -> dict[str, Any]:
    """Delete a class only after explicit user confirmation.

    Parameters
    ----------
    user_id, class_id:
        Identify which class to remove. ``delete_fn`` enforces ownership;
        a non-owner request returns ``status="not_owned"``.
    confirmed:
        Must be ``True``. The page sets this when the user presses the
        destructive primary CTA. Any other value short-circuits and
        returns ``status="cancelled"`` without calling ``delete_fn``.
    delete_fn:
        Injectable hook for tests / preview sandboxes. Production code
        defaults to :func:`app.db.queries_classes.delete_class_for_user`.

    Returns a small renderer-friendly status dict::

        {"status": "deleted", "class_id": ...}
        {"status": "not_owned", "class_id": ...}
        {"status": "cancelled", "class_id": ...}
        {"status": "error", "class_id": ...}
    """
    if not confirmed:
        return {"status": "cancelled", "class_id": class_id}

    try:
        result = delete_fn(user_id, class_id)
    except Exception:
        return {"status": "error", "class_id": class_id}

    if result.get("deleted"):
        return {"status": "deleted", "class_id": class_id}
    return {"status": "not_owned", "class_id": class_id}

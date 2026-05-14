# `class_delete` — P2 confirmation-gated class delete service

This module is a thin safety layer between the destructive dialog rendered
on P2 and the `delete_class_for_user` query helper. It exists to enforce
that no class is ever removed without the user pressing `DELETE CLASS`
inside the locked confirmation dialog, and to convert the helper's raw
`{"deleted": bool, "class_id": int}` shape into renderer-friendly status
codes.

## How to call it

```python
from app.my_classes.class_delete import (
    DIALOG_TITLE,
    KEEP_LABEL,
    DELETE_LABEL,
    DELETE_SUCCESS_TOAST,
    DELETE_TRIGGER_LABEL,
    format_dialog_body,
    delete_class_after_confirmation,
)

# Page renderer side:
if st.button(DELETE_TRIGGER_LABEL, ...):
    st.session_state["p2_delete_class_id"] = class_id

# Inside the destructive dialog after the user pressed DELETE CLASS:
result = delete_class_after_confirmation(
    user_id=user_id,
    class_id=class_id,
    confirmed=True,
)
```

## Inputs

| Argument | Type | Required | Purpose |
|---|---|---|---|
| `user_id` | `int` | yes | Active local user. The DB helper enforces ownership; a non-owner request returns `status="not_owned"`. |
| `class_id` | `int` | yes | The class to delete. |
| `confirmed` | `bool` | yes | Must be `True`. Anything else short-circuits to `status="cancelled"` without calling the DB helper. |
| `delete_fn` | callable | no | Injectable — defaults to `app.db.queries_classes.delete_class_for_user`. Tests/preview pass a fake. |

## Outputs

```text
{"status": "deleted",   "class_id": <int>}   # owned + helper deleted the row
{"status": "not_owned", "class_id": <int>}   # helper returned deleted=False
{"status": "cancelled", "class_id": <int>}   # confirmed=False — never called DB
{"status": "error",     "class_id": <int>}   # helper raised; logged + suppressed
```

## Locked content

| Constant | Value |
|---|---|
| `DIALOG_TITLE` | `"Delete this class?"` |
| `DIALOG_BODY_TEMPLATE` | `'Deleting "{class_name}" also deletes its lectures, generated questions, mock attempts, and answers from this computer. This cannot be undone.'` |
| `KEEP_LABEL` | `"KEEP CLASS"` |
| `DELETE_LABEL` | `"DELETE CLASS"` |
| `DELETE_TRIGGER_LABEL` | `"DELETE CLASS"` (card-level trigger; matches the destructive dialog primary copy so the user sees the same delete wording from card to confirmation.) |
| `DELETE_SUCCESS_TOAST` | `"Class deleted."` |

`format_dialog_body(class_name)` interpolates the class name into the
locked template; the helper is also reused by the preview sandbox so the
two strings stay aligned.

## Code walkthrough

### Imports and exports

```python
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
```

The DB helper is bound at import-time via a normal `from` import so tests
can monkeypatch `app.my_classes.class_delete.delete_class_for_user` to
prove no real DB row was touched. The recommended pattern for runtime
callers is to leave `delete_fn` at its default and pass `confirmed=True`
only from inside the destructive dialog button branch.

### `format_dialog_body(class_name)`

Pure string formatter; never mutates state. Used by the renderer and the
preview sandbox.

### `delete_class_after_confirmation(*, user_id, class_id, confirmed, delete_fn=...)`

1. If `confirmed` is anything but `True`, return `{"status":
   "cancelled", "class_id": class_id}`. The DB helper is **not** called.
2. Otherwise call `delete_fn(user_id, class_id)` inside a `try`. If it
   raises, return `{"status": "error", "class_id": class_id}` so the page
   can show a non-fatal toast.
3. If `result.get("deleted")` is truthy, return `{"status": "deleted",
   "class_id": class_id}`.
4. Otherwise return `{"status": "not_owned", "class_id": class_id}` —
   reachable when the row is missing or owned by another local user.

## Constraints

- **Confirmation gate is non-negotiable.** A renderer that wires the quiet
  `Delete` trigger directly to this service without going through the
  destructive dialog is incorrect — `confirmed` must be the result of the
  dialog's primary button branch.
- **Locked copy.** The dialog title and body should stay aligned with the approved destructive-delete wording used across the P2 card and dialog surface.
- **No partial state.** The DB helper relies on FK cascades to drop
  lectures, questions, attempts, and answers atomically. This service
  does not orchestrate per-table deletes; if `delete_fn` fails the page
  surfaces an error rather than retrying inconsistent partial deletes.

## Verification commands

```bash
pytest tests/test_class_delete.py -q
ruff check app/my_classes/class_delete
```

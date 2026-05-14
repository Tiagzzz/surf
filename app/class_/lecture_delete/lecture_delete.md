# `lecture_delete` — confirmation-gated lecture deletion

This service gives the Class Hub a small, testable delete boundary. The UI owns the destructive dialog; this module only calls the database helper after explicit confirmation.

## Inputs / outputs

- **Input:** `user_id`, `class_id`, `lecture_id`, `confirmed`, and an injectable delete function.
- **Output:** a status dict: `cancelled`, `deleted`, `not_owned`, `blocked`, or `error`.
- **DB write:** only the injected `delete_fn` can delete rows, and only when `confirmed=True`.

## Data flow

```text
Class Hub delete mode
        │
        ├── user clicks a deletable lecture cell
        ├── `@st.dialog` asks for confirmation
        └── delete_lecture_after_confirmation(..., confirmed=True)
                └── app.db.queries_lectures.delete_lecture_for_user(...)
```

## Code walkthrough

### `delete_lecture_after_confirmation(...)`
If `confirmed` is false, it returns `cancelled` without calling the database. If confirmed, it calls the injected delete helper. A successful delete returns `deleted`; ownership failures return `not_owned`; history-linked or otherwise blocked deletes return `blocked` with the reason.

## Class Hub behavior

1. The `DELETE LECTURE` action enters delete mode and clears `p3_selected_lecture_ids` so mock building and deleting cannot mix.
2. Only cells with `deletable=True` stay clickable.
3. The dialog calls this service only from the destructive confirm button.
4. The database helper blocks lectures referenced by attempt history.

## Testing notes

```bash
python -m pytest -q tests/test_lecture_delete.py tests/test_lecture_delete_ui_contract.py
python -m ruff check app/class_/lecture_delete --no-cache
```

## What could break if changed

- Calling the DB when `confirmed=False` would make cancel unsafe.
- Bypassing `delete_lecture_for_user` would skip ownership and history checks.
- Treating blocked deletes as success would make users think history-linked lectures disappeared.

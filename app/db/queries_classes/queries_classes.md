# queries_classes.md

This file is the small set of helpers Surf uses to save and read a
class (a course the student is studying for) inside the local database.
A class carries its name, its cleaned-up factsheet (the structured
summary of what the course is about, stored as JSON text in one
column), and the percent grade needed to pass. The "Add Class" page
(P2) calls these helpers to create a class; the Class hub (P3) and
Dashboard (P6) call them to read it back. Helpers return plain Python
dictionaries (no pandas) so any caller can use the data without an
extra library.

## How to call

```python
from app.db.queries_classes import (
    get_class_by_id,
    get_class_pass_threshold,
    insert_class,
    list_classes_for_user,
)

cid       = insert_class(user_id=1, name="BWL", factsheet_json={"core_course_content": {...}})
row       = get_class_by_id(cid)             # dict (factsheet decoded back to dict) or None
rows      = list_classes_for_user(user_id=1) # list[dict]; factsheet stays as raw JSON text
threshold = get_class_pass_threshold(cid)    # int pass threshold or None
```

## In / out (Phase 02-03 contract)

| Function | In | Out |
|----------|----|-----|
| `insert_class(user_id, name, factsheet_json, pass_threshold_pct=50)` | factsheet may be dict OR str | `int` lastrowid |
| `get_class_by_id(class_id)` | int | `dict` (factsheet decoded) or `None` |
| `list_classes_for_user(user_id)` | int | `list[dict]` (factsheet stays as raw JSON text per-row) |
| `get_class_pass_threshold(class_id, *, conn=None)` | int class id, optional explicit SQLite connection | `int` threshold percent or `None` when the class is missing or the DB value is NULL |

## Code walkthrough

- Module docstring states the the pandas-free contract pandas-free contract.
- `_row_to_dict(cur)` — fetch one row and zip column descriptions into a dict, or return `None` if the result set was empty.
- `_rows_to_dicts(cur)` — same pattern for list reads: read column names once, zip every row.
- `insert_class(...)` — accepts the factsheet either as a dict (encoded with `json.dumps`) or as an already-encoded JSON string. Wraps the INSERT in `with DB:` so the implicit transaction commits or rolls back together. Returns `cur.lastrowid`.
- `get_class_by_id(class_id)` — single-row read; uses `_row_to_dict` and decodes the `factsheet_json` column back to a Python dict before returning.
- `list_classes_for_user(user_id)` — list read ordered by `id`. Returns `list[dict]`; the factsheet column is left as raw JSON text so callers can decode lazily.
- `get_class_pass_threshold(class_id, *, conn=None)` — tiny scalar read for `classes.pass_threshold_pct`. It uses an explicit caller-provided connection when supplied (tests and composed query flows) or the lazy module `DB` otherwise. Missing classes and NULL threshold values return `None`; stored values return `int`.

## Where it fits

Page P2 (My Classes) reads the list. Page P3 (Class Detail) reads one row. The factsheet pipeline writes a row after `factsheet_clean` finishes. P4/P5/P6 flows can use `get_class_pass_threshold(...)` when they need only the saved grade-4 threshold without fetching/decoding the whole factsheet. The dashboard package (`queries_dashboard`) also reads `pass_threshold_pct` from this table.

## Gotchas-if-real

- Factsheet is encoded with `json.dumps` on insert and decoded with `json.loads` only inside `get_class_by_id`. List rows return the raw JSON string; decode it in the consumer if you need a dict.
- FK to `users(id)` with `ON DELETE CASCADE`: deleting a user wipes their classes, lectures, slide_pages, and questions.
- This module must not import pandas. Re-introducing `import pandas` or `pd.read_sql` reverts the Phase 02-03 fix and fails `tests/test_query_return_shapes.py::test_no_pandas_import_in_query_modules`. Pandas remains allowed only at chart/ML/preview boundaries. `get_class_pass_threshold(...)` is intentionally a scalar SQLite query, not a DataFrame read.
- Static check: `grep -n "import pandas\|pd.read_sql" app/db/queries_classes/__init__.py` must return zero matches.
- Verification: `python -m pytest tests/test_query_return_shapes.py tests/test_queries_classes.py -q`.

## Phase 03-06 update — destructive class delete helper

Phase 03-06 added `delete_class_for_user(user_id, class_id)` for the P2 delete
confirmation flow. The page owns the visible confirmation dialog; the helper
owns the database safety rule: delete only when the class belongs to the given
user.

### Code walkthrough for `delete_class_for_user`

```python
def delete_class_for_user(user_id: int, class_id: int) -> dict[str, Any]:
    with DB:
        cur = DB.execute(
            "DELETE FROM classes WHERE id = ? AND user_id = ?",
            (class_id, user_id),
        )
        return {"deleted": cur.rowcount > 0, "class_id": class_id}
```

The `WHERE id = ? AND user_id = ?` clause is the ownership check. If it matches,
SQLite's `ON DELETE CASCADE` graph removes the class's lectures, learning
objectives, slide pages, questions, attempts, and attempt answers. If it does
not match, nothing is deleted and the helper returns `deleted: False`.

Verification added in Phase 03-06:

```bash
pytest tests/test_class_delete.py tests/test_no_real_db.py -q
ruff check app/db/queries_classes tests/test_class_delete.py
```

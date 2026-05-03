# queries_classes.md

What this file is: read/write helpers for the `classes` table. Each class carries the cleaned factsheet as JSON inside one column — no separate factsheet table.

## How to call

```python
from app.db.queries_classes import insert_class, get_class_by_id, list_classes_for_user

cid = insert_class(user_id=1, name="BWL", factsheet_json={"core_course_content": {...}})
row = get_class_by_id(cid)             # dict; row["factsheet_json"] is back to dict
df  = list_classes_for_user(user_id=1) # pandas.DataFrame
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `insert_class(user_id, name, factsheet_json, pass_threshold_pct=50)` | factsheet may be dict OR str | `int` lastrowid |
| `get_class_by_id(class_id)` | int | dict (factsheet decoded) or `None` |
| `list_classes_for_user(user_id)` | int | DataFrame (factsheet stays as raw JSON text in the frame) |

## Where it fits

Page P2 (My Classes) reads the list. Page P3 (Class Detail) reads one row. The factsheet pipeline writes a row after `factsheet_clean` finishes.

## Gotchas-if-real

- Factsheet is encoded with `json.dumps` on insert and decoded with `json.loads` only in `get_class_by_id`. The DataFrame from `list_classes_for_user` contains the raw JSON string — decode it on the consumer side if you need the dict.
- FK to `users(id)` with `ON DELETE CASCADE`: deleting a user wipes their classes, lectures, slide_pages, and questions.

## Code walkthrough

This script is the read/write helpers for the `classes` table — one row per class the user creates. Each class carries the cleaned factsheet as JSON inside one column (rather than a separate factsheet table), which keeps the schema small. Here's what each function does, top to bottom.

**`insert_class(user_id, name, factsheet_json, pass_threshold_pct=50)`** — In plain language: writes a new class row. The factsheet can be passed either as a Python dict OR as a pre-serialized JSON string; the function checks the type and runs `json.dumps` only when it's a dict so callers don't have to remember which form they're holding. The `with DB:` wraps the write in a transaction. Returns the new row's auto-assigned `id`. Watch out for: `pass_threshold_pct` defaults to 50 (the Swiss "passing percentage") — pass a different value if the class has a different threshold.

**`get_class_by_id(class_id)`** — In plain language: looks up one class row by its id and hands back a dict. The factsheet column is automatically `json.loads`-decoded back into a Python dict before returning, so the caller doesn't have to remember to decode it. Returns `None` if no class has that id.

**`list_classes_for_user(user_id)`** — In plain language: returns ALL classes belonging to one user as a pandas DataFrame, ordered by id (= creation order). Used by P2 (My Classes) to render the class-card grid. Watch out for: the DataFrame's `factsheet_json` column stays as raw JSON text — `pd.read_sql` doesn't auto-decode it. If you need the dict shape on the consumer side, run `df["factsheet_json"].apply(json.loads)`.

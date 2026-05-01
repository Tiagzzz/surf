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

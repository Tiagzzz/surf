# queries_learning_objectives.md

This file is the small set of helpers Surf uses to save and read
learning objectives (the short "by the end of this section, students
should be able to..." statements that Surf pulls out of a lecture)
inside the local database. There is one row per learning objective,
and each row remembers which lecture it came from and the page range
of slides it covers. The lecture-ingestion pipeline writes these rows
when a lecture is processed; the Review page (P5), the Dashboard (P6),
and the Study Next selector read them back to group questions by
objective and to spot weak topics. Helpers return plain Python
dictionaries (no pandas) so any caller can use the data without an
extra library.

## How to call

```python
from app.db.queries_learning_objectives import (
    insert_learning_objective,
    get_learning_objective_by_id,
    list_learning_objectives_for_lecture,
)

lo_id = insert_learning_objective(
    lecture_id=1,
    title="Forecast intermittent demand using Croston's method",
    page_start=12,
    page_end=18,
)
row  = get_learning_objective_by_id(lo_id)             # dict or None
rows = list_learning_objectives_for_lecture(lecture_id=1)  # list[dict] ordered by page_start
```

## In / out (Phase 02-03 contract)

| Function | In | Out |
|----------|----|-----|
| `insert_learning_objective(lecture_id, title, page_start, page_end)` | required | `int` lastrowid |
| `get_learning_objective_by_id(lo_id)` | int | `dict` or `None` |
| `list_learning_objectives_for_lecture(lecture_id)` | int | `list[dict]` ordered by `page_start` |

## Code walkthrough

- Module docstring states the the pandas-free contract pandas-free contract.
- `_row_to_dict` / `_rows_to_dicts` — turn one cursor row (or all rows) into dicts using the cursor's `description` for column names.
- `insert_learning_objective(...)` — wraps `INSERT INTO learning_objectives ...` in `with DB:` and returns `cur.lastrowid`.
- `get_learning_objective_by_id(lo_id)` — single-row SELECT.
- `list_learning_objectives_for_lecture(lecture_id)` — list read ordered by `page_start` so consumers see LOs in lecture order.

## Where it fits

The LO-extractor inside `app/class_/lecture_ingest` writes rows here. The orchestrator then maps each kept slide to its LO via `set_slide_page_learning_objective`. P5 review and P6 dashboard group questions/aggregates by LO; `queries_dashboard.get_weakest_learning_objectives` joins through `slide_pages.learning_objective_id` to rank LOs by error rate.

## Gotchas-if-real

- Per the coverage rule (coverage rule), every kept slide MUST belong to exactly one LO's `page_start..page_end` window. The orchestrator enforces this invariant — these helpers do not.
- Per the learning-objective cap (cap), max LOs per lecture is `total_pages / 5`. The LO-extractor enforces it; the DB does not.
- This module must not import pandas. Re-introducing `import pandas` or `pd.read_sql` reverts the Phase 02-03 fix and fails `tests/test_query_return_shapes.py::test_no_pandas_import_in_query_modules`. Pandas remains allowed only at chart/ML/preview boundaries.
- Static check: `grep -n "import pandas\|pd.read_sql" app/db/queries_learning_objectives/__init__.py` must return zero matches.
- Verification: `python -m pytest tests/test_query_return_shapes.py -q`.

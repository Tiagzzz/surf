# queries_learning_objectives.md

What this file is: read/write helpers for the `learning_objectives` table. Each row is one LO the LO-extractor produced for a lecture, with the page range it covers.

## How to call

```python
from app.db.queries_learning_objectives import (
    insert_learning_objective, list_learning_objectives_for_lecture,
)

lo_id = insert_learning_objective(
    lecture_id=1,
    title="Forecast intermittent demand using Croston's method",
    page_start=12,
    page_end=18,
)
df = list_learning_objectives_for_lecture(lecture_id=1)  # ordered by page_start
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `insert_learning_objective(lecture_id, title, page_start, page_end)` | required | `int` lastrowid |
| `get_learning_objective_by_id(lo_id)` | int | dict or `None` |
| `list_learning_objectives_for_lecture(lecture_id)` | int | DataFrame ordered by `page_start` |

## Where it fits

Plan 03's LO-extractor writes rows here. Plan 05's orchestrator then maps each kept slide to its LO via `set_slide_page_learning_objective`. Phase 2's mock-review page groups questions by LO when displaying results.

## Gotchas-if-real

- Per D-1.5 (coverage rule), every kept slide MUST belong to exactly one LO's `page_start..page_end` window. The orchestrator enforces this invariant — these helpers do not.
- Per D-1.4 (cap), max LOs per lecture is `total_pages / 5`. The LO-extractor enforces it; the DB does not.

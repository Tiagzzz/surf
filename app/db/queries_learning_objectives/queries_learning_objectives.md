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

## Code walkthrough

This script is the read/write helpers for the `learning_objectives` table — one row per LO that the LO-extractor pulls out of a lecture PDF. An LO is a single learning goal (e.g. "Forecast intermittent demand using Croston's method") with a page range that says which slides cover it. Here's what each function does, top to bottom.

**`insert_learning_objective(lecture_id, title, page_start, page_end)`** — In plain language: writes one LO row with its title and inclusive page range. Returns the new row's id. The orchestrator uses this id to bind kept slides to their LO via `queries_pages.set_slide_page_learning_objective`. Watch out for: the page range is INCLUSIVE on both ends (`page_start=12, page_end=18` covers slides 12 through 18, that's 7 slides).

**`get_learning_objective_by_id(lo_id)`** — In plain language: looks up one LO row by id, hands back a dict.

**`list_learning_objectives_for_lecture(lecture_id)`** — In plain language: returns all LOs for a lecture as a DataFrame, ordered by `page_start` so the LOs appear in the order they show up in the PDF rather than the order they were inserted. Used by P5 (Mock Review) to group results by LO and by the LO-extractor itself for sanity-checking that LO ranges don't overlap.

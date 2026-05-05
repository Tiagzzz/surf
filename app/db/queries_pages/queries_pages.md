# queries_pages.md

What this file is: read/write helpers for the `slide_pages` table. One row per slide. Each row says what we kept (`status='kept'`), what we skipped (`'ignored'`), what failed (`'pending'`), and which learning objective it belongs to.

## How to call

```python
from app.db.queries_pages import (
    insert_slide_page, set_slide_page_status, list_slide_pages_for_lecture,
)

spid = insert_slide_page(lecture_id=1, page_number=3, raw_md="# Slide 3\n...")
set_slide_page_status(spid, "ignored")  # turned out to be a divider
df = list_slide_pages_for_lecture(lecture_id=1)  # pages 1..N in order
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `insert_slide_page(lecture_id, page_number, raw_md, status='kept', learning_objective_id=None)` | row data | `int` lastrowid |
| `get_slide_page_by_id(slide_page_id)` | int | dict or `None` |
| `list_slide_pages_for_lecture(lecture_id)` | int | DataFrame ordered by `page_number` |
| `set_slide_page_status(slide_page_id, status, learning_objective_id=None)` | both updated together | `None` |
| `set_slide_page_learning_objective(slide_page_id, learning_objective_id)` | int + int | `None` |

## Where it fits

Plan 05's orchestrator inserts one row per slide right after the splitter runs. The LO-extractor (Plan 03) updates `status` and `learning_objective_id`. The MCQ-generator (Plan 04) reads kept slides and writes questions against them.

## Gotchas-if-real

- `(lecture_id, page_number)` is `UNIQUE`. Re-inserting the same page raises `sqlite3.IntegrityError`. Treat that as "already processed, skip".
- `learning_objective_id` is nullable on purpose: `'ignored'` and `'pending'` slides have no LO.

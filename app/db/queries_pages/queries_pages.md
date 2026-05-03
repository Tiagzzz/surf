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

## Code walkthrough

This script is the read/write helpers for the `slide_pages` table — one row per slide of an uploaded lecture PDF. Each row carries the slide's markdown text plus a `status` field that says what happened to it: `'kept'` (a real content slide we'll generate questions from), `'ignored'` (a divider, table of contents, or anything else not worth questioning), or `'pending'` (split happened but classification didn't finish). Here's what each function does, top to bottom.

**`insert_slide_page(lecture_id, page_number, raw_md, status='kept', learning_objective_id=None)`** — In plain language: writes one slide row. The page splitter calls this for every page in the PDF; the LO-extractor or MCQ-generator may flip the status later. Returns the new row's id. Watch out for: `(lecture_id, page_number)` is a UNIQUE pair in the schema, so re-inserting the same page raises a database error you need to treat as "already processed, skip".

**`get_slide_page_by_id(slide_page_id)`** — In plain language: looks up one slide row by id, hands back a dict.

**`list_slide_pages_for_lecture(lecture_id)`** — In plain language: returns all slides for a lecture, ordered by `page_number` so the rows are in physical PDF order, not insertion order. Used by the LO-extractor and MCQ-generator to walk every slide in sequence.

**`set_slide_page_status(slide_page_id, status, learning_objective_id=None)`** — In plain language: updates BOTH the status and the LO link for a slide in a single SQL statement. The LO-extractor uses this when it decides a slide is `'ignored'` (no LO) or `'kept'` and binds it to a specific LO. Watch out for: passing `learning_objective_id=None` will overwrite any existing LO link with NULL — that's intentional for the `'ignored'` case but a footgun if you only meant to change status.

**`set_slide_page_learning_objective(slide_page_id, learning_objective_id)`** — In plain language: same idea but ONLY updates the LO link, leaving status alone. Used when the LO-extractor wants to rebind a kept slide to a different LO without re-classifying it.

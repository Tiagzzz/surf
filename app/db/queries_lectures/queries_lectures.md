# queries_lectures.md

What this file is: read/write helpers for the `lectures` table. One row per uploaded PDF. Each row carries a `status` so the UI can tell what's ingested vs still being processed.

## How to call

```python
from app.db.queries_lectures import insert_lecture, set_lecture_status, list_lectures_for_class

lid = insert_lecture(class_id=1, title="Lecture 03 — Forecasting",
                     source_pdf_path="/path/to/lec03.pdf", total_pages=42)
# ... ingestion runs ...
set_lecture_status(lid, "ready")
df  = list_lectures_for_class(class_id=1)
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `insert_lecture(class_id, title, source_pdf_path, total_pages, status='pending')` | required + default status | `int` lastrowid |
| `get_lecture_by_id(lecture_id)` | int | dict or `None` |
| `list_lectures_for_class(class_id)` | int | DataFrame (ordered by id) |
| `set_lecture_status(lecture_id, status)` | int + 'pending' or 'ready' | `None` |

## Where it fits

Page P3 (Class Detail) shows the lecture cards and their status. Plan 05's orchestrator inserts a row at upload time and flips the status to `ready` after MCQ generation finishes.

## Gotchas-if-real

- New rows default to `status='pending'` — this is the signal Phase 2 uses to show "Ingesting…" instead of "Take mock".
- FK to `classes(id)`: deleting a class wipes its lectures (and the slide_pages, questions, LOs underneath).

## Code walkthrough

This script is the read/write helpers for the `lectures` table — one row per uploaded PDF. Each row carries a `status` field (`pending` while the orchestrator is ingesting, `done` when MCQs are ready) so the UI can show the right affordance per card. Here's what each function does, top to bottom.

**`insert_lecture(class_id, title, source_pdf_path, total_pages, status='pending')`** — In plain language: writes a new lecture row at upload time. Defaults to `status='pending'` because the row is created BEFORE the ingestion pipeline runs; the orchestrator flips the status to `done` only after MCQ generation finishes. Returns the new row's id so the orchestrator can reference it when inserting `slide_pages`, `learning_objectives`, and `questions` rows underneath.

**`get_lecture_by_id(lecture_id)`** — In plain language: looks up one lecture row by id, hands back a dict, or `None` if the id doesn't exist.

**`list_lectures_for_class(class_id)`** — In plain language: returns all lectures for a given class as a DataFrame, ordered by id (creation order). Used on P3 to render the lecture-card list. The order is stable because lecture id is auto-increment.

**`set_lecture_status(lecture_id, status)`** — In plain language: flips the status field on one lecture row. The orchestrator calls this twice: once at the start (`'pending'` is already the default; this can be skipped) and once at the end with `'done'` when ingestion finishes. Watch out for: the status field is a free-text TEXT column in the schema — typos like `'Done'` vs `'done'` won't be caught by SQLite. The codebase consistently uses `'pending'` and `'done'`.

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

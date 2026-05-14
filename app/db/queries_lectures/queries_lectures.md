# queries_lectures.md

This file is the small set of helpers Surf uses to save and read
lectures (the slide-deck PDFs a student uploads to a class) inside the
local database. There is one row per uploaded PDF, and each row carries
a `status` flag — `pending` while Surf is still processing the slides,
`ready` once it is safe for the student to take a
mock from it. The Class hub (P3) calls these helpers to list lecture
cards and show their state; the upload pipeline calls them to create a
new row and flip its status. Phase 4 also treats `failed` as a durable
hard-failure state for uploads that cannot be processed. Helpers return
plain Python dictionaries (no pandas) so any caller can use the data
without an extra library.

## How to call

```python
from app.db.queries_lectures import (
    insert_lecture,
    get_lecture_by_id,
    list_lectures_for_class,
    set_lecture_status,
    get_lecture_delete_summary,
    delete_lecture_for_user,
)

lid  = insert_lecture(class_id=1, title="Lecture 03 — Forecasting",
                      source_pdf_path="/path/to/lec03.pdf", total_pages=42)
row  = get_lecture_by_id(lid)             # dict or None
rows = list_lectures_for_class(class_id=1) # list[dict] ordered by id
set_lecture_status(lid, "ready")
summary = get_lecture_delete_summary(user_id=1, class_id=1, lecture_id=lid)
result = delete_lecture_for_user(user_id=1, class_id=1, lecture_id=lid)
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `insert_lecture(class_id, title, source_pdf_path, total_pages, status='pending')` | required + default status | `int` lastrowid |
| `get_lecture_by_id(lecture_id)` | int | `dict` or `None` |
| `list_lectures_for_class(class_id)` | int | `list[dict]` ordered by id |
| `set_lecture_status(lecture_id, status)` | int + status string | `None` |
| `get_lecture_delete_summary(user_id, class_id, lecture_id)` | ownership identifiers | delete summary dict |
| `delete_lecture_for_user(user_id, class_id, lecture_id)` | ownership identifiers | delete result dict |

## Code walkthrough

- Module docstring states the the pandas-free contract pandas-free contract.
- `_row_to_dict` / `_rows_to_dicts` — small helpers that turn one cursor row (or all rows) into dicts using the cursor's `description` for column names.
- `insert_lecture(...)` — wraps `INSERT INTO lectures ...` in `with DB:` so the implicit transaction commits or rolls back together. Returns `cur.lastrowid`.
- `get_lecture_by_id(lecture_id)` — single-row SELECT; returns the dict or `None`.
- `list_lectures_for_class(class_id)` — list read ordered by `id`; returns `list[dict]`.
- `set_lecture_status(lecture_id, status)` — wraps a status `UPDATE` in `with DB:`. Used by ingestion to flip from `pending` to `ready` after MCQs are stored.
- `get_lecture_delete_summary(user_id, class_id, lecture_id)` — joins `lectures -> classes` to prove ownership, then left-joins down to `slide_pages`, `questions`, and `attempt_answers`. It returns:
  - `ownership`;
  - lecture `title` / `status`;
  - `question_count`;
  - `used_answer_count`;
  - `distinct_used_attempt_count`;
  - `can_delete`;
  - `blocker_reason`.
  Missing or wrong-owner lectures return `ownership=False` and `blocker_reason="not_owned"`.
- `delete_lecture_for_user(user_id, class_id, lecture_id)` — first calls the summary helper. It deletes only when the lecture is owned and `used_answer_count == 0`. The actual `DELETE FROM lectures` repeats the ownership condition so the operation remains scoped even if a caller races or passes stale IDs.

## Where it fits

Page P3 (Class Detail) shows the lecture cards and their status. The lecture-ingestion orchestrator (`app/class_/lecture_ingest`) inserts a row at upload time and updates status after MCQ generation finishes or fails. P3's safe-delete affordance uses the summary/delete helpers. P4/P5 read lecture rows by id when launching/replaying an attempt.

## How the P3 Class Hub consumes these helpers

`app/class_/class_hub` reads from this module on every render and writes through it only via the destructive-confirmation gate.

- `list_lectures_for_class(class_id)` feeds the 3×4 lecture chooser grid in `class_hub.render_class_hub_page`. Each row's `id`, `title`, and `status` are turned into a grid view-model by `class_hub.build_lecture_grid_view_models`. Insertion order drives the `L01`, `L02`, ... order labels, the `status` field decides whether a cell is selectable (`ready` only) or eligible for the safe-delete affordance (`failed` / `pending`, or `ready` with no completed attempt history). Lectures are never re-fetched mid-render; the renderer trusts the snapshot returned by this helper.
- `get_lecture_delete_summary(user_id, class_id, lecture_id)` is not called directly by `class_hub`; it runs underneath `delete_lecture_for_user` to enforce the `attempt_history_exists` block. The renderer's `Delete lecture` trigger only sets the `p3_delete_lecture_id` session-state slot, which opens the destructive dialog.
- `delete_lecture_for_user(user_id, class_id, lecture_id)` is the only write path P3 uses against this module, and `class_hub` never calls it directly. The destructive dialog routes through `class_hub.handle_lecture_delete` → `app.class_.lecture_delete.delete_lecture_after_confirmation` → this helper. That keeps the ownership and `used_answer_count == 0` checks at the DB layer and leaves the confirmation gate at the service layer above.

## Gotchas-if-real

- New rows default to `status='pending'` — P3 uses this to show processing state instead of enabling mock launch.
- `status='failed'` is delete-eligible only when no `attempt_answers` rows reference the lecture's questions. Attempt history always blocks deletion because cascading question deletes would corrupt review/dashboard history.
- FK to `classes(id)`: deleting a class wipes its lectures (and the slide_pages, questions, LOs underneath).
- Lecture delete relies on schema FKs for unused dependent rows. Tests use temp SQLite connections with foreign keys enabled; never run these helpers against the live local DB during tests.
- This module must not import pandas. Re-introducing `import pandas` or `pd.read_sql` reverts the Phase 02-03 fix and fails `tests/test_query_return_shapes.py::test_no_pandas_import_in_query_modules`. Pandas remains allowed only at chart/ML/preview boundaries.
- Static check: `grep -n "import pandas\|pd.read_sql" app/db/queries_lectures/__init__.py` must return zero matches.
- Verification: `python -m pytest tests/test_lecture_delete.py tests/test_no_real_db.py -q`.

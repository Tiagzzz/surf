# queries_pages.md

This file is the small set of helpers Surf uses to save and read the
individual slides Surf extracts from a lecture PDF. There is one row
per slide, and each slide carries its text in markdown form, a
`status` that tells Surf whether to use it (`kept`), skip it
(`ignored`), or wait for the orchestrator to decide (`pending`), and
an optional pointer to the learning objective the slide belongs to.
The lecture-ingestion pipeline writes these rows during upload; the
Class hub (P3), the question generator, and the Review page (P5) read
them back when they need the slide's text. Helpers return plain
Python dictionaries (no pandas) so any caller can use the data
without an extra library.

## How to call

```python
from app.db.queries_pages import (
    insert_slide_page, get_slide_page_by_id, list_slide_pages_for_lecture,
    set_slide_page_status, set_slide_page_learning_objective,
)

sid  = insert_slide_page(lecture_id=1, page_number=12, raw_md="# Forecasting basics")
row  = get_slide_page_by_id(sid)             # dict or None
rows = list_slide_pages_for_lecture(lecture_id=1) # list[dict] ordered by page_number
set_slide_page_status(sid, "kept", learning_objective_id=3)
```

## In / out (Phase 02-03 contract)

| Function | In | Out |
|----------|----|-----|
| `insert_slide_page(lecture_id, page_number, raw_md, status='kept', learning_objective_id=None)` | int + str + optional FK | `int` lastrowid |
| `get_slide_page_by_id(slide_page_id)` | int | `dict` or `None` |
| `list_slide_pages_for_lecture(lecture_id)` | int | `list[dict]` ordered by page_number |
| `set_slide_page_status(slide_page_id, status, learning_objective_id=None)` | int + str + optional FK | `None` |
| `set_slide_page_learning_objective(slide_page_id, learning_objective_id)` | int + int | `None` |

## Code walkthrough

- Module docstring states the the pandas-free contract pandas-free contract.
- `_row_to_dict` / `_rows_to_dicts` — small helpers that turn one cursor row (or all rows) into dicts using the cursor's `description` for column names.
- `insert_slide_page(...)` — wraps the slide INSERT in `with DB:`; default `status='kept'` and `learning_objective_id=None` match the ignored/pending slide-status rules (ignored/pending slides are tagged after LO mapping).
- `get_slide_page_by_id(slide_page_id)` — single-row SELECT.
- `list_slide_pages_for_lecture(lecture_id)` — list read ordered by `page_number` so the consumer sees the user-facing slide order.
- `set_slide_page_status(slide_page_id, status, learning_objective_id=None)` — wraps an `UPDATE` in `with DB:`; used after LO mapping to mark `kept`/`ignored`/`pending`.
- `set_slide_page_learning_objective(slide_page_id, learning_objective_id)` — narrower update for binding a slide to its LO.

## Where it fits

The lecture-ingestion orchestrator (`app/class_/lecture_ingest`) writes one row per slide produced by the splitter, then calls the LO setters once the LO-extractor's page ranges are known. P3 lecture review and P4 question replay read these rows when they need raw slide context.

## Gotchas-if-real

- `UNIQUE (lecture_id, page_number)` in `schema.sql` prevents accidentally inserting the same page twice.
- `status='kept'` is the only status that drives MCQ generation; `ignored`/`pending` slides are skipped by the orchestrator.
- This module must not import pandas. Re-introducing `import pandas` or `pd.read_sql` reverts the Phase 02-03 fix and fails `tests/test_query_return_shapes.py::test_no_pandas_import_in_query_modules`. Pandas remains allowed only at chart/ML/preview boundaries.
- Static check: `grep -n "import pandas\|pd.read_sql" app/db/queries_pages/__init__.py` must return zero matches.
- Verification: `python -m pytest tests/test_query_return_shapes.py -q`.

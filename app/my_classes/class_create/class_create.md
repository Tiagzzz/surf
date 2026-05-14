# `class_create` — P2 factsheet-before-insert service

This module owns the non-visual P2 Add Class save path. It takes the class name,
grade-4 threshold, and uploaded factsheet PDF from the page renderer; validates
them; extracts Markdown from the PDF; cleans that Markdown with Claude using the
saved local user's API key; and inserts the class row only after cleaning
succeeds.

## How to call it

```python
from app.my_classes.class_create import create_class_from_factsheet

result = create_class_from_factsheet(
    user_id=user["id"],
    class_name="Microeconomics",
    grade4_threshold_percent=60,
    factsheet_file_or_bytes=uploaded_pdf,
)

if result["ok"]:
    class_id = result["class_id"]
else:
    error_code = result["error"]
```

## Inputs

| Argument | Type | Required | Purpose |
|---|---|---|---|
| `user_id` | `int` | yes | The active saved local user. Used only to fetch that user's saved Anthropic key and to own the inserted class row. |
| `class_name` | `str` | yes | Class name. Trimmed; blank names are rejected. |
| `grade4_threshold_percent` | `int`-like | yes | Percent needed for Swiss grade 4. Must normalize to an integer from 1 to 100. |
| `factsheet_file_or_bytes` | bytes or file-like | yes | Uploaded factsheet PDF content. Written to a temporary `.pdf` before extraction. |

## Outputs

Small status dicts for page renderers:

- Success: `{"ok": True, "class_id": <int>, "class_name": <trimmed name>}`
- Input error: `{"ok": False, "error": "invalid_input", "field": <field>}`
- Missing key: `{"ok": False, "error": "missing_api_key"}`
- Processing error: `{"ok": False, "error": "factsheet_processing_failed"}`
- Save error: `{"ok": False, "error": "class_save_failed"}`

The service never returns or logs the saved Anthropic key.

## Dependencies

- `app.db.queries_users.get_saved_anthropic_api_key(user_id)` — the only allowed
  key source.
- `app.brain.ingestion.pdf_to_md_v3.extract_with_tables(Path(temp_pdf))` —
  converts the uploaded factsheet PDF to raw Markdown.
- `app.my_classes.factsheet_clean.clean_factsheet(raw_markdown, api_key=saved_key)` —
  cleans extracted Markdown into Surf factsheet JSON using the saved user key.
- `app.db.queries_classes.insert_class(...)` — writes the class after factsheet
  processing succeeds.

## Code walkthrough

### Imports and exports

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from app.brain.ingestion.pdf_to_md_v3 import extract_with_tables
from app.db.queries_classes import insert_class
from app.db.queries_users import get_saved_anthropic_api_key
from app.my_classes.factsheet_clean import clean_factsheet

__all__ = ["create_class_from_factsheet"]
```

The module imports concrete functions so tests can monkeypatch this module's
names and prove no real DB/API/PDF extraction happens.

### Validation helpers

- `_invalid_input(field)` builds the renderer-friendly invalid-input status.
- `_normalize_threshold(value)` rejects booleans, non-integers, and values outside
  1–100.
- `_read_upload_bytes(factsheet_file_or_bytes)` accepts raw bytes, Streamlit-style
  `.getvalue()` uploads, or generic `.read()` file-like objects. Empty uploads
  are rejected. If a file-like upload has already been closed or raises while
  being read, the helper treats it as an invalid factsheet instead of letting an
  exception escape to the page.
- `_markdown_from_extraction(extracted)` takes the Markdown string from
  `extract_with_tables`, whose current implementation returns
  `(markdown, tables_count, total_text_chars)`.

### `create_class_from_factsheet`

The public function intentionally follows this order:

1. Trim and validate `class_name`.
2. Normalize and validate `grade4_threshold_percent`.
3. Read and validate uploaded PDF bytes.
4. Fetch the saved key for exactly `user_id` through
   `get_saved_anthropic_api_key(user_id)`.
5. Write the upload to a `TemporaryDirectory` path named `factsheet.pdf`.
6. Call `extract_with_tables(Path(temp_pdf))`.
7. Reject empty Markdown as `factsheet_processing_failed`.
8. Call `clean_factsheet(raw_markdown, api_key=saved_key)`.
9. Exit the temporary directory context so the uploaded PDF copy is removed.
10. Insert the class with `insert_class(user_id, cleaned_name, factsheet_json, threshold)`.

Because insert happens after extraction and cleaning, PDF/Claude failures create
no partial class row.

## What could break if changed

- Moving `insert_class` above `clean_factsheet` breaks the P2-01 no-partial-row
  guarantee.
- Fetching a key without `user_id` or reading `ANTHROPIC_API_KEY` can route
  factsheet cleaning through the wrong account.
- Keeping the temporary file outside `TemporaryDirectory` can leave uploaded
  factsheets on disk after success or failure.
- Letting file-like upload read errors escape would break the page-facing status
  dict contract and could show a traceback instead of a friendly factsheet error.
- Letting extraction return empty Markdown and still cleaning/inserting creates
  misleading class setup state.

## Verification commands

```bash
pytest tests/test_class_create.py tests/test_no_real_db.py tests/test_no_secrets_committed.py -q
ruff check app/my_classes/class_create tests/test_class_create.py
```

## Add Class visual notes

The large P2 Dropbox-style uploader and stamped form buttons live in `class_list_render`. Those visual wrappers do not change this service: submitted files still reach `create_class_from_factsheet` as `factsheet_file_or_bytes`, and the validation → extract → clean → insert order described above remains unchanged.

The button-font CSS is also renderer-only. Class creation validation, saved-key lookup, temporary PDF extraction, factsheet cleaning, and insert order remain owned by this module.

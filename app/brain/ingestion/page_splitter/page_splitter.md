# `app/brain/ingestion/page_splitter`

Splits lecture Markdown into per-page records, then groups those records into
small batches for MCQ generation.

## Purpose

`pdf_to_md_v3.py` writes lecture text with `--- PAGE N ---` markers. The page
splitter turns that single Markdown document into records like:

```python
{"page_number": 3, "raw_md": "...slide text..."}
```

MCQ generation can then process a few pages at a time while preserving the
source page for each question.

## Inputs / outputs

| Function | Input | Output |
|---|---|---|
| `split_lecture_md(md)` | Full lecture Markdown with page markers | `list[dict]`, one record per page |
| `batch_slides(slides, size=10)` | Slide records and optional batch size | `list[list[dict]]`, each batch no larger than `size` |

Empty text or text without page markers returns an empty list. Batch size must be
at least one.

## Data flow

```text
pdf_to_md_v3 Markdown
        │
        ▼
split_lecture_md(...)
        │
        ▼
[{page_number, raw_md}, ...]
        │
        ▼
batch_slides(...)
        │
        ▼
small page batches for MCQ generation
```

## Connected code and tools

- Upstream: `app/brain/ingestion/pdf_to_md_v3.py` emits the markers.
- Downstream: `app/class_/mcq_generate/` receives batches through lecture
  ingestion.
- Learning-objective extraction reads the full Markdown directly instead of
  using this splitter.
- No Anthropic call happens in this helper; it only prepares local text records.

## Code walkthrough

### Package re-export

`__init__.py` re-exports `split_lecture_md` and `batch_slides` from
`page_splitter.py` so callers can import from `app.brain.ingestion.page_splitter`.

### Imports and constants

`page_splitter.py` imports `re`, compiles the page-marker regex once, and keeps
`DEFAULT_BATCH_SIZE = 10` as the default MCQ-generation chunk size.

### `split_lecture_md(...)`

The function returns early for empty text or missing markers. Otherwise it walks
marker matches, slices the text between the current marker and the next marker,
strips whitespace, and stores the integer page number from the marker.

### `batch_slides(...)`

The function rejects batch sizes below one, then slices the slide list into
fixed-size chunks. It does not inspect slide content.

## Testing notes

```bash
ruff check app/brain/ingestion/page_splitter --no-cache
```

The splitter is also exercised through lecture-ingest tests that validate page
handoff and MCQ generation boundaries.

## What could break if changed

- A looser marker regex can split unrelated Markdown lines by accident.
- Dropping the page number would make review/dashboard source references harder
  to explain.
- Increasing batch size too far can make MCQ-generation requests too large.

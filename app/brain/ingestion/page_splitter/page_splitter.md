# page_splitter.py

What this file is: turns a lecture markdown string into a list of per-slide records, then groups those records into small batches the MCQ-generator can chew through one Claude call at a time.

## How to call

```python
from app.brain.ingestion.page_splitter import split_lecture_md, batch_slides

# 1) split the markdown emitted by pdf_to_md_v3 into per-slide records
slides = split_lecture_md(lecture_markdown)
# -> [{"page_number": 1, "raw_md": "..."}, {"page_number": 2, "raw_md": "..."}, ...]

# 2) chunk those records for the MCQ generator (max 10 per call by default)
for batch in batch_slides(slides):
    mcqs = generate_mcqs(batch)   # one Claude call per batch
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `split_lecture_md(md: str)` | full lecture markdown | `list[dict]` (one dict per slide) |
| `batch_slides(slides, size=10)` | the list above | `list[list[dict]]` (≤size each) |

Each slide dict has `page_number: int` (1-based, from the marker) and `raw_md: str` (everything between this marker and the next, stripped).

## Where it fits

Upstream: `app/brain/ingestion/pdf_to_md_v3.py` (its `--- PAGE N ---` markers are what we split on).
Downstream: `app/class_/mcq_generate/` (Plan 04) reads one batch at a time; `app/class_/lo_extract/` (Plan 03) reads the full markdown directly, not these records.

## Gotchas-if-real

- Anything before the first `--- PAGE 1 ---` marker is dropped silently. `pdf_to_md_v3` never emits preamble, so this is fine in practice — flagged here only because future callers might be surprised.
- `split_lecture_md('')` and `split_lecture_md('text without any markers')` both return `[]`, not an error. The caller decides whether that's a problem.

## Code walkthrough

This script does two small, related jobs: (1) cut a long lecture-markdown string into one record per slide, and (2) group those records into batches small enough for the MCQ generator to feed Claude in one call. Here's what each piece does.

**`_PAGE_MARKER` regex** — A pre-compiled regex that matches the literal string `--- PAGE N ---` on its own line, where N is one or more digits. The `re.MULTILINE` flag makes `^` and `$` match at the start/end of each line rather than the whole string. This is the boundary marker that `pdf_to_md_v3` writes between slides; the splitter relies on its exact shape.

**`DEFAULT_BATCH_SIZE = 10`** — Module-level constant for the batch size, locked at 10 by D-4.3. Living as a constant (rather than a magic number) means the orchestrator can override it for tests without editing the function.

**`split_lecture_md(md)`** — In plain language: takes the full lecture markdown and returns a list of dicts, one per slide, with the page number and the body text. The function uses `re.finditer` to find every page-marker position in one pass, then walks pairs of adjacent matches: each slide's body is the chunk of text between the END of one marker and the START of the next. The last slide runs to the end of the string. The body text gets `.strip()`-ed so leading/trailing blank lines don't pollute the MCQ generator's input. Watch out for: anything before the first `--- PAGE 1 ---` marker is silently dropped (intentional — `pdf_to_md_v3` never emits a preamble, so there's nothing to keep). Empty string in → empty list out.

**`batch_slides(slides, size=10)`** — In plain language: chops a list of slide records into chunks of at most `size` items, returning a list-of-lists. The implementation is one Python list comprehension: `[slides[i : i + size] for i in range(0, len(slides), size)]`. Used by the orchestrator to loop one Claude call per batch. Watch out for: a `size` of 0 or negative would cause an infinite loop in `range`, so the function raises `ValueError` upfront if `size < 1`.

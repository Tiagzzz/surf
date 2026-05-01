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

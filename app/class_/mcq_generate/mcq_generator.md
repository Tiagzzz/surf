# mcq_generator.py

What this file is: asks Claude to write 1–3 multiple-choice questions per slide, each with 4 options and a list of correct answers (1 to 4 of them) plus a one-sentence reason for each option. It's step 4 of the lecture-ingestion pipeline.

The actual *intelligence* lives in `mcq_generator_system_prompt.md` — edit that file to change Claude's behaviour. No Python redeploy needed; the prompt is read on every call.

## How to call

```python
from app.class_.mcq_generate import generate_mcqs

result = generate_mcqs([
    {"page_number": 3, "raw_md": "# Forecasting horizons\nShort-term: ..."},
    {"page_number": 4, "raw_md": "# Croston's method\nFor intermittent demand..."},
])
# result == {
#   "by_slide": [
#     {"page_number": 3, "mcqs": [{...one MCQ...}]},
#     {"page_number": 4, "mcqs": [{...one MCQ...}]},
#   ]
# }
```

## In / out

| | Type | Meaning |
|---|---|---|
| `slides_batch` | `list[dict]`, length 1..10 | Output of `page_splitter.split_lecture_md` (one batch). |
| **return** | `dict` | `{ "by_slide": [{ "page_number": int, "mcqs": [...] }, ...] }` — one entry per input slide, in input order. |

Each MCQ inside `mcqs`:

| Field | Type | Notes |
|---|---|---|
| `question` | `str` | The question stem in the slide's language. |
| `options` | `list[str]` | **Exactly 4.** |
| `correct_indices` | `list[int]` | **1..4 entries**, 0-based indices into `options`. Always a list. |
| `rationales_per_option` | `list[str]` | **Exactly 4**, one per option (right or wrong). |
| `source_page` | `int` | Equals the slide's `page_number`. |
| `language` | `str` | ISO-639-1 (`'en'`, `'de'`, ...). |

## Where it fits

Step 4 in the lecture-ingest pipeline: **PDF → MD → split → extract_los → generate_mcqs → DB**. Plan 05's orchestrator loops over `batch_slides(slides, size=10)` and calls this once per batch, then writes each MCQ via `queries_questions.insert_question`. The orchestrator computes the 3 locked difficulty features (word_count, readability, distractor_similarity) and leaves the 3 pending features + the final score as NULL until Phase 4.

## Gotchas-if-real

- **Never pass more than 10 slides** — you get a `ValueError`. The orchestrator handles batching via `page_splitter.batch_slides`.
- **Empty batches raise `ValueError`** too — defensive, since an empty batch is always a caller bug.
- **An empty `mcqs: []` for a slide is normal** — the slide turned out to have no testable content (agenda, image-only, etc.) and the orchestrator reclassifies it as `ignored` per D-4.8.
- **Wrong-length `options` or `rationales_per_option` from Claude is the orchestrator's problem** to detect. The wrapper does not validate the response shape — it just parses JSON. Plan 05 catches malformed batches and triggers the D-4.4 retry policy.

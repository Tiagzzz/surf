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

## Code walkthrough

This script is the same shape as the LO-extractor: a thin Python wrapper around one Claude call. It packages a batch of slides, ships them to Claude with the MCQ-generator system prompt, and returns Claude's JSON response. The actual generation intelligence lives in the system prompt — the Python is roughly 15 lines because that's the whole job.

**Module-level `_SYSTEM_PROMPT_PATH` and `MAX_BATCH_SIZE = 10`** — `_SYSTEM_PROMPT_PATH` resolves to the sibling `mcq_generator_system_prompt.md` (re-read on every call so prompt edits take effect immediately). `MAX_BATCH_SIZE = 10` is the locked D-4.3 cap on slides per Claude call — sized to keep the response under Claude's output-token limit and short enough that a retry isn't expensive. Living as a constant means tests can monkey-patch it without editing the function.

**`generate_mcqs(slides_batch)`** — In plain language: validates the batch size, bundles the slides into one JSON object, reads the system prompt from disk, and asks `call_claude` for JSON back. Claude does the work: for each slide, read the markdown, decide if it's testable (an empty `mcqs: []` is the legitimate "no, this slide has no testable content" answer), and write 1-3 MCQs with 4 options each, a list of 1-4 correct indices, and a one-sentence rationale per option. The function returns Claude's `{by_slide: [...]}` dict unchanged. Watch out for: passing 0 slides or more than 10 raises `ValueError` upfront with a clear message — the orchestrator's batching helper (`page_splitter.batch_slides`) is what produces correctly-sized batches, so a `ValueError` here means caller-side logic is broken. The function does NOT validate the SHAPE of Claude's response — wrong-length `options` or missing keys are the orchestrator's problem to detect and retry.

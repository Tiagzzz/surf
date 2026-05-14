# `mcq_generator.py` — MCQ prompt caller

This module asks the Anthropic API to generate multi-select MCQs for a small batch of slides. The prompt text lives in `mcq_generator_system_prompt.md` next to the Python file.

## Inputs / outputs

| Item | Type | Meaning |
|---|---|---|
| `slides_batch` | `list[dict]` | One to ten slide records with `page_number` and `raw_md`. |
| `api_key` | `str | None` | Optional saved Anthropic key for this one request. |
| return | `dict` | `by_slide`, one entry per input slide, each containing zero or more MCQs. |

Each generated MCQ must include four options, 1–4 unique correct indices, four rationales, one canonical `question_type`, source page, and language.

## Data flow

```text
lecture_ingest.ingest_lecture(...)
        │
        └── generate_mcqs(slides_batch, api_key=saved_key)
                ├── validate batch length
                ├── JSON-encode {"slides": slides_batch}
                ├── read mcq_generator_system_prompt.md
                └── call_claude(..., expect_json=True, api_key=api_key)
```

## Code walkthrough

### Imports and constants
The module imports `json`, `Path`, and `call_claude`. `_SYSTEM_PROMPT_PATH` points at the sibling prompt file. `MAX_BATCH_SIZE = 10` keeps prompt payloads bounded; the orchestrator uses the same value when batching slides.

### `generate_mcqs(...)`
Rejects empty or oversized batches, JSON-encodes the slide list, reads the prompt, and calls the shared Anthropic wrapper. It does not validate response shape; `lecture_ingest._validate_mcq(...)` and question query helpers own storage validation.

## Testing notes

```bash
python -m ruff check app/class_/mcq_generate --no-cache
```

## What could break if changed

- Sending more than ten slides can make prompts too large or slow.
- Removing the optional `api_key` would bypass the saved-key upload flow.
- Adding storage validation here would duplicate the ingestion and query boundaries.
- Returning correct answers in launch payloads would be unsafe; this wrapper returns generation JSON only, and launch helpers strip answers before P4.
- `question_type` is taxonomy metadata, not an executable difficulty hook.

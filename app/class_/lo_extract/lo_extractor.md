# `lo_extractor.py` — learning-objective prompt caller

This module asks the Anthropic API to group a lecture's slide Markdown into learning objectives and ignored pages. The prompt text lives in `lo_extractor_system_prompt.md` next to the Python file.

## Inputs / outputs

| Item | Type | Meaning |
|---|---|---|
| `lecture_md` | `str` | Full lecture Markdown with `--- PAGE N ---` markers. |
| `factsheet_subset` | `dict` | The seven factsheet fields curated by `lecture_ingest`. |
| return | `dict` | `learning_objectives`, `ignored_pages`, and `language`. |

Each learning objective has a title and inclusive page range. Each ignored page has a page number and reason.

## Data flow

```text
lecture_ingest._default_extract_los(...)
        │
        └── extract_los(lecture_md, factsheet_subset)
                ├── JSON-encode prompt input
                ├── read lo_extractor_system_prompt.md
                └── call_claude(..., expect_json=True)
```

## Code walkthrough

### Imports and prompt path
The module imports `json`, `Path`, and `call_claude`. `_SYSTEM_PROMPT_PATH` points at the sibling system prompt so prompt edits do not require Python changes.

### `extract_los(...)`
Builds a JSON user message containing the lecture Markdown and factsheet subset, reads the system prompt, and calls `call_claude(..., expect_json=True)`. The orchestrator owns retries, saved-key routing, and failure handling.

## Testing notes

```bash
python -m ruff check app/class_/lo_extract --no-cache
```

## What could break if changed

- Removing page markers from the user message would make slide ranges unreliable.
- Passing the full factsheet can waste tokens and make prompt inputs harder to reason about.
- Adding retries here would duplicate the orchestrator's retry policy.

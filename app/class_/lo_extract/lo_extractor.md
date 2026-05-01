# lo_extractor.py

What this file is: asks Claude to read one lecture and group its slides into learning objectives, plus flag the slides we should skip when generating practice questions. It's the third step of the lecture-ingestion pipeline (after `pdf_to_md_v3` and `page_splitter`) and runs once per lecture.

The actual *intelligence* lives in `lo_extractor_system_prompt.md` — edit that file to change Claude's behaviour. No Python redeploy needed; the prompt is read on every call.

## How to call

```python
from app.class_.lo_extract import extract_los

result = extract_los(
    lecture_md="--- PAGE 1 ---\nForecasting overview\n\n--- PAGE 2 ---\n...",
    factsheet_subset={
        "FSLO": ["Distinguish forecasting horizons", "..."],
        "core_course_content.main_topics": ["Demand forecasting", "..."],
    },
)
# result == {
#   "learning_objectives": [{"title": "...", "page_range": [2, 7]}, ...],
#   "ignored_pages": [{"page_number": 1, "reason": "title"}, ...],
#   "language": "en",
# }
```

## In / out

| | Type | Meaning |
|---|---|---|
| `lecture_md` | `str` | The full lecture markdown emitted by `pdf_to_md_v3.py`, with `--- PAGE N ---` markers between slides. |
| `factsheet_subset` | `dict` | A 7-key subset of the cleaned factsheet (D-1.2). Only these 7 keys are used — passing the full factsheet works but wastes input tokens. |
| **return** | `dict` | `{ "learning_objectives": [...], "ignored_pages": [...], "language": "<2-letter>" }` |

Each LO: `{ "title": str, "page_range": [start, end] }` (inclusive integers, ranges do not overlap).
Each ignored page: `{ "page_number": int, "reason": str }` where `reason` is one of the 10 snake_case keys (9 structural + `off_topic`).

## Where it fits

Step 3 in the lecture-ingest pipeline: **PDF → MD → split → extract_los → MCQ generator → DB**. Plan 05's orchestrator calls this once per lecture, then writes the LOs to the `learning_objectives` table and updates each slide's `status` and `learning_objective_id` accordingly.

## Gotchas-if-real

- **Pass the 7-key subset, not the whole factsheet.** Claude still works on the full thing but burns ~40% extra input tokens. The orchestrator (Plan 05) is responsible for trimming.
- **No markers → empty arrays.** If `lecture_md` has no `--- PAGE N ---` markers, Claude returns `{"learning_objectives": [], "ignored_pages": [], "language": "..."}` rather than guessing page numbers from the prose.
- **Failure handling is owned by the orchestrator.** Per D-4.7: if `extract_los` raises (network error, invalid JSON after retry), the lecture row gets `status='pending'` and MCQ generation is skipped for that lecture — the user retries from the UI.

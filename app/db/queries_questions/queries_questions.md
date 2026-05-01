# queries_questions.md

What this file is: read/write helpers for the `questions` table. One row per MCQ. Lists (options, correct indices, per-option rationales) are JSON-encoded into single columns to keep the schema small.

## How to call

```python
from app.db.queries_questions import insert_question, list_questions_for_lecture

qid = insert_question(
    slide_page_id=12,
    question_text="Which forecasting method assumes seasonality?",
    options=["Naive", "Holt-Winters", "Linear regression", "ARIMA(1,0,0)"],
    correct_indices=[1],            # always a list, even for single-correct
    rationales_per_option=["...", "...", "...", "..."],
    source_page=8,
    language="en",
    difficulty_word_count=42,        # optional Phase 1 features
)
df = list_questions_for_lecture(lecture_id=1)
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `insert_question(...)` | see signature; all 7 difficulty fields are kwargs, default `None` | `int` lastrowid |
| `list_questions_for_slide_page(slide_page_id)` | int | DataFrame |
| `list_questions_for_lecture(lecture_id)` | int — JOINs through slide_pages | DataFrame |

## Where it fits

Plan 04's MCQ-generator writes rows here, normally passing only the 3 LOCKED Phase 1 difficulty kwargs (`word_count`, `readability`, `distractor_similarity`). Phase 2's mock-take page reads them via `list_questions_for_lecture`. Phase 4's ML pipeline can pass the 4 PENDING kwargs (`topic`, `concept_overlap`, `skip_confidence`, `score`) through this same wrapper rather than writing raw `UPDATE` SQL.

## Gotchas-if-real

- `correct_indices` is **always a list of int**, even when there is one correct answer. Decode with `json.loads(row["correct_indices"])`. The UI uses checkboxes when `len(correct_indices) >= 2`.
- All 7 difficulty fields are kwargs (3 LOCKED + 4 PENDING). Phase 1 ingestion normally fills only the 3 LOCKED ones; the 4 PENDING ones default to `None`. Phase 4's ML pipeline can either call `insert_question(... difficulty_score=0.7)` for new rows or run a raw `UPDATE` for backfill.

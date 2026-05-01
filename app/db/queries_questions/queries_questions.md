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
| `insert_question(...)` | see signature; 3 LOCKED difficulty fields are kwargs, default `None` | `int` lastrowid |
| `list_questions_for_slide_page(slide_page_id)` | int | DataFrame |
| `list_questions_for_lecture(lecture_id)` | int — JOINs through slide_pages | DataFrame |

## Where it fits

Plan 04's MCQ-generator writes rows here. Phase 2's mock-take page reads them via `list_questions_for_lecture`. Phase 4's ML difficulty model backfills the 4 PENDING fields directly with raw `UPDATE` SQL — those columns stay NULL until then.

## Gotchas-if-real

- `correct_indices` is **always a list of int**, even when there is one correct answer. Decode with `json.loads(row["correct_indices"])`. The UI uses checkboxes when `len(correct_indices) >= 2`.
- Only the 3 LOCKED difficulty kwargs are accepted today. The 4 PENDING ones (`difficulty_topic`, `difficulty_concept_overlap`, `difficulty_skip_confidence`, `difficulty_score`) are filled in Phase 4 by raw SQL — adding kwargs for them now would lock a contract that may change.

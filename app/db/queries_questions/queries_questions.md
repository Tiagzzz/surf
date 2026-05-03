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

Plan 04's MCQ-generator writes rows here. The orchestrator (Plan 05) passes the 3 LOCKED Phase 1 difficulty kwargs (`word_count`, `readability`, `distractor_similarity`) plus optionally the 3 PENDING Claude-computed kwargs (`conceptual_density`, `distractor_derivation`, `reasoning_steps`). Phase 2's mock-take page reads via `list_questions_for_lecture`. Phase 4's ML model fills `difficulty_score` (the final composite) once trained.

## Gotchas-if-real

- `correct_indices` is **always a list of int**, even when there is one correct answer. Decode with `json.loads(row["correct_indices"])`. The UI uses checkboxes when `len(correct_indices) >= 2`.
- All 7 difficulty fields are kwargs (3 LOCKED + 3 PENDING + the final `difficulty_score`). Phase 1 ingestion fills the 3 LOCKED + optionally the 3 PENDING; `difficulty_score` is filled by Phase 4's ML model (raw `UPDATE` for backfill is fine).

## Code walkthrough

This script is the read/write helpers for the `questions` table — one row per multiple-choice question (MCQ). Each row holds the question text, four options, the indices of the correct answers, and a per-option rationale, plus seven difficulty-feature columns (six raw features + one final ML-computed score). The lists are JSON-encoded into single columns to keep the schema small (no separate `options` table). Here's what each function does, top to bottom.

**`insert_question(slide_page_id, question_text, options, correct_indices, rationales_per_option, source_page, language, difficulty_*=None)`** — In plain language: writes one MCQ row. The function takes Python lists for options, correct indices, and rationales — it serializes them into JSON strings (`json.dumps`) before the SQL INSERT so each fits in a single TEXT column. The seven difficulty kwargs are all optional with `None` defaults so Phase-1 ingestion can fill the three LOCKED features (word count, readability, distractor similarity), the three PENDING Claude-computed features (conceptual density, distractor derivation, reasoning steps), and leave the final `difficulty_score` for Phase 4's ML model to backfill later. Returns the new row's id. Watch out for: `correct_indices` is ALWAYS a list of ints — even when there's only one correct answer, pass `[1]` not `1`. The downstream UI uses checkboxes when the list has 2+ entries.

**`list_questions_for_slide_page(slide_page_id)`** — In plain language: returns every MCQ tied to one slide as a DataFrame, ordered by id. Used when the user is reviewing a single slide's questions.

**`list_questions_for_lecture(lecture_id)`** — In plain language: returns every MCQ across an entire lecture as a DataFrame, ordered by id. The SQL JOINs through `slide_pages` because questions reference `slide_page_id`, not `lecture_id` directly — the JOIN walks one indirection so the caller can ask for questions per lecture without writing the join themselves. This is the function P4 (Take Mock) uses to load the question pool for a mock attempt.

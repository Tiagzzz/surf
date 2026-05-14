# queries_dashboard.md

This file is Surf's number-crunching helper for the P6 dashboard and
the P3 "Study Next" suggestion. It returns production dashboard math from
stored attempts (no fake data, no ML in production), and exposes helpers for:

- mock history math and class averages
- coverage donuts based on the latest answer per question
- weakest learning objectives
- lecture availability and lecture-level performance series
- per-lecture mock averages
- question-type performance

All helpers return plain Python dictionaries/lists (no pandas, no
Streamlit, no chart code, no Claude/tool calls) so pages can render freely.
Data is read-only and derived from SQLite rows only.

## How to call

```python
from app.db.queries_dashboard import (
    get_mock_grade_metrics,
    get_coverage_summary,
    get_weakest_learning_objectives,
    get_lecture_mock_averages,
    list_lectures_for_class,
    get_completion_donut_summary,
    list_lecture_performance_series,
    get_question_type_performance_for_class,
)

mocks   = get_mock_grade_metrics(class_id=1)         # dict
coverage = get_coverage_summary(class_id=1)           # dict
weak    = get_weakest_learning_objectives(class_id=1) # list[dict] (max 5 by default)
all_lectures = list_lectures_for_class(class_id=1)    # list[dict]
donut   = get_completion_donut_summary(class_id=1)     # dict
perf    = list_lecture_performance_series(class_id=1)  # list[dict]
per_lec = get_lecture_mock_averages(class_id=1)       # list[dict]
types   = get_question_type_performance_for_class(1)   # list[dict]
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `get_mock_grade_metrics(class_id, *, limit=4, conn=None)` | int + optional limit | `dict` with `mock_count`, `last_grade`, `class_average` (last two may be `None`) |
| `get_coverage_summary(class_id, conn=None)` | int | `dict` with `total_questions`, `correct_at_least_once`, `attempted_never_correct`, `never_attempted` |
| `get_completion_donut_summary(class_id, conn=None)` | int | `dict` with `total_questions`, `latest_correct`, `latest_wrong_or_skipped`, `not_covered`; uses latest finished answer per question |
| `list_lectures_for_class(class_id, conn=None)` | int | `list[dict]` with lecture rows in upload order: `{lecture_id, title, source_pdf_path, total_pages, status}` |
| `get_weakest_learning_objectives(class_id, *, limit=5, conn=None)` | int + optional limit | `list[dict]` worst-first; each row `{lo_id, lo_title, lecture_id, answered_count, wrong_count, error_rate}` |
| `list_lecture_performance_series(class_id, *, limit=4, conn=None)` | int + optional limit | `list[dict]`; each row `{lecture_id, title, performance}` where `performance` is a list of `{attempt_id, attempt_position, attempted_count, correct_count, percent_correct, swiss_grade}` for the last `limit` completed mock attempts |
| `get_lecture_mock_averages(class_id, *, limit=4, conn=None)` | int + optional limit | `list[dict]`; each row `{lecture_id, lecture_title, mock_count, avg_swiss_grade}` |
| `get_question_type_performance_for_class(class_id, conn=None)` | int | `list[dict]`; each row `{question_type, attempted_count, correct_count, accuracy}`; empty when no finished answers exist |

## Code walkthrough

- Module docstring states the pandas/Streamlit-free query-helper contract and lists the dashboard formulas plus the question-type performance handoff.
- `_resolve_conn(conn)` — caller may pass an explicit `sqlite3.Connection` (used by tests) or accept the lazy `app.db.connection.DB` proxy (production default).
- `get_mock_grade_metrics(...)`:
  - Counts completed mock attempts for the class (mock-only, `finished_at NOT NULL`, `swiss_grade NOT NULL`) — that count is the canonical `mock_count` for the "Based on N of 4 mocks" copy.
  - When `mock_count == 0`, returns early with `last_grade=None` and `class_average=None`.
  - Otherwise reads the last `limit` Swiss grades newest-first (`ORDER BY finished_at DESC, id DESC LIMIT ?`); the first one is `last_grade`, the mean of the slice is `class_average`.
  - Practice attempts and unfinished mocks are deliberately excluded from both the count and the average.
- `get_coverage_summary(...)`:
  - One SQL query joins `questions -> slide_pages -> lectures` (filtering by `class_id`) so the denominator is "generated questions for this class", and `LEFT JOIN`s `attempt_answers` plus the matching `attempts` (only finished attempts of either kind for the class).
  - Per question: `attempted = MAX(1 when there is at least one matching finished attempt row)`, `ever_correct = MAX(is_correct from matching finished attempt rows)`. The Python loop classifies each row into exactly one of `correct_at_least_once`, `attempted_never_correct`, or `never_attempted`.
  - The attempted/correct flags are based on the joined `attempts` row, not merely on a raw `attempt_answers` row. That prevents unfinished attempts from counting as coverage if a buggy or manual row exists before final submit.
  - Skipped answers are stored with `is_correct = 0` (the skipped-is-wrong rule), so they correctly count as attempted-and-wrong.
- `get_completion_donut_summary(...)`:
  - Pulls the most recent `attempt_answers.id` per generated question using a CTE over finished attempts only.
  - Buckets the latest answer into:
    - `latest_correct` when `is_correct = 1`
    - `latest_wrong_or_skipped` otherwise
    - `not_covered` for questions without any finished answer row
  - `total_questions` is all generated questions for the class (not just attempted ones), so percentages can be computed from a stable denominator.
- `list_lectures_for_class(...)`:
  - Simple read-only query on `lectures` filtered by `class_id`, ordered by `id ASC`.
  - Returns every uploaded lecture row in stored order so dropdowns can list classes even when no analytics exist yet.
- `list_lecture_performance_series(...)`:
  - Resolves the latest `limit` completed mock attempts for the class (`finished_at` and `swiss_grade` required; unfinished and practice are ignored).
  - Builds per-lecture/per-attempt aggregates for those mocks only:
    - `attempted_count = COUNT(answer rows)` for that lecture in that attempt
    - `correct_count = SUM(is_correct)` for that lecture in that attempt
    - `percent_correct = 100 * correct_count / attempted_count`
    - `swiss_grade = compute_swiss_grade(correct_count, attempted_count, class pass_threshold_pct)`
  - `attempt_position` is a window-local, newest-first index (1 for newest, 2 for next, etc.) so chart points can be aligned to the same mock chronology as other P6 widgets.
- `get_weakest_learning_objectives(...)`:
  - The CTE `latest` picks one row per `question_id` — the answer with the largest `attempt_answers.id`, restricted to finished attempts in the class, mock or practice both. Practice affects Study Next by the V1 rule.
  - The outer query joins LOs to their lectures (filtered by `class_id`), to slide_pages by `learning_objective_id`, to questions by `slide_page_id`, then to the `latest` CTE. It groups by LO and computes `wrong_count` (rows where the latest answer is incorrect; skipped is already wrong) and `answered_count`.
  - Ordering is `error_rate DESC, lo_id ASC` so the worst LO ranks first; ties are stable.
  - LOs whose questions have no answer in the latest set are dropped (the inner `JOIN latest` filters them out); when no questions are answered at all the result is `[]`.
- `get_lecture_mock_averages(...)`:
  - Reads the last `limit` completed mock attempts for the class (newest first) and short-circuits to `[]` if there are none.
  - Builds a SELECT joining `lectures -> slide_pages -> questions -> attempt_answers -> attempts`, restricted to `attempts.id IN (...)` (the last-`limit` attempt ids). This collapses every question-answer pair touching that lecture inside the windowed mocks.
  - Aggregates: `mock_count = COUNT(DISTINCT attempts.id)` (so the count remains "how many mocks touched this lecture"); `avg_swiss_grade = AVG(attempts.swiss_grade)` over the joined question-answer rows. This deliberately makes the average question-weighted, not attempt-weighted. Example: if one mock grade was 6.0 and had three questions from Lecture A, and another mock grade was 2.0 and had one Lecture A question, Lecture A's average is `(6 + 6 + 6 + 2) / 4 = 5.0`, not `(6 + 2) / 2 = 4.0`.
  - Returns rows sorted by `lecture_id ASC`.
- `get_question_type_performance_for_class(...)`:
  - Joins `attempt_answers -> attempts -> questions`.
  - Filters to finished attempts for the class.
  - Groups by stored `questions.question_type` and returns attempted,
    correct, and accuracy values.
  - Returns no rows when no finished answers exist. It does not invent
    type rows, difficulty profiles, or ML-derived metadata.

## Where it fits

P6 dashboard renders the cards and charts using these aggregates. P3 lecture cards may consume `get_lecture_mock_averages` to show "your mock average for this lecture: X". The Study Next selector ranks LOs from `get_weakest_learning_objectives` and feeds practice scope. P6 type-performance UI should use `get_question_type_performance_for_class`; Current app code does not add a difficulty-profile or ML dashboard seam.

## Gotchas-if-real

- This is the **only sanctioned location for production dashboard math**. Visual fake-data fixtures live in `previews/` and may not import `app.db.queries_dashboard`.
- All helpers are read-only — no `INSERT/UPDATE` calls.
- Skipped questions stay wrong (the skipped-is-wrong rule). Don't add a "skipped doesn't count" mode here without re-reviewing the locked app rules.
- Practice attempts ARE included in coverage and weakness math but EXCLUDED from grade metrics and per-lecture mock averages (those use mock attempts only).
- Coverage and weakness ignore unfinished attempts even if an `attempt_answers` row exists. V1 answering is session-only until final submit; submitted attempts are the only analytics input.
- Class average is the mean of the last `limit` (default 4) `swiss_grade` values; if fewer exist, the average is computed over what's there. The page must show the partial-count copy using `mock_count`.
- `get_completion_donut_summary` and `list_lecture_performance_series` also ignore unfinished attempts when selecting answer rows. `list_lecture_performance_series` uses only completed mock attempts (not practice) and converts each lecture point with `compute_swiss_grade`.
- Per-lecture average is question-weighted by design. Do not "simplify" it to one grade per mock unless the product owner changes the V1 lock.
- This module must not import pandas or Streamlit. Re-introducing either reverts the query-helper contract and fails `tests/test_queries_dashboard.py::test_no_streamlit_or_pandas_in_dashboard_module`.
- Static check: `grep -nE "import pandas|import streamlit|pd\.read_sql" app/db/queries_dashboard/__init__.py` must return zero matches.
- Verification: `python -m pytest tests/test_queries_dashboard.py -q`.

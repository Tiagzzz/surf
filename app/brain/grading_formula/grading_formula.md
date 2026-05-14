# `app/brain/grading_formula`

Surf's pure Python grading rulebook. It answers two questions after final
submit: whether one multi-select MCQ was exactly correct, and what Swiss grade a
finished mock/practice score earns.

## Purpose

- `is_exact_match(...)` grades one answer with no partial credit.
- `compute_swiss_grade(...)` converts correct/total counts into a 1.00-6.00
  Swiss quarter-grade.
- `compute_score_summary(...)` returns the fields persisted on a finished
  attempt row.

The module reads no database rows, imports no Streamlit, makes no Anthropic
call, and logs nothing.

## Inputs / outputs

| Function | Input | Output |
|---|---|---|
| `is_exact_match(selected_indices, correct_indices, was_skipped=False)` | User-selected option indices, correct indices, skipped flag | `True` only for exact set match; skipped or duplicate inputs are wrong |
| `compute_swiss_grade(correct_count, total_count, pass_threshold_pct)` | Final counts and class pass threshold | Quarter-grade float from `1.00` to `6.00` |
| `compute_score_summary(correct_count, total_count, pass_threshold_pct)` | Same counts and threshold | Dict with `correct_count`, `total_count`, `score_pct`, `swiss_grade` |

## Data flow

```text
P4 final submit answers + questions.correct_indices
        │
        ▼
is_exact_match(...) for each row
        │
        ▼
compute_score_summary(...) for the attempt
        │
        ▼
app.db.queries_attempts persists attempts + attempt_answers in one transaction
```

P5 and P6 read stored results instead of recalculating them for display.

## Connected code and tools

- `app/db/queries_attempts.finalize_attempt(...)` calls these helpers during
  final submit.
- Inputs come from session-only answer state and stored `questions.correct_indices`.
- Stored outputs feed Review, Dashboard, class averages, and Study Next.

## Code walkthrough

### Public exports

`__all__` exposes the three helpers and keeps `_all_unique(...)` private.

### `is_exact_match(...)`

Skipped answers return `False`. Duplicate selected or correct indices return
`False` so malformed generated MCQs cannot accidentally score as correct. The
final comparison uses sets, so answer order does not matter but subset/superset
answers are wrong.

### `compute_swiss_grade(...)`

Validates the total and threshold, calculates percent correct, then maps the
score into two ladders: 12 quarter-grade buckets below the pass threshold and 9
quarter-grade buckets at or above it. Index clamping keeps the result inside the
legal grade range.

### `compute_score_summary(...)`

Computes `score_pct`, calls `compute_swiss_grade(...)`, and returns the compact
summary dict that persistence writes to `attempts`.

### `_all_unique(...)`

Small private helper used by `is_exact_match(...)` to reject duplicate indices.

## Testing notes

```bash
python -m pytest -q tests/test_grading_formula.py
ruff check app/brain/grading_formula --no-cache
```

## What could break if changed

- Allowing partial credit would change every stored correctness and dashboard
  average.
- Removing duplicate guards can hide malformed generated questions.
- Changing the grade ladders can silently drift stored grades and class trends.
- Adding DB/Streamlit/API work here would make the grade math harder to test and
  reason about.

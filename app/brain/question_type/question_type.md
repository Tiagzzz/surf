# `app/brain/question_type`

Single source of truth for Surf's provisional `question_type` taxonomy. The app
stores and displays these types for generated MCQs, but this helper does not
classify questions with ML and does not write to the database.

## Purpose

Generated MCQs carry one `question_type` slug so P4/P5 can show the type and P6
can compute real performance by type from completed attempts. Keeping the slug
list in Python makes later taxonomy changes easier than hard-coding the list in
multiple pages or a SQLite `CHECK` constraint.

## Inputs / outputs

| Export | Purpose |
|---|---|
| `QUESTION_TYPE_SLUGS` | Ordered storage slugs: `evaluation`, `synthesis`, `analysis`, `application`, `comprehension`, `knowledge` |
| `QUESTION_TYPE_LABELS` | UI labels for those slugs |
| `normalize_question_type(value)` | Strips/lowercases incoming values and maps `Analysi` to `analysis` |
| `is_valid_question_type(value)` | Validates after normalization |

## Data flow

```text
MCQ generation payload
        │
        ▼
lecture ingestion normalizes and validates question_type
        │
        ▼
questions.question_type stores the canonical slug
        │
        ▼
P4/P5 display labels and P6 type-performance analytics read the stored slug
```

## Connected code and tools

- `app/class_/lecture_ingest/` validates generated MCQs before storage.
- `app/db/queries_questions/` persists the stored slug.
- P4/P5 review/take renderers use `QUESTION_TYPE_LABELS` for display.
- P6 dashboard type-performance helpers aggregate completed answers by stored
  slug.
- Future ML work may read these slugs, but this module contains no ML model,
  no prompt call, and no network code.

## Code walkthrough

### `QUESTION_TYPE_SLUGS`

The ordered tuple is the canonical storage list. Other production code should
import it instead of duplicating the slugs.

### `QUESTION_TYPE_LABELS`

Maps each slug to title-case UI copy. The labels are display text, not a second
source of truth.

### `_QUESTION_TYPE_ALIASES`

Contains explicit known cleanup rules only. The current rule maps `analysi` to
`analysis`; this is a narrow typo normalization, not fuzzy inference.

### `normalize_question_type(value)`

Converts `None` to an empty string, otherwise casts the value to text, strips
whitespace, lowercases it, and applies explicit aliases. Unsupported values are
returned as normalized text so callers can decide how to handle validation.

### `is_valid_question_type(value)`

Normalizes the value, then checks membership in `QUESTION_TYPE_SLUGS`.

## Testing notes

```bash
python -m pytest -q tests/test_question_type.py
ruff check app/brain/question_type --no-cache
```

## What could break if changed

- Reordering slugs can make charts and tests disagree about display order.
- Removing the `Analysi` alias can reject known generated payloads that should
  normalize to `analysis`.
- Adding fuzzy matching can silently accept invented categories, which would
  make later type-performance analytics unreliable.
- Duplicating the slug list in another bucket can drift when the taxonomy is
  renamed or reduced later.

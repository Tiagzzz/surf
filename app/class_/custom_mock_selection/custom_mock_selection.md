# `app/class_/custom_mock_selection/` — Phase 7 Custom Mock selector

This module is the **ranking seam** for the red `CUSTOM MOCK >` button on the Class page. It joins ready question rows for a class with the student's completed answer examples, asks `app.ml.personal_difficulty.score_questions(...)` for a personal wrong-risk score per question, and returns the highest-risk rows in deterministic order.

The selector is intentionally separate from the standard mock launch helper (`app/class_/mock_standard_launch/`) and the Study Next launch helper (`app/class_/study_next_launch/`). It does **not** alter those flows: normal `TAKE MOCK >` and Study Next behavior in Phase 7 stay exactly as they were.

The actual session-state launch (writing the P4 launch keys) lives in `app/class_/mock_custom_launch/` (Plan 07-03). This module only computes the ranking.

## Files

| File | Purpose |
| --- | --- |
| `app/class_/custom_mock_selection/__init__.py` | `select_custom_mock_questions(class_id, limit, conn, ...)`. |
| `app/class_/custom_mock_selection/custom_mock_selection.md` | This sidecar. |

## Connected callers and inputs

- Reads ready questions via `app.db.queries_questions.list_ready_questions_for_class` (Plan 07-02).
- Reads completed answers via `app.db.queries_attempts.list_personal_difficulty_examples_for_class` (Plan 07-02).
- Scores via `app.ml.personal_difficulty.score_questions(...)` (Plan 07-01).
- Output is consumed by `app/class_/mock_custom_launch/` (Plan 07-03) and rendered on the Class page hub.

## How to call

```python
from app.class_.custom_mock_selection import select_custom_mock_questions

rows = select_custom_mock_questions(class_id=42, limit=10)
# rows: list[dict] — each row carries:
#   - everything from the ready-question helper (id, question_text,
#     options_json, question_type, lecture_id, learning_objective_id, ...),
#   - personal_difficulty_score: int in 0..100,
#   - personal_difficulty_source: "rule" or "ml".
```

## Code walkthrough

### `DEFAULT_CUSTOM_MOCK_LIMIT`

Set to `10`. This matches D-12 (Custom Mock chooses up to 10 highest-risk ready questions).

### `_decode_json_list(value)`

The DB stores `options`, `correct_indices`, and saved selections as JSON strings. The scoring core wants real lists. This helper accepts either a list (already decoded) or a JSON string and returns a list. Bad / non-JSON strings return an empty list so a single broken row cannot crash the selector.

### `_scoring_view(row)`

Builds the plain dict that the scoring core consumes for a ready question. It maps `question_text` → both `stem` and `question_text`, coalesces `id`/`question_id`, decodes `options_json` and `correct_indices`, and forwards `question_type`, LO title, word-count/readability, and all Phase 7.1 Claude difficulty metadata fields. This is the shared scoring-input contract also used by P5 review rows. The helper never mutates the underlying row.

### `_example_view(row)`

Builds the plain dict for a completed answer example by starting with `_scoring_view(row)`, then adding decoded `selected_indices` plus Python-bool `is_correct` and `is_skipped`. This keeps training/history examples on the same metadata-rich feature contract as the ranked ready questions. The helper accepts the SQLite-shaped `was_skipped` column as well so the SQL adapter and the scoring core stay loosely coupled.

### `select_custom_mock_questions(class_id, limit=10, conn=None, *, ready_questions_fn=..., examples_fn=..., score_questions_fn=...)`

The public entry point.

1. Reject non-positive `class_id` or `limit` with `ValueError` — the launch helper in Plan 07-03 calls this for the active user's class, so any invalid value indicates a wiring bug, not a recoverable state.
2. Read every ready question for the class (default = `list_ready_questions_for_class`). If the class has no ready questions, return `[]` so the Class page can show an honest empty state rather than crashing.
3. Read completed answer examples for the class (default = `list_personal_difficulty_examples_for_class`). Missing/empty history still scores cleanly — the scoring core will return rule scores.
4. Project both lists into the shared metadata-rich plain-dict view that `score_questions(...)` expects.
5. Call the scoring core. If the result count does not match the ready-row count (defensive — should be impossible), fall back to row-by-row `score_rule_based(...)` so Custom Mock launches deterministically rather than failing.
6. Annotate each ready row with `personal_difficulty_score` (int) and `personal_difficulty_source` (`"rule"` or `"ml"`).
7. Sort descending by `personal_difficulty_score`, with ties broken by ascending `id` for determinism.
8. Slice to `limit` and return.

The function does not call `mock_standard_launch`, `study_next_launch`, the Claude client, or NotebookLM. It does not write to the DB. It does not import `streamlit`.

## Safety boundaries

- SELECT-only DB reads; all writes are forbidden by the underlying query helpers in `app.db.queries_questions` / `app.db.queries_attempts`.
- No `streamlit`, `app.brain.claude_client`, or NotebookLM imports.
- No mutation of stored `question_type` — the scoring core reads it as a feature only.
- Determinism: ties always break the same way; `sorted` is stable, but the tuple key still pins the order.

## What could break if changed carelessly

- Removing the `limit` slice would silently launch full-class Custom Mocks well over D-12's "up to 10" rule.
- Calling `mock_standard_launch.launch_mock_standard(...)` from this module would re-mix the Custom Mock and standard mock flows; the regression test guards against this.
- Changing the score field names (`personal_difficulty_score`, `personal_difficulty_source`) would break Plan 07-03's launch helper and Plan 07-04's P5 display lookup.

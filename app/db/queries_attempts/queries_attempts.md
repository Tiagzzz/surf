# queries_attempts.md

This file is the bookkeeper for every mock exam and practice attempt
the student takes in Surf. While the student is answering, nothing is
saved. The moment they press the final Submit button, this file writes
the entire attempt — the overall result and every single answer — to
the local database in one go, so the database never ends up with a
half-saved attempt. It also provides the read-back helpers the Review
page (P5) and the Dashboard (P6) use to show past results.

Sibling sidecar for `app/db/queries_attempts/__init__.py`. Plain-language
walkthrough so anyone on the team can explain how P4 saves a finished
mock/practice and how P5/P6 read it back.

## What this module does

Owns the entire `attempts` and `attempt_answers` write/read contract.

- One write entry point: `finalize_attempt(...)`. It is called exactly once
  per finished attempt. It writes the attempt row and every answer row in
  one SQLite transaction.
- Read helpers for P5 review (per attempt) and P6 dashboard (per class),
  plus a Study Next helper (latest answer per generated question).
- There are no `start_attempt`, `record_answer`, or any draft-attempt
  helpers. P4 answering is session-only until final submit (session-only answering, no draft-attempt persistence).

## Public helpers

- `finalize_attempt(*, class_id, mock_kind, question_ids, answers_by_question_id, skipped_question_ids=None, started_at=None, finished_at=None, submit_token=None, conn=None) -> dict`
- `get_attempt_summary(attempt_id, class_id=None, conn=None) -> dict | None`
- `get_attempt_review_rows(attempt_id, conn=None) -> list[dict]`
  includes stored `question_type`, `correct_indices`, `options_json`,
  learning-objective context, and the same Phase 7.1 difficulty metadata
  fields the Custom Mock scorer receives. It orders by the saved answer
  `position` and does not store or read a frozen personal-difficulty snapshot.
- `list_completed_attempts_for_class(class_id, mock_kind=None, limit=None, conn=None) -> list[dict]`
- `latest_answer_per_question_for_class(class_id, conn=None) -> list[dict]`
- `list_personal_difficulty_examples_for_class(class_id, conn=None) -> list[dict]`
  joins finished attempt answers with their question text/options/type and
  surfaces `is_correct` / `is_skipped` for the Phase 7 personal-difficulty
  scoring core. It now also returns `question_id`, `correct_indices`, and
  every stored Phase 7.1 difficulty metadata field so example rows use the
  same feature contract as ready questions and P5 review rows. It is scoped by
  `attempts.class_id`, ignores unfinished/draft attempts, is SELECT-only, and
  never writes.

All return `dict | None` or `list[dict]`. Pandas is not imported.

## P4/P5 attempt-flow note

The attempt flow adds a thin P4 submit service at
`app/mock_take/attempt_save/__init__.py`. That service does not write SQL. It
normalizes session-only answers, excludes skipped questions from
`answers_by_question_id`, passes skipped question ids as ints, and calls
`finalize_attempt(...)` exactly once. P5 must keep reading saved attempts through
`get_attempt_summary(...)` and `get_attempt_review_rows(...)`, including the
stored `question_type` field for display.

## Connected files / tables

- Reads `classes.pass_threshold_pct` (Swiss-grade input).
- Reads `questions.correct_indices` for grading.
- Writes `attempts` (id, class_id, mock_kind, started_at, finished_at,
  correct_count, total_count, raw_score_pct, swiss_grade) and
  `attempt_answers` (attempt_id, question_id, position, selected_indices,
  was_skipped, is_correct).
- Calls `app.brain.grading_formula.is_exact_match` and `compute_swiss_grade`.
- Used by `app/mock_take/` (P4 final submit), `app/mock_review/` (P5
  display), `app/dashboard/` (P6 metrics), and the Study Next ranker.

## Code walkthrough

### Module setup

```python
from app.brain.grading_formula import compute_swiss_grade, is_exact_match
from app.db.connection import DB

_VALID_MOCK_KINDS = ("mock", "practice")
```

- Pulls in the pure grading helpers and the lazy DB proxy from 02-01.
- The mock-kind allowlist matches the schema-level CHECK constraint locked
  in 02-01, so invalid kinds are rejected twice (helper + DB).

### `_resolve_conn(conn)` and `_underlying_sqlite(db)`

- `_resolve_conn` lets callers pass a real connection (tests do this) or
  fall back to the lazy default `DB` (production).
- `_underlying_sqlite` unwraps the `_LazyConnection` proxy when needed.
  Explicit BEGIN/COMMIT/ROLLBACK requires the real `sqlite3.Connection` so
  we toggle `isolation_level` on it directly.

### `_validate_finalize_inputs(...)`

Pre-write contract checks. Raises `ValueError` for any of:

- `mock_kind` not in `('mock','practice')`,
- bad/missing `class_id`,
- empty `question_ids` or duplicate question ids,
- a non-skipped question with no answer entry,
- selected_indices that aren't lists of ints,
- selected_indices outside `0..3` (4-option MCQ shape),
- selected_indices with duplicates (answer-order safety, MCQ-validation).

Running this before BEGIN means the most common contract violations never
even open a transaction.

### `finalize_attempt(...)` — one-shot atomic write

```python
threshold_row = db.execute("SELECT pass_threshold_pct FROM classes WHERE id = ?", (class_id,)).fetchone()
...
cur = db.execute(f"SELECT id, correct_indices FROM questions WHERE id IN ({placeholders})", tuple(question_ids))
correct_by_qid = {int(qid): json.loads(ci_json) for qid, ci_json in cur.fetchall()}
missing = [qid for qid in question_ids if qid not in correct_by_qid]
if missing: raise ValueError(...)
```

- Loads the class threshold and every question's `correct_indices` in one
  batch before BEGIN. If any question id is unknown we raise BEFORE we
  touch `attempts`, so we never leave an orphan attempt row.

```python
raw_conn = _underlying_sqlite(db)
prior_isolation = raw_conn.isolation_level
raw_conn.isolation_level = None
try:
    raw_conn.execute("BEGIN")
    # 1) attempt row
    attempt_cur = raw_conn.execute("INSERT INTO attempts ...", ...)
    attempt_id = attempt_cur.lastrowid
    # 2) one answer row per frozen question, in original order
    for position, qid in enumerate(question_ids, start=1):
        ...
        raw_conn.execute("INSERT INTO attempt_answers ...", ...)
    # 3) attempt summary update
    raw_conn.execute("UPDATE attempts SET correct_count=..., raw_score_pct=..., swiss_grade=...")
    raw_conn.execute("COMMIT")
except Exception:
    raw_conn.execute("ROLLBACK")
    raise
finally:
    raw_conn.isolation_level = prior_isolation
```

- Disables autocommit so we own the BEGIN/COMMIT/ROLLBACK boundary.
- Inserts the attempt first, then one answer row per question id, in the
  exact order P4 displayed them. `position` is 1-based and unique within
  the attempt (answer-order safety); the `UNIQUE(attempt_id, position)` constraint locks
  this.
- Skipped questions have `selected_indices = []`, `was_skipped = 1`, and
  `is_correct = 0` (the skipped-is-wrong rule, session-only answering). Non-skipped answers are graded with
  `is_exact_match`.
- The summary update writes counts, percentage, and Swiss grade in one
  statement using the threshold loaded above.
- Any exception triggers ROLLBACK and re-raises so the caller sees the
  original error. The combined `UNIQUE(attempt_id, question_id)` and
  `UNIQUE(attempt_id, position)` constraints make duplicate or out-of-order
  rows unrepresentable.
- The `try/finally` restores the prior `isolation_level` so other code
  using the same connection keeps its expected default.
- The function returns a dict with `attempt_id`, `class_id`, `mock_kind`,
  `correct_count`, `total_count`, `score_pct`, `swiss_grade`,
  `skipped_count`, `finished_at`.

### Read helpers

- `get_attempt_summary` returns the single attempt row as a dict, with an
  optional `class_id` guard (P5 ownership check).
- `get_attempt_review_rows` joins `attempt_answers` to `questions`,
  `slide_pages`, and `learning_objectives`, then orders by `position` ASC
  (answer-order safety). P5 renders rows in this order. The row includes
  `question_type`, `correct_indices`, `options_json`, the LO title/id, and
  all stored Phase 7.1 difficulty metadata fields. It still does not write a
  score snapshot, does not read `questions.difficulty_score` as the visible
  score source, and does not mutate the saved attempt.
- `list_completed_attempts_for_class` filters by class, optionally by
  `mock_kind`, drops in-progress rows (NULL `finished_at`), and orders by
  newest first. Used by P6 dashboard "last N mocks" metrics and by P5 to
  list a class's history.
- `latest_answer_per_question_for_class` returns the most recent answer row
  per generated question id (mock or practice), powering Study Next /
  weakness ranking. Practice attempts count, by the V1 rule.
- `list_personal_difficulty_examples_for_class` (Phase 7) joins
  `attempt_answers` ↔ `attempts` ↔ `questions` ↔ `slide_pages` ↔
  `learning_objectives`, restricts to finished attempts only
  (`attempts.finished_at IS NOT NULL`), and returns plain dict rows with
  `answer_id`, `attempt_id`, `question_id`, `selected_indices`,
  `was_skipped`, `is_correct`, `answered_at`, `mock_kind`, `question_text`,
  `options_json`, `correct_indices`, `question_type`, lecture id, LO title,
  and every stored Phase 7.1 `difficulty_*` feature. The helper also surfaces
  `is_correct` and `is_skipped` as Python bools for the scoring core. It is
  SELECT-only — no `INSERT/UPDATE/DELETE/ALTER` keywords — and is guarded by a
  regression test. Wrong/skipped vs correct mapping happens in
  `app.ml.personal_difficulty._target_from_example`, not in SQL. The default
  Study Next and dashboard read helpers are unchanged. The legacy nullable
  `questions.difficulty_score` column is not used here; Phase 7.1 visible
  difficulty is computed from metadata, exact-question history, and the pure
  scorer.

## What breaks if this changes

- Adding a `start_attempt`/`record_answer` helper resurrects durable draft
  persistence and breaks session-only answering/no draft-attempt persistence.
- Skipping the explicit `BEGIN`/`COMMIT`/`ROLLBACK` block (e.g. relying on
  Python's implicit transaction) lets a single failing INSERT leave the
  attempt row but no answers — exactly the partial-state we are blocking.
- Removing the duplicate-`selected_indices` guard lets `[0, 0]` reach
  grading and silently corrupts both the per-row `is_correct` and the
  aggregate summary.
- Reading review rows in any order other than `position ASC` breaks P5's
  contract that the user re-sees the same order they answered in.
- Using `questions.difficulty_score` as the review/example score would surface
  stale or NULL legacy data instead of the Phase 7.1 computed score.
- Importing pandas here breaks the no-pandas query-helper rule and the no-pandas test guard.

### 2026-05-09 wiring note

The submit wiring routes final confirmation through
`app.mock_take.attempt_save.submit_attempt → finalize_attempt` as the single
DB write boundary (single write-boundary).

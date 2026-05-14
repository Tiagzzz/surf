# schema.sql

This file is the blueprint for Surf's local database. A "schema" is the
list of tables, the columns in each table, and the rules between them
(what is required, what links to what, what values are allowed). Surf
keeps the entire blueprint in this single SQL file so anyone on the
team can read it top-to-bottom and see what the app stores. It is read
every time the app opens its database, which means changing this file
changes what the app can remember about users, classes, lectures,
questions, and mock-exam attempts.

What this file is: the full SQLite schema for Surf in one file. Eight
tables, all the indexes, no migration scripts.

## Tables (in dependency order)

| # | Table | What it stores |
|---|-------|---------------|
| 1 | `users` | The single signed-in user (username + Anthropic API key). |
| 2 | `classes` | HSG courses the user has added. The cleaned factsheet lives in `factsheet_json` as JSON text. |
| 3 | `lectures` | One row per uploaded PDF. Carries a checked `status`: `pending`, `ready`, or `failed`. |
| 4 | `learning_objectives` | LOs the LO-extractor produced for a lecture. Each LO covers a `page_start..page_end` range. |
| 5 | `slide_pages` | One row per slide. `status` is 'kept', 'ignored', or 'pending'. Optionally links to its LO. |
| 6 | `questions` | MCQs the generator made for a slide. Holds the full MCQ shape plus nullable `question_type`. |
| 7 | `attempts` | One row per mock or practice the user takes (V1 mock-kind locked). |
| 8 | `attempt_answers` | One row per question shown in an attempt; locked final-submit shape. |

## JSON-encoded columns

Some columns store JSON-serialized lists rather than separate tables — keeps
the schema small and matches the course pattern (no ORM, no junction tables
we don't need).

| Column | Shape |
|--------|-------|
| `classes.factsheet_json` | the full cleaned-factsheet dict |
| `questions.options_json` | `["a", "b", "c", "d"]` (always 4) |
| `questions.correct_indices` | list of int, length 1..4 |
| `questions.rationales_per_option_json` | `["why a", "why b", "why c", "why d"]` |
| `attempt_answers.selected_indices` | list of int as JSON text — `[]` when skipped, never NULL |

## Difficulty fields on `questions`

Fresh `schema.sql` is the source of truth for the Phase 7.1 metadata fields on
`questions`:

- `difficulty_word_count`
- `difficulty_readability`
- `difficulty_distractor_similarity`
- `difficulty_conceptual_density`
- `difficulty_distractor_derivation`
- `difficulty_reasoning_steps`
- `difficulty_wording_complexity`
- `difficulty_wording_clarity_issue`
- `difficulty_score`

The Phase 7.1 Claude critic fills five `1..5` rubric fields
(`difficulty_distractor_similarity`, `difficulty_conceptual_density`,
`difficulty_distractor_derivation`, `difficulty_reasoning_steps`, and
`difficulty_wording_complexity`) plus the `difficulty_wording_clarity_issue`
flag. Rubric scores are nullable so valid MCQs can be kept when the second
Claude call fails; `difficulty_wording_clarity_issue` is a non-null `0/1` flag
with default `0`. The optional `difficulty_score` column stays nullable
legacy/planned compatibility storage only. Phase 7 and 7.1 compute the visible
personal-difficulty score on demand through `app/ml/personal_difficulty/` and
do **not** treat `questions.difficulty_score` as the visible score source.

## Question type seam (Current app)

`questions.question_type` is nullable `TEXT` with no SQLite `CHECK`
constraint. The provisional V1 slug list
(`evaluation`, `synthesis`, `analysis`, `application`, `comprehension`,
`knowledge`) is enforced in Python via `app.brain.question_type` and the
generation/storage validators, not in the DB. This keeps the schema stable if
a later product decision renames or reduces the taxonomy.

## Status constraints (Current app)

`lectures.status` is checked to allow only `pending`, `ready`, or `failed`.
`slide_pages.status` is checked to allow only `kept`, `ignored`, or `pending`.
These are DB-layer guardrails for the P3 class hub and safe lecture-delete
flow.

## Locked attempt semantics (Current app)

`attempts.mock_kind` is locked to `'mock'` or `'practice'` via a CHECK
constraint. P5 review and P6 dashboard helpers can rely on the closed
enum instead of pattern-matching strings.

`attempts.raw_score_pct` and `attempts.swiss_grade` are nullable summary
columns populated atomically by the P4 final-submit transaction . They stay NULL while an attempt is in progress.

`attempt_answers` carries the locked final-submit row shape:

| Column | Constraint | Why |
|---|---|---|
| `position` | `INTEGER NOT NULL` | Original mock/practice order for P5 review. |
| `selected_indices` | `TEXT NOT NULL` (JSON text; `[]` when skipped) | Canonical answer field; never NULL so review queries can `json_each` safely. |
| `was_skipped` | `INTEGER NOT NULL CHECK (was_skipped IN (0,1))` | Explicit skip state distinct from "no correct selections". |
| `is_correct` | `INTEGER NOT NULL CHECK (is_correct IN (0,1))` | Exact-match grading result; computed at final submit. |
| `UNIQUE (attempt_id, question_id)` | — | Prevents the all-or-nothing transaction from writing duplicate answers. |
| `UNIQUE (attempt_id, position)` | — | Preserves stable original ordering for review (no two answers share a position). |

These constraints are the DB-layer mitigation for the app-level schema-mismatch guardrail. Together with the
queries layer's transactional helpers, they make
partial submits unrepresentable.

## Wipe-and-rerun policy (wipe-and-rerun, backup-then-rebuild)

Schema changes during the build are made by editing this file. Fresh DBs get
these fields directly from `schema.sql`; older local DBs are kept compatible by
the additive `_backfill_existing_schema(...)` path in `connection.py`. Phase 7.1
does not automate a live DB reset just to add metadata columns. If a later
approved workflow really needs a live rebuild, use
`app.db.connection.rebuild_user_database_with_backup()` rather than deleting the
file by hand — that helper detects the live DB, copies it to
`~/.surf/user.sqlite.<UTC-timestamp>.bak`, and only then rebuilds from
`schema.sql`. The old empty `app/db/migrations/` scaffold was removed on
2026-05-13; recreate it only for a later approved one-shot conversion script.

## Where it fits

Read by `app/db/connection.py` via `executescript()` on every
`connect()` call. All `app/db/queries_*` modules read/write rows defined
here.

## Code walkthrough

The file is plain DDL; the walkthrough below traces each table block in
file order and explains what changes between the first schema version and Current app.

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    anthropic_api_key TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

`users` is the single-row table that backs the auth/session helper. The
key is stored as plaintext per the V1 product decision (local-only app);
no code path may print or log it.

```sql
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    factsheet_json TEXT NOT NULL,
    pass_threshold_pct INTEGER NOT NULL DEFAULT 50,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

`classes` carries the cleaned factsheet and the user-set grade-4
threshold. Threshold edit-after-setup is V2; in V1 the row is set once
at class creation.

```sql
CREATE TABLE IF NOT EXISTS lectures (... status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','ready','failed')) ...);
CREATE TABLE IF NOT EXISTS learning_objectives (...);
CREATE TABLE IF NOT EXISTS slide_pages (... status TEXT NOT NULL DEFAULT 'kept'
    CHECK (status IN ('kept','ignored','pending')) ...);
CREATE TABLE IF NOT EXISTS questions (... question_type TEXT,
    difficulty_wording_complexity INTEGER,
    difficulty_wording_clarity_issue INTEGER NOT NULL DEFAULT 0, ...);
```

Lecture / LO / slide / question tables form the ingestion chain. Current app
adds the two status CHECK constraints, the nullable `question_type` seam, and
the Phase 7.1 difficulty metadata storage fields. Question-type slug validation
remains in Python so taxonomy changes do not force an immediate SQLite
migration. Difficulty metadata is intentionally stored on `questions` because
the values describe the generated MCQ itself, not any one attempt. Fresh DBs get
these fields here; older DBs receive the same columns through connection-level
additive backfill, not through an automated wipe.

```sql
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    mock_kind TEXT NOT NULL CHECK (mock_kind IN ('mock','practice')),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    correct_count INTEGER,
    total_count INTEGER,
    raw_score_pct REAL,
    swiss_grade REAL,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);
```

The current schema adds the `mock_kind` CHECK plus `raw_score_pct` and
`swiss_grade` for the P4 final-submit summary write. `finished_at`,
`correct_count`, `total_count`, `raw_score_pct`, and `swiss_grade` stay
NULL during an in-progress attempt and are populated atomically by the
final-submit transaction owned by plan 02-02.

```sql
CREATE TABLE IF NOT EXISTS attempt_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    selected_indices TEXT NOT NULL,
    was_skipped INTEGER NOT NULL CHECK (was_skipped IN (0,1)),
    is_correct INTEGER NOT NULL CHECK (is_correct IN (0,1)),
    answered_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (attempt_id) REFERENCES attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE (attempt_id, question_id),
    UNIQUE (attempt_id, position)
);
```

This is the locked final-submit row shape. The CHECK + NOT NULL +
UNIQUE constraints together make partial or duplicate submits
unrepresentable at the DB layer; the transactional helpers in 02-02
inherit these guarantees.

```sql
-- Indexes (indexing rule) — every FK + composite (class_id, lecture_id)
CREATE INDEX IF NOT EXISTS idx_classes_user_id ON classes(user_id);
...
CREATE INDEX IF NOT EXISTS idx_lectures_class_id_id ON lectures(class_id, id);
```

All foreign keys are indexed plus one composite index for the dashboard
rollup `(class_id, id)`. No dashboard-specific index is added in
Current app; the dashboard plan owns those.

## What could break if changed

- Removing the `mock_kind` CHECK lets P5/P6 see kinds the UI never
  produces, breaking dashboard aggregation.
- Removing the `lectures.status` or `slide_pages.status` CHECK lets P3/P4 see
  lifecycle states the UI and delete guards do not understand.
- Adding a SQLite CHECK to `questions.question_type` would make a later
  taxonomy rename/reduce decision require a DB migration instead of a Python
  validator change.
- Making the Phase 7.1 rubric columns required would turn an optional
  metadata-critic failure into lost valid MCQs; only the clarity flag is
  non-null because its safe fallback is `0`.
- Removing `was_skipped` or making it nullable resurrects the
  ambiguous-skip state explicitly rejected by the V1 spec
  (`attempt_answers.chosen_index` legacy).
- Removing either UNIQUE on `attempt_answers` lets the final-submit
  transaction silently double-insert.
- Treating `difficulty_score` as the visible score source would bypass the
  Phase 7.1 metadata/history/DecisionTree scoring path and show stale or NULL
  legacy data.
- Editing the schema and then deleting the live DB by hand instead of relying
  on additive backfill or an explicitly approved backup-first rebuild would
  skip the backup and lose user data.

## Verification

- `pytest tests/test_db_schema.py -q`
- Static check: `grep -n "CHECK (mock_kind IN" app/db/schema/schema.sql`
  must return one line.
- Static check: `grep -n "question_type TEXT" app/db/schema/schema.sql`
  must return one line.
- `pytest -q tests/test_question_type_schema.py tests/test_status_check_constraints.py`
- Static check: `grep -n "UNIQUE (attempt_id, question_id)"
  app/db/schema/schema.sql` must return one line.
- Static check: `grep -n "UNIQUE (attempt_id, position)"
  app/db/schema/schema.sql` must return one line.

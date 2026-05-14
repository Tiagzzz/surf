# Database Guide

Surf uses SQLite through Python's standard `sqlite3` module. The schema source
is `app/db/schema/schema.sql`, and the detailed schema sidecar is
`app/db/schema/schema.md`. Query helpers under `app/db/queries_*` return plain
`dict`, `list[dict]`, scalar, or boolean values so Streamlit pages can render
without importing pandas in the database layer. Pandas belongs only at chart or
preview boundaries if a future chart needs it.

## Engine and storage

- Engine: SQLite.
- Normal user database: local machine only, under `~/.surf/user.sqlite`; this
  file is private and must not be committed.
- Schema loader: `app/db/connection.py` applies `schema.sql` when the app
  connects.
- Safe rebuild helper: `rebuild_user_database_with_backup()` copies an existing
  local DB to a timestamped backup before rebuilding it from `schema.sql`.
- Query modules: `app/db/queries_*` hide raw SQL from the pages and return
  dictionaries/lists.

## Table relationships

```text
users
  └─ classes
       ├─ lectures
       │    ├─ learning_objectives
       │    └─ slide_pages
       │         └─ questions
       └─ attempts
            └─ attempt_answers ── questions
```

| Table | Main purpose | Read/write examples |
|---|---|---|
| `users` | one local user and saved Anthropic API key | Signup and Settings save/read setup state. |
| `classes` | class name, factsheet JSON, grade threshold | My Classes creates rows; Class Hub and Dashboard read them. |
| `lectures` | uploaded lecture metadata and processing status | Class Hub creates and updates pending/ready/failed lectures. |
| `learning_objectives` | extracted objectives for a lecture | Lecture ingestion writes them; Study Next reads weaknesses by objective. |
| `slide_pages` | page-level lecture content | Ingestion writes pages; question generation links questions to pages. |
| `questions` | MCQ text, options, `correct_indices`, rationales, `question_type`, and Phase 7.1 difficulty metadata | P4/P5/Custom Mock read questions; generation plus the second metadata critic write them. |
| `attempts` | completed mock/practice summary | P4 writes final attempts; P5/P6 read results. |
| `attempt_answers` | per-question `selected_indices`, skip flag, correctness, and original `position` | P4 writes answer rows in one transaction; P5 reviews them in stored order. |

## Important constraints

- `questions.correct_indices` is JSON text and must represent unique answer
  indices. Duplicate values such as `[0, 0]` are invalid.
- `questions.question_type` is nullable text in SQLite. Slug validation lives in
  Python so the taxonomy can change later without forcing a DB rebuild.
- Phase 7.1 adds six question difficulty metadata columns:
  `difficulty_distractor_similarity`, `difficulty_conceptual_density`,
  `difficulty_distractor_derivation`, `difficulty_reasoning_steps`,
  `difficulty_wording_complexity`, and
  `difficulty_wording_clarity_issue`. The detailed column notes live in
  `app/db/schema/schema.md`.
- Missing metadata must not break valid questions. Numeric metadata can be
  `NULL`; `difficulty_wording_clarity_issue` stores a safe `0/1` flag.
- `attempt_answers.selected_indices` is the canonical answer field. Skipped
  answers store `[]`, `was_skipped = 1`, and `is_correct = 0`.
- `attempt_answers.position` stores the original mock/practice order so review
  screens show questions in the same order the user saw them.
- `attempts.mock_kind` is either `mock` or `practice`. Dashboard grade cards use
  completed mocks only; coverage and weakness stats include completed mock and
  practice attempts.
- Lecture and slide statuses are checked values so the UI does not receive
  unknown lifecycle states.
- Final submit is all-or-nothing: the attempt row, every answer row, and the
  attempt summary are written inside one transaction.

## Safe reset and rebuild approach

Do not delete the live DB by hand when testing schema changes. Use
`app.db.connection.rebuild_user_database_with_backup()` so an existing local DB
is copied before it is rebuilt. Tests should use temporary SQLite paths through
`tmp_path` or an explicitly rebound connection; they should not inspect or
mutate `~/.surf/user.sqlite`.

Normal tracked development files must never contain local SQLite databases,
private uploads, generated app data, `.env` files, or real API keys.

## Teacher/demo database strategy

The normal repo should not include a real personal database. A teacher/demo DB
is a later approval-gated artifact, separate from normal development history.
The recipe is documented here so the team can create it safely later; this wave
does not create the final SQLite file, does not select final real lecture data,
and does not insert a real teacher/demo API key.

Recipe-level sequence for the later approval gate:

1. Confirm the exact approval gate, output path, and package timing.
2. Start from an isolated clean database path outside the tracked repo.
3. Select the real demo lectures and any factsheet/class data intended for the
   handoff. Document that this data is approved demo/handoff data.
4. Ingest those lectures and generate questions through the normal app flow.
5. Create representative completed mock and practice attempts so Dashboard and
   Review pages show real stored rows, not fake analytics.
6. If a teacher/demo API key is included, generate a dedicated key only for that
   handoff, give it a spending cap, and keep a revocation plan. The key belongs
   only inside the final generated handoff artifact after the exact file/path
   and timing are approved.
7. Verify the package before handoff: run no-real-DB/no-secrets checks on the
   normal repo, open the packaged app against the isolated DB, and confirm the
   package contains no unrelated private uploads or generated app data.
8. Keep the final teacher/demo artifact out of normal commits unless a later
   approval explicitly names the committed path.

Files and paths that must never be committed during normal development:

- `*.sqlite`, `*.sqlite3`, and `*.db` files.
- `~/.surf/user.sqlite` or backups copied from it.
- Private upload folders or generated course data.
- `teacher_package/` and `handoff_artifacts/` unless a later packaging gate
  explicitly approves a trackable subset.
- `.env` files and real Anthropic API keys.

## Code walkthrough

### `app/db/connection.py`

Opens SQLite lazily, applies `schema.sql`, turns on foreign keys, and owns the
backup-then-rebuild helper. The lazy connection pattern keeps imports and tests
from touching the live DB until production code actually needs data.

### `app/db/schema/schema.sql`

Defines the eight tables and indexes in dependency order. This file is the
schema source of truth; schema comments may explain behavior, but table,
column, constraint, and index changes must be tested because they affect every
page.

The current `questions` table includes the Phase 7.1 difficulty metadata
columns listed above. They support the red Custom Mock selector and P5
`Difficulty for you: X/100` badge; they are not a visible six-feature breakdown
for students.

### `app/db/queries_*`

Each query package wraps a focused table or workflow: users, classes, lectures,
slide pages, learning objectives, questions, attempts, and dashboard aggregates.
They return plain Python values and keep pandas out of the query layer.

The personal-difficulty query paths stay SELECT-only for scoring. They pass
stored metadata and completed-answer history to `app.ml.personal_difficulty`
instead of writing model snapshots or derived scores back into attempts.

### `app/db/demo_seed/`

Seeds a deterministic local `Surf` demo graph when explicitly called. It is
useful for local preview/testing, but it is not the final teacher/demo DB
creation step. Do not run it against the default live DB during this cleanup
wave.

## External tools and functions

- `sqlite3.connect(...)` through `app.db.connection.connect()`.
- `app.db.connection.rebuild_user_database_with_backup()` for approved rebuilds
  with backup.
- `app/db/schema/schema.sql` for DDL.
- Query modules under `app/db/queries_*` for page reads/writes.
- `json.dumps` / `json.loads` for JSON columns such as options and selected
  indices.

## Verification

Useful checks before handing off database changes:

```bash
python -m pytest -q tests/test_db_schema.py tests/test_query_return_shapes.py tests/test_queries_attempts.py tests/test_queries_dashboard.py tests/test_demo_seed_surf_data.py tests/test_no_real_db.py tests/test_no_secrets_committed.py
ruff check app/db --no-cache
```

# app/db/ bucket — Surf's local data layer

This folder is the entire local database side of Surf. Everything
that ever touches the SQLite file `~/.surf/user.sqlite` lives here:
the schema definition, the one place that opens a connection, and the
small "query helper" packages that wrap raw `INSERT` / `SELECT` /
`UPDATE` calls so the rest of the codebase can stay readable. If you
want to know how a student account, a class, a lecture, or a mock
attempt is stored on disk, this bucket is the only place you need to
read.

## What lives in this bucket

| Folder / file | What it does |
|---|---|
| `connection.py` (+ `connection.md`) | The single place that opens the local SQLite database. Owns the lazy module-level `DB` proxy, the explicit `connect()` helper, additive old-DB backfills, and the backup-then-rebuild `rebuild_user_database_with_backup()` "wipe and start over" helper used by P7 Settings. |
| `schema/schema.sql` (+ `schema/schema.md`) | The canonical schema source of truth. Every table (`users`, `classes`, `lectures`, `slide_pages`, `learning_objectives`, `questions`, `attempts`, `attempt_answers`) is declared here, including checked lecture/page statuses, nullable `questions.question_type`, Phase 7.1 `questions.difficulty_*` metadata fields, the locked `attempts.mock_kind` CHECK, and the `attempt_answers` UNIQUEs. |
| `queries_users/` | User setup/profile/key helpers for the `users` table: upsert setup, saved-key lookup, display-name update, API-key replacement, and auth reads. Returns plain `dict` / `list[dict]` / `bool` / `int`. |
| `queries_classes/` | Helpers for the `classes` table (factsheet upload + grade-4 threshold + class-name lock) plus ownership-checked class delete for P2. |
| `queries_lectures/` | Helpers for the `lectures` table (PDF lecture upload + status lifecycle). |
| `queries_pages/` | Helpers for the `slide_pages` table (the page-marker ingestion intermediate from `pdf_to_md_v3`). |
| `queries_learning_objectives/` | Helpers for the `learning_objectives` table (LO extraction output). |
| `queries_questions/` (+ `queries_questions.md`) | Helpers for the `questions` table including the **storage-boundary MCQ validator** (`_validate_mcq`) that mirrors the generated-boundary MCQ guard — duplicate `correct_indices` like `[0, 0]` are rejected here in addition to at the generated boundary. `insert_question(...)` accepts Phase 7.1 metadata kwargs, and class-ready question rows expose those fields for Custom Mock scoring. |
| `queries_attempts/` (+ `queries_attempts.md`) | Helpers for the `attempts` and `attempt_answers` tables. Owns the all-or-nothing `finalize_attempt()` transaction (the skipped-is-wrong rule plus MCQ validation) — one BEGIN / COMMIT / ROLLBACK; no draft-attempt persistence; no `frozen_question_list`. P5 review rows and completed-answer example rows carry metadata-rich scoring fields. |
| `queries_dashboard/` (+ `queries_dashboard.md`) | P6 dashboard math helpers: mock grade metrics, coverage summary, latest-answer completion donuts, weakest-LO ranking, per-lecture series/averages, and question-type performance. **No fake analytics.** |
| `demo_seed/` (+ `demo_seed.md`) | Idempotent local bootstrap helper that seeds a local `Surf` demo class graph (`seed_surf_demo_class`) with a controlled backup + replace model and explicit demo-row guardrails. |

## How the pieces interact

```
streamlit_app.py + views/*
        │
        ▼
app/brain/session    ───────►  app/db/queries_users      (real saved-user auth)
app/brain/grading_formula                                  (pure Python; no DB)
app/class_/lecture_ingest  ───►  queries_pages / LO / questions
app/mock_take + mock_review ───►  queries_attempts        (final-submit only)
app/dashboard               ───►  queries_dashboard       (read-only aggregates)
app/db/demo_seed             ───►  demo_seed              (local seeded demo graph)

every query helper imports `DB` from connection.py (lazy)
schema.sql is applied once on first connect, or after a P7 reset.
```

## Pages and tools this bucket connects to

- **P1 Signup** — `queries_users.insert_user` saves the local user/key row; `app.brain.session` reads saved-user state for routing.
- **P2 My Classes / P3 Class** — `queries_classes`, `queries_lectures`, `queries_pages`, `queries_learning_objectives`, `queries_questions`.
- **P4 Take Mock Exam** — `queries_questions` supplies the generated MCQs for the session-only answering flow; `queries_attempts.finalize_attempt` is called once at final submit to save the all-or-nothing attempt transaction. There is no `start_attempt` or other durable draft helper in V1.
- **P5 Review Mock Exam** — `queries_attempts.get_attempt_summary` + `queries_attempts.get_attempt_review_rows` + `queries_classes.get_class_pass_threshold`; review rows include stored question text/options, `selected_indices`, correctness flags, rationales, and `question_type`.
- **P6 Dashboard** — `queries_dashboard` only (no fake ML analytics).
- **Demo seed CLI path** — `seed_surf_demo_class` plus CLI flags `--seed-surf-demo`/`--replace` used for local seeded-graph safety checks and deterministic local previews.
- **P7 Settings** — `queries_users.update_display_name`, `queries_users.replace_anthropic_api_key`, and `app.settings.reset_account.reset_local_account_data`. P7 reset deletes the local account graph without creating a plaintext-key backup.
- **Lecture ingestion pipeline** — `app/class_/lecture_ingest` calls the page/LO/question query helpers in order.
- **CLI ingestion / pdf_to_md_v3** — does NOT touch this bucket directly; it produces a Markdown file on disk that `lecture_ingest` then ingests.

## Constraints (non-negotiable for V1)

- **No SQLAlchemy or ORM.** Plain `sqlite3` only. (Idea v1 hard constraint, not taught in the course.)
- **No pandas in `queries_*` modules.** query-helper return-shape contract: helpers return `dict` / `list[dict]` / `int` / `bool`. Pandas may stay in `requirements.txt` for chart/ML/preview boundaries only. The `tests/test_query_return_shapes.py` and `tests/test_dependency_contracts.py` static guards enforce this.
- **No live-DB access from the test suite.** Tests use `tmp_path` or `:memory:` SQLite only; `tests/test_no_real_db.py` enforces this with line-by-line scanning.
- **No silent live-DB wipe.** Only `rebuild_user_database_with_backup()` ever resets the live DB, and only after writing a timestamped backup file under `~/.surf/`. P7 reset requires the user to type `DELETE` first. Phase 7.1 metadata compatibility uses additive `connect()` backfill, not an automated reset.
- **No migration scaffold by default.** The old empty `migrations/` folder was deleted on 2026-05-13. If a later approved live-DB conversion needs a one-shot script, recreate `app/db/migrations/` in that task and document the backup/approval flow.
- **Demo seed defaults are idempotent and conservative.** `seed_surf_demo_class()` will not replace an unmarked `Surf` class; repeated seed calls are safe when the existing class is already demo-tagged, and backup/replace is explicit.
- **Old-DB backfills must be additive and stable.** `connect()` may add missing
  compatibility columns/indexes, but it must not rebuild the user's live DB. For
  legacy `attempt_answers` rows, it assigns per-attempt `position` values before
  creating the unique `(attempt_id, position)` index so startup does not crash
  when several old answers belong to the same attempt.
- **Phase 7.1 difficulty metadata is nullable question metadata.** The fresh
  schema and additive backfill include the selected `difficulty_*` columns.
  `difficulty_wording_clarity_issue` falls back to `0`; the other rubric values
  may stay `NULL` when the second Claude call fails. The legacy nullable
  `difficulty_score` column is not the visible personal-difficulty source.
- **`attempt_answers.selected_indices` is canonical.** The legacy `chosen_index` field is stale and must not be used (current V1 answer-storage lock).
- **`questions.question_type` is nullable DB text; slug validation is Python-owned.** Use `app.brain.question_type` and later ingestion/storage validators rather than a SQLite slug CHECK so the taxonomy can change without a DB rebuild.
- **Final-submit transaction is all-or-nothing.** P4 saves the attempt and answer rows in one `BEGIN` / `COMMIT` / `ROLLBACK` block; if any single answer insert fails, zero rows survive. `tests/test_queries_attempts.py::test_rollback_*` proves this.

## Code walkthrough

This bucket has ten sidecars (`connection.md`, `schema/schema.md`,
`queries_users.md`, `queries_classes.md`, `queries_lectures.md`,
`queries_pages.md`, `queries_learning_objectives.md`,
`queries_questions.md`, `queries_attempts.md`, `demo_seed.md`,
`queries_dashboard.md`). Each one explains its own file
section by section. This bucket-level walkthrough only describes the
shape of the bucket as a whole and where to read next:

- **First-time-readers should start with** `connection.md` to learn how
  the lazy `DB` proxy and the backup-then-rebuild helper
  work, then `schema/schema.md` to see the table layout, then
  `queries_users.md` because it is the simplest helper module.
- **For P3 lecture/class hub work**, read `queries_classes.md`,
  `queries_lectures.md`, `queries_pages.md`,
  `queries_learning_objectives.md`, and `queries_questions.md` in that
  order; the lecture ingestion pipeline writes pages → LOs →
  questions in that sequence.
- **For P4/P5 attempt and review work**, read
  `queries_attempts.md` (the `finalize_attempt` transaction is the
  load-bearing part), `queries_questions.md` (the storage-boundary MCQ
  validator), and `queries_classes.md` (the `get_class_pass_threshold`
  helper used by P5). P5 reads `get_attempt_summary` and
  `get_attempt_review_rows` only; it never re-grades. Phase 7.1 review rows
  carry metadata fields so P5 can ask the pure scorer for the current displayed
  difficulty badge without reading a stored `difficulty_score`.
- **For Custom Mock / personal-difficulty work**, read
  `queries_questions.md`, `queries_attempts.md`, and
  `app/ml/personal_difficulty/personal_difficulty.md`. The DB helpers only
  return class-scoped ready rows and finished-answer examples as plain dicts;
  scoring, history adjustment, and DecisionTree reliability live outside the DB
  layer.
- **For P6 dashboard work**, read `queries_dashboard.md`.
  Mock-grade metrics use mock-only completed attempts; coverage and
  weakness include submitted mock + practice with skipped-as-wrong;
  unfinished attempts are ignored; completion donuts use the latest
  finished answer only; lecture trend data uses completed mock history
  and question-weighted per-lecture averages; question-type performance
  reads stored `question_type` from finished attempts only.
- **For seeded local data workflows**, read `demo_seed.md`.
  The seeded graph intentionally writes a four-lecture, one-LO-per-lecture
  `Surf` class with deterministic question graph size; repeated runs are
  idempotent for tagged demo data, and `replace=True` is required to
  overwrite that exact tagged graph.

## What could break if changed

- Touching `schema.sql` or `connection.py` without running
  `tests/test_db_schema.py` can ship a malformed schema or accidentally
  open the live DB at import time (import-safety violation).
- Loosening `lectures.status` or `slide_pages.status` can leave P3 with
  lifecycle states the UI/delete flow does not know how to explain.
- Moving `question_type` slug validation into SQLite makes future taxonomy
  rename/reduce decisions harder than the approved Python-owned seam.
- Adding `import pandas` to any `queries_*` module fails
  `tests/test_query_return_shapes.py` and
  `tests/test_dependency_contracts.py` (query-helper return-shape).
- Changing the `attempt_answers` UNIQUEs or `attempts.mock_kind` CHECK
  silently breaks P4 final submit and P5 review.
- Modifying `finalize_attempt()` to use multiple commits removes the
  all-or-nothing guarantee and breaks
  `tests/test_queries_attempts.py::test_rollback_*`.
- Changing `get_lecture_mock_averages()` from question-weighted to
  attempt-weighted would break the V1 rule that a mock with more
  questions from a lecture should influence that lecture average more.
- Inserting `chosen_index` reads/writes anywhere reintroduces the stale
  single-choice contract that V1 rejected in favour of
  `selected_indices` JSON.
- Treating `questions.difficulty_score` as the visible difficulty source would
  bypass the Phase 7.1 scorer and expose stale/null legacy data.

## Verification commands

```bash
# Schema + import-safety + helper transaction tests
python -m pytest tests/test_db_schema.py tests/test_queries_attempts.py tests/test_query_return_shapes.py tests/test_queries_questions_validation.py tests/test_queries_dashboard.py -q
python -m pytest tests/test_question_type_schema.py tests/test_status_check_constraints.py tests/test_question_type.py -q

# No-live-DB / no-secrets / no-pandas-in-queries static guards
python -m pytest tests/test_no_real_db.py tests/test_no_secrets_committed.py tests/test_dependency_contracts.py -q
```


## Local setup update — class delete and reset

Local setup added the persistence helpers consumed by P1/P2/P7: `upsert_user_setup`, `get_saved_anthropic_api_key`, `update_display_name`, `replace_anthropic_api_key`, `get_local_db_path`, `delete_class_for_user`, and `reset_local_account_data`. All are plain `sqlite3`, return small Python values, and are tested only against temp DBs.

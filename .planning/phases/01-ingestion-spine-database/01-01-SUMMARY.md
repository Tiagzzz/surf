---
phase: 01-ingestion-spine-database
plan: 01
subsystem: database
tags: [sqlite, sqlite3, pandas, schema, python311]

requires: []
provides:
  - Single-file SQLite schema (8 tables, 10 indexes) at app/db/schema/schema.sql
  - app/db/connection.connect() + module-level DB symbol
  - 6 verb-named query-wrapper modules (users, classes, lectures, pages, questions, learning_objectives)
affects:
  - "01-02 (page_splitter): no DB dependency yet, but will feed slide_pages via 01-05"
  - "01-03 (LO extractor): writes via insert_learning_objective + set_slide_page_learning_objective"
  - "01-04 (MCQ generator): writes via insert_question"
  - "01-05 (orchestrator): coordinates all writes through these helpers"
  - "Phase 2 mock-take/review: reads via list_questions_for_lecture"

tech-stack:
  added: [sqlite3 stdlib, pandas (already present)]
  patterns:
    - Module-level DB connection per D-3.4 (course-aligned)
    - Sidecar .md per code module per C-22 (≤100 lines, simpler than existing 4)
    - JSON-encoded list columns (options, correct_indices, rationales) — no junction tables

key-files:
  created:
    - app/db/schema/schema.sql
    - app/db/schema/schema.md
    - app/db/connection.py
    - app/db/connection.md
    - app/db/queries_users/__init__.py + sidecar
    - app/db/queries_classes/__init__.py + sidecar
    - app/db/queries_lectures/__init__.py + sidecar
    - app/db/queries_pages/__init__.py + sidecar
    - app/db/queries_questions/__init__.py + sidecar
    - app/db/queries_learning_objectives/__init__.py + sidecar
  modified: []

key-decisions:
  - "D-3.1 honored: single schema.sql, no migrations, IF NOT EXISTS everywhere"
  - "D-3.2 honored: NOT NULL on every non-empty column; PRAGMA foreign_keys = 1 at every connect()"
  - "D-3.3 honored: 9 single-column FK indexes + 1 composite (class_id, id) on lectures"
  - "D-3.4 honored: course idiom — sqlite3 + pandas.read_sql + ? placeholders + with DB:"
  - "D-3.5 honored: ~/.surf/user.sqlite via Path.expanduser()"
  - "D-2.5 honored: correct_indices stored as JSON-serialized TEXT NOT NULL"
  - "queries_questions accepts only the 3 LOCKED Phase 1 difficulty kwargs (word_count, readability, distractor_similarity); the 4 PENDING Phase 4 fields are populated later via raw SQL — keeps the contract from being locked too early"

patterns-established:
  - "Single-row read pattern: cur = DB.execute(...); cols = [c[0] for c in cur.description]; return dict(zip(cols, row))"
  - "Multi-row read pattern: pd.read_sql(sql, DB, params=(...))"
  - "Write pattern: with DB: cur = DB.execute(sql, (...)); return cur.lastrowid"
  - "Sidecar template: plain-language summary → how to call → in/out → where it fits → gotchas-if-real"

requirements-completed:
  - DB-01
  - GRADE-02

duration: ~25min
completed: 2026-05-01
---

# Plan 01-01: SQLite Database Spine

**Persistent storage layer for Surf is live — every Phase 1 pipeline can now `from app.db.connection import DB` and use verb-named wrappers to read/write the 8 tables.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-05-01
- **Tasks:** 2 (TDD-style — verify gates between tasks)
- **Files modified:** 14 created, 0 modified

## Accomplishments

- 8-table schema (`users`, `classes`, `lectures`, `learning_objectives`, `slide_pages`, `questions`, `attempts`, `attempt_answers`) created in a single idempotent DDL file.
- Module-level connection helper exposes `connect(db_file)` for tests + `DB` for runtime use; FK pragma is set at every connect.
- 6 query-wrapper modules totalling ~250 lines of pure stdlib + pandas; no ORM, no abstractions beyond the course pattern.
- Round-trip insert→read→JSON-decode verified end-to-end against a fresh tmp DB.

## Task Commits

1. **Task 1: schema.sql + connection.py + sidecars** — `58a22ef` (feat)
2. **Task 2: six query-wrapper modules + sidecars** — `180ac25` (feat)

## Files Created

- `app/db/schema/schema.sql` (118 lines) — full DDL: 8 tables, 10 indexes, JSON-encoded list columns
- `app/db/schema/schema.md` (40 lines) — sidecar
- `app/db/connection.py` (24 lines) — `connect()` + `DB`
- `app/db/connection.md` (45 lines) — sidecar
- `app/db/queries_users/__init__.py` + 30-line sidecar
- `app/db/queries_classes/__init__.py` + 30-line sidecar
- `app/db/queries_lectures/__init__.py` + 33-line sidecar
- `app/db/queries_pages/__init__.py` + 34-line sidecar
- `app/db/queries_questions/__init__.py` + 38-line sidecar
- `app/db/queries_learning_objectives/__init__.py` + 36-line sidecar

## Verification

- `pytest -q`: 2 passed, 2 skipped (existing smoke + schema imports clean)
- `ruff check app/db/`: all checks passed (after I001 + E501 fixes)
- Acceptance grep gates: all 18 checks pass (8 tables, 10 indexes, FK pragma, JSON columns, all verb-named functions present, 0 f-string SQL, 6 sidecars ≤100L each)
- Behavioural verify (Task 2): full round-trip insert→read with `correct_indices=[0,2]` decodes back to `[0,2]` ✓

## Self-Check: PASSED

All acceptance criteria met. No deviations from plan. Sidecars stayed within the C-22 ≤100-line ceiling. Schema matches D-2.4/D-2.5/D-3.* exactly.

## What's Unblocked

- Plan 01-02 (page_splitter) can land independently in parallel — no DB dependency.
- Plan 01-03 (LO extractor) can write LOs and update slide_page LO links once it produces output.
- Plan 01-04 (MCQ generator) can write questions with the 3 Phase-1 difficulty fields.
- Plan 01-05 (orchestrator) can wire everything end-to-end into a real `~/.surf/user.sqlite`.

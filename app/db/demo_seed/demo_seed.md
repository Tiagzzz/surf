# Surf demo seed

## Code walkthrough

## Purpose

This module seeds a single local fake class named `Surf` with a complete SQLite
study-to-mock graph that the dashboard and review pages can render without any
external dependencies.

The helper is intentionally explicit: it only runs when called directly (or from
its CLI flag) and does not run during app startup.

## Exact row graph

`seed_surf_demo_class()` writes the following graph through normal SQL tables:

- `users`: one local demo user when none exists.
- `classes`: one class named `Surf` marked as demo content in `factsheet_json`.
- `lectures`: **4** rows with status `ready`.
- `learning_objectives`: one LO per lecture.
- `slide_pages`: **6** kept pages per lecture (`6 × 4 = 24`).
- `questions`: **6** generated MCQs per lecture (`6 × 4 = 24`) with
  `question_type` stored on every question.
- `attempts`: completed mock and practice attempts:
  - mock #1, mock #2, practice #1
- `attempt_answers`: one answer row per question per attempt, with `position` (`1..24`),
  `selected_indices`, `was_skipped`, and `is_correct` explicitly populated.

## Idempotency contract

- If one marked demo class named `Surf` already exists, repeated calls return a
  summary without inserting duplicates.
- If marked `Surf` data already exists and ``replace=True`` is passed, the old
  marked graph is removed and recreated.
- A class named `Surf` without the demo marker is treated as real data.
  `seed_surf_demo_class()` refuses to replace it.

## Backup behavior

When called with the default live DB path (`~/.surf/user.sqlite`) and that file
already exists, the helper creates a timestamped backup copy next to the live DB
before writing.

## Remove and reseed

- Re-run with ``--seed-surf-demo`` for normal idempotent re-check.
- Re-run with ``--seed-surf-demo --replace`` after confirming the existing
  `Surf` class is marked as demo.


## Teacher/demo database boundary

This helper is a local seed utility, not the final teacher/demo database builder.
The final teacher/demo SQLite file is a later approval-gated artifact. At that
later gate, the team chooses the real demo lectures, output path, package timing,
and whether a dedicated teacher/demo API key is included. This wave does not run
seed commands, does not create the final DB, and does not store a real
teacher/demo key.

Files that must never be committed to the normal development repo include local
SQLite files (`*.sqlite`, `*.sqlite3`, `*.db`), private uploads, generated app
data, final teacher/demo artifacts, `.env` files, and real API keys. If a
teacher/demo key is approved later, it should be spending-capped, revocable, and
stored only inside the final generated handoff artifact after the exact path and
timing are approved.

## API

```python
from app.db.demo_seed import seed_surf_demo_class

seed_surf_demo_class()
seed_surf_demo_class(replace=True)
```

CLI:

```bash
python -m app.db.demo_seed --seed-surf-demo
python -m app.db.demo_seed --seed-surf-demo --replace
```

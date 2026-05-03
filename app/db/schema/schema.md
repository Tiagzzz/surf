# schema.sql

What this file is: the full SQLite schema for Surf in one file. Eight tables, all the indexes, no migration scripts.

## Tables (in dependency order)

| # | Table | What it stores |
|---|-------|---------------|
| 1 | `users` | The single signed-in user (username + Anthropic API key). |
| 2 | `classes` | HSG courses the user has added. The cleaned factsheet lives in `factsheet_json` as JSON text. |
| 3 | `lectures` | One row per uploaded PDF. Carries a `status` ('pending' until ingestion finishes, then 'ready'). |
| 4 | `learning_objectives` | LOs the LO-extractor produced for a lecture. Each LO covers a `page_start..page_end` range. |
| 5 | `slide_pages` | One row per slide. `status` is 'kept', 'ignored', or 'pending'. Optionally links to its LO. |
| 6 | `questions` | MCQs the generator made for a slide. Holds the full MCQ shape per D-2.4. |
| 7 | `attempts` | One row per mock the user takes (Phase 2). |
| 8 | `attempt_answers` | One row per question shown in an attempt (Phase 2). |

## JSON-encoded columns

Some columns store JSON-serialized lists rather than separate tables — keeps the schema small and matches the course pattern (no ORM, no junction tables we don't need).

| Column | Shape |
|--------|-------|
| `classes.factsheet_json` | the full cleaned-factsheet dict |
| `questions.options_json` | `["a", "b", "c", "d"]` (always 4) |
| `questions.correct_indices` | list of int, length 1..4 (D-2.5) |
| `questions.rationales_per_option_json` | `["why a", "why b", "why c", "why d"]` |
| `attempt_answers.selected_indices` | list of int (or NULL on SKIP) |

## Difficulty fields on `questions`

Three fields the ingestion pipeline can fill in Phase 1 (word count, readability, distractor similarity). Three more (`difficulty_topic`, `difficulty_concept_overlap`, `difficulty_skip_confidence`) and the final `difficulty_score` stay NULL until Phase 4's ML model lands. All are nullable on purpose.

## Wipe-and-rerun policy (D-3.1)

Schema changes during the 2-week build are made by editing this file and deleting `~/.surf/user.sqlite`. There are no migration scripts and `app/db/migrations/` stays empty. We can revisit migrations if Surf grows past the submission.

## Where it fits

Read by `app/db/connection.py` via `executescript()` on every `connect()`. All `app/db/queries_*` modules read/write rows defined here.

## Code walkthrough

`schema.sql` is a single SQL file — it has no functions, just CREATE TABLE and CREATE INDEX statements. So instead of a function-by-function walkthrough, here's a section-by-section walkthrough of what each table is for and why it's shaped that way. Audience: a non-engineer who needs to follow the data flow without reading SQL syntax.

**`users` table** — One row per signed-in user. Single-user app, so this is always 0 rows (before sign-up) or 1 row (after). Holds the username and the Anthropic API key (plaintext on disk because the app runs locally and the OS file permissions are the security boundary). Auto-incrementing `id` is the foreign-key anchor for `classes`.

**`classes` table** — One row per class the user creates (e.g. "Microeconomics I", "Operations Research"). Belongs to a user via the `user_id` FK with `ON DELETE CASCADE` — deleting a user wipes their classes (and everything underneath: lectures, slides, questions). The cleaned factsheet is stored in `factsheet_json` as a single TEXT column rather than a separate factsheet table; that's a deliberate "no junction tables we don't need" decision per the course pattern.

**`lectures` table** — One row per uploaded PDF. Belongs to a class via `class_id` FK. Carries `status` (`'pending'` while ingesting, `'done'` when MCQ generation finishes) so the UI can show "Ingesting…" vs "Take mock". The original PDF path is stored so the user can find it again later; the PDF itself isn't copied into the DB (storage cost would balloon for no benefit).

**`learning_objectives` table** — One row per LO that the LO-extractor pulls out of a lecture. Each LO has a title and an inclusive page range (`page_start..page_end`) saying which slides cover it. Belongs to a lecture via `lecture_id` FK.

**`slide_pages` table** — One row per slide of a PDF. The page splitter creates these; the LO-extractor flips the `status` to `'kept'`/`'ignored'` and binds each kept slide to its LO. The `(lecture_id, page_number)` UNIQUE constraint is what stops the page splitter from inserting the same slide twice. Watch out for: `learning_objective_id` is nullable on purpose — `'ignored'` slides have no LO.

**`questions` table** — One row per MCQ. Holds the question text, four options (JSON list), correct indices (JSON list — always a list, even when there's only one correct), per-option rationales (JSON list), source page, language, plus seven difficulty-feature columns (six raw features + one final ML score). The seven difficulty fields are all nullable so Phase 1 can fill what it knows and Phase 4's ML model fills the rest.

**`attempts` table** — Phase 2 territory. One row per mock the user takes — start time, finish time, correct count, total count. The `class_id` FK ties an attempt to a class so the dashboard can group attempts per class.

**`attempt_answers` table** — Phase 2 territory. One row per question shown in an attempt. `selected_indices` is a JSON list of which options the user picked (or NULL if they SKIPPED — NULL is meaningful here, it counts as wrong on grading). `is_correct` is computed at write time so the dashboard doesn't have to recompute on every render.

**Indexes block** — Every foreign key gets an index so the JOIN in `list_questions_for_lecture` (and similar cross-table queries) doesn't scan the whole table. The `(class_id, id)` composite on `lectures` is for "give me the most recent lecture in this class" lookups. SQLite doesn't auto-index FKs, so we have to declare them explicitly.

**Wipe-and-rerun policy** — During the 2-week build there are NO migration scripts. Schema changes happen by editing `schema.sql` and deleting `~/.surf/user.sqlite`. The `IF NOT EXISTS` clauses on every CREATE statement mean `connect()` can run the whole script on every startup without erroring on already-existing tables. If Surf ever lives past the submission, this is the first thing that gets reworked into proper migrations.

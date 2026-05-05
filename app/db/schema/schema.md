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

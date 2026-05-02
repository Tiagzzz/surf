---
phase: 02-mock-taking-loop-p1-p5
plan: 04a
type: execute
wave: 3
depends_on: [02-01, 02-02, 02-03]
files_modified:
  - app/class_/__init__.py
  - app/class_/build_mock/__init__.py
  - app/class_/build_mock/build_mock.py
  - app/class_/build_mock/build_mock.md
  - app/class_/build_mock/practice_mock.py
  - app/class_/study_next/__init__.py
  - app/class_/study_next/study_next.py
  - app/class_/study_next/study_next.md
  - app/db/queries_lectures/queries_lectures.py
  - app/db/queries_lectures/queries_lectures.md
  - app/db/queries_questions/queries_questions.py
  - app/db/queries_questions/queries_questions.md
  - app/db/queries_attempts/__init__.py
  - app/db/queries_attempts/queries_attempts.py
  - app/db/queries_attempts/queries_attempts.md
  - app/db/queries_learning_objectives/queries_learning_objectives.py
  - app/db/queries_learning_objectives/queries_learning_objectives.md
  - .planning/REQUIREMENTS.md
  - tests/test_queries_attempts.py
  - tests/test_save_attempt.py
  - tests/test_build_mock.py
  - tests/test_practice_mock.py
  - tests/test_study_next.py
  - tests/test_mock_entry_points.py
autonomous: true
requirements: [MECH-01, MECH-02]
must_haves:
  truths:
    - "Generate Mock CTA opens the lecture multi-select; on 'Build mock' click, build_mock.build_standard_mock(class_id, lecture_ids) returns a mock with 5×N questions selected unseen → previously-wrong → refresh per Phase 1 D-02 (MECH-01)"
    - "Study Next surfaces the weakest-LO via pure SQL (correct/total ratio, tiebreak most-recently-attempted) per D-2.11; tap launches a PRACTICE mock with ALL MCQs in the LO's page_range per D-4.3 amended (MECH-02)"
    - "Two and only two mock entry points exist: build_standard_mock + study_next.render_study_next_card (which calls build_practice_mock); no manual LO picker in Phase 2 (D-2.8 + REQUIREMENTS amendment #1)"
    - "attempt_answers is seeded with one NULL-row per question_id at attempt creation; Plan 05's UPSERT-on-nav is the only writer that fills selected_indices"
    - "REQUIREMENTS.md is amended in this plan: MECH-02 description updated per D-2.8 + D-4.3 wording from CONTEXT"
    - "All sidecar .md files <=140 lines and include ## Code walkthrough section (D-5.1)"
  artifacts:
    - path: "app/class_/build_mock/build_mock.py"
      provides: "build_standard_mock(class_id, lecture_ids) -> attempt_id; selection logic per Phase 1 D-02"
      exports: ["build_standard_mock"]
    - path: "app/class_/build_mock/practice_mock.py"
      provides: "build_practice_mock(class_id, learning_objective_id) -> attempt_id; ALL MCQs in LO page_range per D-4.3"
      exports: ["build_practice_mock"]
    - path: "app/class_/study_next/study_next.py"
      provides: "weakest_lo_for_class(class_id) -> dict | None; render_study_next_card(class_id)"
      exports: ["weakest_lo_for_class", "render_study_next_card"]
    - path: "app/db/queries_attempts/queries_attempts.py"
      provides: "save_attempt(class_id, mock_kind, question_ids) -> attempt_id; seeds attempt_answers with NULL rows; list_attempts_for_class(class_id) -> list"
      exports: ["save_attempt", "list_attempts_for_class", "get_attempt_by_id"]
  key_links:
    - from: "app/class_/build_mock/build_mock.py"
      to: "app/db/queries_questions + queries_attempts"
      via: "selection SQL + attempt insert"
      pattern: "save_attempt"
    - from: "app/class_/study_next/study_next.py"
      to: "app/class_/build_mock.practice_mock.build_practice_mock"
      via: "tap-to-launch"
      pattern: "build_practice_mock"
    - from: "app/db/queries_attempts/queries_attempts.py:save_attempt"
      to: "attempt_answers table"
      via: "INSERT one NULL-row per question_id at attempt creation"
      pattern: "INSERT INTO attempt_answers"
---

# Plan 02-04a — DB Query Upgrades + Mock-Build Pipelines + REQUIREMENTS Amendment

## Objective

Plan 04a ships the backend half of P3: DB query helpers (queries_lectures / queries_questions / queries_learning_objectives / queries_attempts) needed by the mock-build pipelines, plus `build_mock`, `practice_mock`, and `study_next`. Closes the build paths of MECH-01 (Standard mock) and MECH-02 (Practice mock + Study Next), plus the REQUIREMENTS.md amendment for D-2.8 + D-4.3. No UI rendering and no sandboxes — those ship in 04b.

Purpose: factor the backend logic so 04b can wire the page surface against stable, tested interfaces. Splitting prevents Plan 04 from straddling 50% context with both backend pipelines AND four sandboxes.

Output: four DB query module upgrades, three new mock-build pipelines, REQUIREMENTS.md amendment, full TDD coverage.

## Execution context

- Workflow: `~/.claude/get-shit-done/workflows/execute-plan.md`
- Summary template: `~/.claude/get-shit-done/templates/summary.md`

## Context

- /Users/tiagoreimann/surf/CLAUDE.md
- /Users/tiagoreimann/surf/.planning/phases/02-mock-taking-loop-p1-p5/02-CONTEXT.md (D-2.8, D-2.11, D-4.3 amended)
- /Users/tiagoreimann/surf/.planning/phases/01-ingestion-spine-database/01-CONTEXT.md (D-02 selection logic, D-4.5 partial-success)
- /Users/tiagoreimann/surf/app/db/queries_lectures/queries_lectures.py
- /Users/tiagoreimann/surf/app/db/queries_questions/queries_questions.py
- /Users/tiagoreimann/surf/app/db/schema/schema.sql
- /Users/tiagoreimann/surf/.planning/REQUIREMENTS.md
- /Users/tiagoreimann/surf/previews/_fixtures.py

### Interfaces this plan creates (Plan 04b + 05-07 consume)

- `app/class_/build_mock/build_mock.py` — `build_standard_mock(class_id: int, lecture_ids: list[int]) -> int`. Returns new attempt_id. Selection logic per Phase 1 D-02: unseen → previously-wrong → refresh, capped at 5 per lecture.
- `app/class_/build_mock/practice_mock.py` — `build_practice_mock(class_id: int, learning_objective_id: int) -> int`. SELECT every MCQ where `slide_pages.learning_objective_id == X` (or fallback `source_page IN <lo.page_start..page_end>` if FK is missing). D-4.3 wording.
- `app/class_/study_next/study_next.py` — `weakest_lo_for_class(class_id) -> dict | None` (None if zero attempts per D-2.11), `render_study_next_card(class_id) -> None` (taps `build_practice_mock` then `st.switch_page("views/take_mock_exam.py")`).
- `app/db/queries_attempts/queries_attempts.py` — `save_attempt(class_id, mock_kind, question_ids: list[int]) -> int` (seeds attempt_answers with one NULL row per question_id), `list_attempts_for_class(class_id) -> list[dict]`, `get_attempt_by_id(attempt_id) -> dict | None`.

Schema (already locked Phase 1; no schema changes in this plan):
- attempts(id PK, class_id FK, mock_kind TEXT, started_at, finished_at, correct_count, total_count).
- attempt_answers(attempt_id FK, question_id FK, selected_indices, is_correct, ...) — pre-seeded by save_attempt with selected_indices=NULL and is_correct=NULL (Plan 05's UPSERT fills them in).
- learning_objectives(id PK, lecture_id FK, title, page_start, page_end).
- slide_pages(id PK, lecture_id FK, page_number, learning_objective_id, status).
- questions(id PK, slide_page_id FK, source_page, ...).

## Tasks

<task type="auto" tdd="true">
  <name>Task 1: DB query upgrades + queries_attempts (with seeding) + build_mock + practice_mock + study_next + REQUIREMENTS amendment</name>
  <files>app/class_/__init__.py, app/class_/build_mock/__init__.py, app/class_/build_mock/build_mock.py, app/class_/build_mock/build_mock.md, app/class_/build_mock/practice_mock.py, app/class_/study_next/__init__.py, app/class_/study_next/study_next.py, app/class_/study_next/study_next.md, app/db/queries_lectures/queries_lectures.py, app/db/queries_lectures/queries_lectures.md, app/db/queries_questions/queries_questions.py, app/db/queries_questions/queries_questions.md, app/db/queries_attempts/__init__.py, app/db/queries_attempts/queries_attempts.py, app/db/queries_attempts/queries_attempts.md, app/db/queries_learning_objectives/queries_learning_objectives.py, app/db/queries_learning_objectives/queries_learning_objectives.md, .planning/REQUIREMENTS.md, tests/test_queries_attempts.py, tests/test_save_attempt.py, tests/test_build_mock.py, tests/test_practice_mock.py, tests/test_study_next.py, tests/test_mock_entry_points.py</files>
  <read_first>
    - /Users/tiagoreimann/surf/app/db/queries_lectures/queries_lectures.py
    - /Users/tiagoreimann/surf/app/db/queries_questions/queries_questions.py
    - /Users/tiagoreimann/surf/app/db/queries_learning_objectives/queries_learning_objectives.py
    - /Users/tiagoreimann/surf/app/db/queries_attempts/__init__.py
    - /Users/tiagoreimann/surf/app/db/schema/schema.sql
    - /Users/tiagoreimann/surf/.planning/phases/01-ingestion-spine-database/01-CONTEXT.md (D-02 selection logic specifics)
    - /Users/tiagoreimann/surf/.planning/REQUIREMENTS.md (line for MECH-02)
    - /Users/tiagoreimann/surf/previews/_fixtures.py
  </read_first>
  <behavior>
    Tests first (RED → GREEN):
    - test_queries_attempts — `save_attempt(class_id, mock_kind, question_ids=[1,2,3])` returns int; `list_attempts_for_class` returns one row with mock_kind and started_at set.
    - test_save_attempt.test_seeds_answer_rows — after `save_attempt(class_id, "standard", [10, 20, 30])`, `SELECT COUNT(*) FROM attempt_answers WHERE attempt_id=?` returns 3 AND every row has `selected_indices IS NULL` AND `is_correct IS NULL` (proves the pre-seed contract Plan 05 depends on).
    - test_build_mock — given a class with 3 lectures and ≥5 questions each, `build_standard_mock(class_id, [l1, l2])` selects exactly 10 question_ids (5×2). Selection prefers unseen (no attempt_answers row from a *prior* attempt) over previously-wrong over refresh per Phase 1 D-02.
    - test_build_mock — selecting a lecture with <5 questions falls through unseen → previously-wrong → refresh and pads to 5 with refresh (already-correct) per Phase 1 D-02.
    - test_practice_mock — `build_practice_mock(class_id, lo_id)` returns attempt_id; selected questions all have `slide_pages.learning_objective_id == lo_id` (or `source_page IN range(lo.page_start, lo.page_end+1)` fallback if FK column not set). Mock size matches the count of MCQs in that LO range (D-4.3).
    - test_study_next.weakest_lo_for_class — given seeded answers across 2 LOs (LO1: 4/5 correct, LO2: 1/5 correct), `weakest_lo_for_class(class_id)` returns LO2.
    - test_study_next.weakest_lo_for_class — zero attempts → returns None (D-2.11).
    - test_study_next.weakest_lo_for_class — tie on correct/total → returns the most-recently-attempted (Phase 2 v1 tiebreak per D-2.11).
    - test_mock_entry_points — exactly two mock entry-point functions are exposed for P3 (`build_standard_mock`, `build_practice_mock` via `study_next.render_study_next_card`'s callback). No `build_lo_mock(lo_id)` or similar manual-LO entry point exists in the public API surface.
  </behavior>
  <action>
    1. Add `app/db/queries_attempts/queries_attempts.py` with `save_attempt(class_id, mock_kind, question_ids)`, `list_attempts_for_class(class_id)`, `get_attempt_by_id(attempt_id)`. **save_attempt MUST insert one attempt_answers row per question_id with `selected_indices = NULL` and `is_correct = NULL` at attempt creation.** This matches D-3.3 (UPSERT-on-nav populates these in Plan 05) and avoids adding a new column. Use a single transaction (BEGIN; INSERT INTO attempts; INSERT INTO attempt_answers (...); COMMIT). The grep gate in `<verify>` checks the literal `attempt_answers.*selected_indices.*NULL` substring exists in the .py.
    2. Sidecar `queries_attempts.md` (new file, ≤140 lines, walkthrough section).
    3. If `app/db/queries_lectures/queries_lectures.py` does not have `list_lectures_for_class(class_id)`, `get_lecture_by_id(lecture_id)`, or `update_lecture_status(lecture_id, status)`, add them surgically. Keep Phase 1 functions untouched. Append walkthrough rows to the .md if Plan 01 left them out (idempotent).
    4. If `app/db/queries_questions/queries_questions.py` lacks helpers needed by build_mock — `count_questions_for_lecture(lecture_id)`, `select_questions_for_mock(lecture_ids: list[int], n_per_lecture: int = 5)` — add them. Selection SQL implements unseen → previously-wrong → refresh per Phase 1 D-02. Use one query per priority bucket and Python merges to 5; do NOT try to write one mega-CTE. Note: "unseen" here means questions never attempted in any *prior* attempt; the NULL rows seeded for the current attempt-in-flight do not count as "seen".
    5. If `app/db/queries_learning_objectives/queries_learning_objectives.py` lacks `list_los_for_class(class_id)` (joined through lectures) and `get_lo_by_id(lo_id)`, add them.
    6. Implement `app/class_/build_mock/build_mock.py`:
       - `build_standard_mock(class_id: int, lecture_ids: list[int]) -> int`: gathers 5×N question_ids via `queries_questions.select_questions_for_mock`; calls `save_attempt(class_id, "standard", question_ids)`; returns attempt_id.
    7. Implement `app/class_/build_mock/practice_mock.py`:
       - `build_practice_mock(class_id: int, learning_objective_id: int) -> int`: SELECT every question whose `slide_pages.learning_objective_id == X` OR (fallback) `source_page` is in the LO's page_start..page_end range; D-4.3 wording. Calls `save_attempt(class_id, "practice", question_ids)`.
    8. Implement `app/class_/study_next/study_next.py`:
       - `weakest_lo_for_class(class_id) -> dict | None` per D-2.11 (pure SQL, no ML).
       - `render_study_next_card(class_id) -> None`: if `weakest_lo_for_class` returns None, return early (card hidden). Else render `st.container(key="study-next-card")` with the LO title + a CTA "Practice this LO". On click: `attempt_id = build_practice_mock(class_id, lo['id']); st.session_state["attempt_id"] = attempt_id; st.switch_page("views/take_mock_exam.py")`.
    9. Sidecars: `build_mock.md`, `practice_mock.md` (or share one — single file is fine since both are short), `study_next.md`. Each includes the walkthrough section, ≤140 lines, with the edit-this-later notes from CONTEXT D-2.11 + D-4.3 inline.
    10. **REQUIREMENTS.md amendment:** edit `.planning/REQUIREMENTS.md` to update the MECH-02 description per CONTEXT D-2.8 + D-4.3:
        - Old: "PRACTICE mock — user picks one LO → 1 question per slide of that LO, same selection priority."
        - New: "PRACTICE mock — Study Next surfaces an LO; user taps the card to launch a focused mock. PRACTICE mock includes every MCQ tied to the surfaced LO's page range. No manual LO picker in Phase 2."
        Single-line surgical edit per CLAUDE.md Surgical Changes; nothing else in the file changes.
  </action>
  <verify>
    <automated>pytest -q tests/test_queries_attempts.py tests/test_save_attempt.py tests/test_build_mock.py tests/test_practice_mock.py tests/test_study_next.py tests/test_mock_entry_points.py -x &amp;&amp; python -c "from app.class_.build_mock.build_mock import build_standard_mock; from app.class_.build_mock.practice_mock import build_practice_mock; from app.class_.study_next.study_next import weakest_lo_for_class, render_study_next_card; from app.db.queries_attempts.queries_attempts import save_attempt" &amp;&amp; grep -q "Study Next surfaces an LO" .planning/REQUIREMENTS.md &amp;&amp; grep -E "attempt_answers.*selected_indices.*NULL|selected_indices.*NULL.*attempt_answers" app/db/queries_attempts/queries_attempts.py &amp;&amp; grep -q "Code walkthrough" app/class_/build_mock/build_mock.md app/class_/study_next/study_next.md app/db/queries_attempts/queries_attempts.md</automated>
  </verify>
  <done>
    - Six new test files green; selection logic preserves Phase 1 D-02 priorities; attempt_answers pre-seed contract verified.
    - REQUIREMENTS.md MECH-02 row reflects amended wording.
    - All new sidecars exist and contain walkthrough sections.
    - Two mock entry points (Generate Mock + Study Next) and only two; verified by `tests/test_mock_entry_points.py`.
  </done>
</task>

## Verification

- `pytest -q tests/test_queries_attempts.py tests/test_save_attempt.py tests/test_build_mock.py tests/test_practice_mock.py tests/test_study_next.py tests/test_mock_entry_points.py`.
- `grep -q "Study Next surfaces an LO" .planning/REQUIREMENTS.md`.
- All sidecars updated and ≤140 lines.

## Success criteria

- MECH-01 closed (build path): `build_standard_mock` selects 5×N questions per Phase 1 D-02 priorities.
- MECH-02 closed (build path + entry points): `build_practice_mock` selects all MCQs in LO range; only two mock entry points exist.
- REQUIREMENTS.md MECH-02 row reflects amended wording from CONTEXT D-2.8 + D-4.3.
- attempt_answers pre-seed contract is established and tested — Plan 05's UPSERT-on-nav has a stable substrate.

## Output

Create `.planning/phases/02-mock-taking-loop-p1-p5/02-04a-SUMMARY.md` covering: backend pipelines + queries shipped, REQUIREMENTS amendment confirmation, attempt_answers seeding implementation note (transaction semantics), test coverage map (MECH-01 build + MECH-02 build paths).

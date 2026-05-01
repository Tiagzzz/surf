---
phase: 01-ingestion-spine-database
plan: 03
subsystem: ingestion
tags: [claude, llm, prompt, json, learning-objectives, python311]

requires:
  - phase: 01-ingestion-spine-database/01-01
    provides: "queries_learning_objectives.insert_learning_objective + queries_pages.set_slide_page_learning_objective for the orchestrator"
  - phase: 01-ingestion-spine-database/01-02
    provides: "the `--- PAGE N ---` marker contract that lecture_md follows"
provides:
  - "extract_los(lecture_md, factsheet_subset) -> dict — single Claude call producing LOs + ignored-page list"
  - "lo_extractor_system_prompt.md — the editable prompt artifact (76L)"
affects:
  - "01-05 (orchestrator): consumes extract_los output to populate learning_objectives + slide_pages.learning_objective_id"
  - "01-04 (MCQ generator): the orchestrator filters slides by status='kept' (set from this extractor's output) before passing them to mcq_generate"
  - "Phase 2 mock-review: groups questions by LO via learning_objectives.id; the LOs come from this extractor"

tech-stack:
  added: [anthropic SDK installed (was missing — soft dep activated)]
  patterns:
    - "10-line Claude-call wrapper (matches factsheet_cleaner shape exactly)"
    - "System prompt = sibling .md file, read on every call (no restart needed for prompt edits)"
    - "User-message envelope: json.dumps({lecture_md, factsheet_subset}) — single string payload to call_claude"

key-files:
  created:
    - app/class_/lo_extract/__init__.py (4L) — re-exports
    - app/class_/lo_extract/lo_extractor.py (39L) — 10-line wrapper around call_claude
    - app/class_/lo_extract/lo_extractor_system_prompt.md (76L) — the actual product logic
    - app/class_/lo_extract/lo_extractor.md (45L) — plain-language sidecar
  modified: []

key-decisions:
  - "D-1.2 honored: extract_los signature is (lecture_md, factsheet_subset). The system prompt explicitly enumerates the 7 allowed factsheet keys and tells Claude to ignore any others."
  - "D-1.3 honored: each LO is {title: str, page_range: [start, end]}. No summary, no key_terms."
  - "D-1.4 honored: prompt states max LOs = floor(total_pages / 5) and instructs Claude to aim for fewer than the cap."
  - "D-1.5 honored: prompt enforces coverage — every non-ignored page belongs to exactly one LO's page_range, no overlaps."
  - "D-1.1 + D-1.1b honored: prompt enumerates the 9 structural categories (snake_case keys) plus the off-topic semantic rule. Each ignored page returns one of these 10 reason strings verbatim."
  - "Output discipline: strict JSON only (parsed via call_claude's expect_json=True which uses json.loads, not eval). Schema documented inline in the prompt."

patterns-established:
  - "Wrapper reads the .md prompt on every call — Tiago can edit lo_extractor_system_prompt.md directly without touching Python."
  - "factsheet_subset envelope: orchestrator owns trimming the factsheet to the 7 keys before calling extract_los (passing the full thing works but burns ~40% extra input tokens)."

requirements-completed:
  - PIPE-03

duration: ~25min
completed: 2026-05-01
---

# Plan 01-03: LO Extractor

**One Claude call per lecture turns 30 raw slides into 4–5 named learning objectives plus an explicit ignore list — the table of contents that powers Phase 2's mock-review LO grouping and saves Plan 04 from generating MCQs on title pages and dividers.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-05-01
- **Tasks:** 1
- **Files created:** 4

## Accomplishments

- `extract_los(lecture_md, factsheet_subset)` lives at `app/class_/lo_extract/lo_extractor.py` — 39 lines including docstring, 10 of them executable.
- The system prompt (`lo_extractor_system_prompt.md`, 76L) is the single source of truth for skip rules, LO rules, and the JSON schema. Tiago edits it directly to tune behaviour — no Python redeploy.
- Both naming conventions are present in the prompt: snake_case keys (`title`, `agenda`, `section_divider`, `closing`, `references_only`, `image_only`, `blank`, `institutional`, `speaker_bio`, `off_topic`) for machine output AND descriptive synonyms (`title page`, `agenda / table of contents`, `image-only`, `sources/references-only`) for human readability.
- Anthropic SDK installed (was missing locally — soft-dep guard in tests/test_smoke.py was hiding it). pytest now reports 4 passed (was 2 passed / 2 skipped).

## Task Commits

1. **Task 1: lo_extractor.py + system prompt + sidecar + __init__** — `36ba627` (feat)

## Files Created

- `app/class_/lo_extract/__init__.py` — re-exports `extract_los`
- `app/class_/lo_extract/lo_extractor.py` (39L) — 10-line wrapper
- `app/class_/lo_extract/lo_extractor_system_prompt.md` (76L) — the product logic
- `app/class_/lo_extract/lo_extractor.md` (45L) — sidecar (≤100L per C-22)

## Verification

- `pytest -q`: 4 passed
- `ruff check app/class_/lo_extract/`: all checks passed
- `python -c "from app.class_.lo_extract import extract_los; print(list(inspect.signature(extract_los).parameters))"` → `['lecture_md', 'factsheet_subset']`
- All 25 acceptance grep checks pass: 7 factsheet keys present, 7 taxonomy terms present (case-insensitive), JSON schema keys present, wrapper imports `call_claude`, `expect_json=True` set
- Threat T-03-05 mitigated: `grep -r "ANTHROPIC_API_KEY" app/class_/lo_extract/` returns 0 lines

## Self-Check: PASSED

All acceptance criteria met. No deviations from plan.

## What Plan 05 (orchestrator) needs to do with the output

Per D-4.7: if `extract_los` raises (network error or invalid JSON after retry), write the lecture row with `status='pending'` and skip MCQ generation. User sees "Retry ingestion" on the lecture card.

On success, the orchestrator:

1. **Builds `factsheet_subset`** from the cleaned factsheet stored in `classes.factsheet_json` — picks ONLY the 7 keys listed in D-1.2 (passes the full factsheet only as a debug fallback).
2. **Calls** `result = extract_los(lecture_md, factsheet_subset)`.
3. **Inserts each LO** via `insert_learning_objective(lecture_id, lo['title'], lo['page_range'][0], lo['page_range'][1])` and remembers the `lo_id`.
4. **Links every page** in each LO's `page_range` to its `lo_id` via `set_slide_page_learning_objective(slide_page_id, lo_id)`.
5. **Marks ignored pages** via `set_slide_page_status(slide_page_id, 'ignored', learning_objective_id=None)`.
6. **Filters kept slides** (`status='kept'`) and hands them to the MCQ generator (Plan 04).
7. **Sets** `set_lecture_status(lecture_id, 'ready')` only after MCQ generation finishes.

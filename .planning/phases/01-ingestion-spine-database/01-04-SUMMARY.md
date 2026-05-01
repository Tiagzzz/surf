---
phase: 01-ingestion-spine-database
plan: 04
subsystem: ingestion
tags: [claude, llm, prompt, json, mcq, multi-correct, python311]

requires:
  - phase: 01-ingestion-spine-database/01-01
    provides: "queries_questions.insert_question accepting all 7 difficulty kwargs (3 LOCKED + 4 PENDING)"
  - phase: 01-ingestion-spine-database/01-02
    provides: "page_splitter.batch_slides feeds slide records into this generator"
provides:
  - "generate_mcqs(slides_batch) -> dict — single Claude call producing 1-3 MCQs per non-ignored slide"
  - "MAX_BATCH_SIZE = 10 constant (D-4.3)"
  - "mcq_generator_system_prompt.md — the editable prompt artifact (70L)"
affects:
  - "01-05 (orchestrator): consumes generate_mcqs output, computes 3 LOCKED difficulty features, writes via insert_question"
  - "Phase 2 mock-take: reads MCQs via list_questions_for_lecture; UI uses checkboxes when len(correct_indices) >= 2"
  - "Phase 4 ML: difficulty_score column will be backfilled by trained model"

tech-stack:
  added: []
  patterns:
    - "10-line Claude-call wrapper (matches factsheet_cleaner shape exactly)"
    - "Defensive input cap (D-4.3): ValueError on 0-slide and >10-slide batches"
    - "User-message envelope: json.dumps({slides: [...]}) — single string payload to call_claude"
    - "Wrapper does NOT validate Claude's response shape; orchestrator owns retry on malformed JSON (D-4.4) and on schema violations (D-4.5)"

key-files:
  created:
    - app/class_/mcq_generate/__init__.py (4L) — re-exports generate_mcqs + MAX_BATCH_SIZE
    - app/class_/mcq_generate/mcq_generator.py (44L) — wrapper + 2 ValueError guards
    - app/class_/mcq_generate/mcq_generator_system_prompt.md (70L) — the actual product logic
    - app/class_/mcq_generate/mcq_generator.md (51L) — plain-language sidecar
  modified: []

key-decisions:
  - "D-2.1 honored: prompt says 1 MCQ default, 2-3 only when slide has multiple distinct testable pieces."
  - "D-2.2 honored: variety is by sub-topic, NOT by Bloom-style cognitive level — explicit in the prompt."
  - "D-2.3 honored: per-slide language detection (en/de/other) by Claude."
  - "D-2.4 honored: full schema spelled out — question, options (exactly 4), correct_indices (list 1..4), rationales_per_option (exactly 4), source_page, language. Difficulty fields are NOT produced by Claude (orchestrator handles)."
  - "D-2.5 honored: correct_indices is ALWAYS a list, never a bare int. Multi-correct support up to 4."
  - "D-2.6 honored: rationales_per_option has exactly 4 entries, one per option, in option order."
  - "D-4.3 honored: MAX_BATCH_SIZE = 10 enforced in Python; ValueError raised on overflow."
  - "D-4.8 honored: empty mcqs array per slide is a valid response — orchestrator reclassifies as ignored."
  - "Skip taxonomy aligned with D-1.1 + D-1.1b: same 10 categories the LO extractor uses, listed verbatim in the prompt."
  - "Profile-catalog integration deferred (placeholder NOT added to keep CLAUDE.md Simplicity rule clean). When Tiago's NLM analysis lands, profile cards get inserted as a single new section in mcq_generator_system_prompt.md."

patterns-established:
  - "Wrapper enforces input invariants in Python (cap, empty); response invariants are the orchestrator's problem."
  - "by_slide list is in input order — orchestrator can zip(input_slides, by_slide) without re-sorting."

requirements-completed:
  - PIPE-04

duration: ~20min
completed: 2026-05-01
---

# Plan 01-04: MCQ Generator

**One Claude call per ≤10-slide batch produces 1–3 MCQs per non-ignored slide with the full D-2.4 schema (4 options, 1..4 correct indices, 4 per-option rationales, language). Phase 1 ingestion now has every Claude-call building block it needs — only the orchestrator remains.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-05-01
- **Tasks:** 1
- **Files created:** 4

## Accomplishments

- `generate_mcqs(slides_batch)` lives at `app/class_/mcq_generate/mcq_generator.py` — 44 lines including docstring + two ValueError guards (empty batch, > 10 slides).
- The system prompt (`mcq_generator_system_prompt.md`, 70L) is the single source of truth for MCQ shape, multi-correct support, per-option rationales, language detection, and the empty-array signal that triggers slide reclassification.
- The 10 skip categories (9 structural + off_topic) are listed verbatim in the prompt — same taxonomy the LO extractor uses (D-1.1 + D-1.1b alignment).
- All input invariants enforced in Python (D-4.3 cap, defensive empty-batch guard); response invariants are the orchestrator's problem (D-4.4 retry, D-4.5 partial-success).

## Task Commits

1. **Task 1: mcq_generator.py + system prompt + sidecar + __init__** — `47fa87c` (feat)

## Files Created

- `app/class_/mcq_generate/__init__.py` — re-exports `generate_mcqs`, `MAX_BATCH_SIZE`
- `app/class_/mcq_generate/mcq_generator.py` (44L) — wrapper
- `app/class_/mcq_generate/mcq_generator_system_prompt.md` (70L) — the product logic
- `app/class_/mcq_generate/mcq_generator.md` (51L) — sidecar (≤100L per C-22)

## Verification

- `pytest -q`: 4 passed
- `ruff check app/class_/mcq_generate/`: all checks passed
- `python -c "from app.class_.mcq_generate import generate_mcqs, MAX_BATCH_SIZE; assert MAX_BATCH_SIZE == 10"` exits 0
- All 22 acceptance grep checks pass: `MAX_BATCH_SIZE = 10` present, 7 schema tokens present, "exactly 4" appears 4 times (>= 2 required), 7 taxonomy lines (>= 4 required), 2 ValueError raises present
- Threat T-04-01 mitigated: ValueError on both 0-slide and 11-slide inputs
- Threat T-04-05 mitigated: `grep -r "ANTHROPIC_API_KEY" app/class_/mcq_generate/` returns 0 lines

## Self-Check: PASSED

All acceptance criteria met. No deviations from plan.

## What Plan 05 (orchestrator) needs to do with the output

For each batch returned by `generate_mcqs(batch)`:

1. **Iterate `result['by_slide']`** — same order as the input batch.
2. **For each slide entry:**
   - **If `mcqs == []`:** call `set_slide_page_status(slide_page_id, 'ignored', learning_objective_id=None)` — the slide had no testable content (D-4.8).
   - **Else:** for each MCQ, compute the 3 LOCKED Phase 1 difficulty features:
     - `difficulty_word_count` — `len(question_text.split())` (or include options — pick one consistently for Phase 4)
     - `difficulty_readability` — Flesch-Kincaid or similar; may leave NULL if scoring lib not yet wired
     - `difficulty_distractor_similarity` — string similarity between correct option(s) and distractors; may leave NULL
   - Then call `insert_question(slide_page_id, question, options, correct_indices, rationales_per_option, source_page, language, difficulty_word_count=..., difficulty_readability=..., difficulty_distractor_similarity=...)` — the 4 PENDING difficulty kwargs default to None.
3. **On Claude failure** (network, invalid JSON, schema violation): per D-4.4 retry once. Per D-4.5 if both attempts fail, write the slides as `status='pending'` and continue to the next batch — the lecture lands with however many batches succeeded.

## Future integration: profile catalog

Once Tiago's NLM exam-MCQ analysis lands at `docs/exam_mcq_profiles.md`, the integration is a **single new section** appended to `mcq_generator_system_prompt.md` (no Python changes, no DB changes). Same goes for any 3-PENDING difficulty criteria swap — that's a schema rename + D-2.4 update + system-prompt note. Deferred until exam analysis is in.

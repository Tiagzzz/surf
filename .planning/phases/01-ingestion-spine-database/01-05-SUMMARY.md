---
phase: 01-ingestion-spine-database
plan: 05
subsystem: orchestrator
tags: [orchestrator, pipeline, retry, partial-success, smoke-test, python311]

requires:
  - phase: 01-ingestion-spine-database/01-01
    provides: "queries_users/classes/lectures/pages/questions/learning_objectives + DB connection module"
  - phase: 01-ingestion-spine-database/01-02
    provides: "page_splitter.split_lecture_md + batch_slides; pdf_to_md_v3 emits `--- PAGE N ---` markers"
  - phase: 01-ingestion-spine-database/01-03
    provides: "lo_extract.extract_los(lecture_md, factsheet_subset) -> {learning_objectives, ignored_pages, language}"
  - phase: 01-ingestion-spine-database/01-04
    provides: "mcq_generate.generate_mcqs(slides_batch) -> {by_slide: [...]}"
provides:
  - "ingest_lecture(class_id, pdf_path, *, title, claude_call_lo, claude_call_mcq) -> int — single entry point for the 5-step pipeline"
  - "tests/_fakes.py — deterministic fakes for Claude calls used by the smoke test"
  - "assets/sample_lectures/sample_lecture.pdf — 3-page reportlab placeholder driving the smoke test"
affects:
  - "Phase 2 P3 Class page: calls ingest_lecture on user upload, surfaces lectures.status='pending' as a retry button"
  - "Phase 4 ML: difficulty_score column on questions is the only field still NULL after this plan ships (others may be NULL too in Phase 1)"

tech-stack:
  added:
    - "reportlab (generation-time only, NOT a runtime dep) — used to regenerate sample_lecture.pdf"
  patterns:
    - "Injectable Claude callers (claude_call_lo, claude_call_mcq) — defaults to real extract_los/generate_mcqs; tests inject fakes"
    - "DB rebind for tests: tmp_path + reload of every queries_*/__init__ to avoid clobbering ~/.surf/user.sqlite"
    - "5-step pipeline stays in one ~200-line module — no helpers split across files (CLAUDE.md Simplicity)"

key-files:
  created:
    - app/class_/lecture_ingest/__init__.py (3L) — re-exports ingest_lecture
    - app/class_/lecture_ingest/lecture_ingest.py (~210L) — orchestrator
    - app/class_/lecture_ingest/lecture_ingest.md (37L) — plain-language sidecar
    - assets/sample_lectures/sample_lecture.pdf (2.6 KB) — 3-page placeholder
    - assets/sample_lectures/README.md (28L) — what + why + regenerate command
    - tests/_fakes.py (52L) — fake_extract_los + fake_generate_mcqs
  modified:
    - tests/test_smoke.py — added 1 new test (test_ingestion_end_to_end_against_fresh_sqlite); the 4 pre-existing tests untouched

key-decisions:
  - "D-4.2 honored: pipeline order is exactly PDF→MD → split+batch → LO-extract once → MCQ-generate per batch → DB writes."
  - "D-4.4 honored: _call_with_retry(fn) does 2 attempts max, no exponential backoff, no error-class special-casing."
  - "D-4.5 honored: failed MCQ batch flips its slides to status='pending' and the orchestrator continues; lecture status stays 'pending'."
  - "D-4.6 honored: writes are additive — no UPSERT, no dedupe, no idempotency layer."
  - "D-4.7 honored: LO failure (both attempts) returns lecture_id with the row in DB at status='pending'; NO MCQ generation runs and NO slide_pages writes happen."
  - "D-4.8 honored: empty mcqs[] for a slide flips that slide to status='ignored' (Claude-driven skip on top of D-1.1 structural taxonomy)."
  - "D-1.2 honored: orchestrator builds a 7-key factsheet subset (surf_extraction_notes, FSLO, narrative_summary, main_topics, important_concepts_models_methods, skills_students_are_expected_to_develop, exam_relevant_content) before calling extract_los."
  - "D-1.5 defensive: a slide whose page falls outside every LO's range flips to 'pending' rather than crashing the orchestrator (the system prompt is still the authoritative enforcement layer)."
  - "Difficulty fields filled by orchestrator: only difficulty_word_count = len(question.split()). The other 5 difficulty columns + difficulty_score are left NULL in Phase 1."
  - "Defensive _validate_mcq guards against malformed Claude output: bad MCQs are skipped within an otherwise-valid batch (per the plan's 'Single bad MCQs are skipped' rule)."

patterns-established:
  - "End-to-end smoke test pattern: rebind app.db.connection.DB to a tmp SQLite + reload all query modules; inject Claude fakes; assert DB rows."
  - "Sidecar discipline (C-22): orchestrator sidecar is 37L — well under the 100-line cap and simpler than the 4 existing sidecars."

threats-mitigated:
  - "T-05-01 (malformed Claude response) — _validate_mcq enforces D-2.4 shape; bad MCQs skipped, valid ones written; empty array reclassifies slide as ignored (D-4.8)."
  - "T-05-03 (API key leakage in logs) — no ANTHROPIC_API_KEY in lecture_ingest.py (acceptance-grep verified == 0)."
  - "T-05-05 (silent failure) — lectures.status is the audit trail: 'pending' on any partial failure, 'ready' only on full success; smoke test asserts 'ready' on the happy path."
  - "T-05-06 (test clobbers prod DB) — smoke test rebinds DB_FILE to tmp_path before any insert; acceptance-grep for '~/.surf' in tests/ returns 0."

verification:
  acceptance-criteria-passed:
    - "ingest_lecture importable + correct signature (verify command prints OK)"
    - "lecture_ingest.md is 37 lines (≤100)"
    - "All 7 factsheet keys grep-present in lecture_ingest.py"
    - "5 imports from app.db.queries_* (lectures, pages, questions, learning_objectives, classes)"
    - "0 ANTHROPIC_API_KEY references"
    - "0 '~/.surf' references in tests/test_smoke.py"
    - "5 def test_* in tests/test_smoke.py (4 existing + 1 new)"
    - "pytest -q passes 5/5 in 1.11s"
    - "ruff check on plan-touched files: clean"
  pre-existing-tech-debt:
    - "5 ruff errors in app/brain/ingestion/pdf_to_md_v3.py (E501 + I001) on lines NOT modified by this plan — same debt flagged in 01-02-SUMMARY.md."

phase-2-handoff:
  ui-retry-button: |
    Phase 2's P3 Class page can surface a retry control by reading
    list_lectures_for_class(class_id) and rendering a button next to any
    row where status == 'pending'. Clicking the button should re-call
    ingest_lecture with the original pdf_path; the orchestrator's writes
    are additive (D-4.6), so a retry simply attempts LO extraction
    + MCQ generation again without dedup logic. Phase 2 may want to
    add a "delete and retry" mode that drops dependent rows first to
    avoid duplicates if a partial run already wrote some questions.

phase-4-handoff:
  ml-backfill-target: |
    The questions table is the only Phase 4 ML write target. After this
    plan, every question row has difficulty_word_count populated by the
    orchestrator. The 5 other difficulty columns
    (difficulty_readability, difficulty_distractor_similarity,
    difficulty_conceptual_density, difficulty_distractor_derivation,
    difficulty_reasoning_steps) plus the final difficulty_score are NULL.
    Phase 4 should backfill via a single UPDATE per question_id, keyed
    by id; no schema change needed.
---

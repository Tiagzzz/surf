---
phase: 01-ingestion-spine-database
verification_date: 2026-05-01
verdict: PASS
plans_completed: 5
requirements_closed: [PIPE-01, PIPE-03, PIPE-04, DB-01, MECH-04, GRADE-02]
---

# Phase 1 Verification

Goal-backward analysis: did the codebase deliver what Phase 1 promised?

## Phase goal (from ROADMAP.md)

> A lecture PDF can be ingested end-to-end into the SQLite database with
> extracted LOs, page-split slides, and eagerly-generated MCQs (each with
> placeholder difficulty features) — no UI required to verify.

**Verdict: PASS.** Validated by both the synthetic smoke test (`pytest -q`) and a live end-to-end run on a real 31-page HSG microeconomics lecture (MII_SM1.pdf) that produced 4 LOs, 19 kept + 12 ignored slides, and 19 MCQs in `~/.surf/user.sqlite` — all queryable through the `app.db.queries_*` wrappers.

## Success criteria

### SC1 — Pipeline writes to all 4 tables, queryable via db.py wrappers

**Status: PASS.**

- Smoke test `test_ingestion_end_to_end_against_fresh_sqlite` (tests/test_smoke.py) asserts non-zero rows in `lectures`, `slide_pages`, `learning_objectives`, `questions` after one ingest.
- Live MII test produced: 1 row in `lectures`, 31 in `slide_pages`, 4 in `learning_objectives`, 19 in `questions` — read back through `get_lecture_by_id`, `list_slide_pages_for_lecture`, `list_learning_objectives_for_lecture`, `list_questions_for_lecture`.
- All 6 query packages exist: `queries_users`, `queries_classes`, `queries_lectures`, `queries_pages`, `queries_questions`, `queries_learning_objectives`.

### SC2 — pdf_to_md_v3 emits `--- PAGE N ---` markers; splitter regex-splits deterministically

**Status: PASS.**

- `app/brain/ingestion/pdf_to_md_v3.py` lines 22 + 103 emit `--- PAGE N ---` (commit 86228b2 — Plan 01-02 surgical edits).
- `app/brain/ingestion/page_splitter/page_splitter.py` line 7: `_PAGE_MARKER = re.compile(r"^---\s+PAGE\s+(\d+)\s+---\s*$", re.MULTILINE)` — locked D-4.1.
- Live test: 31-page MII lecture → 31 marker matches, 31 slide records, deterministic page numbering.

### SC3 — LO-extractor Claude call returns valid JSON (LOs with page ranges + page-ignore list) against a fixed page-ignore category list

**Status: PASS.**

- `app/class_/lo_extract/lo_extractor.py` invokes Claude with `expect_json=True`; system prompt locks the 9-category D-1.1 structural taxonomy + the D-1.1b semantic off-topic rule.
- Live test: returned 4 LOs (page ranges 4-7, 9-18, 19-26, 28-31 — non-overlapping), 12 ignored pages, each with category reason ("title page", "agenda / table of contents", "section divider", "sources/references-only").
- Floor(N/5) LO cap (D-1.4) honored: 31 pages → max 6 LOs allowed → 4 produced.

### SC4 — MCQ-generator produces ≥1 MCQ per non-ignored slide, with question + 4 options + correct + rationale + 6 difficulty placeholders

**Status: PASS (schema-complete; only 1 of 6 difficulty features filled by Phase 1, by design).**

- `app/class_/mcq_generate/mcq_generator.py` invokes Claude per ≤10-slide batch (D-4.3); locked schema D-2.4 (4 options, list-of-int correct_indices, 4 rationales).
- Live test: 19 kept slides → 19 MCQs (1.0 ratio), all 4-option, all schema-valid, 4 multi-correct after the prompt-tweak commit (bda04e7).
- All 6 difficulty columns exist in schema; orchestrator fills `difficulty_word_count`. The other 5 (`difficulty_readability`, `difficulty_distractor_similarity`, `difficulty_conceptual_density`, `difficulty_distractor_derivation`, `difficulty_reasoning_steps`) are NULL in Phase 1, per 01-CONTEXT.md and Plan 01-05's `<interfaces>` block — Phase 4 ML backfills `difficulty_score` plus the readability/similarity pair.

### SC5 — pytest -q passes and exercises one end-to-end ingestion against a fresh SQLite

**Status: PASS.**

```
$ pytest -q
.....
5 passed in 1.11s
```

5 tests: 4 module-import smokes (claude_client, factsheet_cleaner, factsheet_renderer, pdf_to_md_v3) + 1 end-to-end `test_ingestion_end_to_end_against_fresh_sqlite` that drives `ingest_lecture` against a tmp SQLite using deterministic Claude fakes (`tests/_fakes.py`) and a 3-page reportlab placeholder PDF.

## Requirements coverage

| ID | Title | Plan(s) | Status |
|----|-------|---------|--------|
| PIPE-01 | PDF → Markdown extraction | 01-02 | ✅ pdf_to_md_v3 with `--- PAGE N ---` markers |
| PIPE-03 | Learning-objective extraction | 01-03 | ✅ extract_los; 9-category skip taxonomy |
| PIPE-04 | MCQ generation | 01-04, 01-05 (prompt tweak) | ✅ generate_mcqs; profile catalogue + multi-correct |
| DB-01 | SQLite schema (8 tables, parameterized SQL) | 01-01 | ✅ schema.sql, 6 query packages, FK pragma on |
| MECH-04 | End-to-end orchestrator | 01-05 | ✅ ingest_lecture single entry point |
| GRADE-02 | 3 LOCKED difficulty features stored | 01-01, 01-05 | ✅ schema columns exist; word_count filled |

## Locked decisions honored

All 24 locked decisions D-1.1 .. D-4.8 from `01-CONTEXT.md` are reflected in code paths exercised by the smoke test or covered by acceptance greps. Spot checks:

- D-1.1 (9 structural skip categories) + D-1.1b (semantic off-topic): in `lo_extractor_system_prompt.md` and `mcq_generator_system_prompt.md`.
- D-1.2 (7-key factsheet subset): `_build_factsheet_subset` in `lecture_ingest.py`.
- D-1.5 (every kept slide bound to one LO): `_find_lo_id` + LO assignment in `lecture_ingest.py`.
- D-2.4 (MCQ schema), D-2.5 (correct_indices is always a list), D-2.6 (rationales_per_option, 4 entries): system prompt + `_validate_mcq` defensive check.
- D-3.1 (wipe-and-rerun, no migrations): `connect()` runs schema.sql on every startup; user wipes ~/.surf/user.sqlite to evolve.
- D-3.4 (sqlite3 stdlib + pandas.read_sql, no ORM): every queries_*/__init__.py uses `?` placeholders + `pd.read_sql`.
- D-4.1 (`--- PAGE N ---`), D-4.2 (5-step pipeline), D-4.3 (≤10-slide batch), D-4.4 (2-attempt retry no backoff), D-4.5 (partial success), D-4.6 (additive writes), D-4.7 (LO failure → no MCQs), D-4.8 (empty mcqs → ignored): all visible in `lecture_ingest.py`.

## Live validation evidence

Beyond the synthetic smoke test, ran the real Anthropic API end-to-end on:

- **Factsheet:** `MII_FS.pdf` (297 KB, 8568 chars, 0 tables) → cleaned via `clean_factsheet` in 25.1s → 7 top-level keys including the D-1.2 subset.
- **Lecture:** `MII_SM1.pdf` (1.9 MB, 31 pages) → ingested in 175.8s after the prompt tweak.
- **Output:** 4 LOs (correct page-range partition), 19 kept + 12 ignored slides (correct skip taxonomy), 19 MCQs in 19 kept slides, 4/19 multi-correct (~21%, hitting the post-tweak target), 0 slide-reference leaks.

Saved artifacts to `~/CS/CS_Obsidian/CS_EN_VF/CLAUDE_OUTPUTS/` for human review (factsheet_cleaned.json, factsheet_rendered.md, mcqs.md v1+v2).

## Pre-existing tech debt (not blocking)

- 5 ruff errors in `app/brain/ingestion/pdf_to_md_v3.py` (E501 + I001) on lines NOT modified by Plan 01-02 — flagged in 01-02-SUMMARY.md, deferred to a future cleanup pass per CLAUDE.md Surgical Changes rule.

## Plan summary

| Plan | Title | Wave | Commits |
|------|-------|------|---------|
| 01-01 | SQLite database spine | 1 | 740a895 (+ Plan-01 commits) |
| 01-02 | PDF markers + page_splitter | 1 | 86228b2, 77394fa, b0b9880 |
| 01-03 | LO extractor | 2 | 36ba627, 8b4d408 |
| 01-04 | MCQ generator | 2 | 47fa87c, 2f4cafc, 7308936, 6d6077d |
| 01-05 | Orchestrator + smoke + prompt tweak | 3 | fc0d4cb, 16c51ac, 16c1d38, bda04e7 |

## Phase 2 readiness

The ingestion spine is fully wired and validated. Phase 2 (P1-P5 UI) can call `ingest_lecture(class_id, pdf_path)` directly from a Streamlit upload handler; the `lectures.status` column is the audit signal for surfacing a "retry" button on partial failures (per 01-05-SUMMARY.md handoff note).

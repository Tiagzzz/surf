---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 2 plan 02-01 closed 2026-05-03 — theme + tokens + previews/ scaffold + Wave-1 spike verdicts (Q3 FAIL, Q4 mech-pending-RSS, Q8 FIXED) + 18 script sidecars carry Code walkthroughs. Bench approved at 1c0148b; doc approved at f166ea2. Wave 2 (02-02 + 02-03) ready to begin.
last_updated: "2026-05-03T15:17:00.000Z"
last_activity: 2026-05-03 -- Plan 02-01 complete (12 tasks + 6 deviations + 3 architectural amendments: D-2.20a, D-2.25a, C-22 line-cap-removal+scope-clarification)
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 13
  completed_plans: 6
  percent: 46
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-01)

**Core value:** Pass the grade (≥16/24) AND deliver Idea v1 vision (7-page flow, eager MCQ generation, 6-feature ML difficulty model) by 2026-05-14.
**Current focus:** Phase 2 — Mock Taking Loop (P1–P5) — Wave 1 closed (plan 02-01 done); Wave 2 (02-02 + 02-03) ready to begin

## Current Position

Phase: 2 (Mock Taking Loop, P1–P5) — 🟢 EXECUTING (Wave 1 done 2026-05-03)
Plans: 8 written, 1 done. Plan 02-01 closed 2026-05-03 — see `.planning/phases/02-mock-taking-loop-p1-p5/02-01-SUMMARY.md`.
Wave map: W1 (01) ✅ → W2 (02, 03) NEXT → W3 (04a) → W4 (04b, 05) → W5 (06) → W6 (07)
- [x] 02-01: Theme + tokens + previews/ scaffold + Wave-1 spike verdicts (Q3 FAIL, Q4 mech-pending-RSS, Q8 FIXED) + 18 script sidecars + ui/documentation.md fill + 3 architectural amendments (D-2.20a, D-2.25a, C-22 line-cap-removal+scope-clarification). Bench approved 1c0148b; doc approved f166ea2.
- [ ] 02-02: P1 Sign Up + signup_flow + api_key_validate + queries_users
- [ ] 02-03: P2 My Classes + Add Class flow (wires shipped factsheet_clean)
- [ ] 02-04a: Backend — DB query upgrades + queries_attempts + build_mock + practice_mock + study_next + REQUIREMENTS amend
- [ ] 02-04b: P3 Class hub UI + lecture_upload (with progress_callback) + class_view wiring + 4 sandboxes
- [ ] 02-05: P4 Take Mock + fragment timer + UPSERT-on-nav + UNIQUE constraint amendment
- [ ] 02-06: P5 Review Mock + summary banner + grading_formula extraction
- [ ] 02-07: E2E AppTest P1→P5 + sidecar audit + final visual sweep
Status: Wave 1 closed. 26 components carry `bench-v1` status in `ui/documentation.md § 5.0`; the next wave's preview gates earn the per-component `production-locked` flips (D-2.25a). Constraints inherited by Wave 2: Plan 02-04 ships visible-button per lecture card (no overlay re-litigation, Q3 FAIL); Plan 02-05 must restore OQ-1 Cards/Quizz variant 3 rationale block in Figma + observe Q4 RSS delta before fragment-timer choice.
Last activity: 2026-05-03 -- Plan 02-01 complete (commits a822de3 → 3936ba5 + plan-metadata commit pending)

Phase 1 progress: [██████████] 100%
Phase 2 progress: [█░░░░░░░░░] 13% (1/8 plans)
Overall (1/5 phases): [██░░░░░░░░] 20%

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Ingestion Spine + Database | 0 | — | — |
| 2. Mock Taking Loop | 0 | — | — |
| 3. Dashboard + Settings | 0 | — | — |
| 4. ML Difficulty Model | 0 | — | — |
| 5. Submission Package | 0 | — | — |

**Recent Trend:**

- Last 5 plans: none yet
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table and `.planning/intel/decisions.md` (36 decisions, 1 LOCKED, 35 recorded).

Recent decisions affecting current work:

- D-01 (Phase 1): Eager MCQ generation at ingestion — predictable upfront cost, instant mock-build UX.
- D-03 (Phase 1): PDF→MD uses `--- PAGE N ---` markers — implementation pending in `pdf_to_md_v3.py`.
- D-06 (Phase 1): SQLite via stdlib `sqlite3` only, no ORM — course-aligned (Chinook+Streamlit demo).
- D-17 (Phase 4): 6-feature difficulty model — 3 locked, 3 dataset-dependent — may need pruning if dataset acquisition (B1) fails.

### Pending Todos

- ~~[Phase 2 Streamlit widget catalog research](todos/pending/2026-05-02-phase-2-streamlit-widget-catalog-research.md)~~ — **CLOSED 2026-05-02 by Plan 02-01 Task 3.** Folded into `02-WIDGETS.md` token table + component spec; the parallel-session bench at `previews/components/_theme_bench/preview.py` is the runnable equivalent. Todo file moved to `.planning/todos/done/`.
- **Q4 RSS-delta observation** (Tiago) — go/no-go gate for Plan 02-05's fragment-timer choice. Sandbox at `previews/spikes/fragment_timer/preview.py`; protocol in `previews/spikes/SPIKES.md § Q4`. Not blocking Wave-2 start.
- **OQ-1 Cards/Quizz variant 3 rationale block** (Tiago) — must be restored in Figma before plan 02-05 starts. Tracked in `02-FIGMA-RESEARCH.md` per side-channel commit `f6da2d0`.

### Blockers/Concerns

- ~~**A1 — Page-ignore category list (Phase 1):** RESOLVED 2026-05-01. 9 structural categories locked in 01-CONTEXT.md as D-1.1; semantic off-topic rule split out as D-1.1b.~~
- **B1 — ML dataset acquisition (Phase 4):** ~200 example MCQs with observed difficulty needed for training. Outreach to HSG teachers gated on Tiago's next Übung session. Fallback: ship 3 locked features only.
- **Plaintext API key (Phase 2):** Confirm with Simon Mayer at next Übung that local plaintext storage is acceptable per HSG rules. Likely yes (local-only app).
- **Calendar pressure:** 13 days to buffer-upload (2026-05-13). Auffahrt collision (2026-05-14 = Ascension Day) means submission MUST land by 2026-05-13.

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Process | **Sidecar code-walkthrough sections.** ~~15 files Phase-1 + 2 Phase-2 sidecars need plain-language walkthroughs.~~ | **CLOSED 2026-05-03 by Plan 02-01 Task 9** | 2026-05-01 |
| Plan-02-05 prereq | **OQ-1 Cards/Quizz variant 3 rationale block** must be restored in Figma before plan 02-05 (P4 Take Mock) starts. | OPEN | 2026-05-03 (per `02-FIGMA-RESEARCH.md`, side-channel `f6da2d0`) |
| Plan-02-05 prereq | **Q4 RSS-delta observation** (5-min memory test of `@st.fragment(run_every="1s")`) — go/no-go gate for fragment-timer choice. | OPEN | 2026-05-03 |
| Plan-02-05 spec | **MCQ-card full geometry** (5 difficulty stars + rationale block + 3 action buttons + restored padding decision) — D-2.23 keeps the 22/20/20/20 padding as a Figma-locked exception until 02-05 owns the whole card. | OPEN | 2026-05-02 |
| Cleanup | **`app/brain/topbar/` rename** — directory misnamed (covers sidebar + top header). | OPEN | 2026-05-02 |

## Session Continuity

Last session: 2026-05-03T15:17:00Z
Stopped at: Plan 02-01 complete. Theme + previews/ scaffold + Wave-1 spike verdicts + 18 sidecars + ui/documentation.md filled + 3 architectural amendments. Bench approved 1c0148b; doc approved f166ea2.
Resume file: .planning/phases/02-mock-taking-loop-p1-p5/02-01-SUMMARY.md (read this first for Wave-2 inheritances), then 02-02-PLAN.md or 02-03-PLAN.md to start Wave 2.

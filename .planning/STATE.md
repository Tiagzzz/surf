---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: planning
stopped_at: Phase 2 CONTEXT amended again — fonts self-hosted (D-2.16 locked, 3 variable WOFF2 in assets/fonts/) + MCQ option redesigned per Figma node 4045:282 (D-2.20 replaced; D-2.23 card container + D-2.24 difficulty stars added). Plan 02-01 needs re-plan.
last_updated: "2026-05-02T14:05:00.000Z"
last_activity: 2026-05-02 -- Phase 2 context second amendment (fonts self-hosted, MCQ redesign from Figma node 4045:282)
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 13
  completed_plans: 5
  percent: 38
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-01)

**Core value:** Pass the grade (≥16/24) AND deliver Idea v1 vision (7-page flow, eager MCQ generation, 6-feature ML difficulty model) by 2026-05-14.
**Current focus:** Phase 2 — Mock Taking Loop (P1–P5) — context amended, plan 02-01 needs re-plan

## Current Position

Phase: 2 (Mock Taking Loop, P1–P5) — 🟡 PLANNING (CONTEXT amended 2026-05-02)
Plans: 8 written, 0 done — plan 02-01 (theme + tokens + previews/ scaffold) needs re-plan to fold in Area 6 branding decisions (D-2.12..D-2.22) from the parallel-session audit. Plans 02-02..02-07 unaffected by this amendment.
Wave map (unchanged): W1 (01) → W2 (02, 03) → W3 (04a) → W4 (04b, 05) → W5 (06) → W6 (07)
- 02-01: Theme + tokens + previews/ scaffold + Wave-1 spikes (Q1–Q4, Q8) + Phase 1 sidecar back-fill
- 02-02: P1 Sign Up + signup_flow + api_key_validate + queries_users
- 02-03: P2 My Classes + Add Class flow (wires shipped factsheet_clean)
- 02-04a: Backend — DB query upgrades + queries_attempts + build_mock + practice_mock + study_next + REQUIREMENTS amend
- 02-04b: P3 Class hub UI + lecture_upload (with progress_callback) + class_view wiring + 4 sandboxes
- 02-05: P4 Take Mock + fragment timer + UPSERT-on-nav + UNIQUE constraint amendment
- 02-06: P5 Review Mock + summary banner + grading_formula extraction
- 02-07: E2E AppTest P1→P5 + sidecar audit + final visual sweep
Status: 02-CONTEXT.md amended (Area 6 Branding & Visual Language — D-2.12..D-2.24). Latest pass (2026-05-02 PM): D-2.16 swapped from Google Fonts @import to self-hosted WOFF2 in assets/fonts/ (3 variable files, ~190 KB); D-2.20 (MCQ option) replaced with the canonical Figma node 4045:282 design — custom 20×20 checkbox glyph, paper-1→paper-0 elevation on select (no accent color during P4), accent-soft/ok-wash only in P5 review, 5px container radius, padding shift on selection. D-2.23 (Take Mock card container) and D-2.24 (5-star difficulty display) added. Plans 02-02..02-07 still untouched by these amendments.
Last activity: 2026-05-02 -- Phase 2 second amendment (fonts self-hosted + MCQ redesign per Figma 4045:282)

Phase 1 progress: [██████████] 100%
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

- [Phase 2 Streamlit widget catalog research](todos/pending/2026-05-02-phase-2-streamlit-widget-catalog-research.md) — researcher step at start of Phase 2 (after UI design locks, before plans 02-xx) producing vanilla green-list + streamlit-extras shortlist; user flagged `stylable_container` as top extras candidate.

### Blockers/Concerns

- ~~**A1 — Page-ignore category list (Phase 1):** RESOLVED 2026-05-01. 9 structural categories locked in 01-CONTEXT.md as D-1.1; semantic off-topic rule split out as D-1.1b.~~
- **B1 — ML dataset acquisition (Phase 4):** ~200 example MCQs with observed difficulty needed for training. Outreach to HSG teachers gated on Tiago's next Übung session. Fallback: ship 3 locked features only.
- **Plaintext API key (Phase 2):** Confirm with Simon Mayer at next Übung that local plaintext storage is acceptable per HSG rules. Likely yes (local-only app).
- **Calendar pressure:** 13 days to buffer-upload (2026-05-13). Auffahrt collision (2026-05-14 = Ascension Day) means submission MUST land by 2026-05-13.

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Process | **Sidecar code-walkthrough sections.** Every sidecar `.md` (15 files in Phase 1) needs a new section walking through the code section-by-section in plain language for non-engineer teammates. Structure TBD — discuss at start of Phase 2, then back-fill Phase 1 sidecars + adopt as end-of-wave routine. May require revising C-22's ≤100-line sidecar cap. | OPEN | 2026-05-01 (Tiago request) |

## Session Continuity

Last session: 2026-05-02T09:43:39.011Z
Stopped at: Phase 2 context gathered (02-CONTEXT.md written, 19 decisions across 5 areas)
Resume file: .planning/phases/02-mock-taking-loop-p1-p5/02-CONTEXT.md

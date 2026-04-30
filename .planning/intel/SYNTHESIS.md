# Synthesis Summary

Single entry point for `gsd-roadmapper`. Read this first; drill into per-type files as needed.

---

## Doc counts (11 ingested)

- **ADR:** 1 — `02_decision_log_v0_to_v1.md`
- **PRD:** 1 — `03_brief_and_grading.md`
- **SPEC:** 1 — `06_code_buckets_spec.md`
- **DOC:** 8 — `00_README.md`, `01_idea_v1_state.md`, `04_lectures_oracle.md`, `05_team_task_briefs.md`, `07_repo_state.md`, `08_figjam_references.md`, `09_open_tbds.md`, `10_communication_rules.md`

## Decisions: 36 extracted (1 locked, 35 recorded)

- **Locked (1):** D-33 (Communication / working-style rules — per `10_communication_rules.md` self-description "these rules ARE locked")
- **Recorded (35):** D-01 through D-32, D-34 through D-36
- **Per-source breakdown:**
  - From 02 (ADR): D-01 through D-12 (timing, fallback, page markers, Swiss grading, ML methodology, SQLite, P4 timer, P7 reset/backup, Streamlit Cloud skip)
  - From 01 (DOC, mined per user direction): D-13 through D-18 (mock pinning, selection logic, 7-page UI, dashboard charts, 6-feature ML, cohort) — also D-19 through D-21 cross-confirmed
  - From 03 (PRD): D-22 through D-26 (deadline, attendance, video length, team size, Contribution Matrix)
  - From 06 (SPEC): D-27 through D-29 (10-bucket layout, lowercase casing, `class_` trailing underscore)
  - From 07 (DOC) + CLAUDE.md: D-30 (Claude wrapper), D-34 (branch policy), D-35 (Python 3.11), D-36 (auth gate)
  - From 02 §B + §F (ADR + DOC): D-31 (session_state course-extension), D-32 (doc standard)
  - Note 01_idea_v1_state.md classified DOC (medium) — its in-document "locked" tags treated as decision content per user instruction; flagged WARNING in INGEST-CONFLICTS.md

## Requirements: 24 extracted

- **Graded requirements (8):** REQ-grade-1-problem · REQ-grade-2-data-api-db · REQ-grade-3-visualisation · REQ-grade-4-user-interactions · REQ-grade-5-ml · REQ-grade-6-doc-source-code · REQ-grade-7-contribution-matrix · REQ-grade-8-video — from 03_brief_and_grading.md (PRD)
- **Page requirements (7):** REQ-p1-signup · REQ-p2-my-classes · REQ-p3-class · REQ-p4-take-mock · REQ-p5-review-mock · REQ-p6-dashboard · REQ-p7-settings — from 01_idea_v1_state.md
- **Pipeline requirements (3):** REQ-pipeline-pdf-md · REQ-pipeline-factsheet-clean (shipped) · REQ-pipeline-lo-extract (TBD) · REQ-pipeline-mcq-generate (TBD) — from 01 + 07 + 09
- **Mechanics (4):** REQ-mock-standard · REQ-mock-practice · REQ-grading-formula · REQ-data-flow — from 01
- **ML (2):** REQ-ml-difficulty-features · REQ-ml-training — from 01 + 05
- **DB (1):** REQ-db-schema — from 01 + 05 + 09
- **Process (3):** REQ-team-split · REQ-sample-data · REQ-ai-citation-block — from 05 + 09 + 03

## Constraints: 20 extracted

- **NFR (10):** C-06 stack · C-07 LLM · C-08 persistence · C-09 video · C-10 deadline · C-11 team size · C-13 grading rubric · C-14 Ruff · C-15 tests · C-16 requirements.txt policy
- **Protocol (5):** C-01 10-bucket org · C-02 pipeline catalog · C-03 cross-bucket deps · C-04 views/ wrappers · C-18 FigJam legend · C-19 FigJam SOP
- **API contract (1):** C-05 standard Claude-call pattern
- **Schema (3):** C-12 Contribution Matrix layout · C-17 .gitignore · C-20 data model (partial — column types/indexes TBD)

## Context topics: 12

Project pitch · re-discussion candidates · shipped vs pending · commit history · Lectures NotebookLM oracle · team task split · FigJam references · open TBDs (build-blocking · dataset/ML · UX/process) · outreach list · grading forecast · vault cleanup · GSD-session framing · reading order

## Conflicts: 0 blockers, 1 variant, 5 auto-resolved

- **0 BLOCKER** — no LOCKED-vs-LOCKED contradictions, no UNKNOWN low-confidence docs, no cycles
- **1 WARNING** — classification mismatch on 01_idea_v1_state.md (DOC tag vs user-stated "most important file" containing locked decisions). Needs Tiago's confirmation before routing.
- **5 INFO** — folder-casing resolution (PEP 8 wins); brief hard-constraints lifted to constraints.md as NFR; ADR Decision Log self-describes as "recorded not immutable" (status applied); 10_communication_rules.md is the only formally locked content; cycle detection clean

## Pointers

- **Conflict report:** `/Users/tiagoreimann/surf/.planning/INGEST-CONFLICTS.md`
- **Decisions:** `/Users/tiagoreimann/surf/.planning/intel/decisions.md`
- **Requirements:** `/Users/tiagoreimann/surf/.planning/intel/requirements.md`
- **Constraints:** `/Users/tiagoreimann/surf/.planning/intel/constraints.md`
- **Context:** `/Users/tiagoreimann/surf/.planning/intel/context.md`
- **Per-doc classifications:** `/Users/tiagoreimann/surf/.planning/intel/classifications/`
- **Source bundle:** `/Users/tiagoreimann/surf/docs/handoff_2026-04-30_gsd_planning/`

## Status

**AWAITING USER** — 1 WARNING (classification mismatch on 01_idea_v1_state.md) requires Tiago's resolution before downstream routing to `gsd-roadmapper`. Recommended path: either reclassify 01 as PRD (or split it PRD+ADR) and re-run synthesis, OR explicitly accept the current synthesis where 01's content is mined into decisions/requirements despite the DOC tag.

# Context (running notes from DOC-classified sources)

> Topic-keyed running notes. Decisions and requirements are extracted to `decisions.md` and `requirements.md`; this file holds the narrative + open-question + process material that doesn't fit those buckets.

---

## Topic: Project pitch and pedagogical bet

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "What Surf is"
- **Note:** Surf is an adaptive Streamlit web app for HSG FCS-BWL students. Student creates a class, uploads class factsheet (Merkblatt) + lecture PDFs, and Surf auto-generates timed multiple-choice mock exams from slide content via Claude. Student takes mocks, reviews per-question results, and sees weakness patterns through a class dashboard.
- **Pedagogical bet:** targeted spaced-repetition over slide-pages + a 6-criteria difficulty model gives a sharper view of where the student is weak than a single accuracy number.

## Topic: Re-discussion candidates (open in GSD session)

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Re-discussion candidates"
- **Note:** All "locked" tags in 01/02/06 are open for re-confirmation in the GSD session. Specifically:
  1. Eager vs. lazy MCQ generation (recorded eager per A1; worth re-confirming given dataset/cost picture).
  2. 6 difficulty features — only 3 locked; dataset-dependent candidates may force re-scoping.
  3. MCQ count per slide for dense pages — Idea v0 said "≥1" with "dense pages may get more". v1 doesn't specify multiplier. Open.
  4. PRACTICE-button-when-LO-fully-mastered UX.
  5. Page-ignore category list — needs fixed list before LO-extractor prompt can be written.
  6. Plaintext API key — Tiago to ask Simon Mayer at next Übung.
  7. Cohort filter for ML training data.

## Topic: Shipped vs pending status (as of 2026-04-30 evening)

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md "What's built"; 01_idea_v1_state.md "What's been shipped"
- **Note:**
  - **Shipped:** repo bootstrapped (https://github.com/Tiagzzz/surf, `main` branch); 10-bucket structure scaffolded; `app/brain/claude_client/claude_client.py` + doc; `app/brain/ingestion/pdf_to_md_v3.py` + doc (TODO: marker injection D-03 not applied — still emits `# Page N`); `app/my_classes/factsheet_clean/` (system prompt + 10-line cleaner + pure-Python renderer + sibling docs); `streamlit_app.py` auth router; thin `views/` placeholders; `tests/test_smoke.py`; `pyproject.toml` (Ruff); `requirements.txt`; `docs/idea_v1.md`; `docs/architecture.md`; `docs/contribution_matrix.md` (template, all TBD); top-level `CLAUDE.md`.
  - **Scaffold only (~30 sub-folders):** signup/, my_classes/{class_create, factsheet_upload, class_list_render, class_delete}, class_/{lecture_upload, lecture_ingest, lo_extract, mcq_generate, mock_standard_launch, study_next_launch}, mock_take/*, mock_review/*, dashboard/*, settings/*, db/*, ml/*, brain/{topbar, session, grading_formula, routing, state_helpers}.
  - **Not in repo (deferred):** `pip freeze` lock; CI workflow `.github/workflows/lint.yml`; sample factsheet/lecture PDFs in `assets/sample_factsheets/`; `.surf/user.sqlite` schema (Niki); filled Contribution Matrix; LICENSE consent from 5 teammates; brand `primaryColor`.

## Topic: Recent commit history (2026-04-30)

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md "Recent commit history"
- **Note:**
  ```
  add61ec Add repo-scoped CLAUDE.md for code-focused session context
  0837adf Add Idea v1 as source-of-truth doc in repo
  258284e Merge pull request #1 from Tiagzzz/feature/factsheet-pipeline-migration
  ea3c405 Convert Obsidian wikilinks to GitHub-friendly relative Markdown links
  d0e31ea Clarify "7 page files" wording in README to match streamlit_app.py docstring
  8ad2304 Add Ruff config + smoke test (review R5 partial)
  6510f5d Migrate factsheet pipeline + structural fixes
  034c8e4 Update team member names in README.md
  9c5c6bc Initial scaffold: 10-bucket structure + Streamlit conventions
  ```

## Topic: Lectures NotebookLM oracle (course-alignment)

- **Source:** docs/handoff_2026-04-30_gsd_planning/04_lectures_oracle.md
- **Note:** Lectures NotebookLM (`6bc919e0-21c9-452e-b203-507f078efa33`) holds 7 lecture PDFs + recordings. Query when:
  - "Is approach Y within course-scope?" — graders wrote the course; non-course methods risk unjustified-complexity penalty.
  - "What library does the course use for X?" — e.g. SQLite vs SQLAlchemy, scikit-learn vs alternatives, plotly vs matplotlib.
  - "Did the course cover Z?" — verify before claiming course-aligned.
  - "What's the recommended pattern for Streamlit Y?" — session state, page nav, st.dialog, st.navigation.
- **Recent course-alignment query verdicts (2026-04-29):**
  - SQLite expected (not just acceptable) — DBMS list slide 8; reference Chinook+Streamlit demo slide 24. → Idea v1 §2; D-06.
  - ORM (SQLAlchemy) NOT taught — use stdlib `sqlite3` only. → Idea v1 §2.
  - Random forest NOT taught — only linear regression [6. ML, 77/78] + decision trees [3. DS, 14]. → D-05.
  - 70/30 train/test is the explicit course standard [6. ML, 55/59]. → D-05.
  - Pairwise scatterplots (not correlation matrix) for feature inspection [6. ML, 63/64]. → D-05.
  - `st.session_state` NOT taught explicitly, BUT Streamlit docs are course-allowed extension [7. Python, slide 25]. → D-31.
  - Auto-refresh patterns NOT taught — total elapsed counter is course-aligned timer mode. → D-07.

## Topic: Provisional team task split (5 people, 4 tracks)

- **Source:** docs/handoff_2026-04-30_gsd_planning/05_team_task_briefs.md
- **Note:** Provisional split validated orally at 2026-04-29 team meeting. Must be contractualised in Contribution Matrix (Req 7) before submission.
  - **Track 0 — Skeleton + AI integration + prompts (cross-cutting): Tiago.** Functional Streamlit app · Claude prompts (factsheet-cleaner ✅ shipped, LO-extraction TBD, question-generator TBD) · cross-task compatibility. No separate brief file — Tiago is the integrator.
  - **Track 1 — Database (SQLite): Nikita.** `schema.sql` + `db.py` + seed + smoke test. Brief: `Database_creation.md`. Open: column types, NOT NULL, indexes. Coordination: schema must align with prompt output shapes.
  - **Track 2 — ML (difficulty predictor): Jojo + Tiago support.** `recommender.pkl` + `feature_extraction.py` + `train_model.py`. Brief: `ML_training_and_build.md`. Two-track methodology (D-05). Blocker: dataset acquisition (B1). 3/6 features still TBD.
  - **Track 3 — Submission video (4 min): Juliette + Cons.** MP4 + script + pre-cached demo. Constraint: NO AI audio. Brief: `Video_Planning.md`.
- **Coordination decisions:**
  - Source of truth: all teammates have read access to **Idea & Progress** NotebookLM. Adding a source goes through Tiago.
  - Brief language: French (team's working language). Code + commits + GitHub artifacts in English.
  - Sync: weekly check-ins; PRs reviewed by ≥1 teammate before merge once contributions start.
- **Open team questions:** per-day roadmap target 2026-05-01; GitHub write-access grant; branch protection on `main` + PR review requirement to be enabled when teammates start contributing.

## Topic: FigJam visual references

- **Source:** docs/handoff_2026-04-30_gsd_planning/08_figjam_references.md
- **Note:** Two live FigJam boards.
  - **Surf Board** (`qoAOJwdMe40MAIyWCVeJlq`, https://www.figma.com/board/qoAOJwdMe40MAIyWCVeJlq/Surf-Board) — pages: App Navigation (P1→P7 graph + topbar), App Engine (PDF→...→dashboard end-to-end flow), Section 1 (per-lecture ingestion detail).
  - **Surf_Off** (`T4I8znq2jeD0SyI4cqPVXu`, https://www.figma.com/board/T4I8znq2jeD0SyI4cqPVXu/Surf_Off) — pages: Legend (locked color/shape system, see C-18), Structure & AI (10-bucket layout, Tier 1 BRAIN/DB/ML on top + Tier 2 page-aligned bottom).
  - Pre-pivot Lucid diagrams archived at `~/CS/CS_Obsidian/CS_EN_VF/Assets/_archive/2026-04-28_pre-Surf-pivot/lucid/` — NOT authoritative.
  - Figma MCP `_get_metadata` is incompatible with FigJam files (verified). Sticky-text transcription requires manual screenshot review.

## Topic: Open TBDs — build-blocking decisions

- **Source:** docs/handoff_2026-04-30_gsd_planning/09_open_tbds.md §A
- **Note:** The build-blocking open items (A1–A5):
  - **A1 Page-ignore category list** — fixed list of slides Claude classifies as ignorable (title slide, ToC, "Thank you", references-only, image-only, blank, institutional disclaimers, etc.). Blocks LO-extractor prompt. Lands at `app/my_classes/factsheet_clean/lo_extractor_system_prompt.md` (future) or `app/class_/lo_extract/`.
  - **A2 LO-extraction prompt + JSON schema** — system prompt + LOs-with-page-ranges + ignore-list output. Blocks all of `class_/lecture_ingest/`. Template: factsheet-cleaner prompt at `app/my_classes/factsheet_clean/factsheet_cleaner_system_prompt.md`.
  - **A3 Question-generator prompt(s)** — system prompt(s) for MCQs from saved slides. Multiple variants for diversity (count + variants TBD). Diversity strategy open: "test recall" vs "test application" vs "test edge case" — variant-selection logic per slide-page TBD. Blocks `class_/mcq_generate/`.
  - **A4 Concrete DB schema** — column types, NOT NULL, indexes, migration strategy (Alembic vs ad-hoc). Blocks all of `db/`. Owner: Niki.
  - **A5 PDF→MD page marker injection** — update `pdf_to_md_v3.py` to emit `--- PAGE N ---` markers instead of `# Page N`. Blocks splitter. ~10 lines of code.

## Topic: Open TBDs — dataset & ML

- **Source:** docs/handoff_2026-04-30_gsd_planning/09_open_tbds.md §B
- **Note:**
  - **B1 Dataset acquisition:** ~200 example MCQs minimum, with observed difficulty (correct-rate or hand label). Approach: outreach to HSG teachers (priority 1) for Canvas quiz answer-rate data + verify public MCQ DB format (priority 2). Status: outreach gated on Tiago's next Übung session.
  - **B2 3/6 difficulty features** still candidates pending dataset (question topic, concept overlap, student skip/confidence behaviour). Pruning method = pairwise scatterplots.
  - **B3 Difficulty scale lock** — options: 1–10 vs 0–1 vs % correct. Depends on dataset shape (B1).
  - **B4 Cohort filter** — example: "18–24 yo undergrads" or "HSG bachelor only". Predicts difficulty for cohort, not personalized.

## Topic: Open TBDs — UX and process

- **Source:** docs/handoff_2026-04-30_gsd_planning/09_open_tbds.md §C + §D
- **Note (UX):**
  - C1 PRACTICE button when LO fully mastered — disable / celebratory empty state / generate fresh.
  - C2 Mock pool fully empty after `unseen ∪ previously-wrong` — recorded fallback = refresh (D-02); UX call to confirm.
  - C3 Coverage chart edge case — when previously-correct slide gets new (regenerated) question, default = stays "covered."
  - C4 Empty / loading / error states per page — all 7 pages, scope TBD.
  - C5 Topbar component spec — shared topbar API (page-name, breadcrumb, settings button placement).
- **Note (process):**
  - D1 Plaintext API key — confirm with Simon Mayer next Übung. Likely yes (local-only app — encryption is theater).
  - D2 Code documentation standard — Google docstrings + Ruff D ruleset working default; final lock during build (D-32).
  - D3 Team task split contractualisation — gate: Contribution Matrix before submission.
  - D4 New per-day roadmap — target 2026-05-01; old 23-day sprint invalidated by 2026-04-28 pivot.
  - D5 Factsheet token cap policy — deferred (no premature optimisation).
  - D6 Full vault redesign with NLM help — standing item, future session.
  - D7 Sample data committed to repo for graders — `assets/sample_factsheets/` currently only `.gitkeep`.
  - D8 LICENSE consent from all 5 teammates.
  - D9 Brand `primaryColor` — currently `#1f77b4` (matplotlib default in `.streamlit/config.toml`).
  - D10 CI workflow `.github/workflows/lint.yml` — add ~2 days before submission.
  - D11 `pip freeze` lock — add ~2 days before submission.

## Topic: Outreach list for next Übung session

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md "Tiago's outreach list"; 03_brief_and_grading.md "Notable open questions"
- **Note:**
  - **Bermeitinger:** confirm sklearn-based ML satisfies Req 5 (likely yes per Lectures query).
  - **Aier:** confirm SQLite + plaintext API key acceptable (likely yes).
  - **HSG teachers (broadly):** Canvas quiz answer-rate data for ML training dataset. Blocking the dataset-acquisition open item.

## Topic: Forecast (per Idea v1 §9)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Forecast"
- **Note:** Floor 17 / realistic 20 / ceiling 22 (out of 24). ≥16 gate cleared on paper. Optional MVP feedback already passed (Wk 7/8 was 16–24 April 2026).

## Topic: Vault & tooling cleanup history

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §G
- **Note:**
  - 2026-04-28 → morning 2026-04-29: 3 NotebookLM notebooks created and seeded; Idea v0 added; old plan artifacts archived to `Assets/_archive/2026-04-28_pre-Surf-pivot/{phase3_reports,lucid,UX_old}/`; CLAUDE.md fully rewritten; `pdf_to_md_v3.py` saved to `scripts/`; 3 team task briefs written + exported to PDF; 2 mindmaps regenerated in Surf Board FigJam.
  - Evening 2026-04-29: Idea v1 added; Decision Log added; `setup/team_tasks/ML_training_and_build.md` rewritten with two-track methodology; ML PDF re-exported. Legacy `setup/` files (17 numbered files + README) archived to `Assets/_archive/2026-04-28_pre-Surf-pivot/setup_old/`. Surviving setup contents: `tiago_guidelines.md` (active) + `briefing_pdf_md/` (PDF→MD outputs) + `team_tasks/`.

## Topic: GSD-session framing (handoff folder rule)

- **Source:** docs/handoff_2026-04-30_gsd_planning/00_README.md (referenced) + 02 + 06 + 10
- **Note:** Per Tiago's explicit framing: in the GSD planning context, "locked" tags in Idea v1 + Decision Log + buckets spec are open for re-discussion. **Communication rules (10) stay locked** — they govern HOW Claude/Codex/the GSD agent communicates with Tiago, not WHAT Surf builds. The synthesizer reflects this: most decisions are `status: recorded`; only the communication-rules block (D-33) and the brief-derived hard constraints (D-21 to D-26, C-06 to C-12) are `locked`.

## Topic: Reading order for the handoff bundle

- **Source:** docs/handoff_2026-04-30_gsd_planning/00_README.md (index)
- **Note:** 11-doc bundle, snapshot 2026-04-30:
  1. 00_README — index (this).
  2. 01_idea_v1_state.md — synthesis of canonical state (THE most important file per user).
  3. 02_decision_log_v0_to_v1.md — v0→v1 deltas.
  4. 03_brief_and_grading.md — non-negotiable constraints + 8 graded reqs.
  5. 04_lectures_oracle.md — when/how to query Lectures NotebookLM.
  6. 05_team_task_briefs.md — 5-person split.
  7. 06_code_buckets_spec.md — 10-bucket organization.
  8. 07_repo_state.md — repo snapshot.
  9. 08_figjam_references.md — FigJam URLs.
  10. 09_open_tbds.md — consolidated TBDs.
  11. 10_communication_rules.md — locked working-style rules.
- **Cross-refs to repo:** `~/surf/docs/idea_v1.md`, `~/surf/CLAUDE.md`, `~/CS/CS_Obsidian/CS_EN_VF/work_log/`.

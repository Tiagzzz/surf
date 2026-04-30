# Requirements (synthesized from PRD + DOC product-scope content)

> Synthesizer note: only `03_brief_and_grading.md` is classified PRD. The 8 graded requirements are extracted from there. Page-level + product-feature requirements are mined from `01_idea_v1_state.md` (DOC, but per user direction is the most-important file and contains the product scope).

---

## Graded requirements (Brief & Grading — non-negotiable, scored 0–3, max 24, ≥16 = pass)

> **`locked: true`** — All REQ-grade-1 through REQ-grade-8 below are locked per teacher's official brief. Cannot be removed, weakened, or marked optional. Implementation details (acceptance, scope) remain open for refinement during phase planning.

### REQ-grade-1-problem — Clearly formulated problem
- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "8 mandatory graded requirements" #1
- **Description:** Surf must clearly articulate the problem it solves.
- **Acceptance (Surf coverage per Idea v1):** "Adaptive HSG Study Companion" pitch + per-class threshold framing in the report and video.
- **Scope:** report, video, README

### REQ-grade-2-data-api-db — Uses data via API and/or DB
- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md #2
- **Description:** App must consume data via API and/or persistent DB.
- **Acceptance:** Anthropic Claude API for content generation + local SQLite for persistence (Chinook-pattern, course-aligned).
- **Scope:** brain/claude_client + db/

### REQ-grade-3-visualisation — Useful data visualisation
- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md #3
- **Description:** App must include useful data visualisation.
- **Acceptance:** P6 dashboard with line + 2 bars + radar (4 charts).
- **Scope:** dashboard/ bucket

### REQ-grade-4-user-interactions — User interactions
- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md #4
- **Description:** App must support meaningful user interactions.
- **Acceptance:** 7-page flow (P1 signup → P2 my classes → P3 class → P4 take mock → P5 review mock → P6 dashboard → P7 settings) with all per-page interactions wired.
- **Scope:** all 7 page buckets

### REQ-grade-5-ml — Implements machine learning
- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md #5; cross-ref D-05
- **Description:** App must implement machine learning, course-aligned.
- **Acceptance (graded baseline):** linear regression + 70/30 split + pairwise scatterplots + MSE/MAE/R². Library scikit-learn. Every choice citable to a course slide.
- **Acceptance (sensitivity bonus, ungraded):** random forest + correlation matrix + 60/40 alt split. Cite Dirk Reimann externally.
- **Scope:** ml/ bucket

### REQ-grade-6-doc-source-code — Documented source code
- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md #6
- **Description:** Source code must be documented.
- **Acceptance (working default):** Google-style docstrings + Ruff D ruleset. Final standard locks during build.
- **Scope:** all Python files

### REQ-grade-7-contribution-matrix — Individual contributions documented
- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md #7; D-26
- **Description:** Each team member's contribution must be documented in the Contribution Matrix.
- **Acceptance:** Layout copies brief slide 6 verbatim (TM rows × {Project Mgmt, Konzept, Präsentation, Dokumentation, Funktion #1–N, Testing} columns). Filled by all 5 team members. Currently template at `docs/contribution_matrix.md` — all TBD.
- **Scope:** docs/contribution_matrix.md

### REQ-grade-8-video — 4-minute video, no AI audio
- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md #8; D-21; D-24
- **Description:** Submission video must be ≤4 min and contain NO AI-generated audio.
- **Acceptance:** Human voiceover · multi-take editing · pre-cached demo path (so live Claude latency doesn't break 4-min budget) · AI-citation closing card · Auffahrt-buffer upload (2026-05-13).
- **Scope:** Juliette + Cons (Track 3)

---

## Page / feature requirements (Idea v1 product scope)

### REQ-p1-signup — P1 Sign Up
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "7-page UI" P1
- **Description:** First-run page; collect username + Anthropic API key (validated).
- **Acceptance:** Username persisted; API key validated against Anthropic before save; subsequent app launches skip P1 if `~/.surf/user.sqlite` exists (D-36).
- **Scope:** signup/ bucket

### REQ-p2-my-classes — P2 My Classes
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md P2
- **Description:** Class list page with cards carousel + Add Class flow.
- **Acceptance:** List existing classes as cards · "Add Class" launches factsheet PDF upload → factsheet-cleaner Claude call → user reviews cleaned JSON → save to DB.
- **Scope:** my_classes/ bucket; reuses `factsheet_clean/` (shipped)

### REQ-p3-class — P3 Class
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md P3
- **Description:** Per-class hub: lecture upload + Build Mock + Past Attempts + Study Next + open Dashboard.
- **Acceptance:** Lecture PDF upload triggers full ingestion pipeline (PDF→MD with `--- PAGE N ---` markers → LO-extraction → splitter → eager MCQ generation per saved slide → DB writes). Build Mock launches P4. Study Next launches PRACTICE mock. Past Attempts shows prior mock summaries. Dashboard link → P6.
- **Scope:** class_/ bucket

### REQ-p4-take-mock — P4 Take Mock
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md P4; D-07; D-13
- **Description:** Mock-taking page.
- **Acceptance:** One MCQ rendered at a time · total-elapsed timer (D-07) · SKIP / NEXT actions only · mock pinned in `st.session_state` (D-13) · answers captured per question · attempts persisted to DB on completion.
- **Scope:** mock_take/ bucket

### REQ-p5-review-mock — P5 Review Mock
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md P5
- **Description:** Post-submit per-question review.
- **Acceptance:** Per-question result (correct/wrong) · Claude rationale display · 6 difficulty scores per question shown alongside mistake explanation.
- **Scope:** mock_review/ bucket

### REQ-p6-dashboard — P6 Class Dashboard
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md P6; D-16
- **Description:** Class-level analytics dashboard.
- **Acceptance:** 4 charts — line (score evolution) + bar (avg per lecture) + bar (completion) + radar (6-criteria strengths/weaknesses).
- **Scope:** dashboard/ bucket

### REQ-p7-settings — P7 Settings
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md P7; D-08; D-09
- **Description:** Account/data management page.
- **Acceptance:** Username change · API key rotation · Reset (drop ALL tables, gated by `st.dialog` + typed-name confirm — D-08) · Backup (download raw `.sqlite` file — D-09).
- **Scope:** settings/ bucket

### REQ-pipeline-pdf-md — PDF→MD ingestion
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Data flow"; 07_repo_state.md
- **Description:** Convert PDF lecture to Markdown with deterministic page boundaries.
- **Acceptance:** `pdf_to_md_v3.py` emits `--- PAGE N ---` markers (D-03 — currently still emits `# Page N`, TODO). Uses pdfplumber + Tesseract OCR fallback.
- **Scope:** brain/ingestion/

### REQ-pipeline-factsheet-clean — Factsheet cleaning
- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md (shipped); 01_idea_v1_state.md
- **Description:** Cleaned factsheet JSON for the user's class context.
- **Acceptance:** Claude factsheet-cleaner system prompt + 10-line wrapper + pure-Python renderer (JSON → student-facing Markdown). Auto-hide empty subsections; bullet-formatted Assessment Components. **Status:** shipped 2026-04-30.
- **Scope:** my_classes/factsheet_clean/

### REQ-pipeline-lo-extract — LO extraction (TBD)
- **Source:** docs/handoff_2026-04-30_gsd_planning/09_open_tbds.md A1+A2; 01_idea_v1_state.md
- **Description:** Extract Learning Objectives + page-ignore list from lecture MD.
- **Acceptance:** System prompt + JSON schema (LOs with page ranges + ignore list). Page-ignore category list = fixed (TBD). Currently NOT shipped.
- **Scope:** class_/lo_extract/ (or my_classes/factsheet_clean/lo_extractor_system_prompt.md)

### REQ-pipeline-mcq-generate — MCQ generation (TBD)
- **Source:** docs/handoff_2026-04-30_gsd_planning/09_open_tbds.md A3; 01_idea_v1_state.md; D-01
- **Description:** Generate ≥1 MCQ per saved slide at ingestion time.
- **Acceptance:** System prompt(s) — multiple variants for diversity (count + variant strategy TBD: recall vs application vs edge-case). Eager generation (D-01). Output: question text + 4 options + correct answer + Claude rationale + 6 difficulty features. Currently NOT shipped.
- **Scope:** class_/mcq_generate/

### REQ-mock-standard — Standard mock
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Mock mechanics"; D-11
- **Description:** Build a standard mock exam.
- **Acceptance:** User picks N lectures on P3 → mock has `5 × N` questions · selection logic = unseen → previously-wrong → refresh (D-14, D-02).
- **Scope:** class_/mock_standard_launch/

### REQ-mock-practice — PRACTICE mock
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Mock mechanics"; D-12
- **Description:** Build a PRACTICE mock for a chosen LO.
- **Acceptance:** User picks one LO → 1 question per slide of that LO · same selection priority as standard mock.
- **Scope:** class_/study_next_launch/

### REQ-grading-formula — Swiss linear grading
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Grading scale"; D-04
- **Description:** Compute grade from correct answers using Swiss linear formula.
- **Acceptance:** `note = 5 × (correct / max) + 1`. Per-class "% needed for a 4" slider exposes anchor (informational only — does not change formula).
- **Scope:** brain/grading_formula/

### REQ-ml-difficulty-features — 6-feature difficulty model
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "ML approach"; D-17
- **Description:** Compute 6 difficulty features per question.
- **Acceptance (locked features):** word count · language complexity (readability) · distractor similarity.
- **Acceptance (candidates pending dataset):** question topic · concept overlap · student skip/confidence behaviour.
- **Acceptance (pruning):** pairwise scatterplots.
- **Scope:** ml/radar_features/, ml/inference_per_question/

### REQ-ml-training — ML training pipeline
- **Source:** docs/handoff_2026-04-30_gsd_planning/05_team_task_briefs.md Task 2; D-05
- **Description:** Train both tracks of the difficulty model.
- **Acceptance:** `feature_extraction.py` (computes the 6 features) · `train_model.py` (trains both tracks, saves artifacts) · `recommender.pkl` (loaded at inference). Linear regression primary; random forest sensitivity. **Blocker:** dataset acquisition (B1).
- **Scope:** ml/training_pipeline/, ml/dataset_labels/, ml/model_artifact/

### REQ-db-schema — SQLite schema
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Data model"; 05_team_task_briefs.md Task 1; 09_open_tbds.md A4; D-06
- **Description:** Define and ship the SQLite schema.
- **Acceptance:** Tables `users`, `classes`, `lectures`, `slide_pages`, `questions`, `attempts`, `attempt_answers`, plus `topics` and `learning_objectives` FK'd in. Stdlib `sqlite3` (D-06). Deliverables: `schema.sql` (DDL with NOT NULL + indexes), `db.py` (query wrappers), seed script, smoke test. Column types, NOT NULL, indexes still TBD.
- **Scope:** db/ bucket; owner Nikita

### REQ-data-flow — End-to-end data flow
- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Data flow shape"
- **Description:** Single canonical pipeline shape.
- **Acceptance:** `PDF factsheet → factsheet-cleaner → JSON → user review → DB.classes.factsheet`; `PDF lecture → pdf_to_md_v3 (--- PAGE N --- markers) → LO-extraction (JSON: LOs + ignore-list) → splitter (chunks by page) → EAGER MCQ generation → DB.slide_pages + DB.questions (with 6 difficulty features each)`.
- **Scope:** cross-bucket (brain/ingestion → my_classes → class_ → db)

### REQ-team-split — Team task split
- **Source:** docs/handoff_2026-04-30_gsd_planning/05_team_task_briefs.md
- **Description:** 5-person split across 4 tracks.
- **Acceptance:** Track 0 Skeleton + AI + prompts (Tiago) · Track 1 Database (Nikita) · Track 2 ML (Jojo + Tiago support) · Track 3 Video (Juliette + Cons). Provisional, must be contractualised in Contribution Matrix before submission.
- **Scope:** team / process

### REQ-sample-data — Grader sample data
- **Source:** docs/handoff_2026-04-30_gsd_planning/09_open_tbds.md D7; 07_repo_state.md
- **Description:** Commit sample factsheet PDF + sample lecture PDF to repo so graders can clone and run end-to-end.
- **Acceptance:** Files land in `assets/sample_factsheets/` (currently only `.gitkeep`).
- **Scope:** assets/

### REQ-ai-citation-block — AI-citation per HSG rules
- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §B; 03_brief_and_grading.md "Hard constraints" (AI references row)
- **Description:** Cite AI-generated content per HSG AI rules.
- **Acceptance:** AI-citation block in README + closing card of submission video. Reference URL: https://universitaetstgallen.sharepoint.com/sites/PruefungenDE/SitePages/Arbeiten-mit-KI.aspx.
- **Scope:** README.md, video closing card

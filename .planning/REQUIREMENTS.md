# Requirements: Surf

**Defined:** 2026-05-01
**Core Value:** Pass the grade (≥16/24) AND deliver Idea v1 vision (7-page flow, eager MCQ generation, 6-feature ML difficulty model) by 2026-05-14.

> Source-of-truth derivation: requirements synthesized from `.planning/intel/requirements.md` (24 requirements). LOCKED flags propagate from teacher's brief (C-06..C-13) and `intel/decisions.md`.

## v1 Requirements

### Graded — Teacher's Brief (LOCKED — non-negotiable; cannot be removed, weakened, or marked optional)

- [ ] **GRADE-01** (REQ-grade-1-problem): Surf clearly articulates the problem it solves — "Adaptive HSG Study Companion" pitch + per-class threshold framing in report, video, README.
- [ ] **GRADE-02** (REQ-grade-2-data-api-db): App consumes data via API and/or persistent DB — Anthropic Claude API + local SQLite.
- [ ] **GRADE-03** (REQ-grade-3-visualisation): Useful data visualisation — P6 dashboard with line + 2 bars + radar (4 charts).
- [ ] **GRADE-04** (REQ-grade-4-user-interactions): Meaningful user interactions — full 7-page flow wired with all per-page interactions.
- [ ] **GRADE-05** (REQ-grade-5-ml): Course-aligned ML — sklearn linear regression, 70/30 split, pairwise scatterplots, MSE/MAE/R². Bonus sensitivity track: random forest + correlation matrix + 60/40.
- [ ] **GRADE-06** (REQ-grade-6-doc-source-code): Documented source code — Google-style docstrings + Ruff D ruleset.
- [ ] **GRADE-07** (REQ-grade-7-contribution-matrix): Contribution Matrix filled by all 5 team members; layout copies brief slide 6 verbatim.
- [ ] **GRADE-08** (REQ-grade-8-video): MP4 ≤4 min, NO AI audio, human voiceover, AI-citation closing card.

### Pages — 7-page Streamlit flow

- [ ] **PAGE-01** (REQ-p1-signup): Sign Up page — collect username + Anthropic API key (validated against Anthropic before save). Subsequent launches skip P1 if `~/.surf/user.sqlite` exists.
- [ ] **PAGE-02** (REQ-p2-my-classes): My Classes page — class list cards carousel + Add Class flow (factsheet PDF upload → cleaner → user reviews JSON → save).
- [ ] **PAGE-03** (REQ-p3-class): Per-class hub — lecture upload + Build Mock + Past Attempts + Study Next + open Dashboard.
- [ ] **PAGE-04** (REQ-p4-take-mock): Take Mock — one MCQ at a time, total-elapsed timer, SKIP/NEXT actions, mock pinned in `st.session_state`, answers persisted on completion.
- [ ] **PAGE-05** (REQ-p5-review-mock): Review Mock — per-question result + Claude rationale + 6 difficulty scores per question.
- [ ] **PAGE-06** (REQ-p6-dashboard): Class Dashboard — 4 charts (line score evolution, bar avg per lecture, bar completion, radar 6-criteria).
- [ ] **PAGE-07** (REQ-p7-settings): Settings — username change, API key rotation, Reset (full wipe gated by typed-name confirm), Backup (raw `.sqlite` download).

### Pipelines — Ingestion

- [ ] **PIPE-01** (REQ-pipeline-pdf-md): PDF→MD with `--- PAGE N ---` markers (currently emits `# Page N`; update needed). Uses pdfplumber + Tesseract OCR fallback.
- [ ] **PIPE-02** (REQ-pipeline-factsheet-clean): Factsheet cleaning — Claude system prompt + 10-line wrapper + pure-Python renderer. **Status: shipped 2026-04-30** (validate end-to-end in P2 flow).
- [ ] **PIPE-03** (REQ-pipeline-lo-extract): LO extraction — system prompt + JSON schema (LOs with page ranges + page-ignore list). **Page-ignore category list TBD** (build-blocking A1).
- [ ] **PIPE-04** (REQ-pipeline-mcq-generate): MCQ generation — system prompt(s) for ≥1 MCQ per saved slide, eager at ingestion. Output: question + 4 options + correct answer + Claude rationale + 6 difficulty features. **Variant strategy TBD** (recall vs application vs edge-case).

### Mechanics — Mocks + grading

- [ ] **MECH-01** (REQ-mock-standard): Standard mock — user picks N lectures → mock has 5 × N questions, selection logic = unseen → previously-wrong → refresh.
- [ ] **MECH-02** (REQ-mock-practice): PRACTICE mock — user picks one LO → 1 question per slide of that LO, same selection priority.
- [ ] **MECH-03** (REQ-grading-formula): Swiss linear grading `note = 5 × (correct / max) + 1`; per-class "% needed for a 4" slider exposes anchor (informational only).
- [ ] **MECH-04** (REQ-data-flow): End-to-end canonical data flow — `PDF factsheet → cleaner → JSON → user review → DB.classes.factsheet`; `PDF lecture → pdf_to_md_v3 → LO-extraction → splitter → eager MCQ generation → DB.slide_pages + DB.questions (with 6 difficulty features)`.

### ML — Difficulty model

- [ ] **ML-01** (REQ-ml-difficulty-features): Compute 6 difficulty features per question. **Locked features (3):** word count, language complexity (readability), distractor similarity. **Pending dataset (3):** question topic, concept overlap, student skip/confidence behaviour. Pruning method = pairwise scatterplots.
- [ ] **ML-02** (REQ-ml-training): Training pipeline — `feature_extraction.py`, `train_model.py`, `recommender.pkl`. Linear regression primary; random forest sensitivity. **Blocker:** dataset acquisition (B1).

### Database

- [ ] **DB-01** (REQ-db-schema): SQLite schema — tables `users`, `classes`, `lectures`, `slide_pages`, `questions`, `attempts`, `attempt_answers`, plus `topics` and `learning_objectives` FK'd in. Stdlib `sqlite3`. Deliverables: `schema.sql` (DDL + NOT NULL + indexes), `db.py` (query wrappers), seed script, smoke test. **Column types/NOT NULL/indexes TBD** (build-blocking A4).

### Process — Submission package

- [ ] **PROC-01** (REQ-team-split): 5-person split across 4 tracks contractualised in Contribution Matrix before submission.
- [ ] **PROC-02** (REQ-sample-data): Sample factsheet PDF + sample lecture PDF committed to `assets/sample_factsheets/` so graders can clone and run end-to-end.
- [ ] **PROC-03** (REQ-ai-citation-block): AI-citation block in README + closing card of submission video, per HSG AI rules (https://universitaetstgallen.sharepoint.com/sites/PruefungenDE/SitePages/Arbeiten-mit-KI.aspx).

## v2 Requirements

Deferred to post-submission (if time permits or future iteration).

### Deployment

- **DEPLOY-01**: Streamlit Cloud deployment (skipped per D-10 — not graded).

### UX Polish

- **UX-01**: Empty / loading / error states for all 7 pages.
- **UX-02**: Topbar component spec (page-name, breadcrumb, settings button placement).
- **UX-03**: PRACTICE-button-when-LO-fully-mastered UX (disable / celebratory empty state / generate fresh).

### CI

- **CI-01**: GitHub Actions lint workflow (`.github/workflows/lint.yml`) — add ~2 days before submission.

## Out of Scope

| Feature | Reason |
|---------|--------|
| OpenAI / non-Anthropic LLM | Project decision (D-19); Claude-only |
| SQLAlchemy / any ORM | Not taught in course; stdlib `sqlite3` only (D-06, C-08) |
| Flask / FastAPI / Django | Brief slide 3 mandates Streamlit only (C-06) |
| AI-generated audio in video | Brief slide 4 hard constraint (C-09, D-21) |
| Per-question countdown timer | Auto-refresh not taught; total-elapsed chosen (D-07) |
| Per-question countdown / total-mock countdown | Same — D-07 |
| Soft reset (preserve content) | Full wipe chosen for clearer semantics (D-08) |
| JSON DB backup format | Raw `.sqlite` chosen for portability (D-09) |
| Personalized difficulty prediction | Cohort-level only (D-18) |
| Encrypted API key storage | Local-only app; plaintext likely fine (pending Simon Mayer) |
| Real-time multi-user features | Local-only single-user app |
| Mobile app | Web-first only; out of course scope |

## Traceability

Coverage map: every v1 requirement → exactly one phase.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GRADE-01 | Phase 5 | Pending |
| GRADE-02 | Phase 1 | Pending |
| GRADE-03 | Phase 3 | Pending |
| GRADE-04 | Phase 2 | Pending |
| GRADE-05 | Phase 4 | Pending |
| GRADE-06 | Phase 5 | Pending |
| GRADE-07 | Phase 5 | Pending |
| GRADE-08 | Phase 5 | Pending |
| PAGE-01 | Phase 2 | Pending |
| PAGE-02 | Phase 2 | Pending |
| PAGE-03 | Phase 2 | Pending |
| PAGE-04 | Phase 2 | Pending |
| PAGE-05 | Phase 2 | Pending |
| PAGE-06 | Phase 3 | Pending |
| PAGE-07 | Phase 3 | Pending |
| PIPE-01 | Phase 1 | Pending |
| PIPE-02 | Phase 2 | Shipped (validate in P2) |
| PIPE-03 | Phase 1 | Pending |
| PIPE-04 | Phase 1 | Pending |
| MECH-01 | Phase 2 | Pending |
| MECH-02 | Phase 2 | Pending |
| MECH-03 | Phase 2 | Pending |
| MECH-04 | Phase 1 | Pending |
| ML-01 | Phase 4 | Pending |
| ML-02 | Phase 4 | Pending |
| DB-01 | Phase 1 | Pending |
| PROC-01 | Phase 5 | Pending |
| PROC-02 | Phase 5 | Pending |
| PROC-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-01*
*Last updated: 2026-05-01 after GSD roadmap creation*

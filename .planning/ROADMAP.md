# Roadmap: Surf

## Overview

Surf must ship by 2026-05-13 (buffer-upload; deadline 2026-05-14 23:59 Europe/Zurich). With ~13 days, the roadmap orders work risk-down: **first close the lecture-ingestion spine** (PDF→MD→LO→MCQ→DB) so every downstream feature has real data to work on; **then wire the mock-taking loop** end-to-end (P1–P5 + grading) so the app is demonstrable; **then add the dashboard + settings** (P6–P7) which complete the user-visible 7-page flow; **then ship the ML difficulty model** (graded Req 5) on top of accumulated mock data; **finally lock the submission package** (video, Contribution Matrix, sample data, docs polish, AI-citation block, requirements freeze).

The video track (Juliette + Cons) runs in parallel with code from Phase 2 onward — pre-cached demo paths get baked in as features land. Already-shipped pieces (`claude_client`, `pdf_to_md_v3`, `factsheet_clean`) are leveraged but validated end-to-end inside their owning phase.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Ingestion Spine + Database** - Close PDF→MD→LO→MCQ→DB pipeline; ship SQLite schema; everything downstream gets real data.
- [ ] **Phase 2: Mock Taking Loop (P1–P5)** - User can sign up, create a class, ingest a lecture, build a mock, take it, and see results with rationales.
- [ ] **Phase 3: Dashboard + Settings (P6–P7)** - User can see analytics across attempts and manage their account/data.
- [ ] **Phase 4: ML Difficulty Model** - Train and integrate the 6-feature sklearn model (linear-regression primary + random-forest sensitivity); per-question scores feed P5 + radar chart.
- [ ] **Phase 5: Submission Package** - Video, Contribution Matrix, sample data, AI-citation, docstrings polish, `requirements.txt` lock, README — buffer-upload by 2026-05-13.

## Phase Details

### Phase 1: Ingestion Spine + Database
**Goal**: A lecture PDF can be ingested end-to-end into the SQLite database with extracted LOs, page-split slides, and eagerly-generated MCQs (each with placeholder difficulty features) — no UI required to verify.
**Depends on**: Nothing (first phase)
**Requirements**: PIPE-01, PIPE-03, PIPE-04, DB-01, MECH-04, GRADE-02
**Success Criteria** (what must be TRUE):
  1. Running the ingestion pipeline on a sample lecture PDF writes to the user's SQLite DB rows in `lectures`, `slide_pages`, `questions`, and `learning_objectives`, all queryable via `db.py` wrappers.
  2. `pdf_to_md_v3.py` emits `--- PAGE N ---` markers (no longer `# Page N`); the splitter regex-splits on them deterministically.
  3. The LO-extractor Claude call returns valid JSON (LOs with page ranges + page-ignore list) against a fixed page-ignore category list.
  4. The MCQ-generator Claude call produces ≥1 MCQ per saved (non-ignored) slide, each with question text + 4 options + correct answer + Claude rationale + 6 difficulty-feature placeholders.
  5. The smoke test (`pytest -q`) passes and exercises one ingestion of a sample lecture PDF end-to-end into a fresh SQLite file.
**Plans**: 5 (4 complete: 01-01 SQLite spine, 01-02 PDF markers + page_splitter, 01-03 LO extractor, 01-04 MCQ generator — Waves 1+2 done)

### Phase 2: Mock Taking Loop (P1–P5)
**Goal**: A first-time user can sign up, create a class from a factsheet PDF, see ingested lectures, build a standard or PRACTICE mock, take it under a timer, and review per-question results with Claude rationales.
**Depends on**: Phase 1
**Requirements**: PAGE-01, PAGE-02, PAGE-03, PAGE-04, PAGE-05, PIPE-02, MECH-01, MECH-02, MECH-03, GRADE-04
**Success Criteria** (what must be TRUE):
  1. First launch routes the user through P1 Sign Up (username + Anthropic API key validated against Anthropic before save); subsequent launches skip P1 because `~/.surf/user.sqlite` exists.
  2. From P2 My Classes, the user can launch the Add Class flow, upload a factsheet PDF, review the cleaned JSON, and save the class — the class then appears as a card.
  3. From P3 Class, the user can upload a lecture PDF (triggering Phase-1 ingestion live), pick N lectures, and launch a Standard mock of `5 × N` questions; or pick one LO and launch a PRACTICE mock of 1-question-per-slide.
  4. P4 renders one MCQ at a time with a total-elapsed timer, SKIP/NEXT actions, mock pinned in `st.session_state`, and persists the attempt + answers to SQLite on completion.
  5. P5 shows each question's correctness, the Claude rationale, the question's 6 difficulty scores, and the Swiss-formula final note (`5 × correct/max + 1`).
**Plans**: TBD
**UI hint**: yes

### Phase 3: Dashboard + Settings (P6–P7)
**Goal**: The user sees class-level analytics across all attempts (4 charts) and can manage their account and data.
**Depends on**: Phase 2
**Requirements**: PAGE-06, PAGE-07, GRADE-03
**Success Criteria** (what must be TRUE):
  1. P6 Dashboard renders 4 charts for the selected class: line (score evolution across attempts), bar (avg per lecture), bar (per-lecture completion %), radar (6-criteria strengths/weaknesses).
  2. P7 Settings allows username change and Anthropic API key rotation, both persisting to SQLite.
  3. P7 Settings → Reset drops all tables, gated by a `st.dialog` typed-name confirm.
  4. P7 Settings → Backup downloads the raw `~/.surf/user.sqlite` file, openable in any SQLite viewer.
**Plans**: TBD
**UI hint**: yes

### Phase 4: ML Difficulty Model
**Goal**: A trained sklearn model scores every saved question with the 6 difficulty features; scores feed P5's per-question display and P6's radar chart.
**Depends on**: Phase 3 (mock attempts data + radar chart consumer in place)
**Requirements**: ML-01, ML-02, GRADE-05
**Success Criteria** (what must be TRUE):
  1. `feature_extraction.py` computes all 6 difficulty features (3 locked: word count, readability, distractor similarity; 3 candidates resolved against acquired dataset or pruned via pairwise scatterplots).
  2. `train_model.py` trains both tracks (linear regression primary on 70/30 split with MSE/MAE/R²; random forest sensitivity on 60/40 with correlation matrix) and saves a `recommender.pkl` artifact, with every methodology choice citable to a course slide.
  3. At ingestion (or via a one-shot rescore script), every row in `questions` gets a 6-feature vector + a final difficulty score persisted in SQLite.
  4. P5 review and P6 radar chart render real (not placeholder) difficulty scores from the trained model.
  5. Training metrics (MSE/MAE/R²) and pairwise scatterplots are saved as artifacts under `ml/` for inclusion in the report and video.
**Plans**: TBD

### Phase 5: Submission Package
**Goal**: The grader can clone the repo, run the app on sample data, watch a 4-minute MP4 explaining what Surf does, see a filled Contribution Matrix, and award the 8 graded points.
**Depends on**: Phase 4
**Requirements**: GRADE-01, GRADE-06, GRADE-07, GRADE-08, PROC-01, PROC-02, PROC-03
**Success Criteria** (what must be TRUE):
  1. `assets/sample_factsheets/` contains a sample factsheet PDF and a sample lecture PDF; cloning the repo and running `streamlit run streamlit_app.py` lets a grader complete the full demo flow on those samples.
  2. The submission MP4 is ≤4 minutes, contains no AI-generated audio, has human voiceover, uses a pre-cached demo path, and ends with the AI-citation closing card; uploaded to Canvas by 2026-05-13 buffer-upload.
  3. `docs/contribution_matrix.md` is filled by all 5 team members (TM rows × {Project Mgmt, Konzept, Präsentation, Dokumentation, Funktion #1–N, Testing} columns) with Hauptbeitragende/r marked.
  4. README contains the problem statement (Adaptive HSG Study Companion) and AI-citation block; all source files have Google-style docstrings; `ruff check .` passes with the D ruleset enabled.
  5. `requirements.txt` is `pip freeze`-locked; the smoke test passes on a clean clone; tag/commit hash recorded for the submission.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Ingestion Spine + Database | 4/5 | In progress | - |
| 2. Mock Taking Loop (P1–P5) | 0/TBD | Not started | - |
| 3. Dashboard + Settings (P6–P7) | 0/TBD | Not started | - |
| 4. ML Difficulty Model | 0/TBD | Not started | - |
| 5. Submission Package | 0/TBD | Not started | - |

## Parallel Track Notes

The roadmap is a serial critical path for the *code* track. Two side tracks run in parallel and don't gate phase transitions:

- **Track 3 (Video — Juliette + Cons)**: starts capturing material as soon as Phase 2 produces a working mock-taking loop. Final cut + AI-citation closing card lands inside Phase 5.
- **Dataset acquisition (Tiago outreach)**: blocks Phase 4. Outreach starts immediately (next Übung session) and runs in parallel with Phases 1–3.

If dataset acquisition fails by mid-Phase 3, fall back to: ship the 3 locked features only, prune the other 3 with pairwise scatterplots and document the prune in the report. This preserves Req 5 (graded) at the cost of the bonus rigor signal.

---
title: "Idea v1 — Surf"
status: ACTIVE
captured: 2026-04-29
supersedes: Idea v0
source_of_truth: true
notebook: "Idea & Progress (https://notebooklm.google.com/notebook/3e02fa3d-8ce2-4a6d-9da7-ac974e32452f)"
notebook_source_id: a815d393-1f9f-4ac1-841c-09f5c23bc285
delta_log: "Decision Log 2026-04-29 — Surf (delta v0 → v1)"
---

# Idea v1 — Surf

**Status:** ACTIVE — current canonical state of Surf, supersedes Idea v0. Idea v0 stays in the notebook as the historical anchor of the 2026-04-28 pivot day.

**Captured:** 2026-04-29 (evening of pivot-day-plus-one)

**Provenance:** Idea v0 architectural baseline + 4 architectural answers (eager generation · refresh fallback · page markers · Swiss linear) + 4 smaller answers (Streamlit Cloud skip · total-elapsed timer · drop teammate repo · P7 reset/backup) + Dirk-meeting ML scope (2026-04-29) + SQLite course-alignment query + ML methodology query (Option B locked) + Streamlit timer query.

This document represents the locked state of Surf going into the build week. Future changes land as Idea v2, v3, etc. Decisions taken between Idea versions go in `Decision Log YYYY-MM-DD — <topic>` notes — see `Decision Log 2026-04-29 — Surf` for the delta narrative from v0.

---

## 1. Problem & vision (unchanged from v0)

HSG students in FCS-BWL (Bachelor "Computer Science for Business", FS 2026) need a way to actively rehearse their lecture material before the final, beyond passively re-reading slides. **Surf** is an adaptive Streamlit web app that lets a student create classes, upload lecture PDFs and a class factsheet, generate timed multiple-choice mock exams from the slide content via Claude, take and review them, and see weakness patterns through a class dashboard. The pedagogical bet: targeted spaced-repetition over slide-pages, combined with a difficulty model that scores generated questions on six measurable criteria, yields a sharper picture of where the student is weak than a single accuracy number.

## 2. Hard constraints (unchanged from v0; SQLite verified course-aligned)

| Constraint | Value | Source |
|---|---|---|
| Stack | Python + Streamlit web app | Brief slide 3 |
| LLM | Anthropic Claude API only | Tiago decision |
| Persistence | Local SQLite at `~/.surf/user.sqlite` | Tiago decision; verified course-aligned via Lectures notebook query 2026-04-29 (Chinook + Streamlit demo, Databases & SQL slide 24) |
| ORM | None — Python stdlib `sqlite3` only | Lectures notebook: SQLAlchemy not taught |
| Submission | Canvas, code + 4-min video, **2026-05-14 23:59 Europe/Zurich** | Brief slide 8 |
| ⚠️ Auffahrt collision | 2026-05-14 = Ascension Day → **buffer-upload by 2026-05-13** | README §5 |
| Mandatory attendance 1 | Friday 2026-05-15 — video showing in Übung + 5-min Q&A | Brief slide 9 |
| Mandatory attendance 2 | Friday 2026-05-21 — top-3 group lecture presentation | Brief slide 9 |
| Video | Max 4 minutes; **no AI-generated audio** | Brief slide 4 |
| AI references | HSG rules: https://universitaetstgallen.sharepoint.com/sites/PruefungenDE/SitePages/Arbeiten-mit-KI.aspx | Brief slide 8 |
| Team | Max 5 students, same Übungsgruppe; Tiago, Nikita, Cons, Juliette, Jojo | Brief slide 5 |
| Contribution Matrix | Mandatory; layout copies brief slide 6 verbatim | Brief slides 4 + 6 |
| Grading | 8 mandatory requirements, each 0–3, max 24 pts; ≥16 pts = 100% of 20% project weight | Brief slide 4 |

## 3. App architecture — 7 pages

### Page 1 — Sign Up

Username + Anthropic Claude API key (validated by a real test call before save). Side-panel buttons: link to Anthropic Console + "How Surf uses AI" explanation drawer (where the key is stored, what data leaves the device, HSG AI-reference URL). On success → DB stores user + key.

### Page 2 — My Classes (Home)

Stacked-cards carousel. Click card → P3 for that class. "Add Class" button → side-form panel with class-setup flow (§4.1). Empty state on first launch.

### Page 3 — Class (central hub)

Brand strip + class name in topbar. Panels: lecture upload sidebar (drag-and-drop) · "Build a Mock Exam" with lecture-checkbox list and live counter (5 × N_lectures = N questions) · Past Attempts list (most-recent first; click → P5 with that attempt loaded) · Study Next widget with PRACTICE buttons · "Open Class Dashboard" button → P6 · side settings drawer (edit class, delete with `st.dialog` confirm).

### Page 4 — Take Mock Exam

Header: brand + breadcrumb + question counter (`Question X of N`) + per-question pager + total-elapsed timer. Body: source-slide preview + question text + four answer-options as radio buttons. Action bar: SKIP / NEXT only. **No FLAG button** (dropped for MVP). Progress bar. On final question's NEXT → save attempt → P5.

**Timer mode (locked, course-aligned):** total elapsed counter updated on every Streamlit rerun (i.e., when user clicks SKIP/NEXT). No live ticking — that would require auto-refresh patterns not taught in the course. Per Lectures query 2026-04-29: per-question countdown is over-engineering risk; total-elapsed-on-rerun is the lowest-cost, course-aligned option.

### Page 5 — Review Mock Exam

Per-question results + slide preview + Claude rationale + the question's six difficulty-feature scores. Reachable from end of mock OR from Past Attempts list on P3.

### Page 6 — Class Dashboard

**4 charts:**
- **Line:** mock-score evolution over time
- **Bar:** average score per lecture
- **Bar:** completion = % of saved slide-pages where ≥1 linked question has been answered correctly
- **Radar:** 6 axes (one per difficulty criterion); plot = student's accuracy on questions with high values for each criterion. **The radar IS the strengths/weaknesses profile** — not a separate page or output.

### Page 7 — Settings

- Rotate API key (re-validates with a test call)
- **Reset account:** drops ALL tables (full wipe). `st.dialog` confirm + typed-name confirm.
- **Backup:** download raw `~/.surf/user.sqlite` file (importable elsewhere, openable in any SQLite viewer).
- AI-citation / About block (HSG AI-rules URL, contact, app version).

### Cross-cutting

- Shared topbar (Home · breadcrumb · Settings link) imported by every page. P3 topbar label dynamic to class name.
- Empty / loading / Claude-error states designed for every page.
- **`st.session_state` contract** — pinned across reruns: `current_attempt_id`, `mock_question_list` (frozen at mock start), `current_question_index`, `answers_so_far`, `timer_start_ts`, `class_id`, `selected_lectures`. Essential for the static-snapshot mock guarantee.
  - **Caveat:** `st.session_state` is NOT taught in the course (Lectures query 2026-04-29). It is self-taught from the Streamlit docs, which the course explicitly recommends as an extension resource [7. Python, slide 25]. Cite the docs in code comments.

## 4. Data flows

### 4.1 Class setup (P2 → side panel)

1. User: class name + "% needed for a 4" slider (default 50%).
2. User: uploads class factsheet PDF.
3. Claude factsheet-cleaner → cleaned JSON. **Exact prompt: TBD.**
4. User reviews + approves.
5. DB: `classes` row + cleaned factsheet (JSON) + threshold.

### 4.2 Lecture ingestion (P3 sidebar → per lecture)

1. User: uploads Slides PDF + assigns 1 topic (lecture-level).
2. `scripts/pdf_to_md_v3.py` converts PDF → MD. **Updated 2026-04-29:** now injects `--- PAGE N ---` delimiter lines between pages so the splitter can chunk reliably.
3. **Claude LO-extraction call:** input = Slide MD + cleaned factsheet (context). Output = JSON with list of LOs (each with a page-range) + list of pages to ignore by category. **Exact prompt: TBD.** Page-ignore categories: TBD (fixed list in system prompt).
4. **Splitter script** chunks MD on PAGE markers, links each kept page to its LO, drops ignored pages.
5. DB: one row per saved page in `slide_pages`, FK'd to `lecture`, `topic`, `class`, `learning_objective`.
6. **Saved-slide guarantee:** every saved (non-ignored) slide page yields ≥1 MCQ candidate at ingestion time (per §4.3 below). Lower bound for question coverage on P6 chart 3.

### 4.3 Question generation — eager at ingestion (locked 2026-04-29)

1. For every saved slide page, immediately after the splitter step, Claude generates 1 MCQ: question text, four options, correct index, short rationale. **Multiple prompt variants for diversity: number + variants TBD.**
2. App computes 6 numeric difficulty features (§4.4) per generated question.
3. DB: `questions` row with FK to `slide_page`, plus the 6 features as columns + nullable `predicted_difficulty`.

**Eager (vs. lazy at mock-build time):** instant mock-build UX, predictable upfront cost, saved-slide guarantee holds.

### 4.4 Question-difficulty ML — Option B (locked 2026-04-29)

**Two-track methodology** — primary track is graded; sensitivity track is bonus.

#### Primary track (graded, course-strict)

- Algorithm: linear regression [6. Machine Learning, slide 77, 78].
- Train/test split: 70/30, shuffled [6. Machine Learning, slide 55, 59].
- Feature inspection: pairwise scatterplots [6. Machine Learning, slide 63, 64].
- Evaluation: MSE, MAE, R² [6. Machine Learning, slide 66, 85]. R² above 0.5 is meaningful; aim ~0.9.
- Library: scikit-learn [6. Machine Learning, slide 50, 59].
- Every choice citable to a course slide.

#### Sensitivity extension (bonus, cited externally)

- Cite source: external ML expert consultation (Dirk Reimann, 2026-04-29). Reported as "exploring non-linear and alternative-split sensitivity".
- Random forest comparison on the same 70/30 split (random forest NOT taught — explicit acknowledgement in the report).
- Correlation matrix alongside scatterplots — both methods reported.
- 60/40 alternative split if budget allows.

#### Six input features (3 locked + 3 candidate)

| # | Feature | Status |
|---|---|---|
| 1 | Word count of question | Locked |
| 2 | Language complexity (readability) | Locked |
| 3 | Distractor similarity | Locked |
| 4 | Question topic | Candidate |
| 5 | Concept overlap (also tested elsewhere?) | Candidate |
| 6 | Student skip / confidence behaviour | Candidate |

Candidates pruned by the pairwise-scatterplot inspection.

#### Cohort framing

Predicts difficulty for the average student of the relevant cohort (e.g. HSG bachelor undergraduate). NOT personalized. Cohort is baked into the dataset filter — TBD.

#### Two consumers

- Per-question `predicted_difficulty` value stored alongside question (visible on P5 review).
- P6 radar (chart 4): per criterion, plot = `mean(was_correct)` over the user's attempts on questions with high values for that criterion.

### 4.5 Mock-exam mechanics — refresh fallback locked 2026-04-29

| Mode | Trigger | Question count | Pool |
|---|---|---|---|
| Standard mock | P3 → user picks lectures → "Generate Mock" | 5 × N_lectures_selected | All saved pages of selected lectures, filtered below |
| PRACTICE mock | P3 Study-Next → "PRACTICE" on a specific LO | 1 question per slide of that LO | Slides linked to the chosen LO, filtered below |

**Selection logic (both modes):** prefer **unseen** → then **previously-wrong** → fall back to **already-correct (refresh)**.

Mock = static snapshot — once generated, the question list does not change mid-exam. Pinned in `st.session_state` (§3 P4 cross-cutting).

### 4.6 Outputs (refresh after each completed mock)

- **Study Next** (P3 widget): ranked LOs with PRACTICE button. Ranking heuristic: TBD — likely a function of (user accuracy on the LO) × (recency) × (number of unseen slides for the LO).
- **Class Dashboard** (P6): 4 charts (line + 2 bars + radar). The radar IS the strengths/weaknesses profile — collapses v0's 3-output structure to 2 surfaces.

## 5. Data model

```
users
  └── classes
        ├── factsheet (cleaned JSON)
        ├── threshold (% needed for 4)
        └── lectures
              ├── topic (FK)
              └── slide_pages
                    ├── md_chunk (text)
                    ├── learning_objective (FK)
                    └── questions
                          ├── stem, options, correct_index, rationale
                          ├── difficulty_features (6 cols)
                          ├── predicted_difficulty (FLOAT, nullable; written by ML model)
                          └── attempt_answers
                                ├── attempt (FK)
                                ├── chosen_index (nullable, null = SKIP)
                                └── was_correct
attempts
  ├── class (FK)
  ├── lectures_selected (JSON)
  ├── started_at, submitted_at
  └── score
topics
  ├── class (FK)
  └── label
learning_objectives
  ├── lecture (FK)
  ├── topic (FK)
  ├── label
  └── page_range
```

Concrete column types, NOT NULL constraints, indexes: TBD per the Database task brief.

### 3.5 Grading scale

> Note on numbering: this section was placed under §5 in the original Idea v1 source. Preserved here verbatim.

- Per-class slider: "% needed for a 4" (default 50%).
- **Formula (locked 2026-04-29):** standard Swiss linear `note = 5 × (p / max) + 1` (0% → 1, 50% → 3.5, 100% → 6).
- Raw correct/total always stored in DB; grade computed at display time.

## 6. Locked decisions (cumulative — Idea v0 + Idea v1 deltas)

(All Idea v0 decisions still hold unless explicitly superseded. See `Decision Log 2026-04-29 — Surf` for the full delta narrative.)

| Date | Decision |
|---|---|
| 2026-04-28 | Pivot to Surf; `LOCKED_DECISIONS_FINAL.md` and `FINAL_ROADMAP.md` archived. |
| 2026-04-28 | 7-page architecture: Sign Up · My Classes · Class · Take Mock Exam · Review Mock Exam · Class Dashboard · Settings. |
| 2026-04-28 | Only Mock Exams; only MCQ. |
| 2026-04-28 | One topic per lecture (lecture-level). |
| 2026-04-28 | Factsheet cleaned by Claude into JSON, used as context for downstream calls. |
| 2026-04-28 | Question difficulty = real ML, post-generation, 6 measurable criteria. |
| 2026-04-28 | P4 action bar = SKIP / NEXT only (no FLAG button). |
| 2026-04-28 | Three NotebookLM notebooks become the working backbone. |
| 2026-04-29 | Standard mock = 5 × N_lectures_selected; PRACTICE = 1 question per slide of the LO. |
| 2026-04-29 | Selection pool for both modes = unseen ∪ previously-wrong, fallback to already-correct (refresh). |
| 2026-04-29 | Page-ignore policy = fixed category list in Claude system prompt; categories TBD. |
| 2026-04-29 | P6 = 4 charts (line + bar avg + bar completion + radar). |
| 2026-04-29 | Coverage = % of saved slides where ≥1 linked question answered correctly. |
| 2026-04-29 | `pdf_to_md_v3.py` injects `--- PAGE N ---` markers; splitter chunks on those. |
| 2026-04-29 | **Eager question generation** at ingestion (was a v0 contradiction — fixed). |
| 2026-04-29 | Swiss grading formula = `note = 5 × (p/max) + 1`. |
| 2026-04-29 | No AI-generated audio in video (explicit). |
| 2026-04-29 | Contribution Matrix layout copies brief slide 6 verbatim. |
| 2026-04-29 | README + video include AI-citation block per HSG rules. |
| 2026-04-29 | `st.session_state` contract pinned (§3 P4). Self-taught from Streamlit docs (course-allowed). |
| 2026-04-29 | Optional Streamlit Cloud deployment: skip. |
| 2026-04-29 | P4 timer = total elapsed counter (course-aligned). |
| 2026-04-29 | Teammate repo at `/tmp/CSproejct10/...`: drop reference (path is dead). |
| 2026-04-29 | P7 Reset = drop ALL tables (full wipe, dialog-confirmed). P7 Backup = raw `.sqlite` download. |
| 2026-04-29 | SQLite verified course-aligned (Chinook + Streamlit). No SQLAlchemy (not in lectures). |
| 2026-04-29 | **ML methodology = Option B (hybrid):** course-strict baseline (linear regression + 70/30 + scatterplots + MSE/MAE/R²) graded as Req 5; random forest + correlation matrix + 60/40 alt as bonus sensitivity extension citing Dirk Reimann externally. |
| 2026-04-29 | Legacy `setup/` numbered files archived (17 files + README → `Assets/_archive/2026-04-28_pre-Surf-pivot/setup_old/`). |

## 7. Rejected alternatives (cumulative)

(All v0 rejections still hold. New rejections below.)

| Rejected | Why | When |
|---|---|---|
| Lazy question generation (on user click) | Conflicted with the saved-slide guarantee; eager wins. | 2026-04-29 |
| Mock pool fallback = "warn user + let them choose" | Too much UX overhead. Refresh-with-already-correct is simpler. | 2026-04-29 |
| Splitter via approximate character offsets | Code blocks throw off offsets. | 2026-04-29 |
| `pdf_to_md_v3.py` left as-is + splitter reads PDF directly | Adds a second PDF dependency. Page markers are deterministic. | 2026-04-29 |
| Old +20pp/-10pp asymmetric grade formula | Replaced by standard Swiss linear for explainability. | 2026-04-29 |
| Token cap on cleaned factsheet | Tiago left as TBD — no premature optimisation. | 2026-04-29 |
| Provisional team-role remap in `CLAUDE.md` §6 | Dropped — old roles stale, new roles need team input. | 2026-04-29 |
| Renaming vault folder `CS_EN_VF` → `Surf` | Deferred to future full vault rewrite session. | 2026-04-29 |
| Random forest as PRIMARY ML model | Course doesn't teach it — over-engineering risk for graded baseline. Moved to sensitivity extension. | 2026-04-29 |
| 60/40 train/test as PRIMARY split | Course teaches 70/30 — moved to sensitivity extension. | 2026-04-29 |
| Correlation matrix as PRIMARY feature inspection | Course teaches pairwise scatterplots — moved to sensitivity extension. | 2026-04-29 |
| Public Streamlit Cloud deployment | Not graded; saves work + avoids public-data risk. | 2026-04-29 |
| Per-question countdown timer on P4 | Over-engineering risk per Lectures query. Total elapsed counter is course-aligned. | 2026-04-29 |
| Triage of teammate repo at `/tmp/CSproejct10/...` | Path is dead. Nothing to triage. | 2026-04-29 |
| Soft reset on P7 (preserve content, wipe history only) | More code to write; full wipe is cleaner semantics. | 2026-04-29 |
| Structured JSON backup on P7 | Raw `.sqlite` file is more portable + opens in any SQLite viewer. | 2026-04-29 |

## 8. Items still to be determined

In rough resolution order:

1. 3 of 6 difficulty features (final lock) — Tiago to provide.
2. Dataset acquisition — outreach to HSG teachers (priority 1) + verify public MCQ DB format (priority 2).
3. Difficulty scale lock — 1–10 vs 0–1 vs % correct, depends on dataset.
4. Cohort filter for training data (e.g. "18–24 yo undergrads").
5. Page-ignore category list for Claude's LO-extraction system prompt.
6. Three Claude prompts — factsheet-cleaner, LO-extraction, question-generator (with diversity variants).
7. Concrete DB schema — column types, NOT NULL, indexes (per Database task brief).
8. Study Next ranking heuristic.
9. Question generation diversity strategy — number of variants, selection logic.
10. PRACTICE button when LO is fully mastered — disable, celebrate, or generate fresh.
11. Empty / loading / error states per page.
12. Topbar component spec.
13. Factsheet token cap policy (deferred — no cap until we see actual sizes).
14. Plaintext API key — confirm with Simon Mayer at next Übung.
15. Code documentation standard — Google docstrings + Ruff D as working default; final lock during build.
16. Team task split under new architecture — gates re-adding §6 to `CLAUDE.md`.
17. New per-day roadmap — target 2026-05-01 to leave buffer to 2026-05-13.
18. Full vault redesign with NLM help — standing item.

## 9. Mapping to 8 graded requirements

| # | Requirement | Surf coverage | Status |
|---|---|---|---|
| 1 | Clear problem | "Adaptive HSG Study Companion" | ✓ |
| 2 | API + DB | Claude API + SQLite (course-aligned, Chinook pattern) | ✓ |
| 3 | Visualisation | P6 line + 2 bars + radar | ✓ |
| 4 | User interactions | 7-page flow | ✓ |
| 5 | ML | Linear regression + 70/30 + scatterplots + MSE/MAE/R² (course-aligned baseline) + RF/correlation/60-40 (sensitivity extension citing Dirk) | ✓ |
| 6 | Documented code | Google docstrings + Ruff (preferred); final standard locks during build | TBD process |
| 7 | Contribution Matrix | Layout copies brief slide 6 verbatim | TBD team |
| 8 | 4-min video | Plan locked: no AI audio · total elapsed timer · pre-cached demo · Auffahrt buffer | TBD production |

**Forecast:** floor 17 · realistic 20 · ceiling 22. ≥16 gate cleared on paper.

## 10. Project-management anchors

- Old artifacts archived: `Assets/_archive/2026-04-28_pre-Surf-pivot/{phase3_reports,lucid,UX_old,setup_old}/`.
- Working repo location: `CS_Obsidian/CS_EN_VF/` (folder rename to `Surf/` deferred).
- App code lives in: `app/` (to be created).
- Scripts location: `CS_Obsidian/CS_EN_VF/scripts/pdf_to_md_v3.py`.
- Team task briefs: `CS_Obsidian/CS_EN_VF/setup/team_tasks/{ML_training_and_build,Database_creation,Video_Planning}.md` + matching PDFs in `~/Downloads/`.

### 3 NotebookLM notebooks (active backbone)

- **Lectures** (course-expectation oracle): https://notebooklm.google.com/notebook/6bc919e0-21c9-452e-b203-507f078efa33
- **Brief & Grading** (compliance gate): https://notebooklm.google.com/notebook/0e457b1d-a6d1-42e0-85e5-6f5f38f7ba75
- **Idea & Progress** (memory): https://notebooklm.google.com/notebook/3e02fa3d-8ce2-4a6d-9da7-ac974e32452f
  - **Idea v0** — historical anchor (frozen)
  - **Idea v1** — current state (this document)
  - **Decision Log 2026-04-29 — Surf** — delta narrative

### FigJam reference

https://www.figma.com/board/qoAOJwdMe40MAIyWCVeJlq/Surf-Board (App Engine + App Navigation mindmaps regenerated 2026-04-29).

---

End of Idea v1. Future edits → Idea v2 etc.

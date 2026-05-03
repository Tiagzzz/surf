# Surf — Adaptive HSG Study Companion

## What This Is

Surf is a Streamlit web app for HSG FCS-BWL bachelor undergraduates. A student creates a class, uploads the class factsheet (Merkblatt) and lecture PDFs, and Surf auto-generates timed multiple-choice mock exams from slide content via the Anthropic Claude API. The student takes mocks, reviews per-question results with rationales, and sees weakness patterns through a class dashboard backed by a 6-feature ML difficulty model.

Submission for FCS-BWL course project, Spring 2026.

## Core Value

Pass the grade (≥16/24 by 2026-05-14) AND deliver something Tiago is proud of: the full Idea v1 vision — 7-page flow, eager MCQ generation, 6-feature ML difficulty model. Floor = the grade. Target = the vision.

## Requirements

### Validated

- ✓ Single shared Claude wrapper (`app/brain/claude_client/claude_client.py`) — shipped 2026-04-30
- ✓ PDF→MD ingestion script (`app/brain/ingestion/pdf_to_md_v3.py`) — shipped 2026-04-30 (TODO `--- PAGE N ---` marker still pending)
- ✓ Factsheet cleaning pipeline (`app/my_classes/factsheet_clean/`) — shipped 2026-04-30
- ✓ Repo bootstrapped: 10-bucket structure scaffolded; Streamlit auth router; thin `views/`; smoke test; Ruff config

### Active

- [ ] Close the lecture-ingestion spine: `--- PAGE N ---` marker injection, LO-extraction prompt, MCQ-generation prompt(s), splitter, eager generation per slide, DB writes
- [ ] Concrete SQLite schema (column types, NOT NULL, indexes) + `db.py` query wrappers + seed script
- [ ] 7-page Streamlit flow wired end-to-end (P1 Sign Up → P2 My Classes → P3 Class → P4 Take Mock → P5 Review Mock → P6 Dashboard → P7 Settings)
- [ ] Standard mock (5 × N lectures) + PRACTICE mock (1 per slide of one LO), with unseen → previously-wrong → refresh selection logic
- [ ] Swiss linear grading: `note = 5 × (correct / max) + 1`
- [ ] P6 Dashboard with 4 charts: line (score evolution) + 2 bars (avg/lecture, completion) + radar (6-criteria)
- [ ] 6-feature ML difficulty model (linear regression primary; random-forest sensitivity), trained on dataset
- [ ] 4-min submission video (no AI audio), human voiceover, pre-cached demo path
- [ ] Filled Contribution Matrix (TM rows × {Project Mgmt, Konzept, Präsentation, Dokumentation, Funktion #1–N, Testing} columns)
- [ ] Sample factsheet PDF + sample lecture PDF committed for graders
- [ ] AI-citation block (README + video closing card)
- [ ] Documented source code (Google-style docstrings + Ruff D ruleset)
- [ ] Submission ready by 2026-05-13 buffer-upload (deadline 2026-05-14 23:59 Europe/Zurich)

### Out of Scope

- **Streamlit Cloud deployment** — not graded; local-only app (D-10).
- **Per-question countdown timer** — not taught in course; total-elapsed counter chosen instead (D-07).
- **SQLAlchemy / any ORM** — not taught in course; stdlib `sqlite3` only (D-06, C-08).
- **OpenAI or any non-Anthropic LLM** — Claude-only per project decision (D-19, C-07).
- **Flask / FastAPI / Django** — Brief mandates Streamlit only (D-20, C-06).
- **AI-generated audio in submission video** — Brief slide 4 hard constraint (D-21, C-09).
- **Soft-reset Settings option** — full wipe only, gated by typed-name confirm (D-08).
- **JSON DB backup format** — raw `.sqlite` download chosen for portability (D-09).
- **Personalized difficulty prediction** — model targets HSG bachelor cohort, not individual users (D-18).
- **Encrypted API key storage** — local-only app; plaintext likely acceptable (pending Simon Mayer confirmation).

## Context

**Status as of 2026-05-01 00:12 GMT+2:**
- 14 calendar days to deadline (2026-05-14 23:59 Europe/Zurich); 13 days to buffer-upload (2026-05-13 — Auffahrt collision).
- Mandatory attendance: 2026-05-15 (video showing + Q&A) and 2026-05-21 (top-3 lecture, if selected).
- Repo: `https://github.com/Tiagzzz/surf`, branch `main`. Solo direct-push for small fixes; PRs for reviewed work.
- Already shipped: claude_client wrapper, pdf_to_md_v3, factsheet_clean pipeline, Streamlit auth router, thin views/ placeholders, smoke test, Ruff config.
- Scaffold-only (~30 sub-folders waiting for code): all of `signup/`, `class_/`, `mock_take/`, `mock_review/`, `dashboard/`, `settings/`, `db/`, `ml/`, plus `brain/{topbar, session, grading_formula, routing, state_helpers}`.

**Team (5 across 4 tracks):**
- Track 0 — Skeleton + AI integration + prompts (cross-cutting): **Tiago**
- Track 1 — Database (SQLite): **Nikita**
- Track 2 — ML (difficulty predictor): **Jojo + Tiago support**
- Track 3 — Submission video: **Juliette + Cons**

**Course-alignment oracle:** Lectures NotebookLM (`6bc919e0-21c9-452e-b203-507f078efa33`) — query before claiming a method is course-aligned. SQLite, sklearn, plotly, linear regression, 70/30 split, pairwise scatterplots, total-elapsed timer all course-verified.

**Open blockers:**
- ML dataset acquisition (~200 example MCQs with observed difficulty) — outreach to HSG teachers gated on Tiago's next Übung session.
- 3 of 6 ML difficulty features (question topic, concept overlap, student skip/confidence) pending dataset.
- Page-ignore category list — must be fixed before LO-extractor prompt can be written.

## Constraints

- **Stack (LOCKED, C-06)**: Python 3.11 + Streamlit only — no Flask, FastAPI, Django, or alternative web framework. Brief slide 3.
- **LLM (LOCKED, C-07)**: Anthropic Claude API only — no OpenAI. All calls via `app/brain/claude_client/claude_client.py`.
- **Persistence (LOCKED, C-08)**: SQLite via Python stdlib `sqlite3` — no SQLAlchemy or ORM (not taught in course). User DB at `~/.surf/user.sqlite`.
- **Video (LOCKED, C-09)**: ≤4 min, no AI-generated audio. Voice/music/SFX must be human or licensed.
- **Deadline (LOCKED, C-10)**: 2026-05-14 23:59 Europe/Zurich, with buffer-upload 2026-05-13 (Auffahrt = 2026-05-14 = Ascension Day).
- **Team size (LOCKED, C-11)**: ≤5 students, all in same Übungsgruppe.
- **Contribution Matrix (LOCKED, C-12)**: TM rows × {Project Mgmt, Konzept, Präsentation, Dokumentation, Funktion #1–N, Testing} columns. Filled by all 5.
- **Grading rubric (LOCKED, C-13)**: 8 reqs scored 0–3, max 24, ≥16 = full 20% weight.
- **Engineering behavior (LOCKED, C-21)**: Think Before Coding · Simplicity First · Surgical Changes · Goal-Driven Execution.
- **Code documentation clarity (LOCKED, C-22 — amended 2026-05-03)**: Every script Claude writes ships with (a) a short module docstring (2–4 sentences, plain-language WHAT + WHY), (b) a sibling `<script>.md` that always includes a `## Code walkthrough` section explaining the code section-by-section in plain language for a non-CS reader (Juliette + Cons + the grading rubric). **No line cap**: clarity is the only criterion. Sections in the typical order: plain-language summary · how to call · in/out · where it fits · gotchas-if-real · `## Code walkthrough`. **Scope:** applies to script sidecars only (sibling-of-.py / sibling-of-.sql docs); system-prompt files (`*_system_prompt.md`) and design-system edit-maps (e.g. `app/brain/theme/edit_this_later.md`) are excluded. Earlier wording (≤100 lines, "deliberately simpler than the existing four sidecars") superseded by the 2026-05-03 amendment — see `.planning/intel/constraints.md` C-22 block for the current rule + scope clarification.
- **Communication rules (LOCKED, D-33)**: 10 rules from `~/CS/CS_Obsidian/CS_EN_VF/setup/tiago_guidelines.md`.
- **Architecture (C-01)**: 10-bucket layout — `brain/`, `db/`, `ml/` (infra) + `signup/`, `my_classes/`, `class_/`, `mock_take/`, `mock_review/`, `dashboard/`, `settings/` (page-aligned). One sub-folder per pipeline. Lower-snake-case verb-driven names.
- **Claude-call pattern (C-05)**: ~10-line wrappers; system prompts as sibling `.md` files; every call goes through `call_claude(system_prompt, user_message, expect_json=...)`.
- **Lint (C-14)**: Ruff E/F/I, line 100, target py311.
- **Tests (C-15)**: `pytest -q` smoke test in `tests/test_smoke.py`; per-module skip on missing optional deps.
- **Repo hygiene (C-17)**: `.gitignore` excludes `.surf/`, `*.sqlite`, `.env*`, secrets.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Eager MCQ generation at ingestion (D-01) | Predictable upfront cost, instant mock-build UX | — Pending |
| Mock fallback = refresh (include already-correct, D-02) | Consistent 5-per-lecture UX; mirrors flashcard "due-cards-depleted" handling | — Pending |
| `--- PAGE N ---` markers in MD (D-03) | Clean MD-only flow; deterministic splitter | — Pending |
| Swiss linear grading `note = 5 × (correct/max) + 1` (D-04) | Simple, explainable, standard at Swiss universities | — Pending |
| ML two-track: linear-regression primary + random-forest sensitivity (D-05) | Course-aligned baseline (graded); RF cited externally as rigor signal | — Pending |
| SQLite stdlib `sqlite3`, no ORM (D-06) | Course-aligned (Chinook+Streamlit demo, slide 24); ORM not taught | — Pending |
| Total-elapsed timer in P4 (D-07) | Auto-refresh patterns not taught; lowest-cost course-aligned | — Pending |
| P7 Reset = full wipe (D-08), Backup = raw `.sqlite` (D-09) | Clearest semantics; portable; matches Chinook | — Pending |
| 7-page UI (D-15) | Maps cleanly to 10-bucket architecture; tested in FigJam Surf Board | — Pending |
| 6-feature difficulty model: 3 locked + 3 pending dataset (D-17) | Word count, readability, distractor similarity locked; rest dataset-dependent | ⚠️ Revisit (dataset blocker) |
| HSG bachelor cohort (D-18), not personalized | Scope; matches available training data | — Pending |
| Skip Streamlit Cloud deploy (D-10) | Not graded; local-only sufficient | ✓ Good |
| Auth gate = `~/.surf/user.sqlite` file existence (D-36) | Stub; trivial; sufficient for local app | — Pending |
| Branch policy: solo direct push for fixes; PR for reviewed work (D-34) | Solo speed + collaboration discipline | ✓ Good |

---
*Last updated: 2026-05-01 after GSD ingest synthesis*

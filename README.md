# Surf — Adaptive HSG Study Companion

Surf is a local Streamlit study app for HSG students. It is designed to turn a class factsheet and lecture PDFs into learning objectives, multiple-choice practice questions, mock exams, review screens, and honest progress analytics.

- **Course:** Computer Science for Business (FCS-BWL), HSG FS 2026
- **Team:** HSG student project team
- **Stack:** Python 3.11 · Streamlit · SQLite (`sqlite3`) · Anthropic Claude API
- **Runtime:** local-first; user data and the Anthropic API key stay on the user's machine

> **Current status:** Phase 7 and Phase 7.1 are complete locally. Surf has the runnable Streamlit V1 app, team-facing docs, selected approved planning/register artifacts, sanitized assets, and a tracked verification subset. Phase 8 is final verification, documentation sync, and publish-readiness. Production uses real stored data only and does not fake dashboard ML analytics.

---

## V1 product scope

Surf V1 is a local study-to-mock-exam app with seven pages:

1. **Signup** — create a local profile and validate an Anthropic API key.
2. **My Classes** — create a class with a required factsheet and grade-4 threshold.
3. **Class Hub** — upload lectures, generate learning objectives/questions, choose lectures for a mock, and start Study Next practice.
4. **Take Mock / Practice** — answer multi-select MCQs one question at a time.
5. **Review** — inspect correct/incorrect/skipped answers and rationales.
6. **Dashboard** — show real progress data only; no fake ML/demo analytics in production.
7. **Settings** — replace the API key safely and reset local data with confirmation.

Key V1 rules:

- MCQs are **multi-select** and may have 1–4 correct answers.
- Grading is exact-match; skipped answers count as wrong.
- Class averages use completed mock exams only; practice affects weaknesses and coverage.
- Class Hub includes a red **`CUSTOM MOCK >`** button that launches up to 10 questions currently ranked as most difficult for the student.
- Review cards can show **`Difficulty for you: X/100`**, recalculated from stored question metadata and the student's completed-answer history.
- The app uses local SQLite and stdlib `sqlite3`; no ORM.
- Every Claude call goes through the shared `app/brain/claude_client/` wrapper.
- A second Claude metadata critic records intrinsic MCQ difficulty fields after question generation. Personal scoring is local and explainable: metadata-first rules plus exact-question history, with a reliability-capped structured `DecisionTreeClassifier` path when enough real answers exist.
- The dashboard remains real-data-only. It has no fake ML widget and does not display placeholder analytics.

---

## Quick start

Python **3.11** is recommended.

```bash
# 1. Clone
git clone https://github.com/Tiagzzz/surf.git
cd surf

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate         # macOS / Linux
# .venv\Scripts\activate          # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

The app is local-first. Do not commit `.env`, local SQLite databases, API keys, or generated cache files.

---

## Project structure

The app follows a 10-bucket structure under `app/`: three shared infrastructure buckets and seven page-aligned buckets.

```text
surf/
├── streamlit_app.py              # Streamlit entry point and router
├── views/                        # Thin Streamlit page wrappers
│   ├── signup.py                 # P1 Signup
│   ├── my_classes.py             # P2 My Classes
│   ├── class_view.py             # P3 Class Hub (`class` is a Python keyword)
│   ├── take_mock_exam.py         # P4 Take Mock / Practice
│   ├── review_mock_exam.py       # P5 Review
│   ├── dashboard.py              # P6 Dashboard
│   └── settings.py               # P7 Settings
├── app/
│   ├── brain/                    # Shared infrastructure
│   │   ├── claude_client/        # Shared Anthropic API wrapper
│   │   ├── grading_formula/      # Swiss grading helpers
│   │   ├── ingestion/            # PDF-to-markdown and page splitting
│   │   ├── page_header/          # Shared page header helper
│   │   ├── page_layout/          # Shared page rail/layout helper
│   │   ├── question_type/        # Canonical question-type slugs/labels
│   │   ├── session/              # Saved-user/session helpers
│   │   └── topbar/               # Shared authenticated topbar
│   ├── db/                       # SQLite schema, connection, query helpers
│   │   ├── schema/               # `schema.sql` and schema notes
│   │   ├── queries_users/
│   │   ├── queries_classes/
│   │   ├── queries_lectures/
│   │   ├── queries_learning_objectives/
│   │   ├── queries_pages/
│   │   ├── queries_questions/
│   │   ├── queries_attempts/
│   │   ├── queries_dashboard/
│   │   └── demo_seed/             # Explicit local demo seeding helper
│   ├── ml/                       # Live personal-difficulty scorer plus offline/reference material
│   ├── signup/                   # P1 implementation modules
│   ├── my_classes/               # P2 implementation modules and factsheet cleaning
│   ├── class_/                   # P3 lecture ingestion, LO extraction, MCQ generation
│   ├── mock_take/                # P4 answer capture and attempt save
│   ├── mock_review/              # P5 result/rationale rendering
│   ├── dashboard/                # P6 chart/data modules
│   └── settings/                 # P7 API key, reset, account settings
├── docs/team/                    # Team/teacher handoff-prep docs
├── tests/test_smoke.py           # Minimal GitHub-visible smoke test
├── assets/                       # Safe sample/demo assets and local fonts/icons
├── .streamlit/                   # Streamlit config
├── requirements.txt
└── pyproject.toml                # Ruff + Python tooling config
```

Most important modules have sibling `.md` sidecar docs explaining purpose, inputs, outputs, data flow, and what could break if changed. Cross-cutting team docs live in [`docs/team/`](docs/team/): start with [`overview.md`](docs/team/overview.md), then use [`database.md`](docs/team/database.md), [`streamlit.md`](docs/team/streamlit.md), [`custom_ui.md`](docs/team/custom_ui.md), [`prompts.md`](docs/team/prompts.md), [`submission_checklist.md`](docs/team/submission_checklist.md), [`demo_script.md`](docs/team/demo_script.md), and [`known_issues.md`](docs/team/known_issues.md).

---

## Development checks

For a fresh GitHub clone, run the tracked tests and then launch the app:

```bash
python -m pytest -q
streamlit run streamlit_app.py
```

For maintainers with the larger local-only verification pack, the normal full checks are:

```bash
python -m ruff check . --no-cache
python -m compileall streamlit_app.py views app
python -m pytest -q
```

The tracked tests cover the smoke path plus the current Phase 7/7.1 difficulty-metadata and personal-scoring surfaces. Larger preview sandboxes and generated local artifacts stay out of the normal repo.

---

## Repository hygiene

The GitHub repo should contain runnable app code, sanitized assets, team-facing documentation, selected approved planning/register artifacts, and the approved tracked verification subset.

Team-facing educational docs under `docs/team/` are tracked. Selected register/planning summaries are tracked when they are useful for handoff context; broader local planning evidence and agent-working files remain ignored unless explicitly approved.

The final teacher package, seeded teacher/demo database, and any capped demo key are approval-gated generated artifacts. They are not part of the normal tracked development repo.

Intentionally local-only / not for GitHub:

- agent instructions and private handoffs (`AGENTS.md`, `CLAUDE.md`, unapproved internal planning docs)
- broad local planning evidence under `.planning/` except selected tracked state/roadmap/summary artifacts
- local assistant worktrees or settings (`.claude/`)
- local databases (`*.sqlite`, `*.sqlite3`, `*.db`, WAL/SHM files)
- secrets (`.env`, API keys, cookies, credentials)
- full local verification suites and preview sandboxes; only `tests/test_smoke.py` is tracked
- generated caches (`__pycache__/`, `.pytest_cache/`, `.ruff_cache/`)

---

## License

MIT — see [LICENSE](LICENSE).

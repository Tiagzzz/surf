# Decisions (synthesized from ADR + ADR-equivalent locked tags in DOCs)

> Synthesizer note: only `02_decision_log_v0_to_v1.md` is classified ADR. `01_idea_v1_state.md` is DOC but per user direction, in-document "locked" tags inside it are treated as ADR-equivalent. Both source documents self-describe as "recorded, not immutable" — so `status: recorded` (not `locked`) for everything below. Communication rules (10) self-describe as "locked across sessions"; recorded as `status: locked` per their own framing.

---

## D-01 — MCQ generation is eager at ingestion

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §A1
- **Status:** recorded (open for re-discussion in GSD)
- **Scope:** lecture ingestion pipeline / question generation timing
- **Decision:** Generate ≥1 MCQ per saved slide at ingestion time (one Claude call per slide, immediately after the LO/page-split step). Not lazy at mock-build time.
- **Rationale:** predictable upfront cost; instant mock-build UX; saved-slide guarantee holds.
- **Rejected:** lazy generation (slow first-mock UX, ~30s for a 25-Q mock); hybrid eager+regenerate-on-demand (over-budget for 2-week window).

## D-02 — Mock pool fallback = refresh (include already-correct)

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §A2
- **Status:** recorded
- **Scope:** mock generation / question selection logic (standard mock + PRACTICE)
- **Decision:** When `unseen ∪ previously-wrong < 5 questions per lecture`, fall back to already-correct slides ("refresh" mode). Same logic for both standard and PRACTICE.
- **Rationale:** consistent 5-per-lecture UX; timer + dashboard charts don't handle variable N; mirrors flashcard-app "due-cards-depleted" handling.
- **Rejected:** shrink-mock-to-pool (variable N is messy); warn-and-prompt (UX overhead); generate-fresh-on-demand (conflicts with eager generation).

## D-03 — PDF→MD page delimiters via injected `--- PAGE N ---` markers

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §A3
- **Status:** recorded; implementation NOT yet applied (script still emits `# Page N`)
- **Scope:** `app/brain/ingestion/pdf_to_md_v3.py` + downstream splitter
- **Decision:** Update v3 script to inject explicit `--- PAGE N ---` markers; the splitter regex-splits on them.
- **Rationale:** clean MD-only flow; ~10 lines in v3; deterministic.
- **Rejected:** splitter reads PDF directly (adds second PDF dependency); approximate character offsets (inaccurate, breaks on code blocks).

## D-04 — Swiss linear grading formula

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §A4 (also 01_idea_v1_state.md "Grading scale")
- **Status:** recorded
- **Scope:** grading formula across the app (P5 review, P6 dashboard, internal scoring)
- **Decision:** `note = 5 × (correct / max) + 1` (0% → 1, 50% → 3.5, 100% → 6). Per-class "% needed for a 4" slider is informational anchor only.
- **Rationale:** simple; explainable in report; standard at Swiss universities.
- **Rejected:** asymmetric +20pp/-10pp formula (harder to explain).

## D-05 — ML methodology = Option B (hybrid two-track)

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §C (cross-ref 01 §4.4)
- **Status:** recorded
- **Scope:** Req 5 (ML); ML training pipeline; report
- **Decision:** Two tracks.
  - **Primary (graded):** linear regression + 70/30 split + pairwise scatterplots + MSE/MAE/R². Every choice citable to a course slide. This is the Req 5 deliverable.
  - **Sensitivity (bonus):** random forest + correlation matrix + 60/40 alt split. Frame as "exploring whether non-linear models capture patterns the linear baseline misses." Cite Dirk Reimann (external ML expert, 2026-04-29).
- **Rationale:** keeps Dirk's contribution while staying course-aligned for the graded baseline; rigor signal in the report.
- **Rejected:** Option A (course-strict, drop Dirk entirely) — loses rigor signal; Option C (full Dirk methodology as primary) — risks unjustified-complexity penalty.

## D-06 — SQLite via stdlib `sqlite3` only (no ORM)

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §D (also 03_brief_and_grading.md, 01_idea_v1_state.md)
- **Status:** recorded; course-verified via Lectures notebook query 2026-04-29
- **Scope:** entire `db/` bucket; persistence layer
- **Decision:** Use Python stdlib `sqlite3` module. NO SQLAlchemy or other ORM. Pattern follows the Chinook + Streamlit demo from the Databases week [Databases & SQL, slide 24].
- **Rationale:** SQLite explicitly listed as a DBMS [Databases & SQL, slide 8]; ORM not taught; over-engineering risk.
- **Rejected:** SQLAlchemy / any ORM; cloud-deployed DB (optional per course; would be over-engineering).

## D-07 — P4 timer mode = total elapsed counter

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §E + §F (Lectures validation)
- **Status:** recorded
- **Scope:** P4 Take Mock page
- **Decision:** Total elapsed counter, updated on each natural Streamlit rerun (when user clicks SKIP/NEXT). Uses only `st.session_state` + Streamlit-docs patterns.
- **Rationale:** Auto-refresh patterns (`st_autorefresh`, time.sleep loops) NOT taught; per-question countdown = over-engineering; total-elapsed lowest-cost + most aligned.
- **Rejected:** per-question countdown; total-mock countdown (acceptable but more work for no graded benefit).

## D-08 — P7 Reset = full wipe (drop ALL tables)

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §E
- **Status:** recorded
- **Scope:** P7 Settings → Reset action
- **Decision:** Drop ALL tables (full wipe), gated by `st.dialog` confirm + typed-name confirm.
- **Rejected:** soft reset (preserve content) — more code for less clear semantics.

## D-09 — P7 Backup = raw `.sqlite` download

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §E
- **Status:** recorded
- **Scope:** P7 Settings → Backup action
- **Decision:** Provide download of the raw `.sqlite` file.
- **Rationale:** more portable than JSON; opens in any SQLite viewer; matches Chinook pattern.
- **Rejected:** JSON backup.

## D-10 — Optional Streamlit Cloud deployment = skip

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §E
- **Status:** recorded
- **Scope:** deployment / submission
- **Decision:** Skip Streamlit Cloud deployment. Local-only app. Defer if bandwidth allows in final week.
- **Rationale:** not graded.

## D-11 — Standard mock size = 5 × N_lectures questions

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Mock mechanics"
- **Status:** recorded
- **Scope:** Standard mock generation
- **Decision:** User picks N lectures on P3; mock contains `5 × N` questions.

## D-12 — PRACTICE mock = 1 question per slide of a chosen LO

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Mock mechanics"
- **Status:** recorded
- **Scope:** PRACTICE mock generation
- **Decision:** User picks one Learning Objective; PRACTICE mock has 1 question per slide of that LO.

## D-13 — Mock = static snapshot pinned in `st.session_state`

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Mock mechanics"
- **Status:** recorded
- **Scope:** P4 mock-take session lifetime
- **Decision:** Once a mock is built, the question set is pinned in `st.session_state` for the duration of the attempt — no regeneration mid-mock.

## D-14 — Question selection priority: unseen → previously-wrong → refresh

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Mock mechanics"; cross-ref D-02
- **Status:** recorded
- **Scope:** mock + PRACTICE selection logic
- **Decision:** Both modes prefer unseen, then previously-wrong, then fall back to already-correct (refresh).

## D-15 — 7-page UI structure (P1–P7)

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "7-page UI"
- **Status:** recorded
- **Scope:** entire app navigation
- **Decision:** P1 Sign Up · P2 My Classes · P3 Class · P4 Take Mock · P5 Review Mock · P6 Class Dashboard · P7 Settings.

## D-16 — P6 dashboard chart set = line + 2 bars + radar

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "7-page UI" P6; 03_brief_and_grading.md Req 3
- **Status:** recorded
- **Scope:** P6 Class Dashboard
- **Decision:** Four charts: line (score evolution) + bar (avg per lecture) + bar (completion) + radar (6-criteria strengths/weaknesses).

## D-17 — 6-feature difficulty model (3 locked, 3 candidates pending dataset)

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "ML approach"; 02 §B; 09_open_tbds.md §B2
- **Status:** partially recorded (3 locked, 3 open)
- **Scope:** ML difficulty features
- **Decision:** Locked features = word count, language complexity (readability), distractor similarity. Candidates pending dataset = question topic, concept overlap, student skip/confidence behaviour. Pruning method = pairwise scatterplots.

## D-18 — Cohort = HSG bachelor undergraduates (not personalized)

- **Source:** docs/handoff_2026-04-30_gsd_planning/05_team_task_briefs.md "Task 2 — Jojo + Tiago"
- **Status:** recorded
- **Scope:** ML training data scope
- **Decision:** Difficulty model predicts difficulty for HSG bachelor undergraduates as a cohort. Not personalized.

## D-19 — Anthropic Claude API only (no OpenAI)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints"; 01_idea_v1_state.md "Tech constraints"
- **Status:** recorded; non-negotiable per Tiago's project preference
- **Scope:** all LLM calls
- **Decision:** Anthropic Claude API only. All calls go through `app/brain/claude_client/claude_client.py`.

## D-20 — Python + Streamlit only (no Flask/FastAPI/Django)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 3); 01_idea_v1_state.md "Tech constraints"
- **Status:** recorded; non-negotiable per Brief slide 3
- **Scope:** entire app stack
- **Decision:** Python 3.11 + Streamlit. No alternative web framework.

## D-21 — No AI-generated audio in submission video

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 4); 10_communication_rules.md §9
- **Status:** locked (Brief constraint, graders enforce; communication rule 9 reinforces)
- **Scope:** submission video (Req 8)
- **Decision:** No AI-generated audio. Voice/music/SFX must be human or licensed.

## D-22 — Submission deadline = 2026-05-14 23:59 Europe/Zurich; buffer-upload 2026-05-13

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 8 + README §5)
- **Status:** locked (graders enforce)
- **Scope:** delivery
- **Decision:** Canvas submission by 2026-05-14 23:59 Europe/Zurich. Buffer-upload by 2026-05-13 (Auffahrt collision — 2026-05-14 = Ascension Day).

## D-23 — Mandatory attendance dates

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 9)
- **Status:** locked
- **Scope:** team logistics
- **Decision:** Friday 2026-05-15 = video showing in Übung + 5-min Q&A per group (mandatory). Friday 2026-05-21 = top-3 group lecture presentation (mandatory if selected).

## D-24 — Submission video = 4 minutes max

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 4)
- **Status:** locked
- **Scope:** Req 8 video deliverable
- **Decision:** MP4 ≤ 4 minutes.

## D-25 — Team size ≤ 5, all in same Übungsgruppe

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 5)
- **Status:** locked
- **Scope:** team composition
- **Decision:** Max 5 students, all in same Übungsgruppe. Surf team = Tiago, Nikita, Cons, Juliette, Jojo.

## D-26 — Contribution Matrix layout = brief slide 6 verbatim

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" + Req 7
- **Status:** locked (graded as Req 7)
- **Scope:** submission deliverable
- **Decision:** TM1–TMn rows × {Project Mgmt, Konzept, Präsentation, Dokumentation, Funktion #1–N, Testing} columns. Hauptbeitragende/r legend. Filled by all 5 team members.

## D-27 — 10-bucket code organization

- **Source:** docs/handoff_2026-04-30_gsd_planning/06_code_buckets_spec.md (SPEC)
- **Status:** recorded (self-describes as "locked 2026-04-30 19:00" but the handoff folder rule re-opens it for GSD)
- **Scope:** entire `app/` folder structure
- **Decision:** 3 infrastructure buckets (`brain/`, `db/`, `ml/`) + 7 page-aligned buckets (`signup/`, `my_classes/`, `class_/`, `mock_take/`, `mock_review/`, `dashboard/`, `settings/`). One sub-folder per pipeline. Lower-snake-case verb-driven names.

## D-28 — Folder casing = lowercase (PEP 8) over spec-uppercase

- **Source:** docs/handoff_2026-04-30_gsd_planning/06_code_buckets_spec.md "Open items"
- **Status:** resolved in repo (lowercase). Spec text still says uppercase — needs sync.
- **Scope:** `app/` folder names
- **Decision:** Use lowercase (`app/brain/`, not `app/BRAIN/`) per Python PEP 8. Spec text to be synced.

## D-29 — `class_` trailing underscore (Python keyword collision)

- **Source:** docs/handoff_2026-04-30_gsd_planning/06_code_buckets_spec.md
- **Status:** recorded
- **Scope:** `class_/` bucket naming
- **Decision:** Bucket name is `class_` (with trailing underscore) because `class` is a Python keyword.

## D-30 — Single shared Claude wrapper (`app/brain/claude_client/claude_client.py`)

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md; 06_code_buckets_spec.md; CLAUDE.md
- **Status:** shipped 2026-04-30
- **Scope:** all Claude API calls
- **Decision:** Every Claude call goes through `from app.brain.claude_client import call_claude`. Prompt caching enabled by default. System prompts live as sibling `.md` files.

## D-31 — Streamlit `session_state` allowed via course-extension rule

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §B + §F
- **Status:** recorded; course-verified
- **Scope:** P4 cross-cutting state (active mock, current question index, timer, answers)
- **Decision:** `st.session_state` is not taught explicitly in lectures, but Streamlit docs are course-allowed extension [7. Python, slide 25]. Use it for pinned mock state and timer.

## D-32 — Code documentation standard (working default)

- **Source:** docs/handoff_2026-04-30_gsd_planning/02_decision_log_v0_to_v1.md §B; 09_open_tbds.md D2
- **Status:** working default; final lock during build
- **Scope:** Req 6 (documented source code)
- **Decision (working):** Google-style docstrings + Ruff D ruleset.

## D-33 — Communication / working-style rules (LOCKED)

- **Source:** docs/handoff_2026-04-30_gsd_planning/10_communication_rules.md
- **Status:** **locked** — non-negotiable across sessions; the only set self-described as "ARE locked" in the handoff folder.
- **Scope:** how Claude/Codex/the GSD agent interacts with Tiago (NOT what Surf builds)
- **Decision:** 10 rules — define jargon inline, avoid jargon chains, structured option presentation, simple/short/decisive/honest base style, reformulate-and-confirm, 2–3 clarifying questions on big tasks, honesty charter (no sycophancy, quantify risks, name rejected alternatives, preserve dissent), cite sources, never recommend AI audio, flag deadlines.

## D-34 — Branch + commit policy

- **Source:** /Users/tiagoreimann/surf/CLAUDE.md ("Branch + commit"); cross-confirmed by 07_repo_state.md commit log
- **Status:** recorded
- **Scope:** repo workflow
- **Decision:** Solo work — direct push to `main` OK for small fixes. Reviewed work — `feature/<short-name>` branch + PR. Atomic commits, imperative subject + body. `Co-Authored-By: Claude Opus 4.7 (1M context)` trailer when Claude generated the change.

## D-35 — Python 3.11 target

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md ("`.python-version` ← 3.11"); pyproject.toml ruff target
- **Status:** recorded
- **Scope:** runtime + linting
- **Decision:** Python 3.11; Ruff target `py311`; line length 100; rules E/F/I.

## D-36 — Auth gate = local SQLite presence

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md ("Auth router using `st.navigation()`. Stub `is_authenticated()` checks `~/.surf/user.sqlite` existence")
- **Status:** recorded (stub)
- **Scope:** P1 sign-up gating
- **Decision:** Authentication = file-existence check on `~/.surf/user.sqlite`. Sign Up creates the DB; subsequent runs auto-route past P1.

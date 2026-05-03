# Constraints (synthesized from SPEC + SPEC-equivalent contracts)

> Synthesizer note: only `06_code_buckets_spec.md` is classified SPEC. Hard-constraint contract rows from `03_brief_and_grading.md` are also folded here as `nfr` constraints since they are non-negotiable inputs to the build, even though that doc is PRD-classified.

---

## C-01 — 10-bucket code organization (architecture contract)

- **Source:** docs/handoff_2026-04-30_gsd_planning/06_code_buckets_spec.md
- **Type:** protocol (architecture)
- **Content:**
  - 3 infrastructure buckets: `brain/`, `db/`, `ml/`
  - 7 page-aligned buckets (one per Streamlit page): `signup/`, `my_classes/`, `class_/` (trailing `_`), `mock_take/`, `mock_review/`, `dashboard/`, `settings/`
  - One sub-folder per pipeline = one self-contained user/system flow (trigger → logic → persistence/output)
  - Naming: `lower_snake_case`, verb-driven, includes the action (`_save`, `_create`, `_launch`, `_render`, `_extract`, `_ingest`)
  - Folder casing: lowercase per PEP 8 (resolves spec text that says uppercase — see D-28)

## C-02 — Pipeline catalog (planned per bucket)

- **Source:** docs/handoff_2026-04-30_gsd_planning/06_code_buckets_spec.md "Pipeline catalog"
- **Type:** protocol
- **Content:**
  - **brain/**: topbar/, session/, claude_client/ (shipped), grading_formula/, routing/, state_helpers/, ingestion/{pdf_to_md_v3.py shipped, page_splitter/}
  - **db/**: schema/, migrations/, queries_users/, queries_classes/, queries_lectures/, queries_pages/, queries_questions/, queries_attempts/
  - **ml/**: training_pipeline/, dataset_labels/, model_artifact/, inference_per_question/, radar_features/
  - **signup/**: signup_flow/
  - **my_classes/**: class_create/, factsheet_upload/, factsheet_clean/ (shipped), class_list_render/, class_delete/
  - **class_/**: lecture_upload/ (may merge into lecture_ingest), lecture_ingest/, lo_extract/, mcq_generate/, mock_standard_launch/, study_next_launch/
  - **mock_take/**: question_render/, answer_capture/, attempt_save/
  - **mock_review/**: results_render/, rationale_display/
  - **dashboard/**: score_evolution_chart/, lecture_avg_chart/, completion_chart/, radar_chart/
  - **settings/**: username_save/, api_key_save/, reset_account/, backup_export/

## C-03 — Cross-bucket dependencies

- **Source:** docs/handoff_2026-04-30_gsd_planning/06_code_buckets_spec.md "Cross-bucket dependencies"
- **Type:** protocol
- **Content:**
  - `my_classes/factsheet_clean/` ⤏ `brain/ingestion/pdf_to_md_v3.py` (shipped link)
  - `my_classes/factsheet_clean/` ⤏ `brain/claude_client/` (shipped link)
  - `class_/lecture_ingest/` ⤏ `brain/ingestion/` (future)
  - All page-aligned buckets ⤏ `db/` (future)
  - `mock_take/attempt_save/` ⤏ `ml/inference_per_question/` (future, post-generation difficulty score)
  - `dashboard/radar_chart/` ⤏ `ml/radar_features/` (future)

## C-04 — Streamlit page wrappers in `views/`

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md; CLAUDE.md
- **Type:** protocol
- **Content:** One thin Streamlit page wrapper per page in top-level `views/` (signup.py, my_classes.py, class_view.py, take_mock_exam.py, review_mock_exam.py, dashboard.py, settings.py). Logic lives in `app/<bucket>/<pipeline>/`; view files are placeholders that call into buckets.

## C-05 — Standard Claude-call pattern (~10 lines)

- **Source:** /Users/tiagoreimann/surf/CLAUDE.md "The standard Claude-call pattern"
- **Type:** api-contract
- **Content:**
  ```python
  from pathlib import Path
  from app.brain.claude_client import call_claude

  _SYSTEM_PROMPT = Path(__file__).with_name("<script>_system_prompt.md")

  def <verb>_<noun>(input_text: str) -> dict:
      return call_claude(
          system_prompt=_SYSTEM_PROMPT.read_text(),
          user_message=input_text,
          expect_json=True,
      )
  ```
  System prompts live as sibling `.md` files (editable without touching Python). Each script has a sibling `.md` doc.

## Teacher's hard constraints — LOCKED (C-06 through C-13)

> **`locked: true`** — The eight constraints below come directly from the official teacher brief (HSG slides 3–8). They are non-negotiable for submission. Implementation details remain open for refinement, but the constraint itself cannot be relaxed, scoped down, or replaced.

## C-06 — Stack constraint: Python 3.11 + Streamlit only (NFR)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 3); D-20; D-35
- **Type:** nfr
- **Content:** Python 3.11 + Streamlit. NO Flask, FastAPI, Django, or any alternative web framework. Ruff target `py311`, line length 100, rules E/F/I.

## C-07 — LLM constraint: Anthropic Claude API only (NFR)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints"; D-19
- **Type:** nfr
- **Content:** Anthropic Claude API only. NO OpenAI or any other LLM provider. All calls go through `app/brain/claude_client/claude_client.py` — `call_claude(system_prompt, user_message, expect_json=False)`. Prompt caching enabled by default.

## C-08 — Persistence constraint: SQLite via stdlib `sqlite3` (NFR)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints"; D-06
- **Type:** nfr
- **Content:** Local SQLite. Use Python stdlib `sqlite3` module. NO SQLAlchemy or any ORM (not taught in course). Pattern follows the Chinook + Streamlit demo [Databases & SQL, slide 24]. User DB lives at `~/.surf/user.sqlite`.

## C-09 — Video constraint: ≤4 min, NO AI audio (NFR)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 4); D-21; D-24
- **Type:** nfr
- **Content:** Submission video MUST be ≤4 minutes. Voice/music/SFX MUST be human or licensed (no AI-generated audio).

## C-10 — Submission deadline (NFR)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 8 + README §5); D-22
- **Type:** nfr
- **Content:** Canvas submission by **2026-05-14 23:59 Europe/Zurich**. Buffer-upload by **2026-05-13** (Auffahrt collision — 2026-05-14 = Ascension Day). Mandatory attendance Friday 2026-05-15 (video showing + Q&A) and Friday 2026-05-21 (top-3 lecture, if selected).

## C-11 — Team-size constraint (NFR)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" (Brief slide 5); D-25
- **Type:** nfr
- **Content:** Max 5 students, all in same Übungsgruppe.

## C-12 — Contribution Matrix layout (artifact contract)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "Hard constraints" + Req 7; D-26
- **Type:** schema (deliverable artifact)
- **Content:** Layout copies brief slide 6 verbatim — TM1–TMn rows × {Project Mgmt, Konzept, Präsentation, Dokumentation, Funktion #1–N, Testing} columns. Hauptbeitragende/r legend. Filled by all 5 team members. Lives at `docs/contribution_matrix.md`.

## C-13 — Grading rubric (NFR)

- **Source:** docs/handoff_2026-04-30_gsd_planning/03_brief_and_grading.md "8 mandatory graded requirements"
- **Type:** nfr
- **Content:** 8 graded requirements scored 0–3 each. Max 24 points. ≥16 = 100% of the 20% project weight. The 8 requirements: clearly formulated problem, data via API/DB, useful visualisation, user interactions, ML implementation, documented source code, individual contributions (matrix), 4-min video with no AI audio.

## C-14 — Ruff config (NFR)

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md `pyproject.toml`; CLAUDE.md
- **Type:** nfr
- **Content:** Ruff rules E/F/I; line-length 100; target py311. Run via `ruff check .`.

## C-15 — Test config (NFR)

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md `tests/test_smoke.py`; CLAUDE.md
- **Type:** nfr
- **Content:** Smoke test at `tests/test_smoke.py` imports the four real modules + asserts public API exists. Per-module skip on missing optional deps. Run via `pytest -q`.

## C-16 — `requirements.txt` policy

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md "What's NOT in the repo"
- **Type:** nfr
- **Content:** Dependencies pinned with `>=`. `pip freeze` lock deferred to ~2 days before 2026-05-14 submission.

## C-17 — `.gitignore` excludes secrets + DB

- **Source:** docs/handoff_2026-04-30_gsd_planning/07_repo_state.md "Repo top-level layout"
- **Type:** schema (repo hygiene)
- **Content:** `.gitignore` excludes `.surf/`, `*.sqlite`, `.env*`, secrets.

## C-18 — FigJam color/shape legend (visual contract)

- **Source:** docs/handoff_2026-04-30_gsd_planning/08_figjam_references.md "Surf_Off — Legend"
- **Type:** protocol (visual)
- **Content:** Locked 2026-04-30 (obs 626/641): Red=Input, Pink=Database, Purple=Python script, Green=Logic, Orange=Claude, Yellow=Output, Black=User action, Blue=Streamlit page, Teal=UI/components, Grey=TBD/Open, `#A70000`=Risk, `#007510`=Locked decision. Mandatory before drawing any new FigJam content for Surf. SOP at `~/.agents/skills/surf-figjam-sop/SKILL.md`.

## C-19 — FigJam SOP (drafting rules)

- **Source:** docs/handoff_2026-04-30_gsd_planning/08_figjam_references.md "FigJam SOP"
- **Type:** protocol (visual)
- **Content:** Multi-zone grids (no mega-sections). Elbow connectors, unlabeled, color-matches-starting-element. Section-drift gotcha: `appendChild` preserves local coords, not absolute (compensate manually). Sticky notes match connected-element color (or yellow for general comments).

## C-20 — Data model (schema contract — partial)

- **Source:** docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md "Data model"
- **Type:** schema
- **Content:**
  ```
  users → classes → lectures → slide_pages → questions → attempt_answers
                                                          ↑
                                                      attempts
  topics, learning_objectives are FK'd in
  ```
  Column types, NOT NULL constraints, and indexes still TBD (owner: Niki, see REQ-db-schema and 09_open_tbds.md A4).

## C-21 — Engineering behavior rules (process contract — LOCKED)

- **Source:** /Users/tiagoreimann/surf/CLAUDE.md "Behavioral guidelines to reduce common LLM coding mistakes"
- **Type:** protocol (process)
- **Status:** `locked: true` — applies to all phases, all agents, all execution.
- **Content:**
  1. **Think Before Coding.** State assumptions explicitly. If multiple interpretations exist, surface them — don't pick silently. If a simpler approach exists, say so. If unclear, stop and ask.
  2. **Simplicity First.** Minimum code that solves the problem. No features beyond what was asked. No abstractions for single-use code. No "flexibility" or "configurability" not requested. No error handling for impossible scenarios. If 200 lines could be 50, rewrite.
  3. **Surgical Changes.** Touch only what you must. Don't "improve" adjacent code, comments, or formatting. Don't refactor things that aren't broken. Match existing style. Mention unrelated dead code — don't delete it. Remove only orphans your own changes created. Every changed line traces directly to the user's request.
  4. **Goal-Driven Execution.** Define falsifiable success criteria before implementing. Transform tasks into verifiable goals ("write tests for invalid inputs, then make them pass"). For multi-step work, state a brief plan with per-step verification.
- **Tradeoff:** these rules bias toward caution over speed. For trivial tasks, agents may use judgment.
- **Verification signal:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, clarifying questions before implementation rather than after mistakes.

## C-22 — Code documentation clarity (process contract — LOCKED, amended 2026-05-03)

- **Source:** Tiago directive 2026-05-01 — "all code well documented and clearly understandable; simpler than current 4 sidecar .md docs in the repo"
- **Amendment:** 2026-05-03 (during Plan 02-01 Task 9 execution) — Tiago's verbatim ruling: **"remove the line cap. Sidecars should explain the code."** The earlier "≤100 lines" / "≤140 flex" caps are SUPERSEDED. New rule: no line cap; clarity is the only criterion; every sidecar must include a `## Code walkthrough` section.
- **Type:** protocol (process)
- **Status:** `locked: true` — applies to every script Claude writes for Surf.
- **Audience target:** a non-CS reader — specifically Juliette and Cons (Surf's video-track teammates) and the grading rubric — should understand WHAT the script does and WHY in under a minute, before touching any code.
- **Content (every Python module Claude writes ships with):**
  1. **A short module docstring** at the top — 2–4 sentences in plain language. Lead with WHAT (one sentence) and WHY (one sentence). No jargon a non-engineer wouldn't know without explanation.
  2. **A sibling `.md` doc** (e.g. `<script>.md` next to `<script>.py`). **No line cap** — explain the code clearly for a non-CS reader. Typical sections, in this order:
     - **Plain-language summary** — 3–6 sentences. Use one analogy if it helps.
     - **How to call it** — single fenced code block, short.
     - **What goes in / what comes out** — bullet list, no nested tables.
     - **Where it fits** — one sentence with relative-path links to the 1–2 most relevant siblings.
     - **Gotchas** — only if real; skip the section otherwise.
     - **`## Code walkthrough`** (mandatory) — function-by-function plain-language paragraphs; no line refs (they rot), no code dumps (the .py is right there). Format: `**def my_func(args)** — In plain language: takes X, does Y because Z, hands back W. Look out for: <one gotcha if any>.` Audience: Juliette + Cons can describe each function in their own words after one read.
  3. **Function docstrings** (Google style) — but only for public functions. Private helpers get one-line comments where the WHY isn't obvious from the name. Don't pad with `Args:` blocks restating type hints.
  4. **No frontmatter blocks** in sidecar `.md` files unless explicitly requested.
- **Verification signal:** a non-engineer teammate opens a sidecar `.md` and can describe what the script does in their own words after one read. Length is whatever it takes to be that clear — no longer, no shorter.
- **Scope clarification (2026-05-03, during Plan 02-01 Task 12 verification):** C-22 applies to **script sidecars** — `.md` files that document a sibling Python (or SQL/etc.) source file. It does NOT apply to:
  - **System-prompt files** (`*_system_prompt.md`) — these ARE the prompt content sent to Claude; their "logic" is the natural-language instructions, not Python functions to walk through.
  - **Design-system edit-maps** (e.g. `app/brain/theme/edit_this_later.md`) — value/where-to-find lookup indexes, not code documentation.

  The walkthrough rule's intent is "explain the code to a non-CS reader." When there is no code, the rule does not apply. The Plan 02-01 verifier (`.planning/phases/02-mock-taking-loop-p1-p5/02-01-PLAN.md`, Task 9 `<automated>` block) walks an explicit list of 18 script sidecars rather than a broad `find` over `app/**/*.md`.

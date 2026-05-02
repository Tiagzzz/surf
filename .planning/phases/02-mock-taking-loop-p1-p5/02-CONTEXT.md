# Phase 2: Mock Taking Loop (P1–P5) - Context

**Gathered:** 2026-05-02
**Status:** Ready for planning (after widget-catalog research step — see locked sequence below)

<domain>
## Phase Boundary

This phase delivers the **demonstrable Surf app** end-to-end for the Standard mock-taking flow. A first-time user signs up, creates a class from a factsheet PDF, ingests a lecture (live, calling the Phase 1 spine), builds a multi-lecture mock or taps Study Next for a focused mock, takes it under a timer, and reviews per-question results with rationales.

In scope:
- **P1 Sign Up** — username + Anthropic API key intake (validated against Anthropic before save). First-launch routing only; subsequent launches skip P1 because `~/.surf/user.sqlite` exists.
- **P2 My Classes** — class card list + Add Class flow (factsheet PDF upload → cleaner pipeline → user reviews rendered factsheet → save class).
- **P3 Class hub** — main column: lecture upload + "Generate Mock" CTA + lecture multi-select (Card Interactive). Sidebar: Past Attempts list + Study Next card. Triggers live Phase-1 ingestion on lecture upload with `st.status` log streaming.
- **P4 Take Mock** — one MCQ at a time, total-elapsed timer in top header, SKIP/PREV/NEXT navigation, mock state persisted to DB on every navigation event (UPSERT semantics, resume-on-revisit), difficulty score visible on each MCQ card.
- **P5 Review Mock** — scrollable list of result Cards, per-option rationale upfront, difficulty scores upfront, Swiss-formula final note at top.
- **Live ingestion via Phase 1** — `lecture_ingest` orchestrator runs in-band on PDF upload; partial-success policy already handles tab-close per Phase 1 D-4.5.
- **Visual identity wired** — `.streamlit/config.toml` `[theme]` block + a single scoped-CSS file at `app/brain/theme/surf_theme.css`. Editorial/paper aesthetic from the locked Figma library.
- **Sidecar walkthrough back-fill (15 Phase 1 sidecars)** — function-by-function plain-language paragraphs added under a `## Code walkthrough` section to every existing sidecar.
- **Sidecar walkthrough cadence going forward** — built into wave closure: every wave in Phase 2 (and beyond) ends with a doc-update step touching the sidecars touched in that wave.

Out of scope (other phases):
- P6 Dashboard with 4 charts → Phase 3
- P7 Settings (username change, API rotation, Reset, Backup) → Phase 3
- ML difficulty model + real difficulty scores → Phase 4 (Phase 2 ships placeholders that auto-light when the model lands)
- Submission video, Contribution Matrix, sample data, README polish → Phase 5
- Dark theme variant of the Paper palette → deferred (Phase 3 Settings could add a toggle if wanted)
- Editable factsheet JSON (correct fields inline before save) → Phase 3 Settings or beyond
- Page-to-page transition animations → not feasible in Streamlit (no router transition layer)
- JS-driven effects: confetti, scroll-triggered animations, animated counters → ruled out by hard-red anti-patterns

</domain>

<decisions>
## Implementation Decisions

### Locked sequence — design-control protocol

**The user's durable preference is to plan and control the design of the App.** The order below is binding for downstream agents:

1. **Discuss intent** (this CONTEXT.md) — captured WHAT we want.
2. **Widget-catalog research step** (next) — produces `02-WIDGETS.md` with vanilla Streamlit green-list, exact hex / font / padding / radius values extracted from the Figma library, and per-element implementation pattern (vanilla widget + scoped-CSS key when needed). Folds the pending todo `todos/pending/2026-05-02-phase-2-streamlit-widget-catalog-research.md`.
3. **Plans 02-xx written** — only after `02-WIDGETS.md` exists.
4. **Execution** — only after plans are approved.

**Edit-this-later rule (LOCKED, applies to every locked visual decision below):** Every visual choice ships with an "edit-this-later" note in the plan/sidecar that says (a) where the value lives in the codebase, (b) what to change, (c) how the swap propagates. No locked visual without an edit note.

### UI design system (Area 1)

- **D-2.1 (Visual identity):** P1–P5 follow the editorial/paper aesthetic established in the user's `SURF_UI(old)` Figma library (`https://www.figma.com/design/EYjkvHArrBonuiG2JUS2sE/SURF_UI?node-id=25-2`). Token surface confirmed via `search_design_system`:
  - Colors: `color/Base/Paper`, `Paper0`–`Paper5` (6-step warm paper ladder), `Base/Shadow`, `Accent/Soft`, `Accent/Deep`, `Accent/Wash` (3-tone accent), `Status/OK`, `Status/Warn`, `Status/Info`.
  - Typography: `Mono/Button Label` (monospace button labels — signature aesthetic move).
  - Components: `Button / Default | Soft | Ghost | Accent | Disabled`, `Container / Card`, `Container / Card Interactive`.
  - **Note:** the file's library is named `SURF_UI(old)` — there may be a newer revision; widget-catalog research should reconcile.
  - **Edit-this-later note:** all tokens flow through `.streamlit/config.toml [theme]` block + a single scoped-CSS file at `app/brain/theme/surf_theme.css` (loaded once via `st.html("<style>{css}</style>")` in the app entrypoint). To change a color, edit the CSS custom property at the top of `surf_theme.css` — every component re-themes automatically.

- **D-2.2 (Light only):** `[theme] base = "light"` in `.streamlit/config.toml`. No dark variant in Phase 2. **Edit-this-later note:** to add later, swap `base` and either let Streamlit auto-invert or ship a hand-derived dark Paper palette as a second CSS file gated by an `@media (prefers-color-scheme: dark)` block.

- **D-2.3 (Subtle motion):** CSS-only — hover transitions on Card Interactive + buttons, gentle fade-in on Cards via `@keyframes`, button press feedback. No JS animations, no page transitions, no confetti, no animated counters. **Edit-this-later note:** motion intensity controlled by a `--surf-motion-scale` CSS custom property in `surf_theme.css` (default `1`); set to `0` to disable, or override per-component via the `.st-key-{name}` scoped class.

- **D-2.4 (Roomy whitespace):** 8-pt spacing scale; generous card padding (24–32px); large block separators between sections. Matches editorial aesthetic and read-heavy P5 review screens. **Edit-this-later note:** spacing scale lives as `--surf-space-*` custom properties in `surf_theme.css`.

### Page-flow UX (Area 2)

- **D-2.5 (P2 factsheet review):** The Add Class flow shows the rendered factsheet (using the already-shipped `app/my_classes/factsheet_clean/factsheet_renderer.py`) only. Raw JSON lives behind a "Show raw JSON" expander for power users. Buttons: `Save class` / `Reject & re-upload`. No editable form in Phase 2. **Edit-this-later note:** to switch to side-by-side or editable view later, change the layout in `app/my_classes/add_class_review/`.

- **D-2.6 (P3 ingest progress):** Lecture upload triggers in-band `lecture_ingest` orchestrator inside an `st.status` block with live log lines: `Extracting PDF…`, `Splitting into pages…`, `Generating LOs…`, `Generating MCQs (batch i/N)…`. Closes to a green checkmark on success, red on failure. **Edit-this-later note:** log strings live as constants in `app/class_/lecture_ingest/lecture_ingest.py` near the top of each stage.

- **D-2.7 (Tab-close during ingestion):** Backend continues. The Phase 1 D-4.5 partial-success policy already lands incomplete batches as `lectures.status = 'pending'`. On revisit, the lecture card on P3 shows a "Resume ingestion" affordance for any pending batches. No `beforeunload` warning, no "in progress on another device" check (single-user, single-device app). **Edit-this-later note:** status enum lives in `app/db/schema/schema.sql`.

- **D-2.8 (Mock entry points):** TWO entry points only:
  1. **"Generate Mock"** CTA on P3 main column → opens lecture multi-select → builds mock from selected lectures (`5 × N` questions, selection logic per Phase 1 D-02 = unseen → previously-wrong → refresh).
  2. **"Study Next" card** in the P3 sidebar → tap → app generates a mock focused on the surfaced LO (algorithm in D-2.11). No manual LO picker on P3.
  - **⚠ REQUIREMENTS.md amendment #1:** MECH-02 originally read "user picks one LO". Amend to: "Study Next surfaces an LO; user taps the card to launch a focused mock — no manual LO picker."
  - **Edit-this-later note:** if a manual LO picker becomes needed later, add a third entry point in `views/class_view.py` and a new `app/class_/build_mock/manual_lo/` pipeline.

- **D-2.9 (Lecture multi-select pattern):** Card Interactive component (from Figma) per lecture, click toggles selection, selected state = `Accent/Deep` border + checkmark icon. Live counter: "{N} lectures × 5 = {5N} questions". **Edit-this-later note:** card key is `lecture-{id}` for scoped CSS targeting.

- **D-2.10 (P3 layout):** Sidebar (`st.sidebar`) = Past Attempts list (clickable to P5) + Study Next card. Main column = Generate Mock CTA + lecture multi-select + Past attempts hint. Matches the course-shipped sidebar pattern from `streamlit_demo_full.py`. **Edit-this-later note:** sidebar content rendered via `app/brain/topbar/` (already scaffolded) — a misnomer for sidebar+top elements; rename in cleanup.

- **D-2.11 (Study Next algorithm — Phase 2 v1):** Pick the LO with the lowest `correct/total` ratio across the user's attempts in this class. Tiebreak: most-recently-attempted. If user has zero attempts in this class, the Study Next card is hidden. Pure SQL, no ML. Phase 4 ML model replaces this. **Edit-this-later note:** query lives in `app/class_/study_next/` (new pipeline); swap the SELECT in the v1 file for the ML-backed call when Phase 4 lands.

### P4 Take Mock runtime (Area 3)

- **D-3.1 (SKIP semantics):** Advance-only, returnable. Skip records `selected_indices = NULL` and advances. User can navigate back via Prev. On submit, NULL-answered questions count as wrong. **Edit-this-later note:** state machine in `app/mock_take/answer_capture/`.

- **D-3.2 (Timer placement):** Top header bar, right-aligned. Format: `Elapsed: 12:34`. Always visible across the mock. **Edit-this-later note:** rendered via `app/brain/topbar/` — change to floating sticky pill by adding `position:fixed` rule scoped to `.st-key-mock-timer` in `surf_theme.css`.

- **D-3.3 (Resume + answer-change persistence):** Mock attempt persists to DB. UPSERT writes happen on Next/Prev/Skip navigation events (NOT on every checkbox tick). Schema: `attempt_answers` has UNIQUE constraint on `(attempt_id, question_id)` → exactly one row per question per attempt. Reopening P4 with an in-progress attempt resumes at the next unanswered question; timer continues from saved `attempts.start_time`. New answer overrides old on next navigation. **Edit-this-later note:** UPSERT SQL in `app/mock_take/attempt_save/`; constraint in `app/db/schema/schema.sql`.

- **D-3.4 (Multi-correct grading):** All-or-nothing for v1. 1 point if and only if `selected_indices == correct_indices` (exact set equality). Otherwise 0. Keeps Swiss formula `5 × correct/max + 1` cleanly integer. **Edit-this-later note:** grading logic in `app/brain/grading_formula/`; partial-credit Jaccard variant lives commented at the bottom of the same file for easy swap.

- **D-3.5 (Difficulty score visible during mock):** The MCQ card on P4 displays the question's difficulty score alongside the question text. In Phase 2, the score is a placeholder (renders as "—" when `difficulty_score IS NULL`). When Phase 4 ML lands, real values display automatically. **Edit-this-later note:** render in `app/mock_take/question_render/`; the placeholder character lives as a constant `_DIFFICULTY_PENDING = "—"`.

### P5 Review + PRACTICE (Area 4)

- **D-4.1 (P5 layout):** Scrollable list of result Cards, one Card per question, ordered by question_order. Final note + summary banner pinned at top (Swiss-formula score, total elapsed, X correct of Y, % to next note). **Edit-this-later note:** card keyed `q-result-{question_id}` in `app/mock_review/question_render/`.

- **D-4.2 (P5 detail density):** Per-option rationale (D-2.6 from Phase 1) is upfront, always visible — this is P5's primary teaching value. Difficulty score also upfront on each Card (no expander). The 6 individual difficulty features can live behind an expander (`▸ Difficulty breakdown`) since they're meta. **Edit-this-later note:** expander label string in `app/mock_review/question_render/`.

- **D-4.3 (PRACTICE size — REVISED):** PRACTICE mock = ALL MCQs where `source_page IN <Study-Next-LO page_range>`. No per-slide picker. Mock size varies with LO span (could be 5–30+ MCQs).
  - **⚠ REQUIREMENTS.md amendment #2:** MECH-02 originally read "1 question per slide of that LO". Amend to: "PRACTICE mock includes every MCQ tied to the Study-Next LO's page range."
  - **Edit-this-later note:** SELECT lives in `app/class_/build_mock/practice_mock.py`; cap on practice mock size (if ever needed) goes here.

### Sidecar walkthroughs (Area 5)

- **D-5.1 (Walkthrough section structure):** Every sidecar `.md` ships with a `## Code walkthrough` section at the bottom. Format = function-by-function plain-language paragraph: `**def my_func(args)** — In plain language: takes X, does Y because Z, hands back W. Look out for: <one gotcha if any>.` No line refs (they rot). No code dumps. Audience: non-CS reader can describe the function in their own words after one read.

- **D-5.2 (Cadence):** End of every wave. Each wave's closure includes a doc-update step that touches every sidecar in that wave. Built into the GSD wave-closure ritual going forward. **Edit-this-later note:** the ritual is enforced by the executor's wave-completion checklist in `app/` plans (each plan's verification block must include "sidecar walkthrough updated").

- **D-5.3 (Back-fill scope):** All 15 Phase 1 sidecars get walkthrough sections back-filled before Phase 2 main work begins (or as the first wave of Phase 2). The 15: `claude_client.md`, `pdf_to_md_v3.md`, `factsheet_cleaner.md`, `factsheet_renderer.md`, `page_splitter.md`, `lo_extractor.md`, `mcq_generator.md`, `lecture_ingest.md`, `db.connection.md`, `db.schema.md`, `db.queries_classes.md`, `db.queries_lectures.md`, `db.queries_questions.md`, `db.queries_pages.md`, `db.queries_learning_objectives.md` (verify exact list when planning).

- **C-22 flex note:** Adding `## Code walkthrough` sections may push some sidecars over the 100-line cap. The cap is allowed to flex up to ~140 lines when the walkthrough section is present. C-22 audit will be revisited at end of Phase 2.

### Claude's Discretion

These are NOT decided here — the widget-catalog researcher and planner pick:
- Exact hex values for Paper0–Paper5, Accent/Soft/Deep/Wash, Status/OK/Warn/Info (extracted from Figma in research step).
- Exact monospace font name (extracted from Figma `Mono/Button Label` text style).
- Exact button paddings, border-radii, shadow values (extracted from Figma per component).
- Card content layout per page (which fields to show on a lecture card vs an attempt card vs a question result card) — extract from Figma.
- P4 progress indicator format ("Question 3 of 15" vs progress bar vs both) — match the Figma.
- Submit-Mock button placement and gating rules (e.g., does it appear only when all answered?) — match the Figma; if Figma is silent, default to "always visible, with a confirm dialog when unanswered questions exist".
- Internal helper function names within each `app/<bucket>/<pipeline>/` folder.
- Whether the scoped-CSS file is one big `surf_theme.css` or split per-component; recommend single file for v1.

### Folded Todos

- **Folded:** `todos/pending/2026-05-02-phase-2-streamlit-widget-catalog-research.md` — "Phase 2 Streamlit widget catalog research." This todo is the formal expression of the locked sequence (UI design lock → widget catalog → plans → execution). It will be executed as the **first task of Phase 2** (a researcher step before plans 02-xx are written), producing `02-WIDGETS.md`. Original todo file should be moved to `.planning/todos/done/` once `02-WIDGETS.md` is written.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project planning (always relevant)
- `.planning/PROJECT.md` — locked constraints, success metric, team split. Especially: C-06 (Streamlit only), C-07 (Anthropic only), C-08 (stdlib sqlite3), C-09 (no AI audio), C-21 (engineering rules), C-22 (doc clarity).
- `.planning/REQUIREMENTS.md` — Phase 2 requirements: PAGE-01..05, PIPE-02 (validate), MECH-01, MECH-02 (⚠ needs amendment per D-2.8 + D-4.3), MECH-03, GRADE-04. **Amendment must be applied before plans 02-xx are written.**
- `.planning/ROADMAP.md` — Phase 2 success criteria + dependencies on Phase 1.
- `.planning/STATE.md` — pending todos + deferred items (sidecar code-walkthrough handled here as D-5.x).
- `.planning/intel/decisions.md` — recorded decisions D-01 through D-36 from Idea v1.
- `.planning/intel/constraints.md` — full text of C-01 through C-22.

### Phase 1 carry-forward (already locked, do not re-litigate)
- `.planning/phases/01-ingestion-spine-database/01-CONTEXT.md` — full Phase 1 decisions; especially:
  - D-2.5 (multi-correct schema with `correct_indices` list, P4 must use checkboxes when ≥2 correct)
  - D-2.6 (per-option rationale)
  - D-4.5 (partial-success ingestion → enables D-2.7 above)
- `.planning/phases/01-ingestion-spine-database/01-VERIFICATION.md` — verifies Phase 1 spine is solid; downstream P3 ingest UI relies on this.

### Idea v1 architecture
- `docs/idea_v1.md` — canonical project state (7-page UI, ML approach, data-flow shape).
- `docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md` — handoff snapshot (gitignored, local).

### Design source of truth (Phase 2 — NEW)
- `https://www.figma.com/design/EYjkvHArrBonuiG2JUS2sE/SURF_UI?node-id=25-2` — **the visual reference.** Components: `Button / Default | Soft | Ghost | Accent | Disabled`, `Container / Card`, `Container / Card Interactive`. Tokens: 6-step Paper ladder, 3-tone Accent (Soft/Deep/Wash), Status/OK/Warn/Info, `Mono/Button Label`. Library is named `SURF_UI(old)` — research step should check for a newer revision.
- `docs/design/figma_exports/` — local PNG export(s) of the Figma. Currently contains `node_25-2.png` (the Components page). The widget-catalog researcher should pull more frame screenshots via `mcp__claude_ai_Figma__get_screenshot` (URL-based, no desktop selection needed).
- `/Users/tiagoreimann/surf/SURF_UI.fig` — local `.fig` file as offline fallback (binary, not directly parseable; relies on Figma to render).

### Existing code (already shipped — patterns to follow + integrate with)
- `app/brain/claude_client/claude_client.py` — single shared Anthropic wrapper. Used by P1 to validate API key (a `client.messages.create` with `max_tokens=1` against the user-entered key).
- `app/brain/ingestion/pdf_to_md_v3.py` — PDF → MD (Phase 1 closed).
- `app/my_classes/factsheet_clean/factsheet_cleaner.py` — JSON cleaner (Phase 1 closed; integrates with P2 Add Class flow).
- `app/my_classes/factsheet_clean/factsheet_renderer.py` — pure-Python renderer (P2 review screen uses this).
- `app/class_/lecture_ingest/` — orchestrator (Phase 1 closed; P3 calls this on lecture upload).
- `app/db/queries_*` — verb-named DB wrappers (Phase 1 closed; P2/P3/P4/P5 read+write through these).
- `streamlit_app.py` — auth router (already scaffolded; P1 ↔ P2/P3/etc gate is here).
- `views/*.py` — 9-line stubs for each page (P1–P7); Phase 2 fills P1–P5 with thin Streamlit wrappers that delegate to `app/<bucket>/<pipeline>/`.

### Course alignment (verify against Lectures notebook before introducing patterns)
- Lectures NotebookLM `6bc919e0-21c9-452e-b203-507f078efa33` — query before introducing Streamlit idioms (sidebar, columns, `st.status`, `st.dialog`, `st.session_state`).
- `~/surf/canvas_downloads/module4/notebooks/Unit04.section5.ipynb` — Streamlit lecture; teaches vanilla Streamlit only with deferral to docs.streamlit.io.
- `~/surf/canvas_downloads/module4/notebooks/streamlit_demo_full.py` — canonical course Streamlit demo. Patterns: `st.set_page_config`, `divider='rainbow'` on `st.header`, `st.columns(2) + with col:`, `st.sidebar.write`, `st.container()`, `st.toggle`, `st.button`, `st.data_editor`, `st.bar_chart`.

### Anti-pattern reminders (hard reds — do not propose)
- `streamlit-shadcn-ui`, `streamlit-elements`, `streamlit-antd-components`, `streamlit-option-menu` — banned community libs.
- Unscoped global `<style>` blocks via `st.html("<style>...</style>")` without a `.st-key-X` selector.
- `unsafe_allow_html=True` for user-invented HTML structure (vs CSS targeting Streamlit's own DOM).
- Custom JS injection (no easy way in Streamlit, and confetti/scroll-anim/counters all need it).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`app/brain/claude_client/claude_client.py`** — used by P1 Sign Up to validate the Anthropic API key (1-token call). Reused everywhere downstream.
- **`app/my_classes/factsheet_clean/`** — entire pipeline (cleaner + renderer) is shipped. P2 Add Class flow calls `factsheet_cleaner` on PDF upload, then renders with `factsheet_renderer` for review.
- **`app/class_/lecture_ingest/`** — Phase 1 orchestrator. P3 calls this in-band on lecture upload, wrapped in `st.status` per D-2.6.
- **`app/db/queries_*`** — DB wrappers shipped in Phase 1. P2 reads `queries_classes`, P3/P4 read `queries_lectures` + `queries_questions`, P4 writes `queries_attempts` (new in this phase) + `queries_attempt_answers` (new in this phase, with UPSERT helper).
- **`streamlit_app.py`** — `is_authenticated()` router gates P1 vs P2–P7. Phase 2 wires the P1 → P2 transition (writes `~/.surf/user.sqlite` with the user row).
- **`views/`** — 9-line stubs for each page are already in place; thin wrappers delegate to `app/<bucket>/<pipeline>/`. Phase 2 fills P1–P5 stubs.

### Established Patterns
- **One sub-folder per pipeline** (C-01, C-02): each new flow lives in its own folder. New folders this phase:
  - `app/signup/signup_flow/` (P1 flow), `app/signup/api_key_validate/` (Anthropic ping)
  - `app/my_classes/add_class/`, `app/my_classes/class_card_render/`
  - `app/class_/build_mock/`, `app/class_/study_next/` (algo + render)
  - `app/mock_take/answer_capture/`, `app/mock_take/attempt_save/`, `app/mock_take/question_render/`
  - `app/mock_review/question_render/`, `app/mock_review/summary_banner/`
  - `app/brain/theme/` (NEW — `surf_theme.css` lives here)
- **System prompt as sibling .md** (C-05): Claude calls in this phase (e.g., the API-key validate ping) follow this. The mock-taking and review flows have NO new Claude calls — all rationales come from MCQs already in DB.
- **Sidecar `.md` per script** (C-22): every new Python module in this phase ships with a `<script>.md` with the `## Code walkthrough` section per D-5.1.
- **Course-aligned DB pattern**: `with DB:` for writes, `pd.read_sql` for reads, `?` placeholders for params, FK pragma at connection. Already locked in Phase 1; P2/P3/P4/P5 inherit.

### Integration Points
- **P1 → DB:** `app/db/queries_users/save_user(username, anthropic_api_key)` — schema for `users` table needs verifying in Phase 1 schema (likely already exists from Phase 1).
- **P2 → DB:** `app/db/queries_classes/save_class(...)`, `list_classes_for_user(...)`.
- **P3 → DB:** `list_lectures_for_class`, `list_attempts_for_class`, `weakest_lo_for_class` (NEW for Study Next).
- **P3 → Phase 1 spine:** `lecture_ingest.run(pdf_path, class_id)` wrapped in `st.status`.
- **P4 → DB:** `save_attempt`, `upsert_attempt_answer(attempt_id, question_id, selected_indices)`, `mark_attempt_completed`.
- **P5 → DB:** `get_attempt_with_questions_and_answers(attempt_id)`.
- **Theme:** `app/brain/theme/surf_theme.css` is loaded once at app entry via `st.html` in `streamlit_app.py` (or a `views/_layout.py` shim).

</code_context>

<specifics>
## Specific Ideas

- The user **explicitly said** the sequence is binding: discuss intent → research what's possible → lock with edit notes → plan → execute. Downstream agents do not skip the widget-catalog research step.
- The user **explicitly said** every locked visual decision must ship with an "edit-this-later" note. This is captured in every D-2.x, D-3.x, D-4.x decision above. The planner must enforce this in plan files.
- The user **explicitly said** difficulty score is visible on the MCQ card during mock-taking (P4), not just at review. This is unusual UX (most exam tools hide it) and should not be "optimized away" by the planner.
- The user **explicitly said** the PRACTICE mock includes ALL MCQs in the LO range (not 1-per-slide). The original MECH-02 wording was wrong. Planner must propagate the amendment to REQUIREMENTS.md.
- The user **explicitly said** Study Next is the only PRACTICE entry point in Phase 2 (no manual LO picker). Planner must propagate that amendment too.
- The Figma library is named `SURF_UI(old)` — this suffix suggests a newer revision exists. Widget-catalog researcher must check Tiago's Figma teams for a non-old version before extracting tokens.
- The user has the Figma file open in Figma desktop app for selection-based MCP tools (`get_design_context`, `get_metadata`, `get_variable_defs`); URL-based tools (`get_screenshot`, `search_design_system`, `get_libraries`) work without selection. Researcher should plan around this.

</specifics>

<deferred>
## Deferred Ideas

### Phase 3 (Dashboard + Settings)
- **Editable factsheet JSON** — let users correct fields inline (typo in course name, missing prof). Currently Phase 2 ships read-only review only.
- **Dark theme variant** of the Paper palette — toggle in P7 Settings; ship a hand-derived dark CSS file.
- **Manual LO picker for PRACTICE mocks** — if the team decides Study Next isn't enough surface area, add a third entry point. Currently Phase 2 has only Generate Mock + Study Next.

### Phase 4 (ML Difficulty Model)
- **Real difficulty scores** wire into the placeholder slots already rendered on P4 MCQ card (D-3.5) and P5 result card (D-4.2). Phase 2 ships UI ready for the model output.
- **Replace Study Next algorithm** (D-2.11 = SQL-only weakest-LO) with the ML-backed weakness prediction. Phase 2 v1 query is intentionally swap-friendly.

### Phase 5 (Submission Package)
- **Sample factsheet PDF + sample lecture PDF** committed to `assets/sample_factsheets/` and `assets/sample_lectures/` so a grader can clone and run the demo. Already noted in Phase 1 deferred (smoke test uses one); Phase 5 polishes for graders.

### Process / housekeeping
- **C-22 line-cap audit at end of Phase 2** — walkthrough sections may push some sidecars to ~120–140 lines. Either accept the flex or split walkthrough into a sibling `<script>_walkthrough.md` per script (less preferred — separation of concerns vs single-file simplicity).
- **`app/brain/topbar/` rename** — currently misnamed (it covers sidebar + top header bits). Rename in cleanup phase.
- **FigJam end-of-phase visualization** — the spec format is still being defined (per `project_figjam_phase_visualization.md` memory). Phase 2 closeout should include a mock-taking-loop diagram once format is locked.

### Reviewed Todos (not folded)
None — the only matched todo (widget-catalog research) was folded into D-5.x sequence + new `02-WIDGETS.md` deliverable.

</deferred>

---

*Phase: 02-mock-taking-loop-p1-p5*
*Context gathered: 2026-05-02 via /gsd-discuss-phase*

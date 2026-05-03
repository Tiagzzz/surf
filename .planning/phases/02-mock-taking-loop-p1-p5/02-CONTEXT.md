# Phase 2: Mock Taking Loop (P1–P5) - Context

**Gathered:** 2026-05-02
**Amended:** 2026-05-02 (Branding & Visual Language area added — Area 6 — after parallel-session audit of `/Streamlit_Test/`)
**Status:** Plans 02-01..02-07 already written; this amendment requires a re-plan run on plan 02-01 (theme + tokens) to fold in the new branding decisions. Plans 02-02..02-07 are unaffected by this amendment except for one canonical-refs addition (the new audit doc).

> **Parallel-session audit:** see `02-PARALLEL-AUDIT.md` (sibling) for the full good/bad/reusable/discard verdict on `/Streamlit_Test/`. **Bottom line:** the parallel session shipped a production-grade design system that supersedes the planned Wave-1 Q1 "Figma extraction" spike — Q1 becomes a *validation* step, not extraction. Three amendments required (`prefers-reduced-motion`, multi-correct checkbox styling, `st.expander`+`st.status` skins).

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

- **C-22 flex note (SUPERSEDED 2026-05-03 by Tiago, during Plan 02-01 Task 9 execution):** Earlier wording capped sidecars at ≤100 (with ≤140 flex when a walkthrough was present). **Both caps are removed.** Tiago's ruling: "no line cap; sidecars should explain the code." Length is whatever it takes to be clear for a non-CS reader (Juliette + Cons + the grading rubric). The `## Code walkthrough` section is now MANDATORY rather than optional. See `.planning/intel/constraints.md` C-22 for the current locked rule.

### Branding & Visual Language (Area 6 — NEW, 2026-05-02 amendment)

This area was added after the parallel-session audit (`02-PARALLEL-AUDIT.md`). It locks the **specific** branding values that earlier areas left to "Claude's Discretion" + widget-catalog research. The seed for every decision below is `/Users/tiagoreimann/surf/Streamlit_Test/ui/theme.py` (598 lines, audited as production-grade).

- **D-2.12 (Token taxonomy — LOCKED):** CSS custom properties at `:root`, sourced from `theme.py`:
  - **Paper ladder (warm cream → charcoal):** `--paper #fdf9f2`, `--paper-0 #f5efe4`, `--paper-1 #ede4d2`, `--paper-2 #c0b49b`, `--paper-3 #6c6455`, `--paper-4 #3b362c`, `--paper-5 #28251f`, `--paper-shadow #171512`, `--paper-shadow-soft #1a1814`, `--white #ffffff`.
  - **Accent (Surf red):** `--accent-vibrant #c8361d`, `--accent-deep #9d2815`, `--accent-soft #e8a798`, `--accent-wash #f7d9d1`.
  - **Status:** `--ok #2d6a3f`, `--ok-wash #9ec7aa`, `--warn #b8860b`, `--info #2a5d7c`.
  - **Radii:** `--r-xs 3px`, `--r-sm 4px`, `--r-md 6px`, `--r-lg 10px`, `--r-pill 999px`.
  - **Motion:** `--ease cubic-bezier(0.2, 0, 0, 1)`, `--t-fast 120ms`, `--t-base 180ms`, `--t-slow 320ms`.
  - **Type:** `--serif 'Fraunces', Georgia, serif`, `--mono 'JetBrains Mono', Menlo, monospace`.
  - **Edit-this-later note:** all values live at the top of `_CSS` in `app/brain/theme/theme.py`. To re-tone the brand, edit the custom property; every component re-themes automatically.

- **D-2.13 (Stamp-shadow recipe — LOCKED, this is the signature visual move):** Hard-edged offset shadow with `border-radius: 0` on the shadow itself. Three offset scales:
  - **3px** for default & tinted buttons, class card, interactive card (rest state).
  - **4px** for interactive card hover (lifted state).
  - **2px** for soft button, passive card, stat card.
  - **Hover:** `transform: translate(-1px, -1px)` + shadow grows by 1px.
  - **Press (`:active`):** `transform: translate(2px, 2px)` + shadow shrinks to 1px.
  - **Disabled:** shadow removed entirely; surface = `--paper-2`, text = `--paper-3`.
  - **Edit-this-later note:** the shadow/transform pairs live next to each component selector in `theme.py`. To soften the stamp, change shadow color from `--paper-shadow` to `--paper-shadow-soft` per-component or globally.

- **D-2.14 (Animation primitives — LOCKED, replaces D-2.3 fade-in):** **Transitions only — no `@keyframes`.** Hover/press states animate via CSS `transition` on `transform`, `box-shadow`, `background-color`, `color`, `border-color`, `filter`. Durations follow the motion tokens: 120ms (button feedback), 180ms (cards, tabs), 320ms (rare slow elements). The earlier D-2.3 plan to add a "gentle fade-in on Cards via @keyframes" is **dropped** — Streamlit reruns top-to-bottom on every interaction, and a fade-in keyframe would re-trigger on every rerun, creating busy flicker. Stamp-shadow hover is the signature; that is enough character. **Edit-this-later note:** to add motion intensity scaling, introduce a `--surf-motion-scale` custom property at `:root` and multiply transition durations by it (defer until requested).

- **D-2.15 (Accessibility — `prefers-reduced-motion`, NEW vs theme.py):** Append a `@media (prefers-reduced-motion: reduce)` block at the bottom of `_CSS` that sets `transition: none !important` and `transform: none !important` on all interactive surfaces (buttons, cards, MCQ option, slider thumb). ~6 lines. **Edit-this-later note:** the block lives at the bottom of `_CSS` so it overrides everything above.

- **D-2.16 (Font loading strategy — LOCKED, self-hosted, 2026-05-02 second amendment):** Fonts ship **self-hosted** in `assets/fonts/`. Three variable WOFF2 files (~190 KB total, latin subset only):
  - `assets/fonts/Fraunces-normal-400_900.woff2` (67 KB) — Fraunces upright, weight axis 400–900.
  - `assets/fonts/Fraunces-italic-400_900.woff2` (82 KB) — Fraunces italic, weight axis 400–900.
  - `assets/fonts/JetBrainsMono-Variable.woff2` (40 KB) — JetBrains Mono, weight axis 100–800.
  - Declared via `@font-face` at the top of `_CSS` (replacing the earlier Google Fonts `@import`). Recipe (paste into `theme.py` `_CSS`):
    ```css
    @font-face { font-family: 'Fraunces'; font-style: normal; font-weight: 400 900;
      src: url('assets/fonts/Fraunces-normal-400_900.woff2') format('woff2'); font-display: swap; }
    @font-face { font-family: 'Fraunces'; font-style: italic; font-weight: 400 900;
      src: url('assets/fonts/Fraunces-italic-400_900.woff2') format('woff2'); font-display: swap; }
    @font-face { font-family: 'JetBrains Mono'; font-style: normal; font-weight: 100 800;
      src: url('assets/fonts/JetBrainsMono-Variable.woff2') format('woff2'); font-display: swap; }
    ```
  - **Streamlit-specific path note:** Streamlit serves files from the working directory; for the URL above to resolve, the app must be launched from the repo root (where `assets/` lives). If launched from elsewhere, swap to absolute paths via `Path(__file__).parent / "assets" / "fonts" / ...` resolved at module load and inlined as `data:font/woff2;base64,...` URIs in `_CSS`. Plan 02-01 picks the simpler path (relative URLs assuming repo-root launch) and documents the alternative as an edit-this-later note.
  - **Axis coverage limitation:** the downloaded files include `wght` (and `ital` via the family-style split) only. The Figma library uses `fontVariationSettings: 'SOFT' 0, 'WONK' 1` for the wonky italic forms (visible in node 4045:282 question text). The current files render the conservative italic — visually close but not pixel-identical. **Edit-this-later note:** to match Figma exactly, re-fetch from Google Fonts CSS2 API with the full axis query `Fraunces:ital,opsz,wght,SOFT,WONK@...` (User-Agent header required for WOFF2 delivery) and apply `font-variation-settings: 'SOFT' 0, 'WONK' 1` on the `:root` selector.
  - **`.streamlit/config.toml` `[theme] font` field** stays at `"serif"` as a fallback for any Streamlit-native widget that paints before the CSS binds.

- **D-2.17 (Theme delivery mechanism — LOCKED, AMENDS D-2.1):** The CSS lives **embedded as a string constant in a Python module** — `app/brain/theme/theme.py` for production, `previews/_theme.py` for the sandbox. Both expose `inject_theme()` which calls `st.markdown(_CSS, unsafe_allow_html=True)`. This **supersedes** D-2.1's earlier wording ("single scoped-CSS file at `app/brain/theme/surf_theme.css`"). Rationale: one importable module is simpler than path-resolved file reads, and the parallel session already validated it.
  - **Edit-this-later note:** if the CSS string ever exceeds ~800 lines (currently ~480), split into `theme.py` + `theme.css` with a one-line `_CSS = (Path(__file__).with_name("theme.css")).read_text()` swap. The module API stays the same.

- **D-2.18 (Scoping pattern — LOCKED):** Component-level styling is reached via `[class*="st-key-XXX"]` selectors targeting wrappers created by `st.container(key="XXX")`. Widgets inside the wrapper are reached via stable `data-testid` attributes (`stButton`, `stTextInput`, `stSelectbox`, `stCheckbox`, `stRadio`, `stTextArea`, `stNumberInput`, `stSlider`, `stDateInput`, `stTimeInput`, `stToggle`, `stMultiSelect`, `stAlertContainer`, `stMarkdownContainer`). Markdown-rendered HTML helpers (`<p class="surf-eyebrow">`, `<p class="surf-meta">`, etc.) target their own custom classes. **No `unsafe_allow_html=True` for layout** — only for typography helpers. **No JS injection.**
  - **Edit-this-later note:** the canonical key vocabulary used in `theme.py` (`btn-default`, `btn-ghost`, `btn-soft`, `btn-tinted-{accent,ok,info,warn}`, `card-passive`, `card-interactive`, `class-card`, `stat-card`, `topbar`, `topbar-icon`, `empty`, `mcq`) MUST be reused verbatim by both production and sandbox code. Drift breaks the scoped CSS silently.

- **D-2.19 (Python helper primitives — LOCKED):** Ship the 9 helpers from `theme.py` verbatim in both `app/brain/theme/theme.py` and `previews/_theme.py`: `inject_theme()`, `eyebrow(text)`, `caption(text)`, `meta(text)`, `score(value: float)`, `chip(text, variant)`, `chips_row(items)`, `steps(items)`, `stat_card(label, value, eyebrow_text, delta, delta_dir)`, `empty_state_text(headline, body)`. Each is 1–10 lines, pure, no state, no Claude/DB calls. **User-supplied strings must be HTML-escaped** before f-string interpolation (current theme.py does NOT escape — plan 02-01 must add `html.escape()` calls). The `score()` color thresholds (red <3.5, gold 3.5–<5, green ≥5) directly match the Swiss 1–6 grading formula `5 × correct/max + 1` from D-3.4 — reused on P5 final-note (D-4.1) and P2 class card.
  - **Edit-this-later note:** all helpers live in the `# Helper components` section at the bottom of `theme.py`. To add a new HTML primitive, follow the 1-liner pattern: `def name(text): st.markdown(f'<p class="surf-name">{html.escape(text)}</p>', unsafe_allow_html=True)`.

- **D-2.20 (MCQ option design — REPLACED with Figma node `4045:282` canonical spec, 2026-05-02 second amendment):** `theme.py`'s current MCQ design (radio styled as paper card, accent-wash + accent-vibrant on hover/select) is **wrong** and must be discarded. The canonical design comes from Figma node `https://www.figma.com/design/EYjkvHArrBonuiG2JUS2sE/SURF_UI?node-id=4045-282` (saved locally as `docs/design/figma_exports/node_4045-282_mcq_take_mock.png`). Key facts:
  - **All MCQ options use a custom checkbox UI**, never a radio circle — even single-correct questions. This unifies single + multi-correct under one visual (and incidentally closes the Phase 1 D-2.5 multi-correct gap from the prior amendment).
  - **Custom checkbox glyph** (replaces Streamlit's native checkbox visual): 20×20px square, 4px radius, 2px `--paper-5` border. Unchecked: `--paper` background, empty interior. Checked: `--paper-5` background, white "✓" glyph rendered in `JetBrains Mono Bold 14px` at left:3.5px / top:-1px. Streamlit's native checkbox visual is hidden (`opacity:0` or `display:none` on `[data-baseweb="checkbox"] svg`) and the custom glyph is rendered via CSS pseudo-elements OR a wrapper helper `mcq_option(label, key)` in `theme.py` (see helper sketch below).
  - **Four states** with distinct surface treatment:
    | State | Background | Border | Stamp shadow | Padding | Where used |
    |---|---|---|---|---|---|
    | **Off** (unanswered or unselected) | `--paper-1 #ede4d2` | 1px `--paper-shadow #171512` | none | `px-14 py-13` | P4 default, P4 selected-then-cleared |
    | **On** (user-selected during P4) | `--paper-0 #f5efe4` (lighter than Off) | 2px `--paper-shadow` | `2px 2px 0 --paper-shadow` | `px-15 py-14` | P4 active selection |
    | **Correct** (review state on P5) | `--ok-wash #9ec7aa` | 2px `--paper-shadow` | `2px 2px 0 --paper-shadow` | `px-15 py-14` | P5 correct option highlighting |
    | **Incorrect** (review state on P5) | `--accent-soft #e8a798` | 2px `--paper-shadow` | `2px 2px 0 --paper-shadow` | `px-15 py-14` | P5 wrong-pick option highlighting |
  - **Padding shift compensates for border-width change**: 14/13 → 15/14 keeps text x-position stable when the 1px border becomes 2px on selection. Don't drop this — it's why the Figma feels solid on hover/select.
  - **5px container `border-radius`** (NOT `--r-sm 4px` — different from buttons/inputs). Locked exactly: `border-radius: 5px`.
  - **Selection signal is paper elevation + stamp shadow appearing — not an accent color.** Accent colors only appear in the P5 review state (incorrect / correct). The user's pick during P4 is signaled by lifting the paper one shade (paper-1 → paper-0) and adding the stamp shadow. This is the most important visual rule from the Figma — DO NOT default to "selected = accent-colored", that pattern is reserved for review.
  - **No hover state separate from On/Off** — the Figma shows only 3 interactive states (Off/On/Incorrect) plus a Correct review state. CSS `:hover` on Off can lighten background slightly toward `--paper-0` as an affordance hint without crossing the elevation threshold (subtle — keep transition tied to the same 120ms `--t-fast` token).
  - **Edit-this-later note:** the four state selectors live in a clearly-delimited `MCQ OPTION` section in `_CSS`. To re-tone (e.g., switch Correct from green to blue), edit the single bg/border line per state. The custom checkbox glyph CSS lives in a `MCQ CHECKBOX` subsection just below.
  - **Helper Python recipe** for `theme.py` (plan 02-01 implements):
    ```python
    def mcq_option(label: str, *, key: str, state: str = "off") -> bool:
        """Render an MCQ option styled per Figma node 4045:282.
        state ∈ {"off","on","correct","incorrect"}.
        Returns True if checked. The 'on' state is set automatically when state=='off'
        and Streamlit's native checkbox is checked; 'correct'/'incorrect' are review-only,
        forced by the caller from P5.
        """
        with st.container(key=f"mcq-opt-{key}-{state}"):
            return st.checkbox(label, key=f"_mcq_{key}", label_visibility="visible")
    ```
  - **Reach pattern for the scoped CSS** — selectors target `[class*="st-key-mcq-opt-"]` and branch on the state suffix: `[class*="st-key-mcq-opt-"][class*="-off"] { ... }`, `...-on`, `...-correct`, `...-incorrect`. Streamlit appends a stable hash but the `st-key-{exact-string}` portion is preserved. **(Superseded by D-2.20a for the Off/On pair — see below.)**

- **D-2.20a (MCQ Off/On driven by `:has(input:checked)`, NEW 2026-05-02 — amends D-2.20):** the Off/On pair is no longer keyed via static suffixes. The container key is just option identity: `mcq-opt-{question_id}-{option_letter}` (e.g. `mcq-opt-q1-a`). The CSS responds to the inner checkbox's `:checked` state via `:has()`:
  - **Off (default):** `[class*="st-key-mcq-opt-"]:not([class*="-correct"]):not([class*="-incorrect"]) { ... }` paints the paper-1 / 1 px border / no shadow / 13/14 padding spec.
  - **On (live, checkbox checked):** `[class*="st-key-mcq-opt-"]:not([class*="-correct"]):not([class*="-incorrect"]):has(input:checked) { ... }` paints the paper-0 / 2 px border / 2 px stamp / 14/15 padding spec.
  - **Correct / Incorrect (review-only):** keep the state-baked suffix keys (`mcq-opt-{key}-correct` / `-incorrect`). P5 renders them at paint time, not via user interaction. Source-order places them after the `:has()` rules so they win the cascade.
  - **Why amended:** the original D-2.20 keying froze the visual state at render time — clicking an option flipped the checkbox but the wrapper key still said `-off`, so the elevation/stamp-shadow On treatment never appeared. The `:has()` mechanism makes the click feel live (the existing 120 ms transition tweens the bg / border / shadow / padding). Ruling 2026-05-02 (Tiago, Defect 8 of theme-bench review).
  - **Browser support:** Chrome ≥ 105, Safari ≥ 15.4, Firefox ≥ 121 — all 2024+ browsers ship `:has()`. Streamlit's webview is the host browser; macOS team is fine.
  - **Edit-this-later note:** the Off/On selectors live in the `MCQ OPTION` section of `_CSS` in `theme.py`. To revert to state-keyed Off/On (e.g. for a browser without `:has()`), swap each `:not(...)... :has(input:checked)` selector for `[class*="-on"]` and re-add static `-on` / `-off` suffix in the call site. Correct/Incorrect rules are unchanged either way.

- **D-2.23 (Take Mock card container — NEW, from Figma node `4045:282`):** The MCQ card container that wraps Q-number chip + Class chip + Difficulty stars + question text + options + actions. Spec:
  - **Container:** `bg --paper`, `border 2px solid --paper-shadow`, `border-radius 6px`, `box-shadow 3px 3px 0 0 --paper-shadow` (the canonical 3px stamp), `padding 22px 20px 20px 20px` (top 22, sides 20, bottom 20), `max-width 600px`, vertical gap 13px between sections (header / question / options / actions).
  - **Header row** (gap 13px, baseline-aligned): one "Q{n}" chip (Display/Chip Neutral variant — `paper-0` bg, 1.5px paper-shadow border, 999px radius, mono bold 10px tracked-uppercase, 24px height) + one "{class abbreviation}" chip (same style) + one Difficulty stars display (see D-2.24).
  - **Question text:** `Fraunces SemiBold Italic 28px`, `line-height 1.15`, `letter-spacing -1` (≈ -0.035em), color `#1A1814` ("Rangoon Green" — slightly darker than `--paper-5 #28251f`; if pixel-perfect doesn't matter, `--paper-5` is acceptable). Uses `font-variation-settings: 'SOFT' 0, 'WONK' 1` per D-2.16 if WONK axis is loaded; harmless if not.
  - **Options block:** vertical stack, gap 8px (`--item-spacing-xs`), top-padding 3px to clear the question's descender clipping.
  - **Actions row:** equal-flex layout (`flex-1` per child), gap 8px in P4 / 0px in P5-checked. P4: `[Clear] [Clear] [Submit/REST]` — Clear buttons use Ghost variant (2px paper-shadow border, no fill, 0.5/0.5 stamp shadow), Submit uses Default variant (paper-5 bg, white text, 0.5/0.5 stamp shadow + 2px paper-shadow border). P5-checked: only `[REST]` shown full-width (already submitted).
  - **Edit-this-later note:** the card selector in `_CSS` is `[class*="st-key-mcq-card"]`; question_render in `app/mock_take/question_render/` wraps the whole card in `st.container(key="mcq-card-q{question_id}")`. To re-flow the layout (e.g., difficulty on the right instead of inline with chips), edit the header `st.columns` configuration in `question_render.py`.

- **D-2.24 (Difficulty stars display — NEW, from Figma node `4028:141`):** Replaces the text placeholder `—` from D-3.5 (which can stay as a fallback when `difficulty_score IS NULL`). Spec:
  - **Container:** 24px height, `bg --paper-1`, `border 2px solid --paper-shadow`, `border-radius 6px`, `box-shadow 2px 2px 0 0 --paper-shadow` (stamp-sm), `padding 2px 10px`, gap 1px between stars.
  - **5 star slots**, each 20×20px. N filled per the difficulty `level` (1–5 in Figma; map from `difficulty_score: float ∈ [0,1]` via `level = round(score * 5)` clamped to `[1, 5]`). Filled star = solid SVG (Foundation/Icon/Star with `filled=true`); empty star = outline-only SVG.
  - **Star SVGs** can either be inlined as base64 data-URIs in `_CSS` or shipped as separate files in `assets/icons/star_filled.svg` and `assets/icons/star_empty.svg`. Plan 02-01 picks: ship as 2 SVG files (cleaner edits) and reference via `background-image`.
  - **Phase 2 ships placeholder behavior:** when `difficulty_score IS NULL` (Phase 4 ML hasn't landed), display the chip with the `paper-3 dashed` border + the text "—" centered, OR render 0 filled stars. Either is acceptable; pick the latter for visual consistency with the chip frame.
  - **Edit-this-later note:** the star SVGs live in `assets/icons/`; the level→fill mapping lives in `app/mock_take/question_render/_difficulty.py`.

- **D-2.21 (`st.status` + `st.expander` skins — NEW vs theme.py, closes ingestion + review-density gaps):** Two Streamlit-native components used by Phase 2 are currently unstyled:
  - **`st.status`** (P3 ingestion log per D-2.6): paper-0 background, 1.5px paper-3 border, accent-vibrant left-border (3px) when running, ok left-border when complete, accent-vibrant left-border when error. Eyebrow-style label (mono, uppercase, tracked).
  - **`st.expander`** (P5 difficulty breakdown per D-4.2): paper-1 background closed, paper-0 open, mono+uppercase header with caret, 2px stamp-shadow on hover.
  - **Edit-this-later note:** both selectors go in a new section near the bottom of `_CSS` titled `STATUS · EXPANDER`. Reach via `[data-testid="stStatusWidget"]` and `[data-testid="stExpander"]`.

- **D-2.22 (Reconciliation with sandbox-isolation rule):** Two copies of the design system exist by deliberate design:
  - **Production:** `app/brain/theme/theme.py` — imported by `streamlit_app.py` and every `views/<page>.py`.
  - **Sandbox:** `previews/_theme.py` — imported by every `previews/components/<x>/preview.py` and `previews/pages/<x>/preview.py`.
  - Sandboxes **must NOT `from app...` import** the production theme. The drift between the two copies is intentional — when production theme.py changes, the next visual task on a sandbox refreshes the sandbox copy and re-runs the preview gate (per `CLAUDE.md` Visual Preview Gate § "Sandbox rules").
  - **Edit-this-later note:** the migration step in plan 02-01 copies `Streamlit_Test/ui/theme.py` → both destinations and applies amendments D-2.15, D-2.20, D-2.21 to both at the same time.

### Documentation & Knowledge Transfer (Area 7 — NEW, 2026-05-02 third amendment)

This area captures the user's request for a teammate-readable design-system reference. The audience is a non-Claude reader (Tiago and 1–2 teammates) who needs to use the design system without reading the CSS source.

- **D-2.25 (`ui/documentation.md` — NEW Phase 2 deliverable):** A single human-readable guide at `ui/documentation.md` (top-level folder, sibling of `app/`). Audience: Tiago + teammates. **Not** consumed by Claude tooling — it is a documentation artifact. Required sections:
  1. **Overview** — paper-and-stamp aesthetic in two paragraphs; where the CSS lives (`app/brain/theme/theme.py`); how to load it (`inject_theme()` at top of every page); why two copies exist (`app/brain/theme/` vs `previews/_theme.py`).
  2. **Token reference** — every CSS custom property from D-2.12 with one-line description and "use this when…" rule (e.g., `--paper-1` = "passive surface backdrop, used for unselected MCQ options, soft buttons, and stat-card backgrounds; never as a CTA fill").
  3. **Typography hierarchy** — when to use `h1` vs `h2` vs `h3` vs `h4` vs `surf-eyebrow` vs `surf-caption` vs `surf-meta` vs `surf-empty-headline` vs `surf-empty-body`. Each line: page where it appears, CSS variable, example.
  4. **Color combination rules** — explicit DO/DON'T pairs:
     - DO use `--accent-vibrant` for the primary CTA on a page (one per page).
     - DON'T use `--accent-vibrant` as a passive-surface fill (passive = use `--paper-0` or `--paper-1`).
     - DO use `--ok-wash` for "this is the correct answer" on P5; DON'T use it elsewhere.
     - DO use `--accent-soft` for "this is a wrong pick" on P5; DON'T use it as a hover state.
     - DO use `--paper-0` to elevate a selected-but-not-yet-graded state (P4 active MCQ option); the elevation IS the selection signal.
     - DON'T use accent colors during P4 to signal "selected" — that's reserved for P5 review.
     - (List grows from D-2.20 + the rest of the Figma rules surfaced by D-2.26 analysis.)
  5. **Component catalog** — one section per scoped-CSS component (`btn-default`, `btn-ghost`, `btn-soft`, `btn-tinted-{accent,ok,info,warn}`, `card-passive`, `card-interactive`, `class-card`, `stat-card`, `topbar`, `topbar-icon`, `empty`, `mcq-opt-{state}`, `mcq-card`, `difficulty-display`, etc.). Each section contains: 1-line description, the `st.container(key=…)` invocation pattern, all variants, and the rule of when to use it vs an alternative. Screenshot reference (path under `docs/design/figma_exports/`) where useful.
  6. **Stamp shadow recipe** — the signature animation. One paragraph + the 3 offset scales (2/3/4px) + the hover-lift / press-sink rule (D-2.13). Why it's the signature. When NOT to use it (passive surfaces that don't accept clicks).
  7. **Motion rules** — transitions only, no keyframes (D-2.14). The 3 timing tokens (`--t-fast` / `--t-base` / `--t-slow`) and when each applies. The `prefers-reduced-motion` accessibility note (D-2.15).
  8. **DOM reach map** — for each Streamlit widget Phase 2 uses (`st.button`, `st.text_input`, `st.checkbox`, `st.radio`, `st.selectbox`, `st.slider`, `st.tabs`, `st.expander`, `st.status`, `st.dialog`, `st.file_uploader`, `st.sidebar`), the `data-testid` attribute that reaches it + which scoped wrapper key activates which variant. This is the most important section for teammates writing new pages — it tells them HOW to compose.
  9. **Adding a new component** — a 5-step recipe: (a) wrap in `st.container(key="my-component-x")`, (b) add a section to `_CSS` in `theme.py` keyed on `[class*="st-key-my-component"]`, (c) refresh both copies (production + sandbox), (d) ship a preview in `previews/components/my_component/preview.py`, (e) document it here.
  - **Length cap:** target ≤500 lines; split into siblings (`ui/tokens.md`, `ui/components.md`) only if the single file exceeds that. Same audience, same voice.
  - **Edit-this-later note:** the doc is updated at the close of every phase that touches the design system (Phase 2 closes the bulk; Phases 3+ append). The plan-level cadence rule from D-5.2 (sidecar walkthroughs at end-of-wave) extends to this doc — every wave that adds a new scoped component appends a section here before the wave commits.

- **D-2.26 (Figma component-logic analysis — NEW research step in plan 02-01):** Before `theme.py` ships to `app/brain/theme/`, plan 02-01 spawns a researcher pass that walks the Figma file (file key `EYjkvHArrBonuiG2JUS2sE`) and extracts the **rules of use** that aren't visible from a single component's spec — they live across pages, in Figma component descriptions, and in the relationships between components. Output feeds the "Color combination rules" and "Component catalog" sections of `ui/documentation.md`.
  - **Method:**
    1. `mcp__dd11b50e-…__get_metadata` on the file root (page `0:1`) to enumerate every page and frame.
    2. `mcp__dd11b50e-…__search_design_system` for `Button`, `Card`, `Chip`, `Display`, `Container`, `Foundation`, `Status` — capture every component's variants + Figma component description (`(canonical) — pick by rule-book §X.Y` notes are the ground truth for use rules).
    3. `mcp__dd11b50e-…__get_design_context` on each "in-use" frame for Phase 2 pages (P1–P5 wireframes if they exist in the file; otherwise sample 3–5 frames that compose multiple components) — this surfaces composition rules that single-component inspection misses.
    4. `mcp__dd11b50e-…__get_variable_defs` on a representative frame to dump the variable taxonomy (color/Base/*, color/Accent/*, etc.) — this validates the D-2.12 token list against Figma's source of truth.
  - **Cap on tool calls:** ≤30 Figma MCP calls total (the file is medium-sized; 30 is enough to exhaust the high-value frames without burning context). Researcher agent saves a per-component JSONL log to `.planning/phases/02-mock-taking-loop-p1-p5/_research/figma_components.jsonl` for traceability.
  - **Open question to resolve during analysis:** Tiago noted in D-2.1 that the library is `SURF_UI(old)` — researcher must check Tiago's Figma teams for a non-`(old)` revision and reconcile any token drift before locking the production `theme.py`. Use `mcp__dd11b50e-…__search_design_system` with query `SURF_UI` and inspect each match's `library_key`.
  - **Output:**
    1. `ui/documentation.md` — written by the researcher (filling the stub created in this discuss pass).
    2. Reconciliation patches to `02-CONTEXT.md` D-2.12 (token taxonomy) if Figma revision drift is found — append a "Drift" subsection, do not overwrite.
    3. New scoped components added to `theme.py` with their own `[class*="st-key-{name}"]` selectors if the analysis surfaces components used by Phase 2 pages but missing from the current `theme.py` (likely candidates: summary banner for P5, sidebar list pattern for P3, file-uploader skin for P2, dialog skin for the API-key-validate confirm).
  - **Edit-this-later note:** the researcher prompt template lives at `.planning/phases/02-mock-taking-loop-p1-p5/_research/figma_logic_research_prompt.md` (created by plan 02-01). Re-running the researcher (e.g., when the Figma library is revised) just edits the prompt and re-spawns.

### Reconciliation with prior decisions (2026-05-02 amendment)

| Prior decision | Status | Reason |
|---|---|---|
| **D-2.1** (visual identity, theme delivery) | **Amended by D-2.17** | "Single scoped-CSS file at `app/brain/theme/surf_theme.css`" → "Embedded `_CSS` string in `app/brain/theme/theme.py`". Token list in D-2.1 is now superseded by the explicit hex values in D-2.12. |
| **D-2.2** (light only) | Unchanged | `[theme] base = "light"` still correct. config.toml in `Streamlit_Test/` confirms. |
| **D-2.3** (subtle motion incl. fade-in) | **Amended by D-2.14** | Fade-in keyframe dropped. Hover/press transitions only. |
| **D-2.4** (roomy whitespace) | Unchanged | Card padding 18–24px in `theme.py` is consistent. Plan 02-01 keeps the 8-pt scale assertion. |
| **D-2.5..D-2.11** (page-flow UX) | Unchanged | No conflicts with branding work. |
| **D-3.1..D-3.5** (P4 runtime) | Unchanged | D-3.5 difficulty placeholder character (`—`) renders correctly with the locked typography. |
| **D-4.1..D-4.3** (P5 review) | Unchanged | `score()` helper in D-2.19 directly drives the D-4.1 summary banner. |
| **D-5.1..D-5.3** (sidecars) | Unchanged | Theme module gets a sidecar like every other script. |
| **Folded todo** (widget-catalog research) | **Resolved early** | The parallel session produced what `02-WIDGETS.md` was supposed to produce. Plan 02-01's Wave-1 Q1 "Figma extraction spike" → restructured as "validate `theme.py` against Figma + check for `SURF_UI` non-`(old)` revision". |

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
- `https://www.figma.com/design/EYjkvHArrBonuiG2JUS2sE/SURF_UI?node-id=25-2` — **the visual reference.** Components: `Button / Default | Soft | Ghost | Accent | Disabled`, `Container / Card`, `Container / Card Interactive`. Tokens: 6-step Paper ladder, 3-tone Accent (Soft/Deep/Wash), Status/OK/Warn/Info, `Mono/Button Label`. Library is named `SURF_UI(old)` — plan 02-01 Wave-1 (now a validation step, not extraction) checks for a newer revision.
- `docs/design/figma_exports/` — local PNG export(s) of the Figma. Currently contains `node_25-2.png` (the Components page). Additional frame screenshots can be pulled via `mcp__dd11b50e-…__get_screenshot` (URL-based, no desktop selection needed).
- `/Users/tiagoreimann/surf/SURF_UI.fig` — local `.fig` file as offline fallback (binary, not directly parseable; relies on Figma to render).

### Parallel-session output (2026-05-02 amendment — supersedes Wave-1 Q1 extraction spike)
- **`02-PARALLEL-AUDIT.md`** (sibling) — full good/bad/reusable/discard verdict on `/Streamlit_Test/`. **Read before plan 02-01 work.**
- `/Users/tiagoreimann/surf/Streamlit_Test/ui/theme.py` — production-grade scoped-CSS design system (598 lines). Seed for `app/brain/theme/theme.py` (production) AND `previews/_theme.py` (sandbox). Two copies, drift is a feature per CLAUDE.md. **Caveat:** the MCQ section is wrong (D-2.20 amendment, 2026-05-02 second pass) — discard and re-implement per Figma node 4045:282.
- `/Users/tiagoreimann/surf/Streamlit_Test/test_components.py` — working sandbox showing every component composed. Seed for `previews/components/_theme_bench/preview.py`.
- `/Users/tiagoreimann/surf/Streamlit_Test/.streamlit/config.toml` — Streamlit native `[theme]` block mirroring the CSS tokens. Seed for project-root `.streamlit/config.toml` (D-2.2 light + D-2.12 token values).

### Self-hosted fonts (2026-05-02 second amendment, D-2.16 lock)
- `assets/fonts/Fraunces-normal-400_900.woff2` — variable upright, weight axis 400–900, latin subset.
- `assets/fonts/Fraunces-italic-400_900.woff2` — variable italic, weight axis 400–900, latin subset.
- `assets/fonts/JetBrainsMono-Variable.woff2` — variable upright, weight axis 100–800, latin subset.
- Total ~190 KB. WONK/SOFT axes for Fraunces not included in v1 (see D-2.16 edit-this-later note for re-fetch recipe).

### Figma frame screenshots (local cache, supplements live Figma file)
- `docs/design/figma_exports/node_25-2.png` — Components page (existing).
- `docs/design/figma_exports/node_4045-282_mcq_take_mock.png` — Take Mock card across 3 states (Unanswered / Answered / Checked). Canonical reference for D-2.20 (MCQ option), D-2.23 (card container), D-2.24 (difficulty stars).

### Team-facing design-system documentation (NEW deliverable, D-2.25)
- `ui/documentation.md` — single human-readable guide for Tiago + teammates. Structure scaffolded as a stub during this discuss pass; filled by plan 02-01's researcher (D-2.26) and the wave closures that add new scoped components. Audience: non-Claude reader who wants to use the design system without reading the CSS source.

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
- **C-22 line-cap audit at end of Phase 2 — REMOVED 2026-05-03.** Tiago amended C-22 mid-execution: no line cap; clarity is the only criterion. The audit is no longer needed. (Earlier flex note here, mentioning ~120–140 lines and a possible `<script>_walkthrough.md` split, is superseded by the same amendment.)
- **`app/brain/topbar/` rename** — currently misnamed (it covers sidebar + top header bits). Rename in cleanup phase.
- **FigJam end-of-phase visualization** — the spec format is still being defined (per `project_figjam_phase_visualization.md` memory). Phase 2 closeout should include a mock-taking-loop diagram once format is locked.

### Reviewed Todos (not folded)
None — the only matched todo (widget-catalog research) was folded into D-5.x sequence + new `02-WIDGETS.md` deliverable.

</deferred>

---

*Phase: 02-mock-taking-loop-p1-p5*
*Context gathered: 2026-05-02 via /gsd-discuss-phase*

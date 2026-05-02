# Phase 2: Mock Taking Loop (P1–P5) - Research

**Researched:** 2026-05-02
**Domain:** Streamlit 1.50+ UI runtime + streamlit-extras 0.7+
**Confidence:** HIGH

> This is the **widget-catalog research step** mandated by the locked sequence in `02-CONTEXT.md` (Discuss → Research → Plans → Execute). The downstream consumer is `gsd-planner`. Plans 02-xx will cite specific sections of this file by anchor.

---

## Summary

Streamlit 1.50+ ships a **complete, native primitive set** for everything Phase 2 needs — sign-up forms (P1), card lists (P2), live ingestion logs (P3 via `st.status`), single-question mock UI (P4 via `st.fragment` for the timer), and scrollable result lists (P5). The only meaningful gap that Phase 2 will hit is "card-shaped multi-element block with hover styling," and the canonical 2026 answer is **vanilla `st.container(key="x")` + a single `<style>` block keyed against `.st-key-x`** — which the user already locked in `02-CONTEXT.md` D-2.1.

The `streamlit-extras` package is a quality library, but **Streamlit core has absorbed almost everything Phase 2 might want**. Of 56 catalogued extras: **0 GREEN (recommended) for Phase 2**, 6 YELLOW (situational), 50 RED (skip — out-of-scope, deprecated, or replaced by native). Most importantly, `stylable_container` (the user's original top extras candidate) is **deprecated by upstream**; the maintainer's replacement is the very same `st.container(key=...)` pattern Phase 2 already locked.

**Primary recommendation:** Build Phase 2 on **100% vanilla Streamlit 1.50+**. Add no community libraries. Use one CSS file (`app/brain/theme/surf_theme.css`) loaded once via `st.html("<style>{css}</style>")` at the app entrypoint. Use `[theme]` in `.streamlit/config.toml` for global tokens, scoped `.st-key-*` selectors for component-level styling.

---

<user_constraints>

## User Constraints (from 02-CONTEXT.md)

### Locked Decisions

**Sequence (binding):**
1. Discuss intent (CONTEXT.md — DONE)
2. Widget-catalog research (THIS FILE)
3. Plans 02-xx (only after this file exists)
4. Execution (only after plans approved)

**UI Design System (Area 1):**
- D-2.1 Visual identity: editorial/paper aesthetic from Figma library `SURF_UI(old)` (file id `EYjkvHArrBonuiG2JUS2sE`). Tokens: `Paper0–Paper5` (6-step warm paper ladder), `Accent/Soft|Deep|Wash` (3-tone), `Status/OK|Warn|Info`, `Mono/Button Label`. **All visual tokens flow through `.streamlit/config.toml [theme]` + `app/brain/theme/surf_theme.css`** (loaded once via `st.html` in `streamlit_app.py`).
- D-2.2 Light theme only — `[theme] base = "light"`. No dark variant in Phase 2.
- D-2.3 Subtle motion — CSS-only (hover transitions on Card Interactive + buttons, gentle fade-in via `@keyframes`, button press feedback). No JS animations, no page transitions, no confetti, no animated counters. Motion intensity controlled by `--surf-motion-scale` custom property (default `1`, set to `0` to disable).
- D-2.4 Roomy whitespace — 8-pt scale, generous card padding (24–32px), spacing scale lives as `--surf-space-*` custom properties.
- **Edit-this-later rule (LOCKED):** every visual decision ships with an "edit-this-later" note in plan/sidecar (where it lives, what to change, how the swap propagates).

**Page-flow UX (Area 2):**
- D-2.5 P2 factsheet review: rendered factsheet only via `factsheet_renderer.py`; raw JSON behind `Show raw JSON` expander; buttons `Save class` / `Reject & re-upload`; no editable form.
- D-2.6 P3 ingest progress: `st.status` block with live log lines (`Extracting PDF…`, `Splitting into pages…`, `Generating LOs…`, `Generating MCQs (batch i/N)…`).
- D-2.7 Tab-close during ingestion: backend continues; pending lectures show "Resume ingestion" affordance on revisit; no `beforeunload` warning.
- D-2.8 Mock entry points: TWO only — (1) "Generate Mock" CTA on P3 main column, (2) "Study Next" card in P3 sidebar. **REQUIREMENTS.md amendment #1:** MECH-02 changes from "user picks one LO" to "Study Next surfaces an LO; user taps the card."
- D-2.9 Lecture multi-select: Card Interactive (Figma) per lecture, click toggles selection, selected = `Accent/Deep` border + checkmark. Live counter "{N} lectures × 5 = {5N} questions". Card key = `lecture-{id}`.
- D-2.10 P3 layout: sidebar = Past Attempts + Study Next. Main = Generate Mock CTA + lecture multi-select.
- D-2.11 Study Next algorithm v1: weakest LO by `correct/total` ratio, tiebreak most-recently-attempted; hide if zero attempts. Pure SQL, no ML.

**P4 Take Mock Runtime (Area 3):**
- D-3.1 SKIP semantics: advance-only, returnable. Skip records `selected_indices = NULL`; user can navigate back via Prev. NULL on submit = wrong.
- D-3.2 Timer placement: top header bar, right-aligned. Format: `Elapsed: 12:34`. Always visible.
- D-3.3 Resume + answer-change: UPSERT on Next/Prev/Skip navigation events (NOT every checkbox tick). Schema enforces `UNIQUE(attempt_id, question_id)`. Reopening resumes at next unanswered question; timer continues from saved `attempts.start_time`.
- D-3.4 Multi-correct grading: all-or-nothing v1. 1 point iff `selected_indices == correct_indices` (exact set equality), else 0.
- D-3.5 Difficulty score visible during P4 mock (placeholder `—` when NULL).

**P5 Review (Area 4):**
- D-4.1 P5 layout: scrollable list of result Cards (one per question, ordered by `question_order`); final note + summary banner pinned at top.
- D-4.2 P5 detail density: rationale upfront (always visible) + difficulty score upfront. 6 individual difficulty features behind `▸ Difficulty breakdown` expander.
- D-4.3 PRACTICE size: ALL MCQs where `source_page IN <Study-Next-LO page_range>`. **REQUIREMENTS.md amendment #2:** MECH-02 changes from "1 question per slide" to "every MCQ tied to the LO's page range."

**Sidecar walkthroughs (Area 5):**
- D-5.1 Structure: `## Code walkthrough` section at bottom. Function-by-function plain-language paragraph, format: `**def my_func(args)** — In plain language: takes X, does Y because Z, hands back W. Look out for: <gotcha>.` No line refs. No code dumps.
- D-5.2 Cadence: end of every wave.
- D-5.3 Back-fill: all 15 Phase 1 sidecars get walkthroughs back-filled before/as first wave of Phase 2.
- C-22 flex: walkthroughs may push sidecars to ~140 lines; cap revisited end of Phase 2.

### Claude's Discretion (open for this researcher / planner)

- Exact hex values for Paper0–Paper5, Accent/Soft|Deep|Wash, Status/OK|Warn|Info — extracted from Figma in research step (NOTE: actual hex extraction requires Figma desktop selection + `get_variable_defs` MCP; **NOT yet in this RESEARCH.md** — see Open Questions §11).
- Exact monospace font name from `Mono/Button Label` text style.
- Exact button paddings, border-radii, shadow values.
- Card content layout per page (lecture card / attempt card / question result card).
- P4 progress indicator format ("Q3 of 15" vs progress bar vs both).
- Submit-Mock button placement and gating.
- Internal helper function names within each pipeline folder.
- Whether scoped CSS is one big `surf_theme.css` or split per-component (recommend single file v1).

### Deferred Ideas (OUT OF SCOPE — do not research alternatives)

- Editable factsheet JSON → Phase 3.
- Dark theme variant → Phase 3.
- Manual LO picker for PRACTICE → Phase 3.
- Real ML difficulty scores → Phase 4.
- ML-based Study Next → Phase 4.
- Sample factsheet/lecture PDFs polish → Phase 5.
- C-22 audit → end of Phase 2.
- `app/brain/topbar/` rename → cleanup.
- FigJam phase visualization → spec pending; **DROPPED from Phase 2 scope** per user direction in this research request.

</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID | Description (from CONTEXT + ROADMAP) | Research Support |
|----|--------------------------------------|------------------|
| **PAGE-01** | P1 Sign Up: username + Anthropic API key, validated against Anthropic before save. | §2 stack (st.text_input, st.form, st.form_submit_button); §4.1 forms-vs-callbacks (P1 = `st.form` for batch); §11 first-launch routing via `is_authenticated()` |
| **PAGE-02** | P2 My Classes: class card list + Add Class flow (PDF upload → cleaner → review → save). | §2 (`st.file_uploader`, `st.expander`, `st.button`, `st.container(key=...)`); §3 scoped CSS card pattern; §4.2 file_uploader reset |
| **PAGE-03** | P3 Class hub: lecture upload triggers live ingestion (`st.status`); Generate Mock CTA; lecture multi-select (Card Interactive); sidebar = Past Attempts + Study Next. | §2 (`st.status`, `st.sidebar`, `st.container`); §3 Card Interactive scoped CSS; §4.3 fragments for log streaming |
| **PAGE-04** | P4 Take Mock: one MCQ at a time; total-elapsed timer in header; SKIP/PREV/NEXT; persists to DB; resumes. | §2 (`st.checkbox`, `st.radio`, `st.button`, `st.fragment(run_every="1s")`); §4.4 fragment isolation rules; §4.5 session_state vs DB; §5 anti-pattern: stale widget after rerun |
| **PAGE-05** | P5 Review Mock: scrollable list of result Cards; rationales upfront; difficulty scores upfront; Swiss-formula final note. | §2 (`st.container(key=...)`, `st.expander`, `st.metric`, `st.markdown`); §3 result-card scoped CSS |
| **PIPE-02** | Validate API key via `claude_client` before save. | §2 (`st.spinner` during validation); existing `app/brain/claude_client/claude_client.py` does the call |
| **MECH-01** | Mock taking loop end-to-end with timer + persistence. | §2 + §4 (timer fragment + UPSERT-on-navigation pattern) |
| **MECH-02** | (AMENDED — see CONTEXT D-2.8 + D-4.3) Generate Mock + Study Next; PRACTICE = all MCQs in LO page range. | §4.6 navigation patterns; pure-SQL Study Next algo (D-2.11) |
| **MECH-03** | All-or-nothing grading; Swiss formula `5 × correct/max + 1`. | No new UI primitives needed; render via `st.metric` or `st.markdown` |
| **GRADE-04** | Per-question rationale + difficulty visible on P5 result card. | §3 result-card scoped CSS pattern |

</phase_requirements>

---

## Architectural Responsibility Map

Phase 2 is a **single-tier** Streamlit app. There is no separate API tier, CDN, or browser SPA — every capability runs in the Streamlit Python process.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Sign-up form (P1) | Streamlit page (`views/signup.py` + `app/signup/signup_flow/`) | SQLite (`~/.surf/user.sqlite`) | Local single-user app; no auth provider |
| API key validation (P1) | Streamlit page → `app/signup/api_key_validate/` → existing `claude_client` | Anthropic API (1-token call) | Validation is a Claude ping, run in-band |
| Class CRUD (P2) | Streamlit page (`views/my_classes.py`) | SQLite via `app/db/queries_classes` | Stdlib `sqlite3` — no ORM (C-08) |
| PDF → factsheet (P2 Add Class) | Already-shipped Phase 1 pipeline (`factsheet_clean/`) | — | Reuse, do not re-implement |
| Lecture ingestion (P3) | Already-shipped Phase 1 orchestrator (`lecture_ingest/`) wrapped in `st.status` | Anthropic API | In-band call; Phase 1 D-4.5 partial-success policy handles tab-close |
| Mock building (P3) | `app/class_/build_mock/` (NEW) | SQLite | Pure SQL; selection logic per Phase 1 D-02 |
| Mock taking (P4) | Streamlit page (`views/mock_take.py`) + `app/mock_take/*` | SQLite (UPSERT on navigation) | `st.fragment` runs the timer; main page handles question render + nav |
| Timer (P4) | `st.fragment(run_every="1s")` inside header bar | `st.session_state["mock_start_ts"]` | Fragment partial-rerun; does NOT reset MCQ widget state. See §4.3 |
| Mock review (P5) | Streamlit page (`views/mock_review.py`) + `app/mock_review/*` | SQLite read | Pure render; no Claude calls |
| Theme + scoped CSS | `.streamlit/config.toml [theme]` + `app/brain/theme/surf_theme.css` loaded via `st.html` once at `streamlit_app.py` entry | — | Token-driven, see §3 |

---

## Streamlit Version + Course-Alignment Note

**Pinned version:** **Streamlit ≥ 1.50.0** (latest stable: 1.54.0 per Context7 `/streamlit/streamlit` library record on 2026-05-02). Phase 2 uses 1.50+ features that postdate the course material. The course Streamlit notebook (`canvas_downloads/module4/notebooks/streamlit_demo_full.py`) teaches: `st.set_page_config`, `st.header(divider='rainbow')`, `st.columns(2) + with col:`, `st.sidebar.write`, `st.container()`, `st.toggle`, `st.button`, `st.data_editor`, `st.bar_chart`. **The course defers to docs.streamlit.io for everything else.** [VERIFIED: course notebook content in `canvas_downloads/module4/`]

### Features Surf uses that postdate the course material

These are the features the planner must flag in sidecar walkthroughs (D-5.1) — non-engineer teammates will not have seen them in class:

| Feature | Streamlit version added | Used in Phase 2 for | Walkthrough framing |
|---------|------------------------|---------------------|---------------------|
| `st.fragment` (decorator + `run_every`) | 1.33 | P4 timer (independent rerun every 1s without resetting MCQ widget state) | "A fragment is a slice of the page that re-runs by itself. We use it to tick the timer." |
| `st.dialog` (decorator) | 1.35 | (Phase 3 P7 reset confirm — flagged here for forward awareness) | — |
| `st.container(key=...)` (CSS-targetable class `.st-key-<key>`) | 1.36 | Every editorial Card in Phase 2 | "We add a `key` so we can write CSS that only targets that card." |
| `st.html("<style>...</style>")` | 1.33 | Loading `surf_theme.css` once at app entry | "Streamlit's polite way to inject our hand-written CSS file." |
| `st.feedback`, `st.pills`, `st.segmented_control` | 1.35–1.39 | NOT used in Phase 2 (Card Interactive replaces segmented control per D-2.9) | — |
| `st.navigation` + `st.Page` | 1.36 | Multipage routing (replaces legacy `pages/` directory) | "The new way to wire pages in Streamlit. Each page is a function." |
| `st.toast` | 1.27 | "Class saved", "Mock submitted" non-blocking confirmations | Course-aligned (commonly shown in demos) |
| `[theme]` color palette knobs (`redColor`, `greenColor`, …) | 1.50 | Setting `Status/OK = green`, `Status/Warn = orange`, `Status/Info = blue` natively | "We tell Streamlit our exact palette so its built-in chips/badges/alerts match our editorial look without CSS." |
| `MultiselectColumn` in dataframes | 1.50 | NOT used in Phase 2 | — |
| `st.write_stream` | 1.31 | (Optional: ingestion log streaming if we want typewriter feel — currently using `st.status`) | — |

[VERIFIED: Streamlit 1.50 release notes via WebSearch 2026-05-02]
[CITED: https://discuss.streamlit.io/t/version-1-50-0/119561]
[CITED: https://docs.streamlit.io/develop/quick-reference/release-notes]

### `st.navigation` vs legacy `pages/` directory — which Surf uses

Surf uses **`st.navigation` + `st.Page`** (the modern pattern), not the legacy `pages/` directory. The codebase already has `streamlit_app.py` as the entrypoint with an `is_authenticated()` router; Phase 2 wires P1–P5 into this entrypoint via `st.navigation`. Legacy `pages/` is auto-discovered and creates a sidebar nav we don't want (P4 hides the standard sidebar; P1 has no nav). [CITED: https://docs.streamlit.io/develop/concepts/multipage-apps]

```python
# streamlit_app.py (illustrative, post-Phase 2)
import streamlit as st
from app.brain.theme import load_theme
from app.signup.signup_flow import is_authenticated

load_theme()  # st.html("<style>...</style>") with surf_theme.css

if not is_authenticated():
    st.Page("views/signup.py", title="Sign up").run()  # P1, full-takeover
    st.stop()

pages = [
    st.Page("views/my_classes.py", title="My Classes", default=True),
    st.Page("views/class_view.py", title="Class"),  # P3
    st.Page("views/mock_take.py", title="Take Mock"),  # P4
    st.Page("views/mock_review.py", title="Review"),  # P5
]
pg = st.navigation(pages, position="hidden")  # P4/P5 control nav themselves
pg.run()
```

---

## §2. Element Catalog (Green-list for Phase 2)

This table is the **planner's vocabulary**. Every plan 02-xx will use only elements from this table (or document why it needs more). Each row: element → use site (page + decision) → key kwargs → snippet ref.

### 2.1 Input widgets

| Element | Phase 2 use site | Key kwargs | Notes |
|---------|------------------|-----------|-------|
| `st.text_input` | P1 username field; P1 API key field (`type="password"`) | `key`, `type`, `placeholder`, `disabled` | Inside `st.form` for P1 (batch submit) |
| `st.file_uploader` | P2 factsheet PDF upload; P3 lecture PDF upload | `key`, `type=["pdf"]`, `accept_multiple_files=False` | **STALE STATE GOTCHA — see §5**. Must reset after consuming via `st.session_state.pop(key)` + `st.rerun()`. |
| `st.button` | P1 submit; P2 "Save class" / "Reject"; P3 "Generate Mock" CTA + Card Interactive (one button per card); P4 PREV/SKIP/NEXT/Submit; P5 "Take another" | `key`, `type="primary"|"secondary"|"tertiary"`, `disabled`, `use_container_width` | **NEVER set state via session_state for buttons** (raises `StreamlitAPIException`). Click logic must run BEFORE downstream widgets render. |
| `st.checkbox` | P4 MCQ option toggles when `len(correct_indices) ≥ 2` | `key=f"q{qid}_opt{i}"`, `value=initial_from_db` | Use checkbox for multi-correct (Phase 1 D-2.5) |
| `st.radio` | P4 MCQ option toggle when `len(correct_indices) == 1` | `key`, `options`, `index=None` for no-default | Use radio for single-correct |
| `st.form` + `st.form_submit_button` | P1 sign-up batch submit (no rerun on per-keystroke) | `key`, `clear_on_submit=False`, `border=True` | See §4.1 — P1 uses form, P3/P4 use raw widgets + buttons |
| `st.toggle` | (none in Phase 2 — flagged for P7 Settings later) | — | Course-aligned but unused in P1–P5 |

### 2.2 Layout & containers

| Element | Phase 2 use site | Key kwargs | Notes |
|---------|------------------|-----------|-------|
| `st.container` | **EVERY editorial Card** (class card, lecture card, attempt card, question card, result card, mock card, etc.) | `key="..."`, `border=True|False` | **The single most-used primitive in Phase 2.** `key` generates a `.st-key-<key>` CSS class for scoped styling — see §3. |
| `st.columns` | P3 Card Interactive grid; P4 PREV/NEXT button row; P5 result-card layout | `spec=[1, 2, 1]` or `spec=N`, `gap="small"|"medium"|"large"`, `vertical_alignment` | Course-aligned. Can nest inside `st.container`. |
| `st.expander` | P2 "Show raw JSON" (D-2.5); P5 "▸ Difficulty breakdown" (D-4.2) | `expanded=False`, `icon=":material/code:"` | Course-aligned. |
| `st.sidebar` | P3 Past Attempts list + Study Next card (D-2.10) | (use as `with st.sidebar:` block) | Course-aligned. **NOTE:** P4 hides the sidebar via custom CSS to maximize MCQ focus. |
| `st.tabs` | (none in Phase 2 — Card Interactive replaces tabbed entry-point switch per D-2.8) | — | Available; not used. |
| `st.popover` | (optional: P4 question-jump menu — Claude discretion per CONTEXT) | `label`, `icon`, `use_container_width` | YELLOW: only if planner picks it. Default = no popover (linear flow). |
| `st.empty` | P3 ingest progress placeholder if `st.status` is insufficient | — | Probably unused; `st.status` is the right primitive. |
| `st.dialog` | (Phase 3 P7 — flagged for forward awareness, NOT used in Phase 2) | — | — |

### 2.3 Display & status

| Element | Phase 2 use site | Key kwargs | Notes |
|---------|------------------|-----------|-------|
| `st.markdown` | Most text rendering; rationale display in P5; factsheet renderer output in P2 | `unsafe_allow_html=False` (default — keep it false except for our own theme injection) | **NEVER set `unsafe_allow_html=True` for user-invented HTML structure** (anti-pattern from CONTEXT). Theme CSS injection uses `st.html` instead. |
| `st.html` | Inject `surf_theme.css` once in `streamlit_app.py` (`st.html(f"<style>{css}</style>")`) | (single string arg) | The polite way to ship our hand-written CSS file. **Do once, not per-page.** |
| `st.status` | **P3 lecture ingestion log (D-2.6).** | `label="Ingesting lecture..."`, `expanded=True`, `state="running"|"complete"|"error"` | The canonical primitive. Use as a context manager; call `.update(label=, state=, expanded=)` from inside. See §4.7. |
| `st.toast` | "Class saved", "Mock submitted", "API key valid" non-blocking confirmations | `body`, `icon="✅"|"❌"|"ℹ️"` | Returns a handle; can call `.toast()` again to update in place. |
| `st.metric` | P5 summary banner (Swiss-formula final note, X/Y correct, total elapsed) | `label`, `value`, `delta`, `delta_color` | Use for the headline number on P5. **Not** for the timer (timer is plain text inside fragment, see §4.3). |
| `st.badge` | Small status chips (e.g., lecture status: `pending` / `done`); difficulty placeholder when score is `—` | `label`, `icon`, `color` | Native in 1.50+. With `[theme]` palette knobs we get exact Surf accent colors. |
| `st.progress` | (optional: P4 mock progress "Q3 of 15" — Claude discretion per CONTEXT) | `value=0..1`, `text` | YELLOW: planner picks per Figma. Default per CONTEXT: match Figma. |
| `st.divider` | Section separators in P5 between cards | (no args) | Roomy whitespace per D-2.4 — `<hr>` styled via theme. |
| `st.image` | (none required in Phase 2 — no logos or hero images yet) | — | Available if Figma needs it. |
| `st.spinner` | P1 API-key validation ("Verifying with Anthropic...") | `text` | Use during the 1-token Claude ping. |
| `st.error` / `st.warning` / `st.info` / `st.success` | P1 invalid API key; P3 "ingestion failed"; P2 "factsheet rejected" | `body`, `icon` | Color-honor `[theme]` palette in 1.50+. |
| `st.write` | (avoid — too magical; use `st.markdown` for text and the typed primitives for everything else) | — | Course-aligned but Surf prefers explicit. |
| `st.json` | P2 "Show raw JSON" expander content | `expanded=False` | Inside `st.expander`. |
| `st.code` | (none expected in Phase 2) | — | — |

### 2.4 Navigation, state, runtime

| Element | Phase 2 use site | Key kwargs | Notes |
|---------|------------------|-----------|-------|
| `st.navigation` + `st.Page` | `streamlit_app.py` entry router | `position="hidden"` for P4/P5 nav | See §1 above. Modern pattern, replaces `pages/`. |
| `st.switch_page` | After P1 success → P2; after P2 save → P3 of new class; after P4 submit → P5 | `page` (path or `st.Page` object) | Use after writing to DB/session_state. |
| `st.session_state` | P4 mock state (`mock_id`, `current_q_index`, `start_ts`); P3 ingest target id | (dict-like) | **STALE STATE GOTCHA — see §5.** Mutate before widgets render, not after. |
| `st.query_params` | (optional: deep-link to a specific attempt for P5 — Claude discretion) | (dict-like) | YELLOW: nice-to-have; not required for Phase 2 success criteria. |
| `st.cache_data` | (avoid for SQLite — SQLite reads are fast enough; only use for expensive pure-Python compute) | `ttl`, `hash_funcs` | See §4.5. |
| `st.cache_resource` | Reuse `sqlite3.Connection` across reruns/sessions; reuse Anthropic client (already inside `claude_client`) | `show_spinner=False` | See §4.5 — sqlite3 thread safety caveat. |
| `st.rerun` | After UPSERT in P4 navigation; after API key validates in P1 | `scope="app"|"fragment"` | Use sparingly — see §5 anti-patterns. |
| `st.stop` | Inside auth router after `st.Page("views/signup.py").run()` to halt below-the-fold code | — | The clean way to gate. |
| `st.set_page_config` | Once at app entry (or per-page for title/icon override) | `page_title`, `page_icon`, `layout="centered"|"wide"`, `initial_sidebar_state` | Course-aligned. |
| `st.fragment` | **P4 timer (`run_every="1s"`)**; (optional: P3 ingest log auto-scroll) | `run_every="1s"`, `args` | See §4.3. **The single most important Streamlit-1.33+ primitive for Phase 2.** |

### 2.5 Elements deliberately NOT used in Phase 2

| Element | Why skipped |
|---------|-------------|
| `st.feedback`, `st.pills`, `st.segmented_control` | Card Interactive replaces them per D-2.9 |
| `st.chat_input`, `st.chat_message`, `st.write_stream` | No chat UI in Phase 2; ingestion log uses `st.status` |
| `st.dataframe`, `st.data_editor` | No tabular data in Phase 2 — every list is a card list |
| `st.bar_chart` / `st.line_chart` / `st.area_chart` / `st.scatter_chart` | Phase 3 (Dashboard) only |
| `st.balloons`, `st.snow` | JS-driven anti-pattern (CONTEXT hard red) |
| `st.audio`, `st.video`, `st.camera_input`, `st.audio_input` | Out of scope |
| `st.connection`, `st.connections.SQLConnection` | **Requires SQLAlchemy** — banned by C-08. Use stdlib `sqlite3` directly. [VERIFIED via Streamlit docs: `pip install SQLAlchemy==1.4.0` listed as required for SQL connection]. |
| `st.login`, `st.logout`, `st.user` | Single-user local app; no identity provider |
| `st.map`, `st.pydeck_chart` | No geo data |
| `st.color_picker`, `st.date_input`, `st.time_input`, `st.datetime_input`, `st.number_input`, `st.slider`, `st.select_slider` | Not needed for P1–P5 forms |
| `st.menu_button`, `st.page_link`, `st.link_button`, `st.download_button` | Phase 3+ |
| `st.echo`, `st.help`, `st.iframe`, `st.latex`, `st.text` | Out of scope |
| `st.balloons` / `st.snow` | JS animation, banned per CONTEXT D-2.3 |

[CITED: https://docs.streamlit.io/develop/api-reference]

---

## §3. Scoped CSS Pattern Reference

**This is the canonical Phase 2 styling pattern. Every plan that creates a new visual component MUST cite this section.**

### 3.1 The pattern in 4 lines

```python
# 1. Wrap content in a keyed container
with st.container(key="surf-class-card"):
    st.markdown("### MII (Microeconomics II)")
    st.caption("Prof. Boscan • Spring 2026")
    st.button("Open class", key="open-MII")
```

```css
/* surf_theme.css — targeted at the auto-generated .st-key-<key> class */
.st-key-surf-class-card {
  background: var(--surf-paper-1);
  border: 1px solid var(--surf-paper-3);
  border-radius: var(--surf-radius-card);
  padding: var(--surf-space-card);
  transition: transform 120ms ease, box-shadow 120ms ease;
}
.st-key-surf-class-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--surf-shadow-soft);
}
```

**How it works:** `st.container(key="X")` adds the class `st-key-X` to the container's outer `<div>`. CSS selectors targeting `.st-key-X` apply only to that container and its descendants. No JS, no `unsafe_allow_html=True`, no dependencies.

[VERIFIED: Context7 `/streamlit/docs` — "the `key` argument in st.container gets added as class name to the container. This is the preferred way to apply CSS styles for specific elements in Streamlit."]
[VERIFIED: WebSearch 2026-05-02 — Streamlit issue #9666 + Discuss thread "CSS Styling For Specific Component" both confirm `.st-key-<key>` is the documented public class.]
[VERIFIED: streamlit-extras maintainer's deprecation note for `stylable_container` — "the key argument in st.container [...] is the preferred way to apply CSS styles for specific elements in Streamlit."]

### 3.2 How CSS is loaded (once, at app entry)

Single source of truth: `app/brain/theme/surf_theme.css`. Loaded ONCE at the top of `streamlit_app.py`:

```python
# app/brain/theme/__init__.py
from pathlib import Path
import streamlit as st

_CSS = Path(__file__).with_name("surf_theme.css")

def load_theme() -> None:
    """Load the Surf theme CSS once at app entry. Idempotent across reruns."""
    st.html(f"<style>{_CSS.read_text()}</style>")
```

```python
# streamlit_app.py
from app.brain.theme import load_theme
load_theme()  # before st.navigation
```

**Why `st.html` and not `st.markdown(unsafe_allow_html=True)`:**
- `st.html` is the **explicit, audited primitive** for HTML/CSS injection (added 1.33). It does not enable HTML in markdown elsewhere.
- `st.markdown(..., unsafe_allow_html=True)` weakens the entire app's markdown safety surface; the CONTEXT anti-pattern reminder explicitly forbids using it for user-invented HTML structure.

[CITED: https://docs.streamlit.io/develop/api-reference/text/st.html]

### 3.3 Theme tokens — `[theme]` block + CSS custom properties

**Two layers:**

1. **`.streamlit/config.toml [theme]` block** — Streamlit-aware tokens. These cascade automatically into Streamlit's own widgets (buttons, sliders, alerts, badges).
2. **CSS custom properties in `surf_theme.css`** — Surf-specific tokens (Paper ladder steps, motion scale, custom shadows). These are referenced by the scoped `.st-key-*` rules.

**Layer 1 — `.streamlit/config.toml`** (ready-to-paste skeleton; exact hex values to be filled in by the planner from Figma extraction — see §11 Open Questions):

```toml
[theme]
base = "light"

# Brand
primaryColor = "#TBD-Accent-Deep"            # from Figma Accent/Deep
backgroundColor = "#TBD-Paper-0"             # from Figma Paper0 (warmest paper)
secondaryBackgroundColor = "#TBD-Paper-1"    # from Figma Paper1
textColor = "#TBD-Shadow"                    # from Figma Base/Shadow

# Borders / radius
borderColor = "#TBD-Paper-3"                 # from Figma Paper3
showBorderAroundInputs = true                # editorial aesthetic
baseRadius = "0.5rem"                        # mid; per-component radius via CSS custom props

# Typography (Mono/Button Label is the signature aesthetic move)
font = "TBD-body-font"                       # likely a serif from Figma
headingFont = "TBD-heading-font"
codeFont = "TBD-mono-font"                   # the same as button labels

# Status palette (1.50+ knobs — set so st.badge/st.success etc. honor Surf colors)
greenColor = "#TBD-Status-OK"
orangeColor = "#TBD-Status-Warn"
blueColor = "#TBD-Status-Info"
```

[CITED: https://docs.streamlit.io/develop/api-reference/configuration/config-toml]

**Layer 2 — `surf_theme.css`** (skeleton):

```css
/* surf_theme.css — Surf editorial Paper theme */

/* === Surf custom properties === */
:root {
  /* Paper ladder (6 steps, warmest → coolest) */
  --surf-paper-0: #TBD;
  --surf-paper-1: #TBD;
  --surf-paper-2: #TBD;
  --surf-paper-3: #TBD;
  --surf-paper-4: #TBD;
  --surf-paper-5: #TBD;

  /* Accent (3 tones) */
  --surf-accent-soft: #TBD;
  --surf-accent-deep: #TBD;
  --surf-accent-wash: #TBD;

  /* Status (mirrors [theme] knobs above) */
  --surf-status-ok: var(--st-green-color);
  --surf-status-warn: var(--st-orange-color);
  --surf-status-info: var(--st-blue-color);

  /* Base */
  --surf-shadow: #TBD;

  /* Spacing (8-pt scale, D-2.4) */
  --surf-space-1: 0.5rem;   /* 8px */
  --surf-space-2: 1rem;     /* 16px */
  --surf-space-3: 1.5rem;   /* 24px */
  --surf-space-4: 2rem;     /* 32px */
  --surf-space-card: var(--surf-space-3);  /* default card padding 24px */
  --surf-space-card-lg: var(--surf-space-4); /* roomy card padding 32px */

  /* Radius */
  --surf-radius-card: 0.75rem;
  --surf-radius-button: 0.5rem;

  /* Shadows */
  --surf-shadow-soft: 0 1px 2px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.04);
  --surf-shadow-card-hover: 0 4px 16px rgba(0, 0, 0, 0.08);

  /* Motion (D-2.3 — set to 0 to disable all motion globally) */
  --surf-motion-scale: 1;
  --surf-transition-card: calc(120ms * var(--surf-motion-scale)) ease;
}

/* === Streamlit-native CSS custom properties Surf reads/overrides === */
/* Streamlit exposes [theme] options as --st-<option-name-in-kebab-case>:
   theme.primaryColor              → --st-primary-color
   theme.backgroundColor           → --st-background-color
   theme.secondaryBackgroundColor  → --st-secondary-background-color
   theme.textColor                 → --st-text-color
   theme.borderColor               → --st-border-color
   theme.font                      → --st-font
   theme.headingFont               → --st-heading-font
   theme.codeFont                  → --st-code-font
   theme.baseRadius                → --st-base-radius
   theme.greenColor                → --st-green-color
   theme.orangeColor               → --st-orange-color
   theme.blueColor                 → --st-blue-color
   theme.redColor                  → --st-red-color
   ... (one per [theme] option, kebab-cased) */
```

[CITED: https://docs.streamlit.io/develop/concepts/custom-components/components-v2/theming — "For any theme configuration option, use the CSS custom property `--st-<option-name>` to reference its value, where `<option-name>` is the option's name in dash-case"]

### 3.4 Worked example — the editorial Card Interactive (P3 lecture multi-select per D-2.9)

The Card Interactive (Figma: `Container / Card Interactive`) is the most CSS-heavy component in Phase 2. Below is the full pattern.

```python
# app/class_/build_mock/lecture_card_render.py
import streamlit as st

def render_lecture_card(lecture_id: int, title: str, status: str, selected: bool) -> bool:
    """Render one Card Interactive for the lecture multi-select grid.
    Returns the new selected state after this render (caller owns the state dict)."""
    key = f"lecture-{lecture_id}"
    selected_class = "is-selected" if selected else ""

    with st.container(key=key):
        # Whole card is clickable via a transparent overlay button
        cols = st.columns([8, 1])
        with cols[0]:
            st.markdown(f"**{title}**")
            st.caption(f"Status: {status}")
        with cols[1]:
            # Checkmark when selected (CSS shows/hides via .is-selected on parent)
            if selected:
                st.markdown(":material/check_circle:")

        clicked = st.button(
            "Toggle selection",
            key=f"{key}-toggle",
            type="tertiary",          # ghost-styled by theme
            use_container_width=True,
        )

    return (not selected) if clicked else selected
```

```css
/* surf_theme.css — Card Interactive styles */
.st-key-lecture-1, .st-key-lecture-2, .st-key-lecture-3 /* ... */ {
  /* NOTE: each lecture key gets its own class. We can also use an attribute selector
     to target all lecture cards: */
}

/* Better: target every Card Interactive via a key prefix */
[class*="st-key-lecture-"] {
  background: var(--surf-paper-1);
  border: 1px solid var(--surf-paper-3);
  border-radius: var(--surf-radius-card);
  padding: var(--surf-space-card);
  cursor: pointer;
  transition: var(--surf-transition-card);
}
[class*="st-key-lecture-"]:hover {
  border-color: var(--surf-accent-soft);
  box-shadow: var(--surf-shadow-card-hover);
  transform: translateY(-2px);
}
/* Selected state — the parent st.container does NOT get a class for selection;
   we encode it in a child element instead. The simplest way is to set selected
   state via a separate keyed sub-container per card: */
.st-key-lecture-1.is-selected,  /* etc. */
[class*="st-key-lecture-"]:has(.st-key-selected-marker) {
  border-color: var(--surf-accent-deep);
  background: var(--surf-accent-wash);
}

/* Hide the toggle button's text but keep it clickable as a full-card overlay */
[class*="st-key-lecture-"] [data-testid="stBaseButton-tertiary"] {
  position: absolute;
  inset: 0;
  opacity: 0;  /* invisible click surface */
}
```

> **`data-testid` warning:** `data-testid="stBaseButton-tertiary"` is **not part of Streamlit's public API**. It is stable across patch versions but **may break on minor Streamlit upgrades**. Surf accepts this risk for the Card Interactive overlay only; pin Streamlit version in `requirements.txt` and re-test on every minor bump. [CITED: Streamlit Discuss thread "CSS hacks" — community confirms `data-testid` is widely used but not guaranteed stable.]

### 3.5 Hard reds (do NOT propose, plan, or ship)

| Anti-pattern | Why |
|--------------|-----|
| Unscoped global `<style>` blocks via `st.html("<style>body { ... }</style>")` without a `.st-key-X` selector | Affects every page; brittle to Streamlit DOM changes (CONTEXT anti-pattern reminder). |
| `st.markdown(<style>, unsafe_allow_html=True)` | Weakens markdown safety surface app-wide; use `st.html` instead. |
| Custom JS injection (e.g., `<script>` tags via `st.html`) | Streamlit sanitizes most of it; what survives is brittle. **CONTEXT hard red.** |
| `position: absolute` outside `st.container` | Streamlit re-mounts deltas; absolute children get orphaned. Always wrap in keyed container. |
| Hover states on `st.button` that try to flip state without rerun | CSS `:hover` works; do NOT try to feed it back into Python state. |
| Transitions across reruns (CSS `transition: opacity 1s` on an element that re-mounts) | Streamlit re-mounts the DOM node on rerun → no transition. Use `st.fragment` if the transition must persist. |
| `streamlit-shadcn-ui`, `streamlit-elements`, `streamlit-antd-components`, `streamlit-option-menu` | Banned by CONTEXT. |
| `stylable_container` from streamlit-extras | **Deprecated by upstream maintainer.** Replacement: `st.container(key=...)` + `.st-key-X` CSS. [CITED: streamlit-extras deprecation page] |

---

## §4. Composition Rules (Cookbook)

### 4.1 Forms vs callbacks vs raw widgets — when to use each

**Three options, decided per-page:**

| Pattern | When to use | Phase 2 use site |
|---------|-------------|------------------|
| **`st.form` + `st.form_submit_button`** | When you want NO rerun on each input change — only one rerun on submit. Best for multi-field forms where intermediate state would be wasteful. | **P1 sign-up** (username + API key — no need to validate per keystroke). |
| **Raw widgets + `on_change` callback** | When each input change should trigger a side effect (e.g., recompute a counter). | (none in Phase 2) |
| **Raw widgets + explicit submit `st.button`** | When you want fine control: validate one field, show inline error, then act on button. Reruns on every input change but submit is gated by button. | **P3 lecture multi-select** (no submit until "Generate Mock" clicked). **P4 MCQ** (no submit until "Next" clicked — UPSERT happens then). |

**Rule of thumb for Phase 2:** Use `st.form` for P1. Use raw widgets + button everywhere else. We do NOT need `on_change` callbacks anywhere.

[CITED: https://docs.streamlit.io/develop/concepts/architecture/forms]

### 4.2 `st.file_uploader` — the stale-state trap

`st.file_uploader` retains its uploaded file across reruns. After consuming the file (e.g., kicking off ingestion), the uploader still shows the file name; if the user uploads a new one, the same widget instance is reused. **Common bug:** the page processes the same file twice on rerun.

**Canonical reset pattern:**

```python
upload = st.file_uploader("Lecture PDF", type=["pdf"], key="lecture_upload")

if upload is not None and st.session_state.get("processed_filename") != upload.name:
    with st.status("Ingesting lecture...", expanded=True) as status:
        ingest_lecture(class_id, upload)  # Phase 1 orchestrator
        status.update(label="Done", state="complete")
    st.session_state["processed_filename"] = upload.name
    st.toast("Lecture ingested ✅")
```

**To force a reset (e.g., after navigating away):**

```python
if st.button("Upload another"):
    # Cannot do st.session_state.pop("lecture_upload") — the widget owns its state
    # and Streamlit raises if you mutate it. Workaround: change the widget key.
    st.session_state["upload_nonce"] = st.session_state.get("upload_nonce", 0) + 1
    st.rerun()

upload = st.file_uploader(
    "Lecture PDF", type=["pdf"],
    key=f"lecture_upload_{st.session_state.get('upload_nonce', 0)}",
)
```

[CITED: https://docs.streamlit.io/develop/concepts/architecture/widget-behavior — "Modifying a widget's value through st.session_state after the widget has been instantiated is not allowed"]
[VERIFIED: Streamlit Discuss community pattern for file_uploader reset via key-nonce.]

### 4.3 `st.fragment` — P4 timer worked example

The P4 timer must update every second WITHOUT resetting MCQ widget state (selected checkboxes/radios). This is exactly what `st.fragment(run_every=...)` is for: the fragment partial-reruns; widgets outside the fragment do not re-execute.

```python
# app/mock_take/timer_render.py
import time
import streamlit as st

@st.fragment(run_every="1s")
def render_mock_timer() -> None:
    """Top-bar timer. Reads st.session_state['mock_start_ts'] and renders elapsed.
    Reruns every 1s in isolation; does NOT trigger a full app rerun."""
    start_ts = st.session_state.get("mock_start_ts")
    if start_ts is None:
        return
    elapsed = int(time.time() - start_ts)
    mm, ss = divmod(elapsed, 60)
    with st.container(key="mock-timer"):
        st.markdown(f"**Elapsed:** `{mm:02d}:{ss:02d}`")
```

```css
/* surf_theme.css — top-bar timer */
.st-key-mock-timer {
  text-align: right;
  font-family: var(--st-code-font);  /* monospace, the signature */
  color: var(--surf-shadow);
  padding: var(--surf-space-1) var(--surf-space-2);
}
```

**Fragment isolation rules (essential):**
- A fragment can read `st.session_state` written by the host page.
- A fragment writing to `st.session_state` propagates the change on the next full rerun (NOT immediately to the host page).
- Calling `st.rerun(scope="fragment")` reruns ONLY the fragment.
- Calling `st.rerun(scope="app")` (or plain `st.rerun()`) reruns the whole app — use this on Next/Prev/Skip nav events in P4.
- A fragment **cannot contain** a `st.dialog`, `st.form_submit_button`, or another fragment.
- A fragment CAN contain `st.columns`, `st.container`, `st.expander`, all input widgets, all display widgets.

[CITED: https://docs.streamlit.io/develop/api-reference/control-flow/fragment]
[CITED: https://docs.streamlit.io/develop/concepts/architecture/fragments]

### 4.4 `st.status` — P3 ingestion log worked example

```python
# views/class_view.py (excerpt)
upload = st.file_uploader("Lecture PDF", type=["pdf"], key="lec_up")
if upload is not None:
    with st.status("Ingesting lecture…", expanded=True) as status:
        try:
            status.update(label="Extracting PDF…")
            md = pdf_to_md(upload)

            status.update(label="Splitting into pages…")
            pages = split_pages(md)

            status.update(label="Generating LOs…")
            los = extract_los(pages, factsheet_subset)

            status.update(label=f"Generating MCQs (batch 1/{n_batches})…")
            for i, batch in enumerate(batches, 1):
                status.update(label=f"Generating MCQs (batch {i}/{n_batches})…")
                generate_mcqs(batch)

            status.update(label="Done ✓", state="complete", expanded=False)
        except Exception as e:
            status.update(label=f"Failed: {e}", state="error")
            raise
```

**`st.status` behavior:**
- Displays a spinner while `state="running"`; checkmark on `complete`; red X on `error`.
- `expanded=True` shows the log lines (anything written inside the `with` block).
- `.update(label=, state=, expanded=)` mutates the block in place — does NOT cause an app rerun.
- Per CONTEXT D-2.7 (tab-close): if the user closes the tab mid-ingestion, the Python process keeps running (Streamlit re-execution model); next visit calls `list_lectures_for_class` and any `pending` lectures show the "Resume ingestion" affordance. No `beforeunload` warning.

[CITED: https://docs.streamlit.io/develop/api-reference/status/st.status]

### 4.5 Caching — `cache_resource` for the SQLite connection (NOT `cache_data`)

| Purpose | Decorator | Why |
|---------|-----------|-----|
| **Reuse a `sqlite3.Connection`** across reruns / sessions | `@st.cache_resource` | Returns the SAME object to all callers. **Critical:** sqlite3 connections in default mode are **not thread-safe across threads** — Streamlit's reruns are single-threaded per session, but Streamlit DOES use a thread pool for some operations. **Solution:** open the connection with `check_same_thread=False` AND serialize writes via `with conn:` context manager (Phase 1 already does this — verify via `app/db/connection.py`). |
| **Cache pure-Python compute** (e.g., parse a JSON, derive Swiss formula bucket) | `@st.cache_data` | Returns a copy — safe to mutate. Pickle-serializes the result. |
| **Cache the Anthropic client** | Already encapsulated in `app/brain/claude_client/claude_client.py` (Phase 1 — do NOT re-implement). | — |
| **Cache DB query results** | DO NOT cache. SQLite reads at Surf scale (≤1000 rows) take <1ms; caching adds invalidation complexity. | — |

```python
# app/db/connection.py — illustrative; verify against Phase 1's existing impl
import sqlite3
from pathlib import Path
import streamlit as st

DB_PATH = Path.home() / ".surf" / "user.sqlite"

@st.cache_resource
def get_db() -> sqlite3.Connection:
    """Single shared SQLite connection for the app session.
    Returns the same object across reruns. Phase 1 already implements this — verify."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn
```

[CITED: https://docs.streamlit.io/develop/concepts/architecture/caching]
[VERIFIED: Streamlit docs explicitly recommend `cache_resource` for DB connections]

### 4.6 `st.session_state` vs `st.query_params` — Phase 2 decisions

| State | Storage | Why |
|-------|---------|-----|
| Current `class_id` (P3 + P4 + P5) | `st.session_state["class_id"]` | Local-only; deep linking not required for Phase 2. |
| Current `mock_id` / `attempt_id` (P4) | `st.session_state["attempt_id"]` | Created on mock launch; cleared on submit. |
| Mock progress (`current_q_index`) | `st.session_state["mock_idx"]` | Re-derived from DB on resume — but session_state is the working pointer during a single take. |
| Timer start (`mock_start_ts`) | `st.session_state["mock_start_ts"]` | Initialized from `attempts.start_time` on resume. |
| Selected lecture ids on P3 | `st.session_state["selected_lecture_ids"]` | Set; toggled by Card Interactive clicks. |
| (deferred) Deep-linkable attempt | (would use `st.query_params`) | YELLOW — Claude discretion; Phase 2 doesn't need it. |

**Initialization pattern (top of every page that reads session_state):**

```python
def _init_session_state() -> None:
    defaults = {
        "class_id": None,
        "attempt_id": None,
        "mock_idx": 0,
        "mock_start_ts": None,
        "selected_lecture_ids": set(),
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)
```

**Multipage state isolation:** `st.session_state` is **per browser session**, **shared across pages**. Navigating P3 → P4 → P5 keeps state. Closing the tab clears it (which is why D-3.3 persists mock state to DB on every navigation).

[CITED: https://docs.streamlit.io/develop/concepts/architecture/session-state]

### 4.7 `st.dialog` — flagged for forward awareness only (NOT used in Phase 2)

```python
# Phase 3 P7 example — included for completeness; do NOT add to Phase 2
@st.dialog("Confirm reset")
def confirm_reset_dialog():
    st.write("Type the username to confirm.")
    typed = st.text_input("Username")
    if st.button("Reset", type="primary"):
        if typed == st.session_state["username"]:
            reset_db()
            st.rerun()
        else:
            st.error("Usernames don't match.")

if st.button("Reset all data"):
    confirm_reset_dialog()
```

`st.dialog` is a **decorator on a function**, not a context manager. Calling the function opens the modal. The dialog reruns independently from the host script. Forms inside dialogs work but are reset on dialog reopen. Phase 2 has no dialogs.

[CITED: https://docs.streamlit.io/develop/api-reference/control-flow/dialog]

---

## §5. Anti-patterns Checklist (1-line each)

- ❌ Setting `st.session_state[key] = value` for a button or file_uploader widget → raises `StreamlitAPIException`.
- ❌ Mutating `st.session_state[key]` AFTER the widget with that key has already rendered in this script run → raises exception.
- ❌ Pressing a button and reading `if st.button(): ...` to update state used by widgets ABOVE the button → user has to click twice (the "press button twice" bug). **Fix:** put the button-handling code BEFORE the dependent widgets, or use `st.rerun()` after the state change.
- ❌ Re-rendering the same `st.file_uploader(key="lec")` after consuming the file expects the file to "clear" → it doesn't. **Fix:** rotate the key via a nonce (see §4.2).
- ❌ Putting `st.form_submit_button` inside `st.fragment` → not supported.
- ❌ Putting `st.dialog` inside `st.fragment` → not supported.
- ❌ Reading `st.session_state["foo"]` before initializing it → `KeyError`. **Fix:** `setdefault` at top of page.
- ❌ Using `st.connection('db', type='sql')` → requires SQLAlchemy → banned by C-08.
- ❌ Using `st.cache_data` on a function that returns a `sqlite3.Connection` → returns a copy, breaking the connection. Use `cache_resource` for resources, `cache_data` for data.
- ❌ CSS injection via `st.markdown("<style>...</style>", unsafe_allow_html=True)` → use `st.html` instead.
- ❌ Targeting `data-testid="stXxx"` selectors without pinning Streamlit version → breaks on minor upgrades.
- ❌ Two `st.container(key="card")` with the same key → raises `StreamlitDuplicateElementKey`. **Fix:** make keys unique per instance (e.g., `f"card-{lecture_id}"`).
- ❌ Calling `st.rerun()` inside a callback that already runs as part of a rerun → infinite loop.
- ❌ Trying to use legacy `pages/` directory alongside `st.navigation` → undefined behavior; pick one (Surf picks `st.navigation`).
- ❌ Relying on JS for any UI behavior (confetti, scroll-anim, animated counters, page transitions) → CONTEXT hard red.
- ❌ Loading `surf_theme.css` once per page render (e.g., calling `load_theme()` in every `views/*.py`) → bloats the DOM with duplicate `<style>` blocks. **Fix:** call exactly once at `streamlit_app.py` top, BEFORE `st.navigation`.
- ❌ Caching DB query results with `cache_data` and then mutating the DB → stale reads. Surf doesn't cache DB results — sqlite is fast enough.
- ❌ Putting fragment-internal widgets in places that read `st.session_state` written by the fragment in the same run → state propagates only on next rerun.

---

## §6. streamlit-extras Catalog (Phase 2 Triage)

**Total catalogued:** 56 extras (50 active + 6 deprecated) [VERIFIED: WebFetch of `arnaudmiribel.github.io/streamlit-extras/` 2026-05-02]

**Verdict for Phase 2:** **0 GREEN, 6 YELLOW, 50 RED.** Add no extras to Phase 2 dependencies. The user's original "top extras candidate" `stylable_container` is deprecated — its replacement is the very same `st.container(key=...)` pattern Phase 2 already locked.

### 6.1 GREEN — recommended (none)

> No extras are required for Phase 2. Every Phase 2 visual decision is achievable with vanilla Streamlit 1.50+. This is intentional — minimizing community dependencies reduces upgrade pain across the 13-day calendar.

### 6.2 YELLOW — situational (planner's call)

These could help Phase 2 but native Streamlit is ≥80% of the way. Pull in only if the planner explicitly chooses one and the cost (an added `pip` dep) is justified.

| Extra | Phase 2 use site | Native alternative | Reason to consider | Reason to skip |
|-------|------------------|--------------------|--------------------|----------------|
| **`grid`** (`from streamlit_extras.grid import grid`) | P3 lecture-card grid | `st.columns` nested in a loop | Cleaner API for variable-width rows. | We have a fixed N-cards-per-row layout; `st.columns` is simpler and one fewer dep. |
| **`bottom_container`** (`from streamlit_extras.bottom_container import bottom`) | P4 PREV/NEXT button bar pinned at viewport bottom | `position: fixed` CSS on a keyed container | Saves CSS. | We already have surf_theme.css for scoped CSS; adds a dep for ~10 lines saved. |
| **`mention`** (`from streamlit_extras.mention import mention`) | P5 rationale "see source slide" link | `st.markdown(f"[icon source slide {n}](...)")` | Pretty Notion-style link. | Our editorial aesthetic uses serif text links, not icon mentions. |
| **`stateful_button`** (`from streamlit_extras.stateful_button import button`) | P3 lecture Card Interactive (toggle selection) | Manual `st.session_state` + `st.button` | Built-in toggle state. | We need the Card Interactive to have CSS-controlled appearance, not button styling — the toggle state is one line of session_state. |
| **`metric_cards`** (`style_metric_cards()`) | P5 summary banner styling | `st.container(key="summary") + scoped CSS` + `st.metric` | Pre-styled cards. | `style_metric_cards()` injects a global `<style>` block — works against Surf's scoped-CSS pattern. **Strong NO unless planner has a specific reason.** |
| **`floating_button`** (`from streamlit_extras.floating_button import floating_button`) | (none in Phase 2 — possible "exit mock" affordance on P4) | `st.button` inside a `st.container(key="floating")` + `position: fixed` CSS | Simpler API. | One-purpose dep. |

### 6.3 RED — skip (50 extras)

Grouped by skip reason. Each row maps to a Phase 2 decision (or explains why irrelevant).

**Replaced by native Streamlit (and/or deprecated):**

| Extra | Native replacement | Source |
|-------|-------------------|--------|
| `stylable_container` (DEPRECATED) | `st.container(key=...)` + `.st-key-X` CSS | [VERIFIED: deprecation page] — **THIS IS THE USER'S ORIGINAL TOP CANDIDATE; UPSTREAM SAYS USE NATIVE.** |
| `colored_header` (DEPRECATED) | `st.header(..., divider=...)` | [CITED: deprecation page] |
| `tags` (DEPRECATED) | `st.badge` (native, 1.50+) or markdown badges | [CITED: deprecation page] |
| `add_vertical_space` (DEPRECATED) | CSS margins on `.st-key-X` containers | [CITED: deprecation page] |
| `app_logo` (DEPRECATED) | `st.logo` (native) | [CITED: deprecation page] |
| `row` (DEPRECATED) | `st.columns` | [CITED: deprecation page] |
| `metric_cards` | `st.metric` + `st.container(border=True)` | YELLOW — listed above; native is enough |
| `card_selector` | Card Interactive built per D-2.9 with `st.container(key=...) + st.button` | We're already building this from Figma |

**Out of scope for Phase 2 (Phase 3+ or never):**

| Extra | Why skipped |
|-------|-------------|
| `dataframe_explorer` | Phase 3 Dashboard (radar/bar/line charts), not P1–P5 |
| `chart_container`, `chart_annotations`, `chartjs_chart` | Phase 3 charts |
| `pagination` | P5 is scrollable list per D-4.1, not paginated |
| `mandatory_date_range` | No date inputs in Phase 2 |
| `image_compare_slider`, `image_crop`, `image_selector`, `three_viewer`, `sigma_graph`, `diagrams` | No images / 3D / graphs in Phase 2 |
| `great_tables` | No tables in P1–P5 |
| `jupyterlite`, `sandbox` | Notebook embedding — out of scope |
| `function_explorer` | Dev tool, not user-facing |
| `keyboard_text`, `keyboard_url` | We have only buttons in Phase 2; no shortcut surface |
| `cookie_manager`, `local_storage_manager` | We persist to SQLite, not browser storage |
| `customize_running` | Dev tool |
| `concurrency_limiter` | Single-user app |
| `redirect`, `scroll_to_element` | We use `st.switch_page` for nav |
| `capture` | Screenshot tool — out of scope |
| `radial_menu` | Off-aesthetic for editorial paper look |
| `resizable_columns` | We have fixed columns from Figma |
| `skeleton` | We have `st.spinner` and `st.status` |
| `specialized_inputs` | We use vanilla inputs |
| `star_rating` | Not in P1–P5 |
| `stateful_chat` | No chat UI in Phase 2 |
| `stoggle` | Notion-style toggle — `st.expander` covers this case for Phase 2 |
| `stodo` | Task list UI — no use site |
| `word_importances` | NLP viz — Phase 4 ML possibly; not Phase 2 |
| `echo_expander` | Dev tool |
| `exception_handler` | We let exceptions propagate to Streamlit's default red box (good UX for Phase 2) |
| `json_editor` | Phase 3 (editable factsheet) — explicitly deferred per CONTEXT |

**Hard-red (ban — JS animation / scope conflict / CONTEXT anti-pattern):**

| Extra | Why banned |
|-------|-----------|
| `let_it_rain` ("Let Emojis Rain") | CSS animation — TECHNICALLY allowed under D-2.3 but conflicts with editorial aesthetic. **Skip.** [VERIFIED: implementation uses CSS keyframes, not JS] |
| `buy_me_a_coffee` | Not relevant to Surf (HSG class project, not monetized) |
| `eval_javascript` | Custom JS injection — **CONTEXT hard red.** |
| `avatar` | No user avatars in Phase 2 |
| `streamlit-shadcn-ui`, `streamlit-elements`, `streamlit-antd-components`, `streamlit-option-menu` | Banned community libs (CONTEXT). Not in extras catalog but listed for completeness — never propose. |

---

## §7. Theme.toml + CSS Variable Map (Ready to Paste)

### 7.1 `.streamlit/config.toml` skeleton

> **The exact hex values are TBD per CONTEXT — extracted from Figma in this research step's MCP-driven sub-task.** This RESEARCH.md ships the SHAPE; the planner fills the values in the first plan that creates `app/brain/theme/`. **See §11 Open Question Q1 for the Figma-extraction gap.**

```toml
# .streamlit/config.toml

[theme]
base = "light"

# Brand identity
primaryColor = "<TBD-Accent-Deep>"
backgroundColor = "<TBD-Paper-0>"
secondaryBackgroundColor = "<TBD-Paper-1>"
textColor = "<TBD-Base-Shadow>"

# Borders + radius (editorial paper aesthetic)
borderColor = "<TBD-Paper-3>"
showBorderAroundInputs = true
baseRadius = "0.5rem"

# Typography (Mono/Button Label is Surf's signature aesthetic move)
font = "<TBD-body-font>"
headingFont = "<TBD-heading-font>"
codeFont = "<TBD-mono-font>"

# Status palette (1.50+ — sets st.badge / st.success / st.error / st.warning colors)
greenColor = "<TBD-Status-OK>"
orangeColor = "<TBD-Status-Warn>"
blueColor = "<TBD-Status-Info>"

# Sidebar (P3 only; P4 hides sidebar)
[theme.sidebar]
backgroundColor = "<TBD-Paper-2>"  # slightly cooler than main bg

[server]
runOnSave = false

[browser]
gatherUsageStats = false
```

### 7.2 CSS custom properties exposed at runtime by `[theme]`

Streamlit auto-exposes every `[theme]` option as a CSS custom property prefixed `--st-` and kebab-cased. `surf_theme.css` can read these:

| `[theme]` option | CSS variable |
|------------------|--------------|
| `primaryColor` | `--st-primary-color` |
| `backgroundColor` | `--st-background-color` |
| `secondaryBackgroundColor` | `--st-secondary-background-color` |
| `textColor` | `--st-text-color` |
| `borderColor` | `--st-border-color` |
| `font` | `--st-font` |
| `headingFont` | `--st-heading-font` |
| `codeFont` | `--st-code-font` |
| `baseRadius` | `--st-base-radius` |
| `redColor` | `--st-red-color` |
| `orangeColor` | `--st-orange-color` |
| `yellowColor` | `--st-yellow-color` |
| `greenColor` | `--st-green-color` |
| `blueColor` | `--st-blue-color` |
| `violetColor` | `--st-violet-color` |
| `greyColor` | `--st-grey-color` |
| `redBackgroundColor` etc. | `--st-red-background-color` etc. |

[CITED: https://docs.streamlit.io/develop/concepts/custom-components/components-v2/theming]
[CITED: https://docs.streamlit.io/develop/api-reference/configuration/config-toml]

`surf_theme.css` then defines the Surf-specific tokens layered on top (Paper ladder, accent tones, motion scale, spacing) — see §3.3 Layer 2 skeleton.

### 7.3 The "edit-this-later" map for visual decisions

Per CONTEXT's edit-this-later rule, every locked visual maps to one swap point:

| Visual decision (CONTEXT) | Where it lives | What to change | Propagation |
|---------------------------|----------------|----------------|-------------|
| Brand primary color (D-2.1 Accent/Deep) | `.streamlit/config.toml [theme] primaryColor` | One hex value | Propagates to every Streamlit-native widget (button, slider, focus ring, badge accent). |
| Paper ladder (D-2.1) | `surf_theme.css :root` `--surf-paper-0` … `--surf-paper-5` | 6 hex values at top of file | Propagates via `var(--surf-paper-N)` to every keyed container that references it. |
| Light/Dark (D-2.2) | `[theme] base` | `"light"` → `"dark"` | Streamlit auto-derives core colors from base; Surf custom props would need a `@media (prefers-color-scheme)` block (Phase 3 work). |
| Motion intensity (D-2.3) | `surf_theme.css :root` `--surf-motion-scale` | `1` (default) → `0` (off) → `0.5` (half) | All `transition-duration` / animation-duration values multiply by this scale. |
| 8-pt spacing (D-2.4) | `surf_theme.css :root` `--surf-space-1..4` | 4 values | Card padding, section gaps. |
| P3 ingest log strings (D-2.6) | `app/class_/lecture_ingest/lecture_ingest.py` top constants | String constants | One source of truth. |
| Mock timer placement (D-3.2) | `surf_theme.css .st-key-mock-timer` | CSS rule | Switch from inline header to floating sticky pill via `position: fixed`. |
| Difficulty placeholder char (D-3.5) | `app/mock_take/question_render/` `_DIFFICULTY_PENDING = "—"` | One string | One source of truth. |
| Result card layout (D-4.1) | `app/mock_review/question_render/` template | Function code | All result cards. |
| Difficulty breakdown expander label (D-4.2) | `app/mock_review/question_render/` constant | One string | — |
| PRACTICE size SQL (D-4.3) | `app/class_/build_mock/practice_mock.py` SELECT | SQL `WHERE` clause | One query. |

---

## §8. Validation Architecture

**Per `.planning/config.json` workflow.nyquist_validation default (treated as enabled).**

### 8.1 Test framework

| Property | Value |
|----------|-------|
| Framework | `pytest 8.x` (already in repo per Phase 1; verify exact version in `pyproject.toml`) |
| Config file | `pyproject.toml` (verify `[tool.pytest.ini_options]` block; if absent, Wave 0) |
| Quick run command | `pytest -q tests/test_smoke.py` |
| Full suite command | `pytest -q` |

### 8.2 Phase requirements → test map

| Req ID | Behavior | Test type | Automated command | File exists? |
|--------|----------|-----------|-------------------|--------------|
| PAGE-01 | Sign-up flow saves user; invalid API key rejected | unit (mocked Anthropic) + integration | `pytest -q tests/test_signup.py -x` | ❌ Wave 0 |
| PAGE-01 | First-launch routes to P1; subsequent launches skip | unit | `pytest -q tests/test_auth_router.py -x` | ❌ Wave 0 |
| PAGE-02 | Add Class flow persists row; rejected factsheet does not | unit | `pytest -q tests/test_add_class.py -x` | ❌ Wave 0 |
| PAGE-03 | Lecture upload triggers `lecture_ingest`; status partial on tab-close | integration | `pytest -q tests/test_class_view.py -x` | ❌ Wave 0 |
| PAGE-03 | Mock build = `5 × N` MCQs; selection logic Phase 1 D-02 | unit (pure SQL) | `pytest -q tests/test_build_mock.py -x` | ❌ Wave 0 |
| PAGE-04 | UPSERT on Next/Prev/Skip; resume picks correct question | unit | `pytest -q tests/test_attempt_save.py -x` | ❌ Wave 0 |
| PAGE-04 | Timer monotonic; not reset by widget interaction | manual + Streamlit AppTest | `pytest -q tests/test_take_mock_apptest.py -x` | ❌ Wave 0 |
| PAGE-05 | Swiss formula `5 × correct/max + 1`; multi-correct exact-set grading | unit | `pytest -q tests/test_grading.py -x` | ❌ Wave 0 |
| PAGE-05 | Result card renders rationale + difficulty score (or `—` placeholder) | unit (render contract) | `pytest -q tests/test_review_render.py -x` | ❌ Wave 0 |
| PIPE-02 | API key validation calls `claude_client` with `max_tokens=1` | unit (mocked) | `pytest -q tests/test_api_key_validate.py -x` | ❌ Wave 0 |
| MECH-01 | End-to-end: P1 → P2 → P3 → P4 → P5 happy path | integration (AppTest) | `pytest -q tests/test_e2e_happy_path.py -x` | ❌ Wave 0 |
| MECH-02 | Generate Mock + Study Next entry points; PRACTICE = all MCQs in LO range | unit | `pytest -q tests/test_mock_entry_points.py -x` | ❌ Wave 0 |
| MECH-03 | Grading = 1 iff exact set match | unit | `pytest -q tests/test_grading.py -x` | ❌ Wave 0 |
| GRADE-04 | Result card structure: rationale + difficulty + correctness | unit | `pytest -q tests/test_review_render.py -x` | ❌ Wave 0 |

### 8.3 Sampling rate

- **Per task commit:** `pytest -q tests/test_smoke.py` (≤2 sec)
- **Per wave merge:** `pytest -q` (full suite, target ≤30 sec)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### 8.4 Wave 0 gaps

- [ ] `tests/test_signup.py` — covers PAGE-01
- [ ] `tests/test_auth_router.py` — covers PAGE-01 routing
- [ ] `tests/test_add_class.py` — covers PAGE-02
- [ ] `tests/test_class_view.py` — covers PAGE-03 ingest trigger
- [ ] `tests/test_build_mock.py` — covers PAGE-03 mock build SQL
- [ ] `tests/test_attempt_save.py` — covers PAGE-04 UPSERT semantics
- [ ] `tests/test_take_mock_apptest.py` — covers PAGE-04 via `st.testing.v1.AppTest`
- [ ] `tests/test_grading.py` — covers PAGE-05 + MECH-03
- [ ] `tests/test_review_render.py` — covers PAGE-05 + GRADE-04
- [ ] `tests/test_api_key_validate.py` — covers PIPE-02
- [ ] `tests/test_e2e_happy_path.py` — covers MECH-01
- [ ] `tests/test_mock_entry_points.py` — covers MECH-02

**Helper file:** `tests/_streamlit_apptest_helpers.py` — shared `AppTest` fixture, fake `claude_client` (extend Phase 1's `tests/_fakes.py`).

[CITED: https://docs.streamlit.io/develop/api-reference/app-testing — `st.testing.v1.AppTest` simulates a running Streamlit app for testing]

---

## §9. Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3.11 | Project (C-06) | Assumed ✓ (Phase 1 ran) | 3.11.x | None — hard requirement |
| Streamlit | All Phase 2 UI | Assumed ✓ (Phase 1 demo notebooks installed it) — **planner must verify ≥1.50.0 in `pyproject.toml`** | ≥1.50.0 (latest 1.54.0) | None — must upgrade if <1.50 |
| `anthropic` SDK | API key validate (PIPE-02) via `claude_client` | ✓ (Phase 1 shipped) | per Phase 1 | — |
| `pandas` | DB read (`pd.read_sql`) | ✓ (Phase 1 shipped) | per Phase 1 | — |
| `pytest` | Tests | ✓ (Phase 1 smoke test passes) | per `pyproject.toml` | — |
| `ruff` | Lint | ✓ (Phase 1 ran ruff) | per `pyproject.toml` | — |
| **Anthropic API key** | P1 validation in PIPE-02 (uses USER-supplied key, NOT a global one) | N/A — user supplies it during P1 | — | App requires key; without one, P1 blocks. |
| **Internet connectivity** | Anthropic API ping during P1 + lecture ingestion (P3) | Assumed ✓ for grader demo | — | Offline fallback = no demo. (Phase 5 sample data optional escape hatch.) |
| streamlit-extras | NOT required (no GREEN extras) | — | — | — |

**Missing dependencies with no fallback:** None blocking — all Phase 2 dependencies inherit from Phase 1 working environment.

**Action items for Wave 0:**
- Verify `streamlit>=1.50.0` is pinned in `pyproject.toml` (or `requirements.txt`).
- Verify `pytest>=8.0` for AppTest API stability.

---

## §10. Project Constraints (from CLAUDE.md — non-negotiable)

These directives must be honored by every plan:

| Constraint | Source | Phase 2 implication |
|------------|--------|---------------------|
| Python 3.11 + Streamlit only | C-06 (CLAUDE.md) | No Flask, FastAPI, Django — confirmed; Phase 2 is 100% Streamlit. |
| Anthropic Claude API only | C-07 (CLAUDE.md) | API key validation (PIPE-02) uses existing `claude_client.py` — no other LLM. |
| stdlib `sqlite3` only | C-08 (CLAUDE.md) | **No SQLAlchemy, no ORM.** Therefore: do NOT use `st.connection('db', type='sql')` (it requires SQLAlchemy). Use `app/db/queries_*` wrappers built on stdlib `sqlite3`. |
| No AI-generated audio | C-09 (CLAUDE.md) | Phase 5 video, not Phase 2 — flagged here for awareness. |
| Sidecar `.md` per script (≤100 lines, flex to ~140 with walkthrough section) | C-22 (CLAUDE.md) + D-5.1 | Every new Python module in Phase 2 ships with `<script>.md` containing a `## Code walkthrough` section. |
| One sub-folder per pipeline | C-01, C-02 (CLAUDE.md) | Phase 2 NEW folders: `app/signup/signup_flow/`, `app/signup/api_key_validate/`, `app/my_classes/add_class/`, `app/my_classes/class_card_render/`, `app/class_/build_mock/`, `app/class_/study_next/`, `app/mock_take/answer_capture/`, `app/mock_take/attempt_save/`, `app/mock_take/question_render/`, `app/mock_review/question_render/`, `app/mock_review/summary_banner/`, `app/brain/theme/`. |
| `lower_snake_case`, verb-driven names | C-21 / CLAUDE.md | `username_save` not `username`; `lecture_card_render` not `card`. |
| Don't re-implement shipped pieces | CLAUDE.md "Already shipped" | `claude_client.py`, `pdf_to_md_v3.py`, `factsheet_clean/` — call, don't rebuild. |
| Atomic commits, `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` | CLAUDE.md "Branch + commit" | Every plan's verification block enforces. |
| Buffer-upload deadline 2026-05-13 | CLAUDE.md / PROJECT.md | 11 days from research date — planner must size waves accordingly. |
| Surgical changes (rule §3 of CLAUDE.md) | CLAUDE.md | Plans MUST limit changes to what user requested; no incidental refactors. |

---

## §11. Open Questions (RESOLVED)

These could not be resolved in research alone; each is operationalized into a Phase 2 plan task:

- **Q1 — RESOLVED:** Figma token extraction is Plan 02-01 Task 1 (Wave 1).
- **Q2 — RESOLVED:** `SURF_UI(old)` library check is Plan 02-01 Task 1 (verified before token extraction).
- **Q3 — RESOLVED:** Card Interactive `data-testid` stability is a Plan 02-01 Task 5 spike + Streamlit version pin in `pyproject.toml`. Fallback (visible "Select" button) documented in Plan 02-04b if spike fails.
- **Q4 — RESOLVED:** `st.fragment(run_every="1s")` 90-min memory spike is Plan 02-01 Task 4. Fallback (manual re-render-on-nav timer) documented in Plan 02-05.
- **Q5 — Forward-awareness only:** `st.dialog` form-state behavior flagged for the Phase 3 P7 researcher (P7 Settings reset-confirm uses dialog). Not actioned in Phase 2.
- **Q6 — RESOLVED:** TDD-per-task adopted (Wave 0 stub-scaffold rejected). Each plan's TDD task writes failing tests first, then implementation. See per-plan `<task type="auto" tdd="true">` blocks.
- **Q7 — RESOLVED:** Sidecar back-fill is Plan 02-01 Task 3 (Wave 1, alongside theme + Figma extraction).
- **Q8 — RESOLVED:** `app/db/connection.py` `@st.cache_resource` audit is Plan 02-01 Task 6 (Wave 1).

---

### Original questions (preserved for reference)

1. **Q1 — Exact Figma token values (hex, font names, paddings, radii, shadows).** The `[theme]` skeleton in §7.1 and the `surf_theme.css :root` skeleton in §3.3 ship `<TBD>` placeholders. Extracting actual values requires Figma desktop selection + the `mcp__claude_ai_Figma__get_variable_defs` MCP tool (selection-based, per CONTEXT specifics). **Recommendation:** Make this the first task of Phase 2 Wave 1 — a 30-min Figma extraction session producing `02-WIDGETS.md` (or appending the values into a §7 update of THIS file). [ASSUMED: Figma library is reachable; the user has it open in Figma desktop per CONTEXT specifics.]

2. **Q2 — `SURF_UI(old)` vs newer revision.** CONTEXT D-2.1 flags that the file's library suffix is `(old)`; a newer revision may exist. **Recommendation:** First-task check — call `mcp__claude_ai_Figma__get_libraries` against Tiago's Figma teams to confirm. If newer, switch tokens. If not, drop the suffix concern.

3. **Q3 — Card Interactive overlay-button trick (§3.4).** The full-card click pattern uses CSS `position: absolute; inset: 0` over a tertiary `st.button` to make the entire card a click target. This **works** in Streamlit 1.50+ but relies on the `data-testid="stBaseButton-tertiary"` selector, which is not a public API. **Risk:** breaks on minor Streamlit upgrades. **Recommendation:** Pin Streamlit version in `pyproject.toml`; add a smoke test `tests/test_card_interactive_click.py` using `AppTest` that asserts the click registers. Alternatively, use a visible button at the bottom of each card ("Select" / "Selected ✓") — uglier but DOM-stable. [ASSUMED: pinning Streamlit version is acceptable to the user.]

4. **Q4 — Does `st.fragment(run_every="1s")` survive a long mock (e.g., 90 minutes / 5400 ticks) without memory growth?** Documented behavior is "reruns every 1s independently" but real-world stress is undocumented. **Recommendation:** Spike before P4 plan finalization — run a 90-min fragment-only test app, watch process memory. If it grows, fall back to a manual re-render-on-nav timer (less smooth, but stable). [ASSUMED: short-running mocks <30 min are the common case; even a slow leak is tolerable.]

5. **Q5 — `st.dialog` retains form state across reruns?** CONTEXT (and §4.7 of this file) note that forms inside dialogs are reset on dialog reopen. Phase 2 doesn't use dialogs (only Phase 3 P7 reset-confirm does), so this is **forward-awareness only** — flagged for the Phase 3 researcher.

6. **Q6 — Wave 0 size.** Plan-checker convention is to seed the test scaffold in Wave 0 (per §8.4). This adds 12 test files before any feature code. **Recommendation:** The planner should consider whether Wave 0 produces stub files with `pytest.mark.skip` markers and the actual asserts get added per-feature, or whether tests are written alongside features (TDD-style). The CLAUDE.md "goal-driven execution" rule §4 favors writing tests first — recommend TDD per-task.

7. **Q7 — Sidecar back-fill timing.** D-5.3 says all 15 Phase 1 sidecars get walkthroughs back-filled "before/as the first wave of Phase 2." **Recommendation:** Make the sidecar back-fill its own wave (Wave 0 or Wave 1 alongside theme + Figma extraction) so it doesn't compete with feature-code waves for attention.

8. **Q8 — `st.cache_resource` connection sharing across pages.** §4.5 recommends `@st.cache_resource def get_db()` for the SQLite connection. Phase 1 already implements this — verify in `app/db/connection.py` whether it uses `cache_resource` or rebuilds the connection per call. If the latter, Phase 2 should fix it.

---

## §12. Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Figma library `SURF_UI(old)` is reachable from Tiago's Figma desktop session | §11 Q1, Q2 | Cannot extract exact tokens — Phase 2 ships with `<TBD>` placeholders the planner manually fills from screenshots. Mitigation: research step has the screenshot in `docs/design/figma_exports/node_25-2.png`. |
| A2 | `data-testid="stBaseButton-tertiary"` is stable across Streamlit 1.50.x patches | §3.4, §11 Q3 | Card Interactive overlay breaks; need fallback to visible button. |
| A3 | `st.fragment(run_every="1s")` does not leak memory over a 90-min mock | §4.3, §11 Q4 | Long mocks degrade browser perf; fall back to nav-driven re-render. |
| A4 | Phase 1's `app/db/connection.py` already uses `@st.cache_resource` for the SQLite connection (or can be updated to without breaking changes) | §4.5, §11 Q8 | If Phase 1 rebuilds the connection per call, Phase 2 inherits a perf bug. Audit needed in Wave 1. |
| A5 | Streamlit 1.50+ is or can be pinned in `pyproject.toml` for Phase 2 | §1, §9 | If user wants to stay on an older version, the `[theme]` palette knobs (greenColor etc.) won't work and the `key=` parameter on st.container may be missing. **High risk** — verify first. |
| A6 | The user accepts `st.html("<style>...</style>")` as the CSS injection mechanism (vs. custom-component-style theming) | §3.2 | If user prefers custom Streamlit components, the entire scoped-CSS pattern changes. CONTEXT explicitly locks scoped CSS, so risk is LOW. |
| A7 | The user accepts that no streamlit-extras package is added to Phase 2 dependencies | §6 | If user wants e.g. the `grid` extra, plans need to add it. CONTEXT does not block but doesn't require — risk is LOW. |
| A8 | "PRACTICE mock includes ALL MCQs in LO page range" (D-4.3) means MCQs grouped by `slide_pages.page_number IN <LO.page_range>` (Phase 1 schema) | §4 phase requirements | If schema differs, the SELECT changes. **Low risk** — verified Phase 1 schema in `01-VERIFICATION.md` SC1. |

---

## Sources

### Primary (HIGH confidence)

- **Context7 `/streamlit/docs`** — fetched 2026-05-02 for: container key, fragments, dialog, status, toast, navigation, theme.toml, session_state, file_uploader, forms, callbacks, caching. (1826 code snippets indexed.)
- **Context7 `/streamlit/streamlit`** — version pinned at 1.54.0 (latest stable as of 2026-05-02).
- **streamlit-extras catalog** — full list of 56 extras enumerated via WebFetch of `https://arnaudmiribel.github.io/streamlit-extras/` 2026-05-02.
- **streamlit-extras deprecation page** for `stylable_container` — confirms native `st.container(key=...)` is the upstream-recommended replacement.
- **Phase 1 carry-forward:** `01-CONTEXT.md`, `01-VERIFICATION.md`, `app/brain/claude_client/claude_client.md`.
- **Project authority:** `CLAUDE.md` (root), `02-CONTEXT.md`, `02-DISCUSSION-LOG.md`, `.planning/ROADMAP.md`.

### Secondary (MEDIUM confidence — verified against primary)

- Streamlit 1.50 release notes — [https://discuss.streamlit.io/t/version-1-50-0/119561](https://discuss.streamlit.io/t/version-1-50-0/119561) (community-hosted; cross-checked against docs.streamlit.io/develop/quick-reference/release-notes).
- GitHub issue #9666 (multi-key containers) — confirms `.st-key-<key>` is documented public class.
- Streamlit Discuss "CSS Styling For Specific Component" — community confirmation of `st-key-` pattern.

### Tertiary (LOW confidence — flagged in Open Questions)

- `data-testid` selector stability across Streamlit minor versions — community-confirmed but not officially documented (§11 Q3).
- `st.fragment` memory behavior under long-running `run_every` — undocumented in primary sources (§11 Q4).
- Exact Figma token values — require Figma MCP extraction not performed in this step (§11 Q1).

---

## Metadata

**Confidence breakdown:**
- Streamlit element catalog: **HIGH** — verified against Context7 + official docs.
- Scoped CSS pattern: **HIGH** — verified against Context7, official docs, AND streamlit-extras maintainer's deprecation note for `stylable_container`.
- Composition rules (§4): **HIGH** — every claim cited.
- streamlit-extras triage: **HIGH** — full catalog enumerated; deprecation status verified per item.
- Theme.toml shape: **HIGH** — sourced from official config.toml docs.
- Theme.toml exact values: **LOW** — `<TBD>` placeholders pending Figma extraction (Q1).
- Test architecture: **MEDIUM** — Streamlit AppTest is solid but Phase 2 hasn't tested it; assumed compatible.
- Anti-patterns: **HIGH** — every item observed in docs or community threads.

**Research date:** 2026-05-02
**Valid until:** 2026-06-02 (Streamlit ships ~monthly; the `key=` parameter and `[theme]` palette knobs are stable since 1.50/1.36 respectively, so the core findings outlive minor Streamlit upgrades).

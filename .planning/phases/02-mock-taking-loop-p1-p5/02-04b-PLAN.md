---
phase: 02-mock-taking-loop-p1-p5
plan: 04b
type: execute
wave: 4
depends_on: [02-01, 02-02, 02-03, 02-04a]
files_modified:
  - views/class_view.py
  - app/class_/lecture_upload/__init__.py
  - app/class_/lecture_upload/lecture_upload.py
  - app/class_/lecture_upload/lecture_upload.md
  - app/class_/lecture_ingest/lecture_ingest.py
  - app/class_/lecture_ingest/lecture_ingest.md
  - app/class_/build_mock/lecture_card_render.py
  - app/class_/build_mock/lecture_card_render.md
  - app/brain/theme/surf_theme.css
  - app/brain/theme/edit_this_later.md
  - tests/test_class_view.py
  - tests/test_lecture_upload.py
  - tests/test_lecture_ingest_progress.py
  - previews/components/lecture_card_interactive/preview.py
  - previews/components/lecture_card_interactive/lecture_card_render.py
  - previews/components/lecture_card_interactive/surf_theme.css
  - previews/components/ingestion_log/preview.py
  - previews/components/ingestion_log/lecture_ingest_stub.py
  - previews/components/ingestion_log/surf_theme.css
  - previews/components/study_next_card/preview.py
  - previews/components/study_next_card/study_next_render.py
  - previews/components/study_next_card/surf_theme.css
  - previews/pages/p3_class_hub/preview.py
  - previews/pages/p3_class_hub/class_view.py
  - previews/pages/p3_class_hub/lecture_upload.py
  - previews/pages/p3_class_hub/lecture_ingest_stub.py
  - previews/pages/p3_class_hub/build_mock.py
  - previews/pages/p3_class_hub/study_next.py
  - previews/pages/p3_class_hub/lecture_card_render.py
  - previews/pages/p3_class_hub/surf_theme.css
autonomous: false
requirements: [PAGE-03, MECH-01, MECH-02, GRADE-04]
must_haves:
  truths:
    - "P3 main column shows: lecture upload (st.file_uploader) + lecture multi-select (Card Interactive grid) + Generate Mock CTA + Past attempts hint (D-2.10)"
    - "P3 sidebar shows: Past Attempts list (clickable to P5) + Study Next card (D-2.10, hidden if zero attempts per D-2.11)"
    - "Lecture upload triggers in-band lecture_ingest from Phase 1 wrapped in st.status with the four log lines from D-2.6: Extracting PDF / Splitting into pages / Generating LOs / Generating MCQs (batch i/N) — wired via an additive progress_callback kwarg on lecture_ingest.ingest_lecture (locked decision D-2.6)"
    - "lecture_ingest.ingest_lecture gains an additive optional kwarg progress_callback: Callable[[str], None] | None = None (additive — existing callers unchanged per CLAUDE.md Surgical Changes)"
    - "Tab close mid-ingestion: backend continues; pending lectures show 'Resume ingestion' affordance (D-2.7) — no beforeunload warning"
    - "Lecture multi-select uses Card Interactive pattern from RESEARCH §3.4 (or fallback from 02-WIDGETS.md Q3 spike) with key=`lecture-{id}`; selected = Accent/Deep border + checkmark; live counter '{N} lectures × 5 = {5N} questions' (D-2.9)"
    - "Sandboxes (4 paths under previews/) contain no `from app...` imports (CLAUDE.md visual preview gate)"
    - "All sidecar .md files <=140 lines and include ## Code walkthrough section (D-5.1)"
  artifacts:
    - path: "app/class_/lecture_upload/lecture_upload.py"
      provides: "render_lecture_upload(class_id) — file_uploader + st.status + lecture_ingest with progress_callback wiring"
      exports: ["render_lecture_upload"]
    - path: "app/class_/lecture_ingest/lecture_ingest.py"
      provides: "ingest_lecture (existing) + new additive progress_callback kwarg emitting D-2.6's 4 phase strings"
      exports: ["ingest_lecture"]
    - path: "app/class_/build_mock/lecture_card_render.py"
      provides: "render_lecture_card(lecture_id, title, status, selected) -> bool — Card Interactive helper for the lecture multi-select grid"
      exports: ["render_lecture_card"]
    - path: "views/class_view.py"
      provides: "P3 page wiring main + sidebar layout"
      contains: "render_lecture_upload"
  key_links:
    - from: "views/class_view.py"
      to: "app/class_/lecture_upload"
      via: "main column block"
      pattern: "render_lecture_upload"
    - from: "app/class_/lecture_upload/lecture_upload.py"
      to: "app/class_/lecture_ingest.ingest_lecture"
      via: "st.status wrapper passes a progress_callback that calls status.update(label=...)"
      pattern: "ingest_lecture\\(.*progress_callback"
    - from: "app/class_/lecture_ingest/lecture_ingest.py"
      to: "the four D-2.6 phase strings"
      via: "progress_callback kwarg"
      pattern: "progress_callback"
---

# Plan 02-04b — P3 Class Hub UI: Lecture Upload, Multi-Select, Page Wiring + Sandboxes

## Objective

Plan 04b ships the UI half of P3: `lecture_upload` (with the locked D-2.6 four-label progress wired via an additive `progress_callback` kwarg on `lecture_ingest.ingest_lecture`), the lecture multi-select Card Interactive helper, the page wiring in `views/class_view.py`, and four sandboxes (lecture card / ingestion log / study next card / full P3 page). Closes PAGE-03 and the UI surfaces of MECH-01 / MECH-02 / GRADE-04.

Purpose: with 04a's backend interfaces stable, this plan focuses purely on the page surface + sandbox harness. The progress_callback amendment to `lecture_ingest` is **additive** — it does not change existing behavior when callers omit the kwarg, so it respects CLAUDE.md Surgical Changes while honoring locked decision D-2.6 (per planner-authority rule: locked user decisions take precedence over scope-reduction language).

Output: `views/class_view.py`, two new pipelines (`lecture_upload`, `lecture_card_render`), one additive change to `lecture_ingest`, four sandboxes, full TDD coverage.

## Execution context

- Workflow: `~/.claude/get-shit-done/workflows/execute-plan.md`
- Summary template: `~/.claude/get-shit-done/templates/summary.md`

## Context

- /Users/tiagoreimann/surf/CLAUDE.md
- /Users/tiagoreimann/surf/.planning/phases/02-mock-taking-loop-p1-p5/02-CONTEXT.md (D-2.6 locked, D-2.7, D-2.9, D-2.10, D-2.11)
- /Users/tiagoreimann/surf/.planning/phases/02-mock-taking-loop-p1-p5/02-RESEARCH.md (§3 scoped CSS, §4.2 file_uploader reset, §4.4 st.status, §4.6 session_state)
- /Users/tiagoreimann/surf/.planning/phases/02-mock-taking-loop-p1-p5/02-WIDGETS.md (Q3 verdict — overlay-button OR fallback)
- /Users/tiagoreimann/surf/.planning/phases/01-ingestion-spine-database/01-CONTEXT.md (D-4.5 partial-success)
- /Users/tiagoreimann/surf/app/class_/lecture_ingest/lecture_ingest.py
- /Users/tiagoreimann/surf/app/class_/lecture_ingest/lecture_ingest.md
- /Users/tiagoreimann/surf/views/class_view.py
- /Users/tiagoreimann/surf/previews/_fixtures.py

### Interfaces this plan creates (downstream Plans 05-07 consume)

- `app/class_/lecture_upload/lecture_upload.py` — `render_lecture_upload(class_id: int) -> None`. Wraps `lecture_ingest.ingest_lecture` in `st.status` and passes a progress_callback that calls `status.update(label=phase, state="running")` for each of D-2.6's four phase strings.
- `app/class_/lecture_ingest/lecture_ingest.py` — adds optional kwarg `progress_callback: Callable[[str], None] | None = None`. When provided, `ingest_lecture` calls it with the four phase strings: `"Extracting PDF…"`, `"Splitting into pages…"`, `"Generating LOs…"`, `"Generating MCQs (batch i/N)…"` at the appropriate points.
- `app/class_/build_mock/lecture_card_render.py` — `render_lecture_card(lecture_id: int, title: str, status: str, selected: bool) -> bool`. Card Interactive per RESEARCH §3.4 OR fallback per Q3 verdict. Caller owns `st.session_state["selected_lecture_ids"]: set[int]`.

## Tasks

<task type="auto" tdd="true">
  <name>Task 1: Wire progress_callback into lecture_ingest (additive) + lecture_upload + lecture_card_render</name>
  <files>app/class_/lecture_upload/__init__.py, app/class_/lecture_upload/lecture_upload.py, app/class_/lecture_upload/lecture_upload.md, app/class_/lecture_ingest/lecture_ingest.py, app/class_/lecture_ingest/lecture_ingest.md, app/class_/build_mock/lecture_card_render.py, app/class_/build_mock/lecture_card_render.md, app/brain/theme/surf_theme.css, app/brain/theme/edit_this_later.md, tests/test_lecture_upload.py, tests/test_lecture_ingest_progress.py</files>
  <read_first>
    - /Users/tiagoreimann/surf/app/class_/lecture_ingest/lecture_ingest.py
    - /Users/tiagoreimann/surf/app/class_/lecture_ingest/lecture_ingest.md
    - /Users/tiagoreimann/surf/.planning/phases/02-mock-taking-loop-p1-p5/02-WIDGETS.md (Q3 verdict — read the chosen Card Interactive approach)
    - /Users/tiagoreimann/surf/.planning/phases/02-mock-taking-loop-p1-p5/02-RESEARCH.md §3.4, §4.4 (st.status worked example)
    - /Users/tiagoreimann/surf/.planning/phases/02-mock-taking-loop-p1-p5/02-CONTEXT.md (D-2.6 locked)
  </read_first>
  <behavior>
    Tests first (RED → GREEN):
    - test_lecture_ingest_progress.test_callback_fired_in_order — given a mock callback, `ingest_lecture(class_id, pdf_path, progress_callback=cb)` invokes cb with the four phase strings in order: "Extracting PDF…", "Splitting into pages…", "Generating LOs…", "Generating MCQs (batch 1/N)…" through "Generating MCQs (batch N/N)…".
    - test_lecture_ingest_progress.test_callback_optional_back_compat — calling `ingest_lecture(class_id, pdf_path)` without the kwarg behaves identically to before this plan (no progress emission, return value unchanged) — preserves existing callers.
    - test_lecture_upload.test_status_labels_in_order — AppTest: `render_lecture_upload(class_id=1)` triggered with a fake ingest that yields the four phase strings — the rendered `st.status` shows them in sequence.
    - test_lecture_upload.test_pending_lecture_resume_button — given a row with status='pending', the page renders a "Resume ingestion" button (D-2.7).
  </behavior>
  <action>
    1. **Additive amendment to `app/class_/lecture_ingest/lecture_ingest.py`** (per locked D-2.6 + planner-authority rule that locked user decisions take precedence over Surgical Changes):
       - Add optional kwarg: `progress_callback: Callable[[str], None] | None = None` to `ingest_lecture`'s signature.
       - At each of the four pipeline phase boundaries, emit the phase string via `if progress_callback: progress_callback(phase_str)`. Phase strings (from D-2.6): `"Extracting PDF…"` (before pdf_to_md), `"Splitting into pages…"` (before page_splitter), `"Generating LOs…"` (before lo_extractor), `"Generating MCQs (batch i/N)…"` (once per MCQ batch).
       - This is **additive only** — existing callers that omit the kwarg behave identically. No other behavior changes.
       - Update sidecar `lecture_ingest.md`: append a new section under `## Code walkthrough` documenting the progress_callback signature + phase strings (≤10 lines added).
    2. Implement `app/class_/lecture_upload/lecture_upload.py`:
       - `render_lecture_upload(class_id: int) -> None`.
       - Build the file_uploader with key-nonce pattern from RESEARCH §4.2.
       - On a fresh upload: write the file to a tmp path, then `with st.status("Ingesting lecture...", expanded=True) as status:` call `lecture_ingest.ingest_lecture(class_id, pdf_path, progress_callback=lambda phase: status.update(label=phase, state="running"))`. On success: `status.update(label=f"Done — {n_kept} slides + {n_mcqs} MCQs", state="complete")`.
       - On exception: `status.update(label=f"Failed: {e}", state="error")` and re-raise per RESEARCH §4.4.
       - After success: `st.toast("Lecture ingested ✅")`, bump nonce, store `processed_filename` in session_state.
       - On revisit: `list_lectures_for_class(class_id)`; for any row with `status='pending'`, render a "Resume ingestion" button next to it (D-2.7). Wire to call `lecture_ingest.ingest_lecture` again with the original `source_pdf_path` (Phase 1 partial-success policy via D-4.5 lets it complete safely on the additive write contract).
    3. Build the lecture multi-select component as `app/class_/build_mock/lecture_card_render.py` (a small render helper next to build_mock since it owns the data):
       - `render_lecture_card(lecture_id: int, title: str, status: str, selected: bool) -> bool` — Card Interactive per RESEARCH §3.4 OR fallback per Q3 verdict in 02-WIDGETS.md.
       - Caller (the page) keeps `st.session_state["selected_lecture_ids"]: set[int]`.
       - Render returns the new selected state (caller owns the mutation).
       - Wrap in `st.container(key=f"lecture-{lecture_id}")`.
    4. Add scoped CSS to `app/brain/theme/surf_theme.css`:
       - `[class*="st-key-lecture-"]` block per RESEARCH §3.4 (or fallback). Selected variant uses Accent/Deep border + checkmark.
       - `.st-key-study-next-card` block (smaller card, accent-wash background).
       - **No `.st-key-mock-status` block — D-2.6 specifies log-line content, not chrome; let Streamlit's default st.status styling stand (resolves WARNING #6 in revision feedback: keep CSS surface tight).**
       - Cite `/* P3 lecture card — D-2.9 Card Interactive, D-2.4 spacing */` and `/* P3 study next — D-2.11 sidebar weakness */`.
    5. Update `app/brain/theme/edit_this_later.md` with two new rows.
    6. Sidecars: `lecture_upload.md`, `lecture_card_render.md`, append walkthrough section to `lecture_ingest.md`. Each ≤140 lines, walkthrough section.
  </action>
  <verify>
    <automated>pytest -q tests/test_lecture_ingest_progress.py tests/test_lecture_upload.py -x &amp;&amp; python -c "from app.class_.lecture_upload.lecture_upload import render_lecture_upload; from app.class_.build_mock.lecture_card_render import render_lecture_card; import inspect, app.class_.lecture_ingest.lecture_ingest as li; assert 'progress_callback' in inspect.signature(li.ingest_lecture).parameters" &amp;&amp; grep -q "st-key-lecture-" app/brain/theme/surf_theme.css &amp;&amp; grep -q "st-key-study-next-card" app/brain/theme/surf_theme.css &amp;&amp; grep -q "Code walkthrough" app/class_/lecture_upload/lecture_upload.md app/class_/build_mock/lecture_card_render.md app/class_/lecture_ingest/lecture_ingest.md</automated>
  </verify>
  <done>
    - lecture_ingest.ingest_lecture has a working additive progress_callback kwarg; old callers untouched.
    - lecture_upload renders the 4-label sequence in st.status via the callback.
    - lecture_card_render is a usable Card Interactive helper.
    - All three sidecars have walkthrough sections; CSS scoped via attribute selectors only.
  </done>
</task>

<task type="auto">
  <name>Task 2: Wire views/class_view.py + build all four P3 sandboxes</name>
  <files>views/class_view.py, tests/test_class_view.py, previews/components/lecture_card_interactive/preview.py, previews/components/lecture_card_interactive/lecture_card_render.py, previews/components/lecture_card_interactive/surf_theme.css, previews/components/ingestion_log/preview.py, previews/components/ingestion_log/lecture_ingest_stub.py, previews/components/ingestion_log/surf_theme.css, previews/components/study_next_card/preview.py, previews/components/study_next_card/study_next_render.py, previews/components/study_next_card/surf_theme.css, previews/pages/p3_class_hub/preview.py, previews/pages/p3_class_hub/class_view.py, previews/pages/p3_class_hub/lecture_upload.py, previews/pages/p3_class_hub/lecture_ingest_stub.py, previews/pages/p3_class_hub/build_mock.py, previews/pages/p3_class_hub/study_next.py, previews/pages/p3_class_hub/lecture_card_render.py, previews/pages/p3_class_hub/surf_theme.css</files>
  <read_first>
    - /Users/tiagoreimann/surf/views/class_view.py
    - /Users/tiagoreimann/surf/CLAUDE.md "Visual preview gate" section
    - /Users/tiagoreimann/surf/previews/_fixtures.py
    - /Users/tiagoreimann/surf/.planning/phases/02-mock-taking-loop-p1-p5/02-WIDGETS.md (Q3 chosen approach)
  </read_first>
  <action>
    1. Wire `views/class_view.py`:
       - Top: read `class_id = st.session_state.get("class_id")`. If None, `st.switch_page("views/my_classes.py")`.
       - Header: `st.header(f"{class_name}", divider="rainbow")` + caption with class metadata (factsheet course name etc.).
       - Sidebar (`with st.sidebar:`):
         - `st.subheader("Past attempts")` + iterate `list_attempts_for_class(class_id)` printing one clickable button per attempt that on click sets `st.session_state["attempt_id"]` and `st.switch_page("views/review_mock_exam.py")`.
         - `st.divider()`
         - `render_study_next_card(class_id)` (hidden internally if zero attempts).
       - Main column:
         - `render_lecture_upload(class_id)` (file_uploader + st.status).
         - `st.subheader("Lectures")` + a 3-column grid of Card Interactive lecture cards via `render_lecture_card`. Live counter "{N} lectures × 5 = {5N} questions".
         - `st.button("Generate mock", type="primary", disabled=len(selected)==0)`. On click: `attempt_id = build_standard_mock(class_id, sorted(selected_lecture_ids)); st.session_state["attempt_id"] = attempt_id; st.session_state["selected_lecture_ids"] = set(); st.switch_page("views/take_mock_exam.py")`.
    2. test_class_view via AppTest covers sidebar+main composition, Past Attempts list rendering, and Generate Mock button disabled-state when no lectures selected.
    3. Build `previews/components/lecture_card_interactive/`:
       - `preview.py` renders 3 lecture cards using FAKE_LECTURES from `_fixtures.py`. Click toggles selection, status shows live counter.
       - `lecture_card_render.py` is a copy of `app/class_/build_mock/lecture_card_render.py` adapted for sandbox (no `from app` imports).
       - `surf_theme.css` copy.
    4. Build `previews/components/ingestion_log/`:
       - `preview.py` exercises the `st.status` log-line sequence using a STUBBED `lecture_ingest_stub.ingest_lecture` that calls `time.sleep(0.5)` between four label updates ("Extracting PDF…" / "Splitting into pages…" / "Generating LOs…" / "Generating MCQs (batch 1/2)…" / "Generating MCQs (batch 2/2)…") and finally `state="complete"`. Stub honors the same `progress_callback` kwarg shape as production.
       - `lecture_ingest_stub.py` is sandbox-local fake (no `from app` imports).
       - `surf_theme.css` copy.
    5. Build `previews/components/study_next_card/`:
       - `preview.py` renders the Study Next card with a hard-coded weakest LO ("LO2: Demand and supply", correct=1, total=5).
       - Also includes a "zero attempts" toggle that rerenders without the card (D-2.11 hidden state).
       - `study_next_render.py` copy.
       - `surf_theme.css` copy.
    6. Build `previews/pages/p3_class_hub/`:
       - Boots in-memory SQLite with a fully seeded MII class (using FAKE_CLASS, FAKE_LECTURES, FAKE_LOS, FAKE_SLIDE_PAGES, FAKE_MCQS, FAKE_ATTEMPT_ANSWERS).
       - `preview.py` calls `class_view.render_page(class_id=1)` (sandbox-copy entry).
       - Files: `class_view.py`, `lecture_upload.py`, `lecture_ingest_stub.py`, `build_mock.py`, `study_next.py`, `lecture_card_render.py`, `surf_theme.css` — all copies, none with `from app` imports. The `lecture_ingest_stub.py` must be wired in place of the real lecture_ingest.
    7. Smoke check: `find previews/components/lecture_card_interactive previews/components/ingestion_log previews/components/study_next_card previews/pages/p3_class_hub -name '*.py' | xargs grep -l "^from app\\|^import app"` returns no matches.
  </action>
  <verify>
    <automated>pytest -q tests/test_class_view.py -x &amp;&amp; python -c "import ast, pathlib; [ast.parse(p.read_text()) for p in pathlib.Path('previews').rglob('*.py')]" &amp;&amp; bash -c 'set +e; out=$(find previews/components/lecture_card_interactive previews/components/ingestion_log previews/components/study_next_card previews/pages/p3_class_hub -name "*.py" -print0 | xargs -0 grep -l "^from app\|^import app"); test -z "$out"' &amp;&amp; grep -q "render_lecture_upload" views/class_view.py &amp;&amp; grep -q "render_study_next_card" views/class_view.py</automated>
  </verify>
  <done>
    - `views/class_view.py` composes sidebar + main column per D-2.10.
    - All four sandbox roots exist and import nothing from `app/`.
    - `tests/test_class_view.py` passes.
  </done>
  <acceptance_criteria>
    - `views/class_view.py` exists and contains `render_lecture_upload` and `render_study_next_card` calls.
    - Four sandbox roots exist: `previews/components/lecture_card_interactive/`, `previews/components/ingestion_log/`, `previews/components/study_next_card/`, `previews/pages/p3_class_hub/`.
    - No file under `previews/` matches `^from app|^import app`.
  </acceptance_criteria>
  <resume-signal>Type "next" to proceed to Task 3 (visual approval).</resume-signal>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 3: Tiago visually approves P3 sandboxes</name>
  <what-built>
    - P3 Class hub layout: sidebar (Past Attempts list + Study Next card) + main column (lecture upload with `st.status` ingestion log, lecture multi-select Card Interactive grid with live "{N} × 5 = {5N}" counter, Generate Mock CTA).
    - Three component sandboxes (`lecture_card_interactive`, `ingestion_log`, `study_next_card`) and one page sandbox (`p3_class_hub`) — all driven by `_fixtures.py` + stubbed `lecture_ingest`, no real Anthropic, no real DB.
  </what-built>
  <how-to-verify>
    1. From repo root: `streamlit run previews/components/lecture_card_interactive/preview.py`
       - Confirm: 3-column grid of lecture cards renders with Paper1 background and Paper3 border; clicking a card toggles selected state (visible lift/border-color shift); the live counter "{N} lectures × 5 = {5N} questions" updates as cards are toggled; Generate Mock button is disabled when zero cards are selected.
    2. Stop, then: `streamlit run previews/components/ingestion_log/preview.py`
       - Confirm: pressing the "Run stub ingest" button opens an `st.status` block that progresses through the four labels ("Extracting PDF…", "Splitting into pages…", "Generating LOs…", "Generating MCQs (batch i/N)…") with ~0.5s between updates; on completion the status frame collapses to "complete" state. This validates D-2.6 (live log lines) end-to-end.
    3. Stop, then: `streamlit run previews/components/study_next_card/preview.py`
       - Confirm: Study Next card renders with the seeded weakest LO ("LO2: Demand and supply"), correct/total counter ("1/5"), and Practice button. Toggling the "zero attempts" switch hides the card entirely (D-2.11 hidden state).
    4. Stop, then: `streamlit run previews/pages/p3_class_hub/preview.py`
       - Confirm: full P3 page boots with sidebar (Past Attempts list + Study Next card) and main column (lecture upload + multi-select grid + Generate Mock CTA). Uploading any PDF triggers the stubbed ingestion log (no real API). Selecting lectures + clicking Generate Mock prints `attempt_id` in the sandbox console (no real navigation).
    5. Optional regression: `streamlit run streamlit_app.py` still boots and routes through P1→P2→P3. CAUTION: per CLAUDE.md API-key-consent rule, do NOT upload a real lecture here — that would call Anthropic with the real key.
  </how-to-verify>
  <acceptance_criteria>
    - Sandbox paths created/updated:
      - `previews/components/lecture_card_interactive/`
      - `previews/components/ingestion_log/`
      - `previews/components/study_next_card/`
      - `previews/pages/p3_class_hub/`
    - Run commands:
      - `streamlit run previews/components/lecture_card_interactive/preview.py`
      - `streamlit run previews/components/ingestion_log/preview.py`
      - `streamlit run previews/components/study_next_card/preview.py`
      - `streamlit run previews/pages/p3_class_hub/preview.py`
    - "Tiago has visually approved the preview"
  </acceptance_criteria>
  <resume-signal>Type "approved" or describe what to fix.</resume-signal>
</task>

## Verification

- `pytest -q tests/test_lecture_ingest_progress.py tests/test_lecture_upload.py tests/test_class_view.py`
- `python -c "import inspect, app.class_.lecture_ingest.lecture_ingest as li; assert 'progress_callback' in inspect.signature(li.ingest_lecture).parameters"` — confirms additive D-2.6 callback wiring landed without breaking the existing signature.
- All four sandboxes runnable; no `from app` imports anywhere under the four sandbox roots.
- Sidecars (`lecture_upload.md`, `lecture_card_render.md`, `lecture_ingest.md`) updated with `## Code walkthrough` sections, ≤140 lines each.

## Success criteria

- PAGE-03 closed: P3 hub renders sidebar + main per D-2.10; lecture upload + multi-select + Generate Mock + Study Next all wired.
- D-2.6 closed: the four-label ingestion log sequence is delivered (additive `progress_callback` on `lecture_ingest.ingest_lecture` — no silent fallback to single label).
- D-2.9 closed: Card Interactive lecture multi-select renders and toggles selection state.
- D-2.11 closed: Study Next card renders weakest LO, hides on zero attempts.
- Four sandboxes (3 component + 1 page) exist and are visually approved.
- No `from app` imports anywhere under `previews/` (sandbox-isolation rule).

## Output

Create `.planning/phases/02-mock-taking-loop-p1-p5/02-04b-SUMMARY.md` covering: page wiring + UI pipelines shipped, D-2.6 progress_callback approach (additive kwarg verified), four-sandbox approval log, sidecar status, test coverage map (PAGE-03 + D-2.6 + D-2.9 + D-2.11).
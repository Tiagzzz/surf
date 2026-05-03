---
phase: 02-mock-taking-loop-p1-p5
plan: 01
subsystem: ui
tags: [streamlit, theme, css, fraunces, jetbrains-mono, fragment, cache_resource, sqlite, sandbox-isolation, figma]

# Dependency graph
requires:
  - phase: 01-ingestion-spine-database
    provides: 16 Phase-1 sidecars (back-filled with Code walkthroughs in this plan), claude_client wrapper, queries_* DB modules, schema, lecture_ingest orchestrator — all touched only at the documentation layer here.
provides:
  - app/brain/theme/theme.py — production design system (CSS string + 11 helper primitives + inject_theme())
  - previews/ — sandbox scaffold (theme bench + 2 spike sandboxes + fixtures + 2 tests)
  - .streamlit/config.toml — D-2.12 token mirror + Streamlit-1.50 theme knobs (showWidgetBorder, baseRadius)
  - app/db/connection.py — @st.cache_resource singleton (Q8 fix)
  - 16 Phase-1 sidecars + 2 new Phase-2 sidecars carrying ## Code walkthrough (D-5.3 back-fill + new code)
  - ui/documentation.md — single team-facing design-system reference (§ 5 catalog + § 8 DOM reach map filled)
  - 02-WIDGETS.md — D-2.12 token validation table + spike verdicts + component spec
  - 02-FIGMA-RESEARCH.md (pre-existing in tree, validated here) — D-2.26 researcher output
  - 3 Wave-1 spike verdicts: Q3 FAIL, Q4 mechanical-pending-RSS, Q8 FIXED
  - C-22 amendment (line cap removed, walkthrough mandatory, scope clarified to script sidecars only)
  - D-2.20a amendment (MCQ Off/On driven by :has(input:checked))
  - D-2.25a amendment (component validation-status taxonomy)
affects: [02-02, 02-03, 02-04, 02-05, 02-06, 02-07, future Phase 3 / Phase 4 plans that reuse the design system]

# Tech tracking
tech-stack:
  added: [Fraunces variable woff2 (already in assets/), JetBrains Mono variable woff2, st.cache_resource on connection.py]
  patterns:
    - "Embedded _CSS Python string + inject_theme() (D-2.17) — CSS lives as a string constant in theme.py; sandbox copies are byte-equal."
    - "Sandbox isolation — every previews/* file zero from app... imports; tests/test_no_app_imports_in_previews.py mechanically enforces."
    - "Scoped CSS via [class*=\"st-key-XYZ\"] on st.container(key=...) wrappers (D-2.18); widgets reached via stable data-testid."
    - ":has(input:checked) for live state-driven CSS (D-2.20a) — Off/On flips paint without rerun delay."
    - "html.escape() on every helper that interpolates user text (D-2.19)."
    - "@st.cache_resource singleton for DB connection (Q8 verification)."
    - "Component validation-status flow (D-2.25a) — bench-v1 vs production-locked, earned per-plan via preview gate, never retroactively."

key-files:
  created:
    - app/brain/theme/__init__.py
    - app/brain/theme/theme.py
    - app/brain/theme/theme.md
    - app/brain/theme/edit_this_later.md
    - app/mock_take/question_render/_difficulty.py
    - app/mock_take/question_render/_difficulty.md
    - assets/icons/star_filled.svg
    - assets/icons/star_empty.svg
    - previews/_theme.py
    - previews/_fixtures.py
    - previews/README.md
    - previews/components/_theme_bench/preview.py
    - previews/components/_theme_bench/_theme.py
    - previews/spikes/SPIKES.md
    - previews/spikes/fragment_timer/preview.py
    - previews/spikes/fragment_timer/_theme.py
    - previews/spikes/card_interactive_overlay/preview.py
    - previews/spikes/card_interactive_overlay/_theme.py
    - tests/_streamlit_apptest_helpers.py
    - tests/test_theme_loader.py
    - tests/test_no_app_imports_in_previews.py
    - tests/test_db_connection_cache_resource.py
    - .planning/phases/02-mock-taking-loop-p1-p5/02-WIDGETS.md
    - .planning/phases/02-mock-taking-loop-p1-p5/02-01-SUMMARY.md
  modified:
    - .streamlit/config.toml
    - pyproject.toml
    - requirements.txt
    - streamlit_app.py
    - app/db/connection.py
    - 16 Phase-1 sidecars (full list under "Files Created/Modified" below)
    - ui/documentation.md
    - .planning/PROJECT.md
    - .planning/intel/constraints.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/phases/02-mock-taking-loop-p1-p5/02-CONTEXT.md
    - .planning/phases/02-mock-taking-loop-p1-p5/02-01-PLAN.md
    - .planning/todos (moved widget-catalog research from pending/ to done/)

key-decisions:
  - "D-2.20a — MCQ Off/On state driven by :has(input:checked), not by a state-baked container key. Original D-2.20 keying froze the visual at render time; the live-click bug fix replaced it with a CSS-only mechanism plus :not() guards on the review-state suffixes."
  - "D-2.25a — Component validation-status taxonomy (bench-v1 / production-locked / draft / deferred). Bench approval is NOT production approval; the flip happens per-plan, per-component, via the plan's preview gate, never retroactively."
  - "C-22 amendment — Sidecar line cap (≤100 / ≤140 flex) removed. Clarity is the only criterion. ## Code walkthrough is mandatory."
  - "C-22 scope clarification — Walkthrough requirement applies to script sidecars only (sibling-of-.py / sibling-of-.sql docs). System-prompt files and design-system edit-maps are excluded."
  - "Streamlit 1.50 config rename — showBorderAroundInputs → showWidgetBorder. .streamlit/config.toml updated; the original plan text still says the old name as a historical match."
  - "Q3 verdict FAIL — overlay-button technique fails in live testing. Plan 02-04 ships the visible 'Select / Selected ✓' button fallback per card; no overlay-button re-litigation."
  - "Q4 verdict WORKS-MECHANICALLY-PENDING-MEMORY-OBSERVATION — boot + tick + state-isolation confirmed; 5-min RSS observation pending. Plan 02-05 design can proceed assuming fragment is on track."
  - "Q8 verdict FIXED — @st.cache_resource decorator on connect() so Streamlit reruns reuse the same SQLite connection. Test passes under bare pytest."
  - "MCQ card 22/20/20/20 padding kept as Figma-locked exception to symmetric-padding rule. Decision deferred to plan 02-05 for full card geometry."
  - "Topbar 14/0 padding kept as exception — bottom IS the separator line, not breathing room."

patterns-established:
  - "Scoped CSS via wrapper key + data-testid — never new global rules"
  - "Sandbox isolation — three theme.py copies (production + previews/ template + bench-local), byte-equal verified by diff -q in CI"
  - "Visual preview gate per plan — bench-v1 components flip to production-locked only via the next plan's real-context preview gate"
  - "html.escape() on every helper that interpolates user text"
  - "Token-table-with-Drift-column in 02-WIDGETS.md so Figma vs CONTEXT vs shipped values stay reconciled"

requirements-completed: [PAGE-01, PAGE-02, PAGE-03, PAGE-04, PAGE-05]

# Metrics
duration: 24h03min wall-clock (across 2 days, ~6h hands-on minus 4 human-verify gates)
completed: 2026-05-03
---

# Phase 2 Plan 01: Theme + tokens + previews/ scaffold + Wave-1 spikes + Phase-1 sidecar back-fill — Summary

**Production design system shipped (Fraunces+JetBrains Mono, paper-and-stamp aesthetic, 26 bench-validated components, 11 Python helpers, html.escape-hardened); previews/ sandbox-isolation scaffold runnable with theme bench + 2 spikes + 4 tests; 18 sidecars carry plain-language Code walkthroughs; Q3 fallback locked, Q4 mechanically working, Q8 fixed; C-22 + D-2.20a + D-2.25a amendments recorded.**

## Performance

- **Duration:** ~24h wall-clock across 2 days (2026-05-02 17:14 → 2026-05-03 17:16 +0200). Hands-on time was substantially less — 4 `checkpoint:human-verify` cycles with Tiago accounted for most of the calendar gap.
- **Started:** 2026-05-02T15:14:13Z
- **Completed:** 2026-05-03T15:16:56Z
- **Tasks:** 12 plan tasks executed (Tasks 1–12) + 2 inserted cleanups (the 5-defect / Defect-6 / Defects 7-9 fix sequences after bench review; the validation-status cleanup after doc review).
- **Commits:** 13 plan commits + 1 metadata commit + 1 side-channel = 15 total on `main`.
- **Files modified:** 51 unique.

## Accomplishments

- **Production theme shipped.** `app/brain/theme/theme.py` with embedded `_CSS` (D-2.17), self-hosted `@font-face` (D-2.16), `prefers-reduced-motion` block (D-2.15), MCQ rebuild from Figma node 4045:282 driven by `:has(input:checked)` (D-2.20 + D-2.20a), `st.status` + `st.expander` skins (D-2.21), and `html.escape()` hardening on every helper (D-2.19). `streamlit_app.py` calls `inject_theme()` once before `st.navigation`.
- **Sandbox isolation scaffold runnable.** `previews/` with three theme.py copies (production + `previews/_theme.py` template + bench-local), `_fixtures.py` (FAKE_USER, FAKE_CLASS, 3 lectures, 4 LOs, 31 slide-pages mirroring MII_SM1, 19 MCQs with 4 multi-correct, 2 attempts, 5 attempt-answers, `fake_call_claude` stub), 1 component bench, 2 spike sandboxes. `tests/test_no_app_imports_in_previews.py` mechanically enforces zero `from app...` reach.
- **Theme bench visually approved at `1c0148b`** after 9 visual defects + 1 Defect-6 typography fix. The path was Tasks 2-4 → Task 5 checkpoint → defects 1-5 fix → re-present → defect 6 fix → re-present → defects 7-9 fix → final approval.
- **3 Wave-1 spike verdicts.** Q3 FAIL (live click test confirmed overlay-button doesn't toggle); Q4 mechanically-working-pending-memory-observation (boot + tick + state isolation confirmed; 5-min RSS observation pending); Q8 FIXED (cache_resource decorator + 3 tests passing).
- **Q8 production fix.** `app/db/connection.py` `connect()` now `@st.cache_resource`-decorated. Pre-existing smoke test continues to pass; new `tests/test_db_connection_cache_resource.py` covers identity, FK pragma, and cache-key isolation.
- **18 script sidecars carry plain-language `## Code walkthrough` sections.** 16 Phase-1 back-fills + 2 new Phase-2 (`theme.md`, `_difficulty.md`). Function-by-function, no line refs, no code dumps. Audience: Juliette + Cons + grading rubric.
- **`ui/documentation.md` filled and approved at `f166ea2`.** § 1.1 Component validation levels, § 5 Component catalog (29-row Status index + 26 per-component sections + 3 deferred), § 8 DOM reach map (3 sub-tables: by widget / by wrapper-key / selector style rules). 495 lines, under D-2.25's 500 cap.
- **3 architectural amendments recorded** (C-22 line-cap-removal + scope-clarification, D-2.20a `:has()` MCQ refactor, D-2.25a validation-status taxonomy).

## Task Commits

Each task was committed atomically:

1. **Task 1: Figma component-logic researcher run (D-2.26)** — pre-existing `4a60394` (parallel-session output already on disk; no new commit). Tiago confirmed at session start.
2. **Task 2: Migrate theme.py with D-2.12..D-2.24 amendments** — `a822de3` (feat)
3. **Task 3: Validate D-2.12 tokens + write 02-WIDGETS.md** — `e747d36` (docs)
4. **Task 4: previews/ sandbox scaffold + _fixtures.py + theme bench migration** — `fc7dd67` (feat)
5. **Task 5: Bench checkpoint** — pure human-verify; the work landed across the next 3 fix commits below.
6. **Defects 1-5 fix** — `bd51b32` (fix) — MCQ Off↔On animation; stat-card min-height; symmetric-padding sweep; topbar 4-sub-fix block; empty-state centring.
7. **Defect 6 fix** — `e70393d` (fix) — Serif/H2 + `heading_h2()` helper; 15 bench section headings migrated.
8. **Defects 7-9 fix** — `1c0148b` (fix) — class-card padding 18→22; MCQ `:has(input:checked)` refactor (D-2.20a); topbar underline kill broadened to whole topbar scope; `showBorderAroundInputs` → `showWidgetBorder` rename. **Bench approved here.**
9. **Task 6: Q4 fragment-timer spike** — `6fada80` (feat)
10. **Task 7: Q3 card overlay spike** — `561c5b7` (feat)
11. **Task 8: Q8 cache_resource fix** — `4de9243` (fix)
12. **Task 9: 16 sidecars + C-22 amendment** — `c28ec7c` (docs)
13. **Task 10: ui/documentation.md § 5 + § 8** — `afedb26` (docs)
14. **Task 11 cleanup: Status column + Q3 FAIL + D-2.25a** — `f166ea2` (docs). **Doc approved here.**
15. **Task 12 verifier scope clarification (Path C)** — `3936ba5` (docs)
16. **Plan metadata** — pending final commit (this SUMMARY + STATE + ROADMAP).

Side-channel commit `f6da2d0` (not from this executor) added OQ-1 to `02-FIGMA-RESEARCH.md` between Tasks 5 and 6 — preserved through the rest of the plan.

## Files Created/Modified

### Production code
- `app/brain/theme/__init__.py` — re-exports 11 callables
- `app/brain/theme/theme.py` — design system `_CSS` + helpers + inject_theme
- `app/brain/theme/theme.md` — sidecar with walkthrough
- `app/brain/theme/edit_this_later.md` — D-2.12..D-2.24 edit-map
- `app/mock_take/question_render/_difficulty.py` — `difficulty_stars()` (5 SVG stars)
- `app/mock_take/question_render/_difficulty.md` — sidecar with walkthrough
- `app/db/connection.py` — `@st.cache_resource` decorator added to `connect()`
- `streamlit_app.py` — calls `inject_theme()` once before `st.navigation`
- `assets/icons/star_filled.svg`, `assets/icons/star_empty.svg`

### Phase-1 sidecars (back-filled with `## Code walkthrough`)
- `app/brain/claude_client/claude_client.md`
- `app/brain/ingestion/pdf_to_md_v3.md`
- `app/brain/ingestion/page_splitter/page_splitter.md`
- `app/my_classes/factsheet_clean/factsheet_cleaner.md`
- `app/my_classes/factsheet_clean/factsheet_renderer.md`
- `app/class_/lo_extract/lo_extractor.md`
- `app/class_/mcq_generate/mcq_generator.md`
- `app/class_/lecture_ingest/lecture_ingest.md`
- `app/db/connection.md`
- `app/db/schema/schema.md` (section-by-section, since SQL has no functions)
- `app/db/queries_classes/queries_classes.md`
- `app/db/queries_lectures/queries_lectures.md`
- `app/db/queries_questions/queries_questions.md`
- `app/db/queries_pages/queries_pages.md`
- `app/db/queries_learning_objectives/queries_learning_objectives.md`
- `app/db/queries_users/queries_users.md`

### Sandboxes (`previews/`)
- `previews/README.md` — sandbox isolation rules + drift policy
- `previews/_theme.py` — byte-for-byte copy of `app/brain/theme/theme.py`
- `previews/_fixtures.py` — pure-data fixtures + `fake_call_claude` stub
- `previews/components/_theme_bench/preview.py` — migrated from `Streamlit_Test/test_components.py`, 15 sections + new "MCQ option states (D-2.20+D-2.20a)" panel + `st.status·st.expander (D-2.21)` panel; 15 section headings via `heading_h2()`
- `previews/components/_theme_bench/_theme.py` — bench-local theme copy
- `previews/spikes/SPIKES.md` — Q3/Q4/Q8 verdict report
- `previews/spikes/fragment_timer/preview.py` + `_theme.py` — Q4 sandbox
- `previews/spikes/card_interactive_overlay/preview.py` + `_theme.py` — Q3 sandbox

### Tests
- `tests/_streamlit_apptest_helpers.py` — `make_apptest()` + `fake_anthropic_client()`
- `tests/test_theme_loader.py` — 6 smoke tests for the public API + CSS markers
- `tests/test_no_app_imports_in_previews.py` — mechanical sandbox-isolation enforcement (parametrised over every `previews/*.py`)
- `tests/test_db_connection_cache_resource.py` — identity + FK pragma + cache-key isolation

### Documentation
- `ui/documentation.md` — § 1.1 validation flow, § 5 component catalog (29-row Status index + 26 per-component sections), § 8 DOM reach map (3 sub-tables)
- `.streamlit/config.toml` — D-2.12 token mirror + Streamlit-1.50 knobs (`baseRadius`, `showWidgetBorder`)
- `pyproject.toml` — `[project]` table with `streamlit>=1.50.0` pin + per-file E501 ignores for embedded-CSS files
- `requirements.txt` — Streamlit pin bumped from ≥1.36 to ≥1.50.0
- `.planning/phases/02-mock-taking-loop-p1-p5/02-WIDGETS.md` — token table + spike verdicts + component spec
- `.planning/phases/02-mock-taking-loop-p1-p5/02-CONTEXT.md` — D-2.20a + D-2.25a amendments + C-22 flex-note supersession + D-5.3 scope footnote
- `.planning/phases/02-mock-taking-loop-p1-p5/02-01-PLAN.md` — Task 9 verifier line-cap removed (Path A); Task 12 verifier scope tightened to explicit sidecar list (Path C)
- `.planning/intel/constraints.md` — C-22 amendment (line cap removed) + scope clarification
- `.planning/PROJECT.md` — C-22 row updated with scope summary
- `.planning/todos/done/2026-05-02-phase-2-streamlit-widget-catalog-research.md` — moved from pending/

## Decisions Made

See the `key-decisions` frontmatter list. The three architectural amendments (D-2.20a, D-2.25a, C-22) are the most consequential — they propagate to every Phase-2+ plan that touches the design system or ships a sidecar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Removed `from app.brain.theme import inject_theme` example from production theme.py docstring**
- **Found during:** Task 4 (previews/ scaffold)
- **Issue:** `tests/test_no_app_imports_in_previews.py` correctly flagged the docstring example as a banned import in the byte-for-byte sandbox copy `previews/_theme.py`.
- **Fix:** Trimmed the production docstring to remove the literal import line. Public API call pattern still documented in `theme.md` sidecar + `__init__.py`. Re-copied to both sandbox locations to restore byte-equality.
- **Files modified:** `app/brain/theme/theme.py`, `previews/_theme.py`, `previews/components/_theme_bench/_theme.py`
- **Verification:** All Task 2 verifiers re-passed; three-way `diff -q` clean; sandbox-isolation test green.
- **Committed in:** `fc7dd67`

**2. [Rule 2 — Missing critical functionality] D-2.20a — MCQ Off/On driven by `:has(input:checked)` instead of state-baked container key**
- **Found during:** Defect 8 review (Tiago, 2026-05-02 bench re-review)
- **Issue:** Original D-2.20 keying froze visual state at render time. Clicking an MCQ option flipped the inner checkbox but the wrapper key still said `-off`, so the elevation/stamp-shadow On treatment never appeared. Production-correctness bug, not just a bench bug.
- **Fix:** Refactored the MCQ option block in `theme.py` to use `:has(input:checked)` for the live Off→On flip, with `:not([class*="-correct"]):not([class*="-incorrect"])` guards keeping `-correct`/`-incorrect` review states mutually exclusive. Recorded as **D-2.20a** in `02-CONTEXT.md`. Updated 02-WIDGETS.md MCQ table format. Updated bench MCQ section to use identity-only keys.
- **Files modified:** `app/brain/theme/theme.py`, `previews/_theme.py`, `previews/components/_theme_bench/_theme.py`, `previews/components/_theme_bench/preview.py`, `02-CONTEXT.md`, `02-WIDGETS.md`
- **Verification:** Defect-8 spot-check (`:has(input:checked)` rule + `:not()` guards present); pytest 17/17; three-way `diff -q` clean; bench re-approved.
- **Committed in:** `1c0148b`

**3. [Rule 2 — Missing critical functionality] D-2.25a — Component validation-status taxonomy**
- **Found during:** Task 11 doc review (Tiago, 2026-05-03)
- **Issue:** § 5 of `ui/documentation.md` over-claimed "locked" on 21 components Tiago had only seen at bench-level isolation. Bench approval ≠ production approval. The doc framing didn't distinguish between "validated in real composition" and "validated as an isolated card."
- **Fix:** Added § 1.1 "Component validation levels" + § 5.0 "Status index" (29 rows) + per-component `**Status:**` lines. 26 components at `bench-v1`, 3 at `deferred`, 0 at `production-locked`. Added **D-2.25a** in `02-CONTEXT.md` recording the per-plan validation-flow rule. Mirrored in `02-WIDGETS.md`.
- **Files modified:** `ui/documentation.md`, `02-CONTEXT.md`, `previews/spikes/SPIKES.md`, `02-WIDGETS.md`
- **Verification:** § 1.1 + § 5.0 present; doc 495 lines under 500 cap; D-2.25a present in CONTEXT.
- **Committed in:** `f166ea2`

**4. [Rule 1 — Bug] Q3 verdict flipped from PENDING-RUN to FAIL based on Tiago's live test**
- **Found during:** Task 11 doc review
- **Issue:** Q3 spike's overlay-tertiary-button technique didn't toggle on card-body click. The original PENDING-RUN status was honest before the test; FAIL is honest after.
- **Fix:** Updated `previews/spikes/SPIKES.md § Q3` with FAIL verdict + chosen-approach lock (visible "Select / Selected ✓" button per card). Pre-verdict spec preserved under a "Reference" subheading. `02-WIDGETS.md ## Spike reports § Q3` mirrored. Plan 02-04 inherits the no-overlay-re-litigation constraint.
- **Files modified:** `previews/spikes/SPIKES.md`, `02-WIDGETS.md`
- **Committed in:** `f166ea2`

**5. [Rule 3 — Blocking] Streamlit 1.50 config knob rename**
- **Found during:** Defect 9 fix
- **Issue:** Streamlit 1.56 emitted `"theme.showBorderAroundInputs" is not a valid config option` warning at startup. The knob was renamed to `showWidgetBorder` in 1.50.
- **Fix:** Renamed in `.streamlit/config.toml` with an inline comment recording the rename. Original plan text still says `showBorderAroundInputs` as a historical match — that's a verifier text-pattern artefact, not an implementation match.
- **Files modified:** `.streamlit/config.toml`
- **Committed in:** `1c0148b`

**6. [Rule 3 — Blocking] C-22 verifier scope tightened to script sidecars only (Path C)**
- **Found during:** Task 12 verification block run
- **Issue:** Original plan verifier `find app -name "*.md" | xargs ...` over-matched on 3 system-prompt files (`*_system_prompt.md`) + 1 design-system edit-map (`edit_this_later.md`) — none of which can carry a `## Code walkthrough` section because they aren't code.
- **Fix:** Per Tiago's Path-C ruling, replaced the `find` walk with an explicit 18-element SIDECARS bash array. Added a "Scope clarification" bullet to C-22 in `.planning/intel/constraints.md`. Mirrored in `.planning/PROJECT.md` C-22 row. Added a scope footnote to D-5.3 in `02-CONTEXT.md`.
- **Files modified:** `02-01-PLAN.md`, `.planning/intel/constraints.md`, `.planning/PROJECT.md`, `02-CONTEXT.md`
- **Verification:** All 10 sub-checks of the plan's `<verification>` block pass; sidecar walkthrough check now targets exactly 18 script sidecars.
- **Committed in:** `3936ba5`

---

**Total deviations:** 6 auto-fixed (1 Rule 1 docstring bug, 2 Rule 2 architectural amendments, 1 Rule 1 verdict honesty fix, 2 Rule 3 Streamlit/verifier compat fixes).
**Impact on plan:** All 6 deviations were necessary for correctness, honesty, or Streamlit version compat. Three of them landed as durable amendments to project-level rules (D-2.20a, D-2.25a, C-22 + scope clarification). No scope creep — every change traces back to a specific bug, version-rename, or rule-precision request.

## Issues Encountered

- **9 visual defects + 1 Defect-6 typography fix** raised by Tiago across the bench review cycles. Each iteration produced a `bench-v1` re-presentation. All resolved across `bd51b32` / `e70393d` / `1c0148b`. Final bench approval at `1c0148b`.
- **Verifier over-match (Path C above)** — addressed by tightening the verifier scope rather than fabricating walkthroughs on non-code .md files.
- **2 PENDING-RUN spikes** (Q3, Q4) at the time of execution because the executor cannot perform live click tests or 5-minute RSS observations from inside a Bash session. Q3 resolved (FAIL) by Tiago during Task 11 review. Q4 still pending the RSS observation but mechanically working.

## User Setup Required

None — no external service configuration required. The plan is entirely local code + sandbox + docs.

## Visual Preview Gate Compliance

**Tiago has visually approved the theme bench at commit `1c0148b`.** Per CLAUDE.md "Visual Preview Gate" section, this is the locked record of bench approval. The 26 `bench-v1` components in `ui/documentation.md § 5.0` are eligible for `production-locked` flips inside their respective downstream-plan preview gates (per D-2.25a).

**Tiago has approved the filled `ui/documentation.md` at commit `f166ea2`.** Per D-2.25, the team-facing design-system reference is now complete and ready for plans 02-02 through 02-07 to consume.

## Deferred to later phases

- **Plan 02-05** must include: 5 difficulty-star slot (ML-driven), rationale block, 3 action buttons, restored MCQ-card padding decision (the 22/20/20/20 lock from D-2.23 is documented as an exception until 02-05 owns the full geometry).
- **OQ-1 Cards/Quizz variant 3** rationale block must be restored in Figma before plan 02-05 starts (tracked in `02-FIGMA-RESEARCH.md` per side-channel commit `f6da2d0`).
- **Q4 RSS-delta observation** still pending Tiago — go/no-go gate for plan 02-05's fragment-timer choice.
- **C-22 audit at end of Phase 2** (originally in the housekeeping list) **REMOVED** during the C-22 amendment — line cap is gone, no audit needed.
- **`app/brain/topbar/` rename** — still deferred to a cleanup phase (the directory is misnamed, covers sidebar + top header bits).

## Next Phase Readiness

### Wave-2 readiness checklist (Plans 02-02 + 02-03 can begin)

- [x] **Theme injected.** `streamlit_app.py` calls `inject_theme()` exactly once before `st.navigation`.
- [x] **Public API stable.** `from app.brain.theme import inject_theme, eyebrow, caption, meta, score, chip, chips_row, steps, stat_card, empty_state_text, heading_h2` — 11 callables.
- [x] **Fixtures available.** `previews/_fixtures.py` ships FAKE_USER, FAKE_CLASS, FAKE_LECTURES, FAKE_LOS, FAKE_SLIDE_PAGES, FAKE_MCQS, FAKE_ATTEMPT, FAKE_ATTEMPT_COMPLETED, FAKE_ATTEMPT_ANSWERS, `fake_call_claude`.
- [x] **AppTest helper ready.** `tests/_streamlit_apptest_helpers.py` provides `make_apptest()` + `fake_anthropic_client()` (composes with Phase-1 `tests/_fakes.py`).
- [x] **DB cache_resource fix in place.** `app/db/connection.py` decorated; pre-existing smoke test still passes.
- [x] **18 script sidecars carry walkthroughs** (D-5.3 + the 2 new Phase-2 code sidecars).
- [x] **`ui/documentation.md` is the single team-facing reference** with § 5 catalog + § 8 DOM reach map + § 1.1 validation-flow rule.
- [x] **Test suite green.** 24/24 pytest passing.
- [x] **Three theme.py copies byte-equal** (production + `previews/_theme.py` + bench-local).
- [x] **No spinner glyph anywhere.** Loading-state convention is button label `…` (ellipsis) and app-level `st.spinner()`.

### Wave-2 inheritances per plan

- **Plan 02-02 (P1 Sign Up):** uses `surf-steps`, `eyebrow`, `caption`, `score`, the auth-router upgrade. `topbar` does NOT appear (P1 has no topbar per CONTEXT). Production-lock targets: `surf-steps`, button families.
- **Plan 02-03 (P2 My Classes + Add Class):** first real-context `class-card`, `topbar`, `empty`, file-uploader-skin (deferred — design decision in this plan). Production-lock targets: `class-card`, `topbar`, `empty`.
- **Plan 02-04 (P3 Class hub):** **inherits Q3 FAIL constraint** — visible button per lecture card, no overlay-button re-litigation. First real-context `card-interactive`, `btn-tinted-accent` ("Generate Mock"), `stStatus` skin (lecture ingestion log), `sidebar-list` (Past Attempts — currently `deferred`).
- **Plan 02-05 (P4 Take Mock):** **gated on Q4 RSS-delta observation** before fragment-timer choice. First real-context `mcq-card` + `mcq-opt-{q}-{letter}` Off/On + `difficulty-stars`. Must restore OQ-1 Cards/Quizz variant 3 rationale block in Figma first.
- **Plan 02-06 (P5 Mock Review):** first real-context `mcq-opt-{key}-correct/-incorrect` review states + `summary-banner` (currently `deferred`) + `stExpander` skin.
- **Plan 02-07 (E2E + audit):** runs `tests/test_no_app_imports_in_previews.py` + the three-way `diff -q` invariant + the verifier block from this plan as part of the phase-close audit.

---
*Phase: 02-mock-taking-loop-p1-p5*
*Completed: 2026-05-03*

## Post-close-out updates

**2026-05-03 17:31 — Q4 verdict flipped to PASS.** Tiago ran the fragment_timer spike for 57 minutes; RSS shrank −240 KB in the final 3-minute window (104,720 → 104,480 KB). Steady state confirmed, no leak. Plan 02-05 ships `@st.fragment(run_every="1s")` for the P4 mock-take timer. Removes one of the deferred items from the standing list (was: "Q4 RSS-delta observation pending Tiago").

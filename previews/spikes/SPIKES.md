# Wave-1 spike reports

Three time-boxed risk-reduction spikes (RESEARCH §11) decide whether
specific Streamlit patterns are safe to ship in Plans 02-04 and 02-05.
Each spike's verdict is recorded here AND mirrored in
`02-WIDGETS.md ## Spike reports` so plan readers find it from either
direction.

| Spike | RESEARCH ref | Owner plan | Status | Sandbox |
|---|---|---|---|---|
| Q3 — Card Interactive overlay | §11 Q3 | 02-04 (P3 lecture multi-select) | **FAIL** (live test 2026-05-03 — Tiago confirmed clicking the card body does NOT toggle. Fallback chosen.) | `previews/spikes/card_interactive_overlay/preview.py` |
| Q4 — Fragment timer 5-min memory | §11 Q4 | 02-05 (P4 mock timer) | **PASS** (live observation 2026-05-03 17:31, 57m05s elapsed — RSS shrank −240 KB in the final 3m20s window; steady state, no leak) | `previews/spikes/fragment_timer/preview.py` |
| Q8 — `@st.cache_resource` on `connection.py` | §11 Q8 | 02-04, 02-05, 02-06 (every page that opens DB) | **FIXED** (Plan 02-01 Task 8, commit `4de9243`) | (production change to `app/db/connection.py` + `tests/test_db_connection_cache_resource.py`) |

---

## Q4 verdict — fragment timer 5-min memory test

**Status:** **PASS** (live observation 2026-05-03, 57m05s window).
Tiago let the sandbox run for 57 minutes and observed steady-state
memory: RSS actually **shrank** −240 KB in the final 3m20s window
(104,720 KB → 104,480 KB). No leak. The 5-min PASS bar from the
original protocol (`< 10 MB` growth across 5 minutes) is comfortably
exceeded — the spike ran more than 11× longer and lost memory
instead of gaining it.

### Verdict block (filled by Tiago)

```
Tester:         Tiago Reimann
Started:        2026-05-03 16:34
Verdict at:     2026-05-03 17:31  (57m05s elapsed)
Fragment ticks: ~3,420 (1 Hz × 57 min)

RSS at baseline (53m45s):  104,720 KB
RSS at verdict   (57m05s): 104,480 KB
Delta over 3m20s window:   −240 KB  (steady state, RSS shrinking)

Timer-state isolation: PASS (checkbox toggles never reset the timer)
Outer-rerun isolation: PASS (outer-rerun counter only ticked on user
                              interactions, not on the 1 Hz fragment
                              clock)

Q4 verdict: PASS
```

### Chosen approach for Plan 02-05

Plan 02-05 (P4 Take Mock) ships **`@st.fragment(run_every="1s")`** for
the elapsed-time timer in the topbar. The sandbox path
(`previews/spikes/fragment_timer/preview.py`) becomes the canonical
reference for the pattern. **No fallback to manual re-render-on-nav**
— the verdict is hard PASS, not conditional. Plan 02-05 inherits this
choice as a hard architectural constraint (no fragment-vs-manual
re-litigation).

### Reference — pre-verdict spec (kept for context)

The text below describes the original 5-minute-test protocol BEFORE
Tiago's 2026-05-03 17:31 live observation resolved Q4 as PASS. Kept
here so a reader can trace what was tested and how the PASS verdict
was reached. The "PASS / FAIL conditional approach" branches no
longer apply; the PASS branch was selected.

#### What the sandbox does

`previews/spikes/fragment_timer/preview.py` renders a `@st.fragment(run_every="1s")`
that paints an "ELAPSED MM:SS" counter inside a passive card. Outside
the fragment, a Reset button + an unrelated checkbox + an outer-script
rerun counter sit as the state-isolation test.

The fragment-isolation contract that was being verified:

1. **Single-body re-execution:** the fragment body re-runs on the 1 Hz
   tick; the outer script does NOT re-run (the outer-rerun counter
   should only increment on user interaction).
2. **State persistence:** `st.session_state["mock_start_ts"]` is set
   once on first session entry; the fragment reads it on every tick to
   compute elapsed seconds. Reset button rewrites it.
3. **No state bleed:** toggling the unrelated checkbox triggers a
   normal outer rerun; the timer must keep ticking from wherever it
   was, NOT reset to 0.
4. **No memory leak:** RSS growth across 5 minutes < 10 MB on the
   `streamlit` Python process. (Live result: passed by an order of
   magnitude — 57 min → −240 KB.)

#### Run command (sandbox is still runnable for reference)

```
streamlit run previews/spikes/fragment_timer/preview.py
```

#### Original measurement protocol

1. Open Activity Monitor (Cmd-Space → "Activity Monitor"). Switch to
   the **Memory** tab. Find the `streamlit` Python process (the row
   whose Command column references the spike's preview.py).
2. Note the **Memory** value (RSS) and the wall-clock time.
3. Wait 5 minutes by the clock. Watch the timer tick from 00:00.
4. During the 5 minutes, toggle the unrelated checkbox at least 3
   times. The timer card MUST keep counting up; it must NOT reset.
5. After 5 minutes, re-read the RSS in Activity Monitor.
6. PASS criteria: RSS growth < 10 MB; timer-state and outer-rerun
   isolation both PASS.

---

## Q3 verdict — Card Interactive overlay-button (RESEARCH §11 Q3)

**Status:** **FAIL.** Tiago ran the sandbox at
`previews/spikes/card_interactive_overlay/preview.py` (Plan 02-01
Task 7) on 2026-05-03 and confirmed: clicking the card body does
NOT toggle selection. The overlay-tertiary-button technique fails
in practice. Per the spike's documented decision tree, the chosen
approach is the visible "Select / Selected ✓" button fallback.

### Verdict block (filled by Tiago)

```
Card-body click toggles selection: FAIL
Multi-select live counter:         FAIL (consequence of the above)
Hover lift survives the overlay:   not material — fallback doesn't use overlay

Q3 verdict: FAIL
```

### Chosen approach for Plan 02-04

Plan 02-04 (P3 lecture multi-select) ships the **visible "Select /
Selected ✓" button per lecture card** — the spike's documented
fallback. The whole-card click-target idea is dropped. The
state-baked key suffix logic (`lecture-{i}-selected` when in
`st.session_state["selected"]`) stays the same; only the visible
affordance changes:

- Each lecture card carries an in-card `st.button("Select")` (default
  state) or `st.button("Selected ✓")` (selected state).
- The CSS for `[class*="st-key-lecture-"][class*="-selected"]` keeps
  the accent-wash bg + accent-deep border so the visual feedback on
  rerun still works.
- The `_SPIKE_CSS` overlay-positioning block does NOT lift into
  `theme.py`. Plan 02-04 writes a new `LECTURE CARD` section directly,
  using only the wrapper-and-button visual rules.

This is the constraint Plan 02-04 inherits — no overlay-button
re-litigation.

### Reference — pre-verdict spec (kept for context)

The text below describes how the spike was structured BEFORE Tiago's
2026-05-03 live test resolved Q3 as FAIL. Kept here so a reader can
trace what was tried and why the FAIL verdict was reached. The
"chosen approach" branches no longer apply; the `FAIL` branch was
selected.

#### What the sandbox does

Three lecture cards rendered via `st.container(key=f"lecture-{i}")`.
Each card has a `type="tertiary"` `st.button` absolutely positioned
to cover its full bounds (`inset: 0`, `opacity: 0`, `z-index: 2`).
The card content sits at `z-index: 1` with `pointer-events: none` so
the invisible button catches every click on the card body.

Selected state uses a state-baked key suffix (`lecture-{i}-selected`
when `lecture['id'] in st.session_state["selected"]`) — the plan's
"OR fallback" path, since `:has()` doesn't easily target a tertiary
button's pressed state. CSS branches on `[class*="-selected"]` to
paint accent-wash bg + accent-deep border on the next rerun.

#### The Q3 contract that was being verified

1. Clicking anywhere on the card body fires the overlay tertiary
   button's `on_click`. The card text is unselectable / unclickable
   directly because of `pointer-events: none` on the inner block.
2. Selection toggles correctly across multiple cards. The live
   counter line ("N lectures × 5 = 5N questions") updates.
3. Hover lift still works — the stamp shadow grows on hover, the
   wrapper translates `(-2px, -2px)`. The tertiary button's
   `data-testid` doesn't bleed into a focus ring.
4. The Q3 fallback (visible "Select / Selected ✓" button at the
   bottom of each card) was unnecessary if 1-3 held. Test result:
   1 failed → fallback chosen.

#### Run command (sandbox is still runnable for reference)

```
streamlit run previews/spikes/card_interactive_overlay/preview.py
```

---

## Q8 verdict — `@st.cache_resource` on `app/db/connection.py` (RESEARCH §11 Q8)

**Status:** **FIXED in Wave 1.** Plan 02-01 Task 8.

### What changed

`app/db/connection.py` `connect()` was missing `@st.cache_resource` —
without the decorator, every Streamlit rerun (and there's one per user
interaction) opened a fresh `sqlite3.Connection`, discarding the
previous one. Phase-1 carry-forward fix:

- Added `import streamlit as st`.
- Decorated `connect()` with `@st.cache_resource`. The cache key is the
  function arguments — no-arg production calls share one connection
  across the session; tests passing `db_file=tmp_path/'…'` get their
  own.
- Updated the module docstring to document the new behaviour and the
  `connect.clear()` escape hatch for tests that need to swap the DB
  at runtime.
- The existing `check_same_thread=False` was already correct (lets the
  cached connection be reused across Streamlit's worker threads).

### Verification

`tests/test_db_connection_cache_resource.py` covers three properties:

1. **Identity** — `connect(db_file)` called twice with the same arg
   returns the same Python object (`is` check).
2. **FK pragma on** — `PRAGMA foreign_keys` returns `1` on the cached
   connection.
3. **Cache key isolation** — `connect(db_a) is not connect(db_b)` when
   `db_a != db_b` (the cache key includes the path argument).

All 3 tests pass under bare pytest (no `streamlit run` context):
`@st.cache_resource` falls back to a Python-dict cache when the
ScriptRunContext is missing — it still returns the same object on
repeat calls, just emits a warning.

### Q8 verdict: **FIXED**

Pre-existing smoke test (`tests/test_smoke.py
::test_ingestion_end_to_end_against_fresh_sqlite`) continues to pass
because it explicitly passes `tmp_path/'user.sqlite'` as `db_file`,
which is a different cache key from the production no-arg call — the
two coexist in the cache without interference.

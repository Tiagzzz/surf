# Wave-1 spike reports

Three time-boxed risk-reduction spikes (RESEARCH §11) decide whether
specific Streamlit patterns are safe to ship in Plans 02-04 and 02-05.
Each spike's verdict is recorded here AND mirrored in
`02-WIDGETS.md ## Spike reports` so plan readers find it from either
direction.

| Spike | RESEARCH ref | Owner plan | Status | Sandbox |
|---|---|---|---|---|
| Q3 — Card Interactive overlay | §11 Q3 | 02-04 (P3 lecture multi-select) | TBD | `previews/spikes/card_interactive_overlay/preview.py` |
| Q4 — Fragment timer 5-min memory | §11 Q4 | 02-05 (P4 mock timer) | **PENDING-RUN** (sandbox built; Tiago to execute) | `previews/spikes/fragment_timer/preview.py` |
| Q8 — `@st.cache_resource` on `connection.py` | §11 Q8 | 02-04, 02-05, 02-06 (every page that opens DB) | TBD | (production change to `app/db/connection.py` + `tests/test_db_connection_cache_resource.py`) |

---

## Q4 verdict — fragment timer 5-min memory test

**Status:** **PENDING-RUN.** Sandbox built and runnable; awaits a live
5-minute RSS measurement that this Bash session cannot perform from
inside the executor.

### What the sandbox does

`previews/spikes/fragment_timer/preview.py` renders a `@st.fragment(run_every="1s")`
that paints an "ELAPSED MM:SS" counter inside a passive card. Outside
the fragment, a Reset button + an unrelated checkbox + an outer-script
rerun counter sit as the state-isolation test.

The fragment-isolation contract being verified:

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
   `streamlit` Python process.

### Run command

```
streamlit run previews/spikes/fragment_timer/preview.py
```

### Measurement protocol (Tiago to execute)

1. Open Activity Monitor (Cmd-Space → "Activity Monitor"). Switch to
   the **Memory** tab. Find the `streamlit` Python process (the row
   whose Command column references the spike's preview.py).
2. Note the **Memory** value (RSS) and the wall-clock time. Round
   to the nearest MB.
3. Wait 5 minutes by the clock. Watch the timer in the browser tick
   from 00:00 toward 05:00.
4. During the 5 minutes, toggle the unrelated checkbox at least 3
   times. The timer card MUST keep counting up; it must NOT reset.
5. After 5 minutes, re-read the RSS in Activity Monitor.
6. **PASS criteria:**
   - RSS growth < 10 MB across the 5 minutes.
   - Timer never reset on checkbox toggle (state isolation held).
   - Outer-rerun counter incremented only on Reset / checkbox click,
     not on each fragment tick (fragment isolation held).

### Verdict — to be filled by Tiago

```
RSS at t=0:    ___ MB
RSS at t=5min: ___ MB
Delta:         ___ MB
Timer-state isolation: PASS / FAIL
Outer-rerun isolation: PASS / FAIL

Q4 verdict: PASS / FAIL
```

### Chosen approach (conditional on verdict)

- **PASS:** Plan 02-05 (P4 Take Mock) ships the
  `@st.fragment(run_every="1s")` pattern for the elapsed-time timer in
  the topbar. Sandbox path becomes the canonical reference.
- **FAIL:** Fall back to a manual re-render-on-nav timer — elapsed
  recomputed only on Next/Prev/Skip/Submit click. The trade-off is
  that the user sees a stale "elapsed: 12:34" between clicks instead
  of a live tick; functionality is unaffected (mock duration is
  recorded from `started_at` to `finished_at` server-side regardless).

---

## Q3 verdict — Card Interactive overlay-button (RESEARCH §11 Q3)

**Status:** **PENDING-RUN.** Sandbox built at
`previews/spikes/card_interactive_overlay/preview.py` (Plan 02-01
Task 7); awaits a live click test that the executor agent cannot
perform from inside a Bash session.

### What the sandbox does

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

### The Q3 contract being verified

1. Clicking anywhere on the card body fires the overlay tertiary
   button's `on_click`. The card text is unselectable / unclickable
   directly because of `pointer-events: none` on the inner block.
2. Selection toggles correctly across multiple cards. The live
   counter line ("N lectures × 5 = 5N questions") updates.
3. Hover lift still works — the stamp shadow grows on hover, the
   wrapper translates `(-2px, -2px)`. The tertiary button's
   `data-testid` doesn't bleed into a focus ring.
4. The Q3 fallback (visible "Select / Selected ✓" button at the
   bottom of each card) is unnecessary if 1-3 hold.

### Run command

```
streamlit run previews/spikes/card_interactive_overlay/preview.py
```

### Verdict — to be filled by Tiago

```
Card-body click toggles selection: PASS / FAIL
Multi-select live counter:         PASS / FAIL
Hover lift survives the overlay:   PASS / FAIL

Q3 verdict: PASS / FAIL
```

### Chosen approach (conditional on verdict)

- **PASS:** Plan 02-04 (P3 lecture multi-select) ships the overlay-
  button pattern. The CSS snippet in this spike's `preview.py`
  (`_SPIKE_CSS` block) lifts into `app/brain/theme/theme.py` under a
  new `LECTURE CARD` section. Both `previews/_theme.py` and the bench
  `_theme.py` re-sync.
- **FAIL:** Plan 02-04 ships the visible "Select / Selected ✓" button
  per card. Less elegant — the click target is a small button rather
  than the whole card body — but no `data-testid` reliance. The
  state-baked key suffix logic stays the same; only the visible button
  changes.

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

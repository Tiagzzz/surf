"""Spike — fragment-timer 5-min memory test (RESEARCH §11 Q4).

Validates the architectural choice for the P4 mock-taking timer:

  Q4 — Does `@st.fragment(run_every="1s")` re-execute ONLY the
  fragment body on each tick, with no full-page rerun and no state
  drift, for at least 5 minutes?

If PASS, Plan 02-05 (P4 Take Mock) ships the fragment-timer pattern.
If FAIL, the fallback is a manual re-render-on-nav timer (recompute
elapsed only on Next/Prev/Skip/Submit click, no auto-tick).

Run from the repo root:
    streamlit run previews/spikes/fragment_timer/preview.py

Then watch the timer for 5 minutes while the unrelated checkbox
OUTSIDE the fragment stays stable. Memory measurement protocol is in
`previews/spikes/SPIKES.md § Q4`.

Sandbox isolation (CLAUDE.md): no `from app...` imports; sibling
`_theme.py` is the byte-for-byte copy at the time of spike write.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Sibling-relative import so the spike is fully self-contained.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402
from _theme import caption, eyebrow, heading_h2, inject_theme, meta  # noqa: E402

st.set_page_config(page_title="Surf — Spike: fragment timer", layout="wide")
inject_theme()


heading_h2("Spike — fragment timer (Q4)")
caption(
    "Watch the elapsed counter tick every second. Toggle the checkbox "
    "OUTSIDE the fragment — it must NOT reset the timer. Run for 5 minutes "
    "and watch RSS in Activity Monitor or `ps -o rss`. PASS if growth "
    "< 10 MB across the 5 minutes."
)


# Initialise the start timestamp once per session so the fragment can
# render "elapsed since start" without recomputing the anchor on every tick.
if "mock_start_ts" not in st.session_state:
    st.session_state["mock_start_ts"] = time.time()
if "tick_count" not in st.session_state:
    st.session_state["tick_count"] = 0


@st.fragment(run_every="1s")
def _timer_fragment() -> None:
    """Re-rendered every second. ONLY this body should re-execute.

    The rest of the page (the Reset button, the unrelated checkbox,
    this script's outer body) must not re-run on the 1-Hz tick — the
    fragment-isolation contract is the whole point of the spike.
    """
    elapsed_total = int(time.time() - st.session_state["mock_start_ts"])
    minutes, seconds = divmod(elapsed_total, 60)
    st.session_state["tick_count"] += 1

    with st.container(key="card-passive-timer"):
        eyebrow("ELAPSED")
        st.markdown(
            f'<p class="surf-stat-value">{minutes:02d}:{seconds:02d}</p>',
            unsafe_allow_html=True,
        )
        meta(f"Tick #{st.session_state['tick_count']}")


_timer_fragment()


st.divider()


# These two widgets sit OUTSIDE the fragment. They are the isolation test:
# clicking either one should NOT reset the timer (the fragment owns its
# own state; outer state changes don't bleed in).
heading_h2("State-isolation test (OUTSIDE the fragment)")
caption(
    "Toggling the checkbox or clicking Reset triggers a normal Streamlit "
    "rerun of the outer script. The timer above should keep ticking from "
    "wherever it was — its mock_start_ts persists in session_state, and "
    "the fragment is the only thing that re-executes on the 1 Hz clock."
)

cols = st.columns([1, 1, 2])
with cols[0]:
    with st.container(key="btn-soft-reset"):
        if st.button("Reset timer", key="reset"):
            st.session_state["mock_start_ts"] = time.time()
            st.session_state["tick_count"] = 0
with cols[1]:
    st.checkbox(
        "Unrelated checkbox (toggle me — timer must not reset)",
        key="unrelated_cb",
    )
with cols[2]:
    meta(
        f"Outer script reruns: {st.session_state.get('outer_rerun_count', 0)}  ·  "
        "Fragment ticks: see card above"
    )

# Track outer-script reruns. This counter only increments when the OUTER
# body re-executes (i.e. on a real user interaction outside the fragment),
# never on a fragment tick.
st.session_state["outer_rerun_count"] = st.session_state.get(
    "outer_rerun_count", 0
) + 1


st.divider()


heading_h2("How to run the 5-minute test")
caption(
    "1. Open Activity Monitor (Cmd-Space → 'Activity Monitor'). Find the "
    "`streamlit` Python process and note its RSS / Memory column. "
    "2. Note the current time. "
    "3. Wait 5 minutes. "
    "4. Re-read the RSS. PASS if the delta is < 10 MB. "
    "5. Toggle the unrelated checkbox during the test — the timer in the "
    "card must not reset. "
    "6. Record the verdict in `previews/spikes/SPIKES.md` § Q4."
)

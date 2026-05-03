"""Spike — Card Interactive overlay-button (RESEARCH §11 Q3).

Validates the architectural choice for the P3 lecture multi-select:

  Q3 — Can a transparent absolutely-positioned `st.button(type=
  "tertiary")` cover an entire card so that a click ANYWHERE on the
  card body toggles selection? The button is invisible
  (`opacity: 0`); its `data-testid` is the reach hook for the CSS.

If PASS, Plan 02-04 (P3 lecture multi-select) ships the overlay-
button pattern — clean visual (the whole card is the click target)
with a hidden tertiary button as the actual click handler.

If FAIL, the fallback is a visible "Select / Selected ✓" button at
the bottom of each card. Uglier but no `data-testid` reliance.

Run from the repo root:
    streamlit run previews/spikes/card_interactive_overlay/preview.py

Sandbox isolation (CLAUDE.md): no `from app...` imports; sibling
`_theme.py` is the byte-for-byte copy at the time of spike write.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Sibling-relative import so the spike is fully self-contained.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402
from _theme import caption, heading_h2, inject_theme, meta  # noqa: E402

st.set_page_config(page_title="Surf — Spike: card overlay button", layout="wide")
inject_theme()


# Local CSS extension — paints the overlay-button technique. Lives in
# the spike (not in the production theme.py) until Q3 verdict is in;
# if PASS, Plan 02-04 lifts this snippet into theme.py with the canon
# `[class*="st-key-lecture-"]` selectors.
_SPIKE_CSS = """
<style>
/* Each lecture card is a relative-positioned wrapper so the absolute
   tertiary button can cover its full bounds. */
[class*="st-key-lecture-"] {
  position: relative;
  background: var(--paper-0);
  border: 1.5px solid var(--paper-2);
  border-radius: var(--r-md);
  padding: 18px 22px;
  margin-bottom: 12px;
  box-shadow: 4px 4px 0 0 var(--paper-shadow);
  transition: transform var(--t-base), box-shadow var(--t-base),
              background-color var(--t-base), border-color var(--t-base);
  cursor: pointer;
}
[class*="st-key-lecture-"]:hover {
  transform: translate(-2px, -2px);
  box-shadow: 6px 6px 0 0 var(--paper-shadow);
}
[class*="st-key-lecture-"]:active {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 0 var(--paper-shadow);
}

/* SELECTED state — paper elevation + accent-deep border + accent-wash
   bg. Triggered by the state-baked suffix `lecture-{i}-selected` (the
   click handler swaps the wrapper key on rerun). */
[class*="st-key-lecture-"][class*="-selected"] {
  background: var(--accent-wash);
  border: 2px solid var(--accent-deep);
}

/* Hide the tertiary button visually but keep it click-active. The
   button covers the entire card (`inset: 0`) so any click on the
   card body fires the button's on_click. */
[class*="st-key-lecture-"] [data-testid="stBaseButton-tertiary"],
[class*="st-key-lecture-"] [data-testid="stButton"] button[kind="tertiary"] {
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  opacity: 0 !important;
  border: none !important;
  background: transparent !important;
  cursor: pointer !important;
  z-index: 2;
}

/* The card content sits below the overlay button via z-index so the
   button receives the click but the text is what's visually shown. */
[class*="st-key-lecture-"] > div[data-testid="stVerticalBlock"] {
  position: relative;
  z-index: 1;
  pointer-events: none;
}
</style>
"""

st.markdown(_SPIKE_CSS, unsafe_allow_html=True)


heading_h2("Spike — Card Interactive overlay-button (Q3)")
caption(
    "Three lecture cards. Each card has a transparent tertiary "
    "`st.button` overlay-positioned over its full bounds. Click "
    "anywhere on a card to toggle its selection. Selected = accent-deep "
    "border + accent-wash background."
)


# Initialise the selection set in session_state.
if "selected" not in st.session_state:
    st.session_state["selected"] = set()


LECTURES = [
    {"id": 1, "title": "Lecture 01 — Introduction to markets", "status": "done"},
    {"id": 2, "title": "Lecture 02 — Supply and demand", "status": "pending"},
    {"id": 3, "title": "Lecture 03 — Elasticity", "status": "done"},
]


def _toggle(lecture_id: int) -> None:
    """Toggle membership in the selected set."""
    if lecture_id in st.session_state["selected"]:
        st.session_state["selected"].remove(lecture_id)
    else:
        st.session_state["selected"].add(lecture_id)


for lecture in LECTURES:
    is_selected = lecture["id"] in st.session_state["selected"]
    # State-baked key suffix per the plan's "OR fallback" path. The
    # CSS branches on `[class*="-selected"]` to paint the selected
    # visual on the next rerun after the click.
    key_suffix = "-selected" if is_selected else ""
    card_key = f"lecture-{lecture['id']}{key_suffix}"

    with st.container(key=card_key):
        # Card content (visible, but pointer-events: none so the
        # overlay button below catches every click).
        cols = st.columns([8, 1])
        with cols[0]:
            st.markdown(f"### {lecture['title']}")
            meta(
                f"Status: {lecture['status'].upper()}  ·  "
                f"{'✓ Selected' if is_selected else 'Tap card to select'}"
            )
        with cols[1]:
            if is_selected:
                st.markdown(
                    '<p class="surf-meta" style="text-align: right; '
                    'font-size: 22px; color: var(--accent-deep);">✓</p>',
                    unsafe_allow_html=True,
                )

        # Overlay button — covers the full card via the CSS above.
        # type="tertiary" is the data-testid hook; opacity: 0 makes
        # it invisible but click-active.
        st.button(
            "Toggle",
            key=f"toggle-{lecture['id']}",
            type="tertiary",
            on_click=_toggle,
            args=(lecture["id"],),
        )


st.divider()


count = len(st.session_state["selected"])
heading_h2("Live counter")
caption(f"{count} lectures × 5 = {count * 5} questions in the mock.")


st.divider()


heading_h2("How to verify (Q3)")
caption(
    "1. Click the body text of any lecture card — selection should "
    "toggle (the card paints accent-wash bg + accent-deep border on "
    "rerun). 2. Click the same card again — selection clears. 3. "
    "Click two different cards — both highlight; counter shows '2 "
    "lectures × 5 = 10 questions'. 4. Hover any card — it lifts via "
    "the stamp shadow growing. 5. If clicking the card body does "
    "NOT toggle (the tertiary button isn't catching the click), the "
    "overlay-button technique fails and the Q3 fallback (visible "
    "'Select / Selected ✓' button per card) is the chosen approach. "
    "Record the verdict in `previews/spikes/SPIKES.md` § Q3."
)

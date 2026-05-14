"""P5 — Review Mock / Practice. Thin Streamlit page wrapper."""
from __future__ import annotations

import streamlit as st

from app.brain.session import get_saved_user
from app.mock_review import render_review_mock_page

# --------------------------------------------------------------------------- #
# P5 REVIEW MOCK / PRACTICE PAGE WRAPPER
# --------------------------------------------------------------------------- #
# Simple explanation:
# This wrapper renders P5 (the review page shown after a mock or practice
# attempt). It checks that a user is signed in, reads the selected class id
# and the current attempt id from session state, and hands off to the
# `mock_review` bucket which owns the per-question review cards, the
# exact-match correctness display, and the 5-star difficulty estimate.
#
# Important code pieces:
# - `get_saved_user()`: from `app/brain/session.py`; returns the saved local
#   user or `None` (falls back to P1 signup).
# - `st.session_state.get("selected_class_id")`: the class context.
# - `st.session_state.get("current_attempt_id")`: the attempt being reviewed,
#   set when the user finishes P4 or opens an entry in Attempt History.
# - `render_review_mock_page(user=..., class_id=..., attempt_id=...)`: from
#   `app/mock_review/`. Owns the page UI and the read-only review layout.
#
# Page identity:
# P5 does NOT use the shared common page header (per the locked design rule),
# but DOES use the shared topbar — the bucket renderer calls
# `render_topbar(current_page="review_mock_exam", class_name=...)`, which
# appends a `Review` segment to the breadcrumb.

_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    _class_id = st.session_state.get("selected_class_id")
    _attempt_id = st.session_state.get("current_attempt_id")
    render_review_mock_page(user=_user, class_id=_class_id, attempt_id=_attempt_id)

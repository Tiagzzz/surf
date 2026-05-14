"""P4 — Take Mock / Practice. Thin Streamlit page wrapper."""
from __future__ import annotations

import streamlit as st

from app.brain.session import get_saved_user
from app.mock_take import render_take_mock_page

# --------------------------------------------------------------------------- #
# P4 TAKE MOCK / PRACTICE PAGE WRAPPER
# --------------------------------------------------------------------------- #
# Simple explanation:
# This wrapper renders P4 (the mock exam / practice taking page). It checks
# that a user is signed in, reads the selected class id from session state,
# and hands off to the `mock_take` bucket which owns the question card, the
# MCQ options, NEXT / SKIP / SUBMIT controls, and the elapsed-time timer.
#
# Important code pieces:
# - `get_saved_user()`: from `app/brain/session.py`; returns the saved local
#   user or `None` (in which case the page falls back to P1 signup).
# - `st.session_state.get("selected_class_id")`: the class id picked on P2 /
#   P3. The bucket renderer is responsible for recovery if it is missing.
# - `render_take_mock_page(user=..., class_id=...)`: from `app/mock_take/`.
#   Owns the page UI, answer state (session-only until final submit), and the
#   final all-or-nothing transaction that saves the attempt and answer rows.
#
# Page identity:
# P4 does NOT use the shared common page header (per the locked design rule),
# but DOES use the shared topbar — the bucket renderer calls
# `render_topbar(current_page="take_mock_exam", ...)` with a class label and
# a mode label.

_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    _class_id = st.session_state.get("selected_class_id")
    render_take_mock_page(user=_user, class_id=_class_id)

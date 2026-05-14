"""P6 — Dashboard. Thin Streamlit page wrapper.

Page logic lives in :mod:`app.dashboard`. This wrapper resolves the
saved local user via :func:`app.brain.session.get_saved_user`, routes
unauthenticated users back to P1, reads ``selected_class_id`` from
``st.session_state``, and delegates the ownership/analytics flow.
"""
from __future__ import annotations

import streamlit as st

from app.brain.session import get_saved_user
from app.dashboard import render_dashboard_page

# --------------------------------------------------------------------------- #
# P6 DASHBOARD PAGE WRAPPER
# --------------------------------------------------------------------------- #
# Simple explanation:
# This wrapper renders P6 (the per-class analytics dashboard). It checks that
# a user is signed in, reads the selected class id from session state, and
# hands off to the `dashboard` bucket which owns the last-N mock metrics, the
# performance-by-question-type chart, and the shared topbar with the
# `Dashboard` breadcrumb segment.
#
# Important code pieces:
# - `get_saved_user()`: from `app/brain/session.py`; returns the saved local
#   user or `None` (falls back to P1 signup).
# - `st.session_state.get("selected_class_id")`: the class context the
#   dashboard scopes its metrics to.
# - `render_dashboard_page(user=..., selected_class_id=...)`: from
#   `app/dashboard/`. Owns the page UI, the partial-average copy when fewer
#   than 4 mocks exist, and the topbar render call.
#
# Page identity:
# P6 is authenticated and uses the shared topbar; the bucket renderer calls
# `render_topbar(current_page="dashboard", class_name=...)` so the breadcrumb
# reads `MY CLASSES › <CLASS> › DASHBOARD` when a class is known.

_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    _selected_class_id = st.session_state.get("selected_class_id")
    render_dashboard_page(user=_user, selected_class_id=_selected_class_id)

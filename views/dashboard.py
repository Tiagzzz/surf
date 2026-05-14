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

_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    _selected_class_id = st.session_state.get("selected_class_id")
    render_dashboard_page(user=_user, selected_class_id=_selected_class_id)

"""P4 — Take Mock / Practice. Thin Streamlit page wrapper."""
from __future__ import annotations

import streamlit as st

from app.brain.session import get_saved_user
from app.mock_take import render_take_mock_page

_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    _class_id = st.session_state.get("selected_class_id")
    render_take_mock_page(user=_user, class_id=_class_id)

"""P2 — My Classes (Home). Thin Streamlit page wrapper.

The page logic and visual contract live in
:mod:`app.my_classes.class_list_render`. This wrapper resolves the
saved local user via :func:`app.brain.session.get_saved_user` and
hands off; if no user is signed in it routes back to P1.
"""
from __future__ import annotations

import streamlit as st

from app.brain.session import get_saved_user
from app.my_classes.class_list_render import render_my_classes_page

# Resolve auth at the page boundary; the app bucket owns the P2 UI and actions.
_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    render_my_classes_page(user=_user)

"""P7 — Settings page (thin Streamlit wrapper).

The page renderer, locked content strings, and routing logic live in
:mod:`app.settings`. This wrapper only resolves the current saved user
and forwards into ``render_settings_page``.
"""
# Loads the saved user before handing the page to the Settings renderer.
from __future__ import annotations

from app.brain.session import get_saved_user
from app.settings import render_settings_page

user = get_saved_user()
if user is None:
    # P7 is gated behind authentication; the streamlit_app router only
    # mounts this page when is_authenticated() is True. The fallthrough
    # here is a defensive no-op that surfaces the unauth state in the
    # rare race where a saved key disappeared between routing and render.
    import streamlit as st

    st.error("Not signed in.")
else:
    render_settings_page(user=user)

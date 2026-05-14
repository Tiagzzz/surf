"""P7 — Settings page (thin Streamlit wrapper).

The page renderer, locked content strings, and routing logic live in
:mod:`app.settings`. This wrapper only resolves the current saved user
and forwards into ``render_settings_page``.
"""
# Loads the saved user before handing the page to the Settings renderer.
from __future__ import annotations

from app.brain.session import get_saved_user
from app.settings import render_settings_page

# --------------------------------------------------------------------------- #
# P7 SETTINGS PAGE WRAPPER
# --------------------------------------------------------------------------- #
# Simple explanation:
# This wrapper renders P7 (Settings — API key replacement and full reset). It
# resolves the saved local user and forwards into the settings bucket, which
# owns the locked content strings, the destructive `DELETE` confirmation, and
# the shared topbar with the `Settings` breadcrumb segment.
#
# Important code pieces:
# - `get_saved_user()`: from `app/brain/session.py`; returns the saved local
#   user or `None`.
# - The `if user is None` branch: P7 is supposed to be gated by the streamlit
#   router (only mounted when authenticated), so this is a defensive no-op for
#   the rare race where the saved key disappeared between routing and render.
# - `render_settings_page(user=user)`: from `app/settings/`. Owns the page UI,
#   the key-replacement validation, the typed-`DELETE` reset confirmation,
#   and the shared topbar call with `current_page="settings"`.
#
# Page identity:
# P7 is authenticated and uses the shared topbar; the bucket renderer calls
# `render_topbar(current_page="settings")` so the breadcrumb reads
# `MY CLASSES › SETTINGS`.

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

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

# --------------------------------------------------------------------------- #
# P2 MY CLASSES PAGE WRAPPER
# --------------------------------------------------------------------------- #
# Simple explanation:
# This wrapper renders P2 (the authenticated home / My Classes list). It checks
# that a local user is signed in, then hands off to the My Classes bucket which
# owns the class grid, the create-class flow, and the shared topbar render call.
#
# Important code pieces:
# - `get_saved_user()`: from `app/brain/session.py`. Returns the locally saved
#   user record, or `None` if no signup has happened yet.
# - `st.switch_page("views/signup.py")`: if no user is signed in, sends the
#   visitor back to P1 so they cannot reach the authenticated surface.
# - `render_my_classes_page(user=_user)`: from
#   `app/my_classes/class_list_render.py`. Owns the page UI and calls the
#   shared `render_topbar(current_page="my_classes")` itself.
#
# App connection:
# This is the landing surface after signup. The shared authenticated topbar is
# drawn by the bucket renderer (P2 is one of the pages that uses the topbar).

# Resolve auth at the page boundary; the app bucket owns the P2 UI and actions.
_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    render_my_classes_page(user=_user)

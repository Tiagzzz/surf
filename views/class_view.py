"""P3 — Class Hub. Thin Streamlit page wrapper.

Page logic lives in :mod:`app.class_.class_hub`. This wrapper:

* resolves the saved local user via :func:`app.brain.session.get_saved_user`
  and routes back to P1 when no user is signed in;
* reads ``selected_class_id`` from ``st.session_state``; when the slot
  is missing (or the lookup is invalid) the renderer itself falls into
  the recovery state with a ``BACK TO MY CLASSES`` button — no extra
  branching needed here.
"""
from __future__ import annotations

import streamlit as st

from app.brain.session import get_saved_user
from app.class_.class_hub import render_class_hub_page

# --------------------------------------------------------------------------- #
# P3 CLASS HUB PAGE WRAPPER
# --------------------------------------------------------------------------- #
# Simple explanation:
# This wrapper renders P3 (the Class Hub for one selected class). It checks
# that a user is signed in and forwards the currently selected class id to the
# `class_` bucket renderer, which owns the hub layout, lecture upload, mock
# launch CTA, attempt history, and the shared topbar with class breadcrumb.
#
# Important code pieces:
# - `get_saved_user()`: from `app/brain/session.py`; returns the saved local
#   user or `None`.
# - `st.session_state.get("selected_class_id")`: reads the class id picked on
#   P2 from Streamlit's per-session memory. `None` is allowed — the renderer
#   shows a recovery screen with a `BACK TO MY CLASSES` button when the slot
#   is missing or invalid.
# - `render_class_hub_page(user=..., class_id=...)`: from
#   `app/class_/class_hub.py`. Owns the P3 UI and the shared topbar call.
#
# App connection:
# P3 is reached from P2 by clicking a class card. The shared topbar shows
# `MY CLASSES › <CLASS NAME>` because the bucket renderer passes the class
# name into `render_topbar(current_page="class_view", class_name=...)`.

_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    _class_id = st.session_state.get("selected_class_id")
    render_class_hub_page(user=_user, class_id=_class_id)

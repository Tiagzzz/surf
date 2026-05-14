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

_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    _class_id = st.session_state.get("selected_class_id")
    render_class_hub_page(user=_user, class_id=_class_id)

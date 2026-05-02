"""Surf — entry point.

Acts as a router: shows SIGNUP when the user has no credentials saved,
otherwise shows the 6 authenticated pages via Streamlit's st.navigation API.

Note on the folder name: pages live in `views/`, not `pages/`. Streamlit's
legacy multi-page magic auto-discovers a `pages/` directory and would
duplicate them in the sidebar alongside `st.navigation`. Using `views/`
keeps `st.navigation` as the single source of truth.
"""
from pathlib import Path

import streamlit as st

from app.brain.theme import inject_theme

inject_theme()


def is_authenticated() -> bool:
    """Has the user signed up on this machine?

    Today's heuristic: `~/.surf/user.sqlite` exists. The Sign Up page will
    create that file on first run; signed-in state then persists across
    browser refreshes (`st.session_state` does not).

    TODO(brain.session): replace with `from app.brain.session import
    is_authenticated` once `app/brain/session/` reads the users table and
    verifies a saved API key.
    """
    return (Path.home() / ".surf" / "user.sqlite").exists()


if is_authenticated():
    pages = [
        st.Page("views/my_classes.py", title="My Classes", default=True),
        st.Page("views/class_view.py", title="Class"),
        st.Page("views/take_mock_exam.py", title="Take Mock Exam"),
        st.Page("views/review_mock_exam.py", title="Review Mock Exam"),
        st.Page("views/dashboard.py", title="Dashboard"),
        st.Page("views/settings.py", title="Settings"),
    ]
else:
    pages = [st.Page("views/signup.py", title="Sign Up", default=True)]

st.navigation(pages).run()

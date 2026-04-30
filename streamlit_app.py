"""Surf — entry point.

Acts as a router: shows SIGNUP when the user has no credentials saved,
otherwise shows the 6 authenticated pages via Streamlit's st.navigation API.
"""
import streamlit as st


def is_authenticated() -> bool:
    """Stub. Replace with `from app.brain.session import is_authenticated`
    once app/brain/session/ is implemented."""
    return st.session_state.get("user_id") is not None


if is_authenticated():
    pages = [
        st.Page("pages/my_classes.py", title="My Classes", default=True),
        st.Page("pages/class_view.py", title="Class"),
        st.Page("pages/take_mock_exam.py", title="Take Mock Exam"),
        st.Page("pages/review_mock_exam.py", title="Review Mock Exam"),
        st.Page("pages/dashboard.py", title="Dashboard"),
        st.Page("pages/settings.py", title="Settings"),
    ]
else:
    pages = [st.Page("pages/signup.py", title="Sign Up", default=True)]

st.navigation(pages).run()

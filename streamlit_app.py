# Surf app entry point.
# The router shows Sign Up until a saved local user with a non-blank Anthropic key exists.
# Authenticated users get the six approved app pages through Streamlit navigation.
# Route files live in views/ so Streamlit's pages/ auto-discovery stays off.

import streamlit as st

from app.brain.session import is_authenticated

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

# Surf app entry point.
# The router shows Sign Up until a saved local user with a non-blank Anthropic key exists.
# Authenticated users get the six approved app pages through Streamlit navigation.
# Route files live in views/ so Streamlit's pages/ auto-discovery stays off.

import streamlit as st

from app.brain.session import is_authenticated

AUTHENTICATED_HOME_VIEW = "views/my_classes.py"
AUTHENTICATED_HOME_REDIRECT_KEY = "_surf_authenticated_home_redirect_done"


def should_redirect_authenticated_session_home(session_state) -> bool:
    """Return True once per signed-in browser session to land on My Classes."""
    # A browser refresh starts a fresh Streamlit session without this flag.
    if session_state.get(AUTHENTICATED_HOME_REDIRECT_KEY):
        return False
    session_state[AUTHENTICATED_HOME_REDIRECT_KEY] = True
    return True


authenticated = is_authenticated()

if authenticated:
    pages = [
        st.Page(AUTHENTICATED_HOME_VIEW, title="My Classes", default=True),
        st.Page("views/class_view.py", title="Class"),
        st.Page("views/take_mock_exam.py", title="Take Mock Exam"),
        st.Page("views/review_mock_exam.py", title="Review Mock Exam"),
        st.Page("views/dashboard.py", title="Dashboard"),
        st.Page("views/settings.py", title="Settings"),
    ]
else:
    pages = [st.Page("views/signup.py", title="Sign Up", default=True)]

navigation = st.navigation(pages)

if authenticated and should_redirect_authenticated_session_home(st.session_state):
    st.switch_page(AUTHENTICATED_HOME_VIEW)

navigation.run()

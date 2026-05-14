"""P1 — Sign Up. Thin Streamlit wrapper around ``render_signup_flow``."""
# Hands the signup route to the signup bucket renderer.

# --------------------------------------------------------------------------- #
# P1 SIGNUP PAGE WRAPPER
# --------------------------------------------------------------------------- #
# Simple explanation:
# This is the entry point Streamlit loads for the Sign Up page (P1). It is the
# only Surf page that runs while the user is unauthenticated, so it deliberately
# does NOT call the shared authenticated topbar. All layout, validation, and
# API-key save behavior live inside the signup bucket renderer below.
#
# Key detail:
# - `render_signup_flow`: imported from `app/signup/signup_flow.py`. Calling it
#   draws the whole P1 page (form, validation, save) into the current Streamlit
#   script run.
#
# App connection:
# Streamlit picks this file up from `streamlit_app.py` as the P1 route. On a
# successful signup the renderer itself navigates the user onward to P2.

from app.signup.signup_flow import render_signup_flow

# Route-level wrapper: the signup bucket owns layout, validation, and save behavior.
render_signup_flow()

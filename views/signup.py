"""P1 — Sign Up. Thin Streamlit wrapper around ``render_signup_flow``."""
# Hands the signup route to the signup bucket renderer.

from app.signup.signup_flow import render_signup_flow

# Route-level wrapper: the signup bucket owns layout, validation, and save behavior.
render_signup_flow()

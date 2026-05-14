"""P6 dashboard package exports."""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# PACKAGE EXPORTS — P6 DASHBOARD PUBLIC SURFACE
# --------------------------------------------------------------------------- #
# Simple explanation:
# This file is the "front door" of the P6 dashboard package. It re-exports the
# single public function `render_dashboard_page` so other parts of the app can
# write `from app.dashboard import render_dashboard_page` instead of reaching
# into the internal `dashboard_flow` module.
#
# Important code pieces:
# - `from app.dashboard.dashboard_flow import render_dashboard_page`: pulls the
#   real implementation up to the package level.
# - `__all__`: lists the names this package promises as public. Anything not
#   listed (the chart sub-packages, helpers, etc.) is internal.
#
# App connection:
# `views/dashboard.py` is the Streamlit view file that calls this entry point
# to draw the P6 page after class ownership has been validated.
from app.dashboard.dashboard_flow import render_dashboard_page

__all__ = ["render_dashboard_page"]

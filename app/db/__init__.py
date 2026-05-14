# --------------------------------------------------------------------------- #
# PACKAGE MARKER — APP.DB
# --------------------------------------------------------------------------- #
# Simple explanation:
# Empty marker file that turns `app/db/` into a Python package so the sibling
# sub-packages (`connection`, `schema`, `queries_*`, `demo_seed`) can be
# imported. There is no code or state here on purpose — all DB logic lives in
# the sub-modules.
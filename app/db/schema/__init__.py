# --------------------------------------------------------------------------- #
# PACKAGE MARKER — APP.DB.SCHEMA
# --------------------------------------------------------------------------- #
# Simple explanation:
# Empty marker file that lets Python treat `app/db/schema/` as a package. The
# real source of truth for the database shape is `schema.sql` next to this
# file; `app.db.connection` reads it at startup with `executescript(...)` to
# create the tables on a fresh SQLite database.
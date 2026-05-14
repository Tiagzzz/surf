"""Surf P7 — local account reset helper.

The reset page requires the user to type ``DELETE`` before calling this helper.
This module performs only the scoped SQLite deletion. It does not create a
plaintext-key backup file.
"""
# --------------------------------------------------------------------------- #
# MODULE OVERVIEW — P7 LOCAL ACCOUNT RESET
# --------------------------------------------------------------------------- #
# Simple explanation:
# Wipes the user's entire local Surf account in one SQLite transaction.
# The renderer requires the user to type the exact word `DELETE` before
# this helper is called. There is no backup file — every row tied to the
# account is removed and the saved Anthropic API key is gone.
#
# Important code pieces:
# - `reset_local_account_data`: the one public function. Runs `DELETE FROM
#   users` inside `BEGIN`/`COMMIT`; on any exception we `rollback` and
#   re-raise so the renderer can show an honest failure toast.
# - Schema foreign-key cascades: removing the `users` row removes
#   classes, lectures, generated questions, attempts, and answers
#   automatically.
# - `connection` / `db_file`: injectable so tests and previews can target
#   a temporary SQLite file.
#
# App connection (privacy):
# This is the only place the locally stored API key is intentionally
# erased. After the call, the renderer also clears `st.session_state` so
# the next page load sends the user back to Sign Up.
# Deletes local account rows through the app's SQLite connection boundary.
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import app.db.connection as conn_mod

__all__ = ["reset_local_account_data"]


def reset_local_account_data(
    *,
    connection: sqlite3.Connection | None = None,
    db_file: Path | str | None = None,
) -> dict[str, Any]:
    """Delete the local Surf account graph in one transaction.

    ``connection`` and ``db_file`` are injectable so tests and previews can use
    temp SQLite files. With no explicit connection, production uses the app's
    current DB proxy. Deleting from ``users`` relies on schema FK cascades to
    remove classes, lectures, questions, attempts, and answers.
    """
    # Uses one transaction so reset either completes or rolls back.
    db = connection if connection is not None else conn_mod.DB
    target = Path(db_file) if db_file is not None else Path(conn_mod.DB_FILE)

    try:
        db.execute("BEGIN")
        db.execute("DELETE FROM users")
        deleted_users = db.execute("SELECT changes()").fetchone()[0]
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "deleted_users": deleted_users,
        "backup_created": False,
        "backup_path": None,
        "reset_target": str(target),
    }

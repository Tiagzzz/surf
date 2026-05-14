"""Surf P7 — local account reset helper.

The reset page requires the user to type ``DELETE`` before calling this helper.
This module performs only the scoped SQLite deletion. It does not create a
plaintext-key backup file.
"""
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

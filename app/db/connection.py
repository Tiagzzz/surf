"""Surf — lazy/test-safe SQLite connection + schema bootstrap.

Importing this module must not create or mutate ``~/.surf/user.sqlite``.
The default live connection is opened on first actual use through a small
lazy proxy (the ``DB`` symbol). Tests pass an explicit ``db_file`` to
``connect()`` and rebind ``DB`` on this module before importing query
helpers, so the real ~/.surf/user.sqlite stays untouched.

``rebuild_user_database_with_backup()`` is the only app-approved way to
wipe-and-rebuild the live DB. It detects an existing
``~/.surf/user.sqlite``, copies it to a timestamped backup before the
reset, returns the backup path and reset target, and never reads or
prints API key values.
"""
# Lazy DB access keeps imports safe and live-data resets backup-first.
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Resolve the live-DB path lazily through ``_default_db_file()`` so that test
# suites that monkeypatch ``Path.home`` see the temp HOME instead of the real
# one. Module-level ``DB_FILE`` is preserved as a writable attribute so the
# existing test smoke pattern (``conn.DB_FILE = tmp_path / "t.sqlite"``)
# keeps working.
_SCHEMA_PATH = Path(__file__).with_name("schema") / "schema.sql"


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return column names for ``table`` in the currently opened DB."""
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _add_column_if_missing(
    conn: sqlite3.Connection,
    *,
    table: str,
    column: str,
    ddl: str,
) -> None:
    """Apply one additive old-DB compatibility column if it is missing."""
    if column not in _table_columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def _dedupe_attempt_answer_positions(conn: sqlite3.Connection) -> None:
    """Assign stable per-attempt positions before adding the unique index.

    Legacy DBs did not have ``attempt_answers.position``. When SQLite adds a
    ``NOT NULL DEFAULT 0`` column to existing rows, every old answer in the
    same attempt receives ``0``. The unique ``(attempt_id, position)`` index
    would then fail on startup. For only the conflicting attempts, use row ID
    order as the stable legacy order and rewrite positions to ``0..n``.
    """
    # Backfill old answer rows so the position uniqueness constraint can apply.
    conflict_attempt_ids = [
        row[0]
        for row in conn.execute(
            """
            SELECT attempt_id
            FROM attempt_answers
            GROUP BY attempt_id, position
            HAVING COUNT(*) > 1
            """
        ).fetchall()
    ]
    for attempt_id in conflict_attempt_ids:
        answer_ids = [
            row[0]
            for row in conn.execute(
                "SELECT id FROM attempt_answers WHERE attempt_id = ? ORDER BY id",
                (attempt_id,),
            ).fetchall()
        ]
        for position, answer_id in enumerate(answer_ids):
            conn.execute(
                "UPDATE attempt_answers SET position = ? WHERE id = ?",
                (position, answer_id),
            )


def _backfill_existing_schema(conn: sqlite3.Connection) -> None:
    """Add columns/indexes required by newer V1 code to older local DBs.

    ``schema.sql`` uses ``CREATE TABLE IF NOT EXISTS`` for a fresh database,
    but SQLite does not update already-existing tables from that statement.
    These additive checks keep existing local DBs usable without a wipe.
    """
    # Keep older local databases compatible with the current schema shape.
    _add_column_if_missing(
        conn, table="questions", column="question_type", ddl="question_type TEXT"
    )
    for column, ddl in (
        ("difficulty_word_count", "difficulty_word_count INTEGER"),
        ("difficulty_readability", "difficulty_readability REAL"),
        ("difficulty_distractor_similarity", "difficulty_distractor_similarity REAL"),
        ("difficulty_conceptual_density", "difficulty_conceptual_density INTEGER"),
        ("difficulty_distractor_derivation", "difficulty_distractor_derivation INTEGER"),
        ("difficulty_reasoning_steps", "difficulty_reasoning_steps INTEGER"),
        ("difficulty_wording_complexity", "difficulty_wording_complexity INTEGER"),
        (
            "difficulty_wording_clarity_issue",
            "difficulty_wording_clarity_issue INTEGER NOT NULL DEFAULT 0",
        ),
        ("difficulty_score", "difficulty_score REAL"),
    ):
        _add_column_if_missing(conn, table="questions", column=column, ddl=ddl)
    _add_column_if_missing(
        conn, table="attempts", column="raw_score_pct", ddl="raw_score_pct REAL"
    )
    _add_column_if_missing(
        conn, table="attempts", column="swiss_grade", ddl="swiss_grade REAL"
    )
    _add_column_if_missing(
        conn,
        table="attempt_answers",
        column="position",
        ddl="position INTEGER NOT NULL DEFAULT 0",
    )
    _dedupe_attempt_answer_positions(conn)
    _add_column_if_missing(
        conn,
        table="attempt_answers",
        column="was_skipped",
        ddl="was_skipped INTEGER NOT NULL DEFAULT 0",
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "idx_attempt_answers_attempt_question_unique "
        "ON attempt_answers(attempt_id, question_id)"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "idx_attempt_answers_attempt_position_unique "
        "ON attempt_answers(attempt_id, position)"
    )


def _default_db_file() -> Path:
    """Return the canonical live DB path under the (possibly monkeypatched) HOME."""
    return Path.home() / ".surf" / "user.sqlite"


# Public attribute. Tests may overwrite this before query modules are
# (re)imported; otherwise it is read on each connect() call when no explicit
# db_file is passed.
DB_FILE: Path = _default_db_file()


def connect(db_file: Path | None = None) -> sqlite3.Connection:
    """Open (or create) a SQLite DB at ``db_file``, run schema, enable FK pragma.

    No default open at import time — callers (or the lazy ``DB`` proxy) must
    request it explicitly. ``db_file=None`` resolves to the module-level
    ``DB_FILE`` so test rebindings still work.
    """
    # Create the DB only on explicit use, then apply schema and safe backfills.
    target = db_file if db_file is not None else DB_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    _backfill_existing_schema(conn)
    conn.commit()
    return conn


def get_connection(db_file: Path | None = None) -> sqlite3.Connection:
    """Explicit-helper alias for ``connect()`` — preferred from non-test code."""
    return connect(db_file)


class _LazyConnection:
    """Lazy proxy around ``sqlite3.Connection``.

    Forwards attribute access (``execute``, ``commit``, …) and context-manager
    behavior to a real connection that is opened only on first use. This
    keeps ``import app.db.connection`` side-effect-free while preserving the
    existing ``from app.db.connection import DB`` import surface used by all
    ``app/db/queries_*`` helpers.

    ``close()`` is a no-op when the underlying connection has not been opened
    yet, so test teardown that calls ``conn.DB.close()`` before reassigning
    ``conn.DB`` does not accidentally trigger a default open of the live DB.
    """
    # Defer opening the default SQLite file until a caller actually uses DB.

    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None

    def _ensure(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = connect()
        return self._conn

    # Connection-like surface ------------------------------------------------
    def execute(self, *args: Any, **kwargs: Any):
        return self._ensure().execute(*args, **kwargs)

    def executemany(self, *args: Any, **kwargs: Any):
        return self._ensure().executemany(*args, **kwargs)

    def executescript(self, *args: Any, **kwargs: Any):
        return self._ensure().executescript(*args, **kwargs)

    def commit(self) -> None:
        if self._conn is not None:
            self._conn.commit()

    def rollback(self) -> None:
        if self._conn is not None:
            self._conn.rollback()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def cursor(self):
        return self._ensure().cursor()

    # Context manager behaves like sqlite3.Connection's transaction CM.
    def __enter__(self) -> sqlite3.Connection:
        return self._ensure().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn is None:
            return False
        return self._conn.__exit__(exc_type, exc_val, exc_tb)

    # Generic attribute fall-through (e.g. ``DB.row_factory``).
    def __getattr__(self, item: str):
        return getattr(self._ensure(), item)


# Module-level lazy proxy. Importing this module does NOT open any DB file.
# Tests may rebind ``DB`` to a real ``sqlite3.Connection`` from ``connect(tmp)``
# and reload the queries modules; production code uses the lazy default.
DB: Any = _LazyConnection()


def rebuild_user_database_with_backup() -> dict[str, Any]:
    """Timestamped backup → reset → fresh schema for the live DB.

    If the live DB exists, copy it to ``~/.surf/user.sqlite.<UTC-timestamp>.bak``
    before deleting it, then create a new DB and apply ``schema.sql``. If the
    live DB does not exist, simply create a fresh DB and report no-backup-
    needed.

    Returns a dict with the backup path (or ``None``) and the reset target.
    Never reads or prints API-key column values. Callers that print/log the
    result must format only ``backup_path`` and ``reset_target`` strings.
    """
    # Reset the local DB only after copying the previous file to a timestamped backup.
    target = _default_db_file()
    surf_dir = target.parent
    surf_dir.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    if target.exists():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = target.with_name(f"{target.name}.{timestamp}.bak")
        shutil.copy2(target, backup_path)
        target.unlink()

    # Open a fresh connection to apply the schema, then close so callers
    # interact with a clean state. We deliberately do not return the open
    # connection — the lazy proxy will reopen it on next use.
    fresh = connect(target)
    fresh.close()

    return {
        "backup_path": str(backup_path) if backup_path is not None else None,
        "reset_target": str(target),
        "backup_created": backup_path is not None,
    }

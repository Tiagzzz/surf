"""Q8 verification (Plan 02-01 Task 8) — `app/db/connection.py` uses
`@st.cache_resource` so the same `sqlite3.Connection` is reused across
Streamlit reruns.

Two checks:

  1. **Identity** — `connect(...)` called twice with the SAME args
     returns the same Python object (`is`, not `==`). This is the
     behaviour `@st.cache_resource` guarantees.
  2. **FK pragma on** — the connection has `PRAGMA foreign_keys = 1`
     enabled (so cascade deletes work as the schema expects).

Both checks pass under bare pytest (no `streamlit run` context) because
`@st.cache_resource` falls back to a Python-dict cache when Streamlit's
runtime is missing — it still returns the same object on repeat calls,
it just emits a warning about the missing ScriptRunContext.
"""

from __future__ import annotations

from pathlib import Path

import app.db.connection as conn_mod


def test_connect_returns_same_connection_on_repeat_call(tmp_path: Path) -> None:
    """Two calls with the same db_file → same Python object."""
    db_file = tmp_path / "identity.sqlite"
    # Clear any cache state from earlier tests in the same session so
    # this test's assertions don't depend on test ordering.
    conn_mod.connect.clear()

    a = conn_mod.connect(db_file)
    b = conn_mod.connect(db_file)
    try:
        assert a is b, (
            "@st.cache_resource is not caching connect() — got two distinct "
            "Connection objects for the same db_file"
        )
    finally:
        a.close()
        conn_mod.connect.clear()


def test_connect_enables_foreign_keys(tmp_path: Path) -> None:
    """The returned connection has the FK pragma on (= 1)."""
    db_file = tmp_path / "fk.sqlite"
    conn_mod.connect.clear()

    conn = conn_mod.connect(db_file)
    try:
        cursor = conn.execute("PRAGMA foreign_keys")
        (value,) = cursor.fetchone()
        assert value == 1, f"PRAGMA foreign_keys = {value}, expected 1"
    finally:
        conn.close()
        conn_mod.connect.clear()


def test_connect_different_db_files_are_distinct(tmp_path: Path) -> None:
    """Different `db_file` args → different cached connections (cache
    key is the args tuple, not a global singleton)."""
    db_a = tmp_path / "a.sqlite"
    db_b = tmp_path / "b.sqlite"
    conn_mod.connect.clear()

    a = conn_mod.connect(db_a)
    b = conn_mod.connect(db_b)
    try:
        assert a is not b, (
            "Two different db_file args returned the same connection — "
            "the cache key isn't including the path argument"
        )
    finally:
        a.close()
        b.close()
        conn_mod.connect.clear()

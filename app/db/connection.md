# app/db/connection.py

This file is the one place in Surf that opens the local SQLite database
file (`~/.surf/user.sqlite`). Every other part of the app — signup,
classes, lectures, mocks — gets its database access through helpers
defined here so the rest of the codebase never has to think about file
paths, schema setup, or backups. It runs the first time the app needs
to read or write data, and it also owns the safe "wipe and start over"
helper used by Settings reset.

What this file is: the one place that opens the SQLite database. It
exposes a lazy module-level `DB` proxy, the explicit `connect()` /
`get_connection()` helpers, and the backup-then-rebuild helper
`rebuild_user_database_with_backup()`.

## How to call

```python
from app.db.connection import DB

# write
with DB:
    cursor = DB.execute(
        "INSERT INTO users (username, anthropic_api_key) VALUES (?, ?)",
        ("alice", "sk-ant-..."),
    )
    user_id = cursor.lastrowid

# read multi-row
rows = DB.execute("SELECT * FROM lectures WHERE class_id = ?", (class_id,)).fetchall()
```

For tests, point at a throwaway file before importing the queries:

```python
from pathlib import Path
import app.db.connection as conn

conn.DB.close()           # no-op when not yet opened — safe even on cold import
conn.DB_FILE = tmp_path / "t.sqlite"
conn.DB = conn.connect(conn.DB_FILE)
# Then `importlib.reload(app.db.queries_*)` so they bind to the new DB.
```

Phase 7.1 schema/backfill tests use temp files or `:memory:` SQLite
connections only. They must not inspect or mutate `~/.surf/user.sqlite` just to
prove metadata columns exist.

## Backup-then-rebuild

```python
from app.db.connection import rebuild_user_database_with_backup

result = rebuild_user_database_with_backup()
print(result["backup_path"])   # str | None
print(result["reset_target"])  # absolute path of the rebuilt DB
print(result["backup_created"])
```

If `~/.surf/user.sqlite` exists, the helper copies it to
`~/.surf/user.sqlite.<UTC-timestamp>.bak` before deleting and
recreating the live DB from `schema.sql`. If it does not exist, the
helper creates a fresh DB and reports `backup_created=False`. The
helper never reads or prints API-key column values; callers that log
the result must format only the `backup_path` and `reset_target` fields.

## In / out

| Symbol | In | Out |
|---|---|---|
| `connect(db_file=None)` | optional `Path`; defaults to module-level `DB_FILE` | `sqlite3.Connection` with `PRAGMA foreign_keys=1`, `schema.sql` applied, and additive old-DB backfills applied. |
| `get_connection(db_file=None)` | as above | as above (alias for `connect`). |
| `DB` | — | A lazy `_LazyConnection` proxy. First attribute access opens the live DB; `close()` is a no-op when not yet opened. |
| `DB_FILE` | — | Module-level `Path` to the live DB; tests may rebind it. |
| `rebuild_user_database_with_backup()` | — | `dict` with `backup_path: str | None`, `reset_target: str`, `backup_created: bool`. |

## Where it fits

Layer below every `app/db/queries_*` module. They `from app.db.connection
import DB` and never open their own connection. The lazy proxy means
test files and short-lived imports do not touch `~/.surf/user.sqlite`.

## Constraints

- Import is side-effect-free (import-safety). No SQLite file is created or
  opened until production code actually calls a query helper.
- `connect()` resolves a default `db_file=None` against the module-level
  `DB_FILE` — that is the seam tests use to redirect at runtime.
- `rebuild_user_database_with_backup()` is the *only* sanctioned wipe
  path for the live DB. Anything else (e.g., manual `os.remove`) loses
  the backup and breaks backup-then-rebuild.
- `_backfill_existing_schema()` may only add missing columns or indexes.
  It must not drop, rewrite, or reset `questions` rows while adding Phase 7.1
  metadata compatibility.
- `connect()` is allowed to apply additive compatibility backfills on an
  already-opened DB, but Phase 7.1 does not automate a live DB reset. A reset is
  a separate P7/user-approved backup-first action through
  `rebuild_user_database_with_backup()`.

## Code walkthrough

```python
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
```

Stdlib only — no SQLAlchemy or other ORM (project hard constraint).
`shutil.copy2` preserves mtime so backups carry their original
timestamp metadata; `datetime.now(timezone.utc)` is the timezone-aware
replacement for the deprecated `utcnow()`.

```python
_SCHEMA_PATH = Path(__file__).with_name("schema") / "schema.sql"

def _table_columns(...)
def _add_column_if_missing(...)
def _backfill_existing_schema(...)

def _default_db_file() -> Path:
    return Path.home() / ".surf" / "user.sqlite"

DB_FILE: Path = _default_db_file()
```

`_SCHEMA_PATH` points at the canonical schema source. `_default_db_file`
resolves the live DB path through `Path.home()` so tests that
monkeypatch `Path.home` see the temp directory. `DB_FILE` is computed
once at import and remains writable as a module attribute for the
existing test rebind pattern.

`_backfill_existing_schema()` is the narrow compatibility shim for
older local databases. `schema.sql` creates the right shape for fresh
DBs, but SQLite does not change tables that already exist. The shim
therefore adds only missing columns/indexes that newer V1 code needs:
`questions.question_type`, every selected `questions.difficulty_*`
column used by Phase 7 / 7.1 scoring
(`difficulty_word_count`, `difficulty_readability`,
`difficulty_distractor_similarity`, `difficulty_conceptual_density`,
`difficulty_distractor_derivation`, `difficulty_reasoning_steps`,
`difficulty_wording_complexity`, `difficulty_wording_clarity_issue`,
and `difficulty_score`), `attempts.raw_score_pct`,
`attempts.swiss_grade`, `attempt_answers.position`,
`attempt_answers.was_skipped`, and the attempt-answer unique indexes.
Before it creates the unique `(attempt_id, position)` index, it repairs
legacy attempts whose old answer rows all received SQLite's `position=0`
default by assigning stable `0..n` positions in answer-row ID order. It
does not wipe data, does not read API keys, and does not run a broad
migration system.

The Phase 7.1 metadata backfill is intentionally additive: it makes old DBs
able to store/read nullable metadata and the clarity default, but it does not
invent metadata for existing questions, does not fill `difficulty_score`, and
does not rebuild the live file.

```python
def _dedupe_attempt_answer_positions(conn: sqlite3.Connection) -> None:
    conflict_attempt_ids = [...]
    for attempt_id in conflict_attempt_ids:
        answer_ids = [...]
        for position, answer_id in enumerate(answer_ids):
            conn.execute(...)
```

`_dedupe_attempt_answer_positions()` is deliberately narrow. It only
touches attempts where two or more rows currently share the same
`(attempt_id, position)` pair. That covers old databases where
`ALTER TABLE ... ADD COLUMN position INTEGER NOT NULL DEFAULT 0` gave
every legacy answer position `0`, while leaving already-valid modern
attempt rows alone.

```python
def connect(db_file: Path | None = None) -> sqlite3.Connection:
    target = db_file if db_file is not None else DB_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    _backfill_existing_schema(conn)
    conn.commit()
    return conn
```

`connect()` is the explicit-helper. Tests pass an explicit `db_file`
to keep the live DB untouched. `check_same_thread=False` is required so
Streamlit's request thread can use the same connection; writes must
still be wrapped in `with DB:` to serialise. The schema is applied with
`executescript` on every open — every CREATE uses `IF NOT EXISTS`, so
this is idempotent on existing DBs (wipe-and-rerun policy). The
follow-up backfill call handles the few additive columns needed by old
local DBs, including the Phase 7.1 difficulty metadata columns, so the
user's live file does not need a blind wipe.

```python
def get_connection(db_file: Path | None = None) -> sqlite3.Connection:
    return connect(db_file)
```

Alias preferred by non-test callers that want the verb-driven name.

```python
class _LazyConnection:
    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None

    def _ensure(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = connect()
        return self._conn
```

`_LazyConnection` is the heart of the test-safety contract. `_conn`
starts as `None`; the first attribute access (or context-manager entry)
calls `_ensure`, which opens the default live DB. Tests that rebind
`DB` to a real connection (`conn.DB = conn.connect(tmp)`) replace the
proxy entirely, so the lazy open is never triggered against the live
DB.

```python
    def execute(self, *args, **kwargs):
        return self._ensure().execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        return self._ensure().executemany(*args, **kwargs)

    def executescript(self, *args, **kwargs):
        return self._ensure().executescript(*args, **kwargs)

    def commit(self) -> None:
        if self._conn is not None:
            self._conn.commit()

    def rollback(self) -> None:
        if self._conn is not None:
            self._conn.rollback()
```

`execute` / `executemany` / `executescript` open the connection on
first use (queries genuinely need a DB). `commit` and `rollback` are
no-ops when the proxy hasn't been opened — there's nothing to commit or
roll back.

```python
    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
```

`close()` is the test-safety wrinkle: it never triggers a default open.
Tests do `conn.DB.close()` before reassigning `conn.DB`; with this
guard, an "uncold" cold close cannot accidentally create the live DB.

```python
    def cursor(self):
        return self._ensure().cursor()

    def __enter__(self) -> sqlite3.Connection:
        return self._ensure().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn is None:
            return False
        return self._conn.__exit__(exc_type, exc_val, exc_tb)

    def __getattr__(self, item: str):
        return getattr(self._ensure(), item)
```

`cursor()` and the context-manager protocol need a real connection so
they ensure on entry. `__getattr__` is the catch-all for less-common
sqlite3 attributes (`row_factory`, `total_changes`, …); it is only
called when a normal attribute lookup misses, so it won't shadow the
explicit methods above.

```python
DB: Any = _LazyConnection()
```

Module-level lazy proxy. All `app/db/queries_*` modules import this
symbol; their behavior is identical to the previous eager
`sqlite3.Connection` because the proxy forwards every operation. The
`Any` type hint avoids leaking a private class into call-site type
checkers.

```python
def rebuild_user_database_with_backup() -> dict[str, Any]:
    target = _default_db_file()
    surf_dir = target.parent
    surf_dir.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    if target.exists():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = target.with_name(f"{target.name}.{timestamp}.bak")
        shutil.copy2(target, backup_path)
        target.unlink()

    fresh = connect(target)
    fresh.close()

    return {
        "backup_path": str(backup_path) if backup_path is not None else None,
        "reset_target": str(target),
        "backup_created": backup_path is not None,
    }
```

The backup-then-rebuild helper. We re-resolve `target` through `_default_db_file()`
(not the cached `DB_FILE`) so a monkeypatched `Path.home` is honoured
even after import. The timestamped suffix uses UTC ISO8601-compact so
backups sort lexicographically. `shutil.copy2` then `target.unlink()`
gives us a hard guarantee that the backup exists on disk before the
original is removed; if the copy fails, the original is still intact.
The fresh `connect(target)` rebuilds the schema and we close it
immediately — the lazy `DB` proxy will reopen it on the next live use.
The returned dict carries the strings UI/CLI surfaces need; no API-key
field is ever read or returned.

## What could break if changed

- Replacing the lazy proxy with an eager `DB = connect()` resurrects
  the import-time live-DB hazard and breaks import-safety.
- Removing the `_conn is None` guard in `close()` means a cold close
  triggers a default open against the live DB.
- Reordering `shutil.copy2` and `target.unlink()` in
  `rebuild_user_database_with_backup` would risk losing the original
  before the backup is durable.
- Reading the `anthropic_api_key` column anywhere in this module
  violates import-safety.

## Verification

- `pytest tests/test_db_schema.py tests/test_session_auth.py -q`
- Static check: `grep -n 'DB: sqlite3.Connection = connect' app/db/connection.py`
  must return nothing.
- Static check: `grep -n 'rebuild_user_database_with_backup' app/db/connection.py`
  must return at least the function definition.

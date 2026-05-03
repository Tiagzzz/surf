# connection.py

What this file is: the one place that opens the SQLite database. It runs the schema, turns foreign-key checks on, and exposes a module-level `DB` you import everywhere else.

## How to call

```python
from app.db.connection import DB

# write
with DB:
    cursor = DB.execute("INSERT INTO users (username, anthropic_api_key) VALUES (?, ?)",
                        ("alice", "sk-..."))
    user_id = cursor.lastrowid

# read multi-row
import pandas as pd
df = pd.read_sql("SELECT * FROM lectures WHERE class_id = ?", DB, params=(class_id,))
```

For tests, point at a throwaway file before importing the queries:

```python
from pathlib import Path
import app.db.connection as conn

conn.DB.close()
conn.DB_FILE = tmp_path / "t.sqlite"
conn.DB = conn.connect(conn.DB_FILE)
```

## In / out

`connect(db_file: Path | None = None) -> sqlite3.Connection` — opens (or creates) the DB file, runs `schema.sql`, sets `PRAGMA foreign_keys = 1`, and returns the connection. Default file is `~/.surf/user.sqlite`. Idempotent: calling it again on an existing DB is a no-op (CREATE statements use `IF NOT EXISTS`).

`DB: sqlite3.Connection` — the module-level connection most code uses. Created at import time.

## Where it fits

Layer below every `app/db/queries_*` module. They `from app.db.connection import DB` and never open their own connection.

## Gotchas-if-real

- Importing `app.db.connection` creates `~/.surf/` if it does not exist. Tests that don't want to touch the real DB must rebind `DB_FILE` and `DB` (snippet above) **before** importing any `queries_*` module — otherwise the queries module captures the real `DB` first.
- `check_same_thread=False` is on so Streamlit's request thread can use the same connection. Wrap writes in `with DB:` so SQLite's per-connection lock serialises them.
- `connect()` is decorated with `@st.cache_resource` (Plan 02-01 Task 8). Repeat calls with the same `db_file` return the SAME connection object — every Streamlit rerun reuses one handle instead of opening a new file. To swap the DB at runtime in tests, call `connect.clear()` before rebinding so the previous cache entry is evicted.

## Code walkthrough

This script is the one place in the whole app that opens the SQLite database. It runs the schema (so a fresh user gets a working DB on first launch), turns on foreign-key checks (so cascading deletes actually cascade), and gives every other module a single shared connection to import. Here's what each piece does, top to bottom.

**Module-level constants `DB_FILE` and `_SCHEMA_PATH`** — `DB_FILE` resolves to `~/.surf/user.sqlite` (the per-user data lives in the home folder, never in the repo). `_SCHEMA_PATH` points at the sibling `schema/schema.sql` file that holds every CREATE TABLE statement. The leading underscore on `_SCHEMA_PATH` says "internal — don't import this from outside".

**`@st.cache_resource` decorator** — Streamlit's cache for "expensive things that should live for the whole session". Without it, every user click would re-run `connect()` and open a fresh SQLite file handle, throwing away the previous one. With it, the SAME `sqlite3.Connection` object is reused across every rerun. The cache key is the function arguments, so `connect()` (no args) shares one connection app-wide while tests passing `connect(tmp_path)` get their own without colliding.

**`connect(db_file=None)`** — In plain language: opens (or creates) the SQLite file at the given path (or the default `~/.surf/user.sqlite`), makes sure the parent folder exists, sets `check_same_thread=False` so Streamlit's worker threads can share the connection, turns on foreign-key enforcement, runs `schema.sql` to create any missing tables, commits, and returns the connection. Idempotent — calling it on an already-set-up DB is a no-op because every CREATE statement in `schema.sql` uses `IF NOT EXISTS`. Watch out for: if you ever need to swap the DB file at runtime (tests, debugging), call `connect.clear()` first to evict the cached connection — otherwise the next `connect(new_path)` call opens the new path correctly but the old cached connection still floats around.

**Module-level `DB = connect()`** — Runs at import time and binds the production connection to the module-level name `DB`. Every `queries_*` module imports this single name, so the whole app shares one connection. Watch out for: this line runs the moment anything imports `app.db.connection`, so test setup that wants a different DB must monkey-patch `DB_FILE` and `DB` BEFORE importing any query module — otherwise the queries module sees the real `~/.surf/user.sqlite`.

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

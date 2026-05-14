# queries_users.md

This file holds the small set of helpers Surf uses to read and write
the user account stored in the local database. Surf is a single-user
app, so there is only ever zero or one user on a machine — these
helpers create that user during sign-up, fetch them at start-up, and
let Settings replace the saved Anthropic API key. The Sign Up page
(P1), the Settings page (P7), and the auth/session check at boot all
go through this file. Helpers return plain Python dictionaries (no
pandas) so the rest of the app can use the data without any extra
library.

## How to call

```python
from app.db.queries_users import (
    insert_user,
    get_user_by_username,
    get_active_user,
    has_saved_user_with_key,
    list_users,
)

uid = insert_user("alice", "sk-ant-...")
row = get_user_by_username("alice")     # dict | None
saved = get_active_user()                # dict | None — used by session helper
ready = has_saved_user_with_key()        # bool — used by is_authenticated()
all_rows = list_users()                  # list[dict]
```

## In / out

| Function | In | Out |
|---|---|---|
| `insert_user(username, anthropic_api_key)` | two strings | `int` lastrowid |
| `get_user_by_id(user_id)` | int | `dict | None` |
| `get_user_by_username(username)` | str | `dict | None` |
| `get_active_user()` | — | `dict | None` (lowest-id row) |
| `has_saved_user_with_key()` | — | `bool` (non-blank `anthropic_api_key`) |
| `list_users()` | — | `list[dict]` (always 0 or 1 row in V1) |

## Where it fits

- Used by P1 (signup) to create the user row.
- Used by P7 (settings) to read/replace the API key.
- Used by `app/brain/session/__init__.py` via `get_active_user` and
  `has_saved_user_with_key` for the authentication gate.

## Constraints

- `username` is `UNIQUE`. A duplicate insert raises
  `sqlite3.IntegrityError`.
- The API key is stored as plaintext on disk per the project decision
  (local-only app). Do not log or print it.
- This module must not import pandas. Helpers return plain
  Python `dict`/`list[dict]` so callers can serialise them safely.
- All helpers run against the lazy `DB` proxy from
  `app.db.connection`; importing this module does not open the live DB.

## Code walkthrough

```python
from typing import Any
from app.db.connection import DB
```

`DB` is the lazy proxy — first attribute access opens the live SQLite
DB. Tests rebind `app.db.connection.DB` and reload this module so it
picks up the temp connection.

```python
def _row_to_dict(cur) -> dict | None:
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def _rows_to_dicts(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]
```

Two tiny helpers turn an open cursor into plain-Python results. They
intentionally do not depend on any third-party library — the cursor's
`description` attribute carries the column names, which is all we need.

```python
def insert_user(username: str, anthropic_api_key: str) -> int:
    with DB:
        cur = DB.execute(
            "INSERT INTO users (username, anthropic_api_key) VALUES (?, ?)",
            (username, anthropic_api_key),
        )
        return cur.lastrowid
```

`with DB:` opens a transaction; the `INSERT` is committed when the
block exits without an exception. `cur.lastrowid` returns the
auto-assigned `id`. Parameters are bound positionally to avoid SQL
injection.

```python
def get_user_by_id(user_id: int) -> dict | None:
    return _row_to_dict(DB.execute("SELECT * FROM users WHERE id = ?", (user_id,)))


def get_user_by_username(username: str) -> dict | None:
    return _row_to_dict(
        DB.execute("SELECT * FROM users WHERE username = ?", (username,))
    )
```

Single-row reads. `SELECT *` is fine here because the column set is
locked by `schema.sql` and the result is a small dict. Both helpers
return `None` cleanly on a miss.

```python
def list_users() -> list[dict[str, Any]]:
    return _rows_to_dicts(DB.execute("SELECT * FROM users ORDER BY id"))
```

`list_users` returns a `list[dict]` ordered by id. In V1 the table
holds at most one row, but the `ORDER BY id` keeps the contract stable
if a future migration needs to walk multiple rows.

```python
def get_active_user() -> dict | None:
    return _row_to_dict(DB.execute("SELECT * FROM users ORDER BY id LIMIT 1"))
```

The session helper's primary read. `LIMIT 1` keeps the query cheap and
makes the "lowest-id row wins" rule explicit. Caller must not log the
returned dict directly because it carries `anthropic_api_key`.

```python
def has_saved_user_with_key() -> bool:
    cur = DB.execute(
        "SELECT 1 FROM users "
        "WHERE anthropic_api_key IS NOT NULL "
        "AND LENGTH(TRIM(anthropic_api_key)) > 0 "
        "LIMIT 1"
    )
    return cur.fetchone() is not None
```

The auth predicate that backs `is_authenticated()`. It looks for a
saved user with a non-blank key without ever returning the key value.
`LENGTH(TRIM(...))` excludes both NULL (via the previous predicate) and
whitespace-only strings.

## What could break if changed

- Re-introducing pandas (`import pandas`, `pd.read_sql`) violates
  the pandas-free contract and breaks the contract test
  `test_queries_users_returns_dict_not_pandas`.
- Returning the raw `anthropic_api_key` from a logging-friendly
  helper would leak the key.
- Removing `LIMIT 1` from `has_saved_user_with_key` makes the query
  scan the whole table — harmless for V1 but expensive later.
- Changing `get_active_user` to return a different ordering (e.g.,
  `ORDER BY created_at DESC`) silently changes who is "the" saved user.

## Verification

- `pytest tests/test_session_auth.py -q`
- Static check: `grep -n 'import pandas\|pd.read_sql'
  app/db/queries_users/__init__.py` must return nothing.

## Phase 03-06 update — setup and key helpers

Phase 03-06 added the helpers P1 and P7 need before page code is wired:

| Function | What it does |
|---|---|
| `upsert_user_setup(username, anthropic_api_key)` | Creates the single local user row, or updates the existing lowest-id row. Re-running setup never creates a second active Surf user. |
| `get_saved_anthropic_api_key(user_id)` | Returns the saved key for exactly that user id, or `None`; it never falls back to `ANTHROPIC_API_KEY` or another row. |
| `update_display_name(user_id, display_name)` | Updates only `users.username`, which is Surf V1's display-name field. |
| `replace_anthropic_api_key(user_id, anthropic_api_key)` | Replaces only the saved key after the caller has validated the new typed key. |
| `get_local_db_path()` | Returns the local DB path for safe display/debug copy; it never includes secret values. |

### Code walkthrough for the new helpers

- `upsert_user_setup(...)` opens one transaction with `with DB:`. It first
  checks `SELECT id FROM users ORDER BY id LIMIT 1`. No row means insert;
  an existing row means update that same id.
- `get_saved_anthropic_api_key(...)` is intentionally user-id scoped. This
  prevents P2/P7 from accidentally using the environment key or another user's
  saved key.
- `update_display_name(...)` and `replace_anthropic_api_key(...)` are narrow
  `UPDATE ... WHERE id = ?` helpers. Each returns `True` only when a row was
  actually changed.
- `get_local_db_path()` reads `app.db.connection.DB_FILE`, not table contents,
  so it cannot leak the plaintext API key.

Verification added in Phase 03-06:

```bash
pytest tests/test_settings_account.py tests/test_no_real_db.py tests/test_no_secrets_committed.py -q
ruff check app/db/queries_users tests/test_settings_account.py
```

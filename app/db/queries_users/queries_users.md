# queries_users.md

What this file is: read/write helpers for the `users` table. There is only ever 0 or 1 user in this app, so the API is small.

## How to call

```python
from app.db.queries_users import insert_user, get_user_by_username

uid = insert_user("alice", "sk-ant-...")
row = get_user_by_username("alice")   # -> dict | None
```

## In / out

| Function | In | Out |
|----------|----|-----|
| `insert_user(username, anthropic_api_key)` | two strings | `int` lastrowid |
| `get_user_by_id(user_id)` | int | dict or `None` |
| `get_user_by_username(username)` | str | dict or `None` |
| `list_users()` | — | DataFrame (always 0 or 1 row) |

## Where it fits

Used by P1 (signup) to create the user row and by P7 (settings) to read/update the API key.

## Gotchas-if-real

- `username` is `UNIQUE`. A duplicate insert raises `sqlite3.IntegrityError`.
- The API key is stored as plaintext on disk per the project decision (local-only app). Do not log it.

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

## Code walkthrough

This script is the read/write helpers for the `users` table — the row that holds "who is using this app" plus their Anthropic API key. Single-user app, so the table is always 0 or 1 row. Here's what each function does, top to bottom.

**`insert_user(username, anthropic_api_key)`** — In plain language: writes a new row into the `users` table with the given username and key, then hands back the new row's auto-assigned `id` number. The `with DB:` line wraps the write in a transaction so a crash mid-write doesn't leave the table half-broken. Watch out for: usernames must be unique; trying to insert a second row with the same username raises a database error you have to handle.

**`_row_to_dict(cur)`** — Internal helper (the leading underscore says "not for outside callers"). Takes a database cursor that just ran a SELECT, pulls the one row it returned, and converts it from a tuple-of-values into a dict-of-named-fields like `{"id": 1, "username": "alice", ...}`. Returns `None` if the SELECT found nothing. Reused by `get_user_by_id` and `get_user_by_username` so the same shape comes back from both.

**`get_user_by_id(user_id)`** — In plain language: looks up a user row by its primary-key number. Returns the row as a dict, or `None` if no user has that id.

**`get_user_by_username(username)`** — In plain language: same as above but looks up by username instead of id. Used during sign-in / sign-up to check whether someone has already claimed a name.

**`list_users()`** — In plain language: returns ALL users as a pandas DataFrame, ordered by id. In this app it's always either an empty frame or a single-row frame. Useful for the Settings page if it ever needs to display the user record.

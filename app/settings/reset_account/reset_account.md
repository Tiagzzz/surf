# reset_account — scoped local reset helper

This helper is used by P7 Settings after the user types the exact `DELETE`
confirmation. It deletes the local Surf account graph from SQLite in one
transaction. It intentionally does **not** call `rebuild_user_database_with_backup()`
because a backup could preserve the plaintext Anthropic key. P7 reset
currently deletes local account data instead of exporting it.

## How to call

```python
from app.settings.reset_account import reset_local_account_data

result = reset_local_account_data()
# or in tests/previews:
result = reset_local_account_data(connection=temp_conn, db_file=temp_path)
```

## Inputs / outputs

| Function | Inputs | Output |
|---|---|---|
| `reset_local_account_data(connection=None, db_file=None)` | optional injected SQLite connection/path | dict with `deleted_users`, `backup_created: False`, `backup_path: None`, and `reset_target` |

## Code walkthrough

- The module imports `sqlite3`, `Path`, and `app.db.connection` only. It does
  not import Streamlit and does not know about page buttons or session state.
- `reset_local_account_data(...)` picks the injected connection when provided;
  otherwise it uses the app DB proxy. This keeps tests on temp SQLite and gives
  P7 one production helper.
- The helper starts an explicit `BEGIN`, runs `DELETE FROM users`, reads
  `SELECT changes()` for a small status object, then commits.
- If anything fails after the delete starts, it rolls back and re-raises. Tests
  prove user/class rows survive a forced mid-transaction failure.
- Deleting from `users` relies on the schema's `ON DELETE CASCADE` links to
  remove classes, lectures, pages, questions, attempts, and answers.
- The returned `backup_created: False` / `backup_path: None` fields are a
  deliberate privacy signal: P7 reset deletes the plaintext API key instead of
  copying it into a `.bak` file.

## What could break if changed

- Calling `rebuild_user_database_with_backup()` here would create a backup that
  can contain the plaintext API key; do not do that for P7 reset.
- Removing the explicit transaction could leave partial local data after a
  failure.
- Running tests without injecting a temp DB would risk the live local
  `~/.surf/user.sqlite`; `tests/test_no_real_db.py` guards this.

## Verification

```bash
pytest tests/test_settings_reset.py tests/test_no_real_db.py -q
ruff check app/settings/reset_account tests/test_settings_reset.py
```

# `app/settings/backup_export/` — reserved backup/export placeholder

This folder currently contains an empty `__init__.py` only. It is preserved as a named seam for a possible future backup/export feature, but P7 Settings does **not** use it today.

## Purpose

- Keep a clear place for a future, deliberately designed export flow.
- Make the absence of a P7 reset backup explicit.
- Prevent accidental use of a plaintext-key backup during reset.

## Inputs / outputs

There are no public functions, no inputs, and no outputs in this folder today.

## Data flow

```text
P7 reset flow
    └── app.settings.reset_account.reset_local_account_data(...)
            └── deletes local account graph in SQLite

backup_export/
    └── no current call path
```

## Connected code and tools

- `app.settings.reset_account.reset_local_account_data` is the real reset helper.
- `tests/test_settings_reset.py` verifies reset behavior with temporary SQLite fixtures.
- `tests/test_no_real_db.py` protects the live local DB from tests.

## Code walkthrough

### `__init__.py`

The file is intentionally empty. It creates an importable package name without exporting any backup function. That is safer than leaving future teammates to guess whether reset currently creates a backup.

## Testing notes

```bash
python -m pytest -q tests/test_settings_reset.py tests/test_no_real_db.py
ruff check app/settings/backup_export --no-cache
```

## What could break if changed

- Adding a backup helper that copies the local SQLite file could preserve a plaintext Anthropic key.
- Wiring this folder into P7 reset would contradict the current local-reset privacy contract.
- Adding file-writing behavior here would need new no-secret and no-real-DB tests before use.

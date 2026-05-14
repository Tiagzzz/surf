---
title: "claude_client.py — Surf shared Claude API wrapper"
tags:
  - surf/script
  - surf/brain
status: docs
bucket: app/brain/claude_client
---

# `app/brain/claude_client/claude_client.py`

One shared wrapper around the Anthropic Claude API. Every Surf generation or
key-validation path that needs Anthropic goes through this bucket so API keys,
prompt caching, text extraction, and JSON parsing stay in one place.

## Purpose

- `call_claude(...)` sends one Anthropic Messages request for Surf generation
  flows such as factsheet cleaning, learning-objective extraction, and MCQ
  generation.
- `validate_anthropic_key(...)` checks a newly typed key before Signup or
  Settings saves it locally.
- Callers pass the saved local key with `api_key=saved_key` for one call only;
  the wrapper never logs or returns the key value.

## Inputs / outputs

| Function | Inputs | Output |
|---|---|---|
| `call_claude(system_prompt, user_message, model=..., max_tokens=..., expect_json=False, cache_system=True, api_key=None)` | Prompt text, user-message text, optional model/token/cache settings, optional saved local API key | Plain response text, or parsed `dict` when `expect_json=True` |
| `validate_anthropic_key(api_key)` | Newly typed Anthropic key | `True` when Anthropic accepts it, otherwise `False` |

`call_claude(..., expect_json=True)` strips a surrounding Markdown code fence
before calling `json.loads(...)`. Invalid JSON still raises a JSON error so the
caller can show an honest generation failure.

## Data flow

```text
caller prompt file + Surf input text
        │
        ▼
call_claude(..., api_key=saved_key)
        │
        ├── builds the Anthropic system block
        ├── adds prompt caching when cache_system=True
        ├── sends one Messages API request
        ├── extracts the first text response block
        └── optionally parses JSON after code-fence cleanup
```

The default environment-key client remains for legacy/default scripts. App
flows that have a saved user row should pass the key explicitly for that one
call, which avoids changing global process state.

## Connected code and tools

- `app/my_classes/factsheet_clean/factsheet_cleaner.py` cleans class
  factsheets before class setup.
- `app/class_/lo_extract/lo_extractor.py` extracts learning objectives from
  lecture Markdown.
- `app/class_/mcq_generate/mcq_generator.py` generates MCQs with
  `question_type` metadata.
- P1 Signup and P7 Settings call `validate_anthropic_key(...)` before saving a
  typed key.
- External tool: `anthropic.Anthropic` SDK only. There is no provider
  abstraction and no alternate model client in Surf V1.

## No-secret boundaries

- Do not print, log, commit, or copy any real Anthropic key.
- `validate_anthropic_key(...)` uses only the string passed by the caller; it
  does not read the environment key and does not read the saved SQLite key.
- Blank keys fail locally before a validation client is created.
- Failed Settings replacement keeps the previous saved key because validation
  happens before persistence.

## Code walkthrough

### Module docstring and imports

The docstring states the single-wrapper contract. Imports are limited to JSON,
regular expressions, environment loading, typing, and the Anthropic SDK.
`load_dotenv()` keeps local development compatible with a gitignored `.env`.

### Defaults and JSON-fence regexes

`DEFAULT_MODEL` and `DEFAULT_MAX_TOKENS` centralize the wrapper defaults. The
compiled fence regexes remove common ```json fences before JSON parsing; they
are intentionally narrow so normal text responses are not changed.

### Module-level client

`_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))` creates
one client for default/environment-key calls. An empty fallback lets imports and
static tests run without a key; a missing key only matters if a real API call is
attempted.

### `call_claude(...)`

The function builds either a cached system block or a plain string system
prompt, chooses a temporary per-call client when `api_key` is provided, sends
one Messages request, and extracts the first text block from the response.
When `expect_json=False`, the text is returned unchanged. When
`expect_json=True`, code fences are stripped and the remaining text is parsed as
JSON.

### `validate_anthropic_key(...)`

The helper rejects blanks, creates a client from the typed string, and calls
`client.models.list(limit=1)`. Any exception returns `False`. The helper does
not read saved state or mutate stored keys.

## Testing notes

```bash
python -m pytest -q tests/test_claude_contract.py tests/test_no_secrets_committed.py
ruff check app/brain/claude_client --no-cache
```

The contract tests use a fake Anthropic client and require no real key.

## What could break if changed

- Direct Anthropic calls outside this wrapper can bypass prompt caching and
  saved-key safeguards.
- Logging a request, client, or saved user dict can expose the plaintext local
  key.
- Changing the JSON cleanup can break factsheet, LO, or MCQ callers that ask
  for parsed JSON.
- Changing validation to read the old saved key would make failed replacement
  flows unsafe because Settings must validate only the newly typed key.

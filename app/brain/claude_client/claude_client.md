---
title: "claude_client.py — Surf shared Claude API wrapper"
tags:
  - surf/script
  - surf/brain
status: docs
bucket: app/brain/claude_client
---

# `claude_client.py`

> Wikilinks: used by [[factsheet_cleaner]]. Will be reused by future `slo_extractor` and `mcq_generator` scripts.

## What it does

A single shared wrapper around the Anthropic Claude API. **Every Claude-backed script in Surf calls this one function.** Specialist scripts only need to bring their own system prompt + user message; this module handles the SDK setup, prompt caching, response parsing, and JSON-fence cleanup.

**Analogy**: think of it like a shared coffee machine in an office. Every team brings their own cup and beans (the prompt), but nobody re-installs the machine each time.

## How to call it

```python
from app.brain.claude_client import call_claude

# Plain-text response
reply = call_claude(
    system_prompt="You are a helpful assistant.",
    user_message="Hi!",
)

# JSON response (parsed into a dict)
data = call_claude(
    system_prompt=open("my_prompt.md").read(),
    user_message="Some input",
    expect_json=True,
)
```

## Dependencies

- **Python ≥ 3.10** (uses `str | dict[str, Any]` union syntax)
- **`anthropic`** SDK — install via `pip install anthropic`
- **`ANTHROPIC_API_KEY`** environment variable (see TODO below)

No other Surf scripts are imported.

## Inputs

| Argument | Type | Required | Default | Purpose |
|---|---|---|---|---|
| `system_prompt` | `str` | yes | — | Full text of the system prompt |
| `user_message` | `str` | yes | — | The user-turn content |
| `model` | `str` | no | `"claude-sonnet-4-6"` | Anthropic model id |
| `max_tokens` | `int` | no | `8192` | Response budget |
| `expect_json` | `bool` | no | `False` | Parse response as JSON when `True` |
| `cache_system` | `bool` | no | `True` | Enable prompt caching on the system block |

## Outputs

- Plain `str` when `expect_json=False` (default)
- Parsed `dict[str, Any]` when `expect_json=True` — raises `json.JSONDecodeError` if Claude's output isn't valid JSON

## Still to do

- [ ] **API-key sourcing**: currently reads from `ANTHROPIC_API_KEY` env var. Surf's locked architecture (Idea v0 §19) is to store the key per-user in `~/.surf/user.sqlite` after the Sign Up flow (P1) collects it. Replace the env-var lookup with a small helper that fetches from SQLite once Sign Up is built.
- [ ] **Error handling**: no retries on transient API errors yet. Add exponential backoff for 429 / 529 once we see real usage patterns.
- [ ] **Token-usage logging**: response object includes `usage` (input/output/cache hit token counts). Not currently captured. Worth wiring into a simple per-call log when the app is built so we can verify the prompt-caching savings empirically.
- [ ] **Type hints for `system_block`**: currently `Any` because the Anthropic SDK's `system=` parameter accepts both `str` and `list[dict]`. Could narrow with a `TypedDict` once the SDK exposes one.

---

## Code, section by section

### Imports and constants

```python
from __future__ import annotations

import json
import os
import re
from typing import Any

from anthropic import Anthropic
from anthropic.types import TextBlockParam

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 8192

# Code-fence stripping for JSON responses: tolerant to `json` / `JSON` /
# leading-space / trailing-whitespace variants Claude occasionally emits.
_FENCE_OPEN = re.compile(r"^```(?:json)?\s*", re.IGNORECASE)
_FENCE_CLOSE = re.compile(r"\s*```$")
```

Standard library + the `anthropic` SDK. `DEFAULT_MODEL` is set to **Sonnet 4.6** because it's the right balance of quality and cost for Surf's high-volume MCQ generation. Specialist scripts can override per call.

`TextBlockParam` is the SDK's typed-dict for system content blocks — used in the type annotation below to let type-checkers catch shape mistakes. The two compiled regexes are pre-built once at import time so the JSON path doesn't recompile them on every call.

### Module-level client

```python
_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
```

The Anthropic SDK is created **once** when the module is imported. Subsequent `call_claude()` invocations reuse it — no reconnection cost. The leading underscore signals "private to this module"; callers shouldn't poke `_client` directly.

The empty string fallback (`""`) means import never crashes if the env var isn't set; the failure surfaces only when you actually try to make a call. This matters when other scripts import this module at startup (e.g. for type checks).

### The `call_claude` function

```python
def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    expect_json: bool = False,
    cache_system: bool = True,
) -> str | dict[str, Any]:
```

One function, one job: send a single message to Claude. The signature is short on purpose — every Surf script can call this with at most 3 arguments (system, user, optionally `expect_json=True`).

### Building the system block (with optional caching)

```python
    system_block: str | list[TextBlockParam]
    if cache_system:
        system_block = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]
    else:
        system_block = system_prompt
```

When `cache_system=True` (the default), the system prompt is wrapped in Anthropic's content-block format with a `cache_control` marker. **What this does**: Anthropic stores the encoded system prompt in their cache layer for ~5 minutes; the next call with the same prompt only pays ~10% of the input token cost.

**Why it matters for Surf**: the factsheet-cleaner system prompt is ~5,500 chars. Without caching, every cleaning pays full price. With caching, only the first call in any 5-min window pays full price — a 5–10× cost reduction across the estimated ~4,000 Claude calls/semester.

When `cache_system=False`, the system prompt is sent as a plain string (no caching). Useful for one-off calls where caching overhead isn't worth it.

The `system_block: str | list[TextBlockParam]` annotation lets type-checkers (mypy, pyright) catch shape mistakes in the cache-control block. `TextBlockParam` is the SDK's official typed-dict for these blocks.

### Making the API call

```python
    response = _client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_block,
        messages=[{"role": "user", "content": user_message}],
    )
```

Standard Anthropic Messages API call. Surf only sends a single user turn (no multi-turn conversations in any current pipeline), so the `messages` list always has exactly one item.

### Finding the first text block (defensive)

```python
    text = next(
        (b.text for b in response.content if getattr(b, "type", "") == "text"),
        None,
    )
    if text is None:
        block_types = [getattr(b, "type", "?") for b in response.content]
        raise TypeError(
            f"Claude response contained no text blocks (got types: {block_types})"
        )
```

Today every Surf call returns a single text block, so `response.content[0].text` would work. **But**: when Surf later enables tool use or extended-thinking modes, the first block could be a `tool_use` or `thinking` block. This `next(...)` walks the content list and returns the first text block it finds — and raises a clear `TypeError` if none exist.

### Returning text (default path)

```python
    if not expect_json:
        return text
```

The most common case — the caller wants the raw string back.

### JSON parsing path with code-fence cleanup

```python
    cleaned = _FENCE_CLOSE.sub("", _FENCE_OPEN.sub("", text.strip())).strip()
    return json.loads(cleaned)
```

When `expect_json=True`, parse the response. The two compiled regexes at module top defensively strip a surrounding code fence — tolerant to ```` ```json ````, ```` ```JSON ````, ```` ``` json ````, leading/trailing whitespace, etc. (Claude occasionally wraps JSON despite being told "JSON only", more often with smaller/older models.) The well-behaved case (no fence) is a fast no-op since the regexes simply don't match.

`json.loads` raises `json.JSONDecodeError` on malformed output — the caller is responsible for handling that (typically by retrying or surfacing the error to the user).

---

## Full code

```python
"""Surf — shared Claude API wrapper.

Single entry point for every Claude API call in the Surf app. Specialist
scripts (factsheet cleaner, future SLO extractor, future MCQ generator)
load their system prompt from a sibling .md file and call call_claude(...).

Prompt caching is enabled by default on the system block, so the same
system prompt only pays full input price once per 5-minute window.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from anthropic import Anthropic
from anthropic.types import TextBlockParam

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 8192

# Code-fence stripping for JSON responses: tolerant to `json` / `JSON` /
# leading-space / trailing-whitespace variants Claude occasionally emits.
_FENCE_OPEN = re.compile(r"^```(?:json)?\s*", re.IGNORECASE)
_FENCE_CLOSE = re.compile(r"\s*```$")

# Module-level client. Reads the API key from the ANTHROPIC_API_KEY env var.
# TODO: replace env-var lookup with a per-user fetch from ~/.surf/user.sqlite
# once the Sign Up + Settings pages are built (Idea v0 §19).
_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    expect_json: bool = False,
    cache_system: bool = True,
) -> str | dict[str, Any]:
    """Single Claude Messages API call.

    Args:
        system_prompt: full text of the system prompt (usually loaded from a
            sibling .md file in the calling script's bucket folder).
        user_message: the user-turn content (e.g. raw factsheet markdown,
            a slide deck, a question prompt).
        model: Anthropic model id. Defaults to claude-sonnet-4-6.
        max_tokens: response token budget.
        expect_json: when True, parses the response as JSON and returns a
            dict. Strips a surrounding ```json fence if present.
        cache_system: when True (default), wraps the system prompt in a
            cache_control block so subsequent calls within ~5 minutes reuse
            the cached prefix and only pay ~10% of full input token cost.

    Returns:
        Plain string by default, or a parsed dict when expect_json=True.
    """
    system_block: str | list[TextBlockParam]
    if cache_system:
        system_block = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]
    else:
        system_block = system_prompt

    response = _client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_block,
        messages=[{"role": "user", "content": user_message}],
    )

    # Defensive: current calls only ever return text blocks, but tool-use
    # or extended-thinking modes could prepend other block types in the future.
    text = next(
        (b.text for b in response.content if getattr(b, "type", "") == "text"),
        None,
    )
    if text is None:
        block_types = [getattr(b, "type", "?") for b in response.content]
        raise TypeError(
            f"Claude response contained no text blocks (got types: {block_types})"
        )

    if not expect_json:
        return text

    cleaned = _FENCE_CLOSE.sub("", _FENCE_OPEN.sub("", text.strip())).strip()
    return json.loads(cleaned)
```

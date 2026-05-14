"""Surf — shared Claude API wrapper.

Single entry point for every Claude API call in the Surf app. Specialist
scripts (factsheet cleaner, future SLO extractor, future MCQ generator)
load their system prompt from a sibling .md file and call call_claude(...).

Prompt caching is enabled by default on the system block, so the same
system prompt only pays full input price once per 5-minute window.
"""
# Shared Claude call wrapper with prompt caching and optional JSON parsing.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This script is the single doorway every Surf module uses to talk to the
# Anthropic Claude API. It depends on three external libraries (the
# Anthropic SDK, the `dotenv` helper that loads a local `.env` file, and
# the standard library `json`/`os`/`re` modules) and nothing from `app/`.
#
# Important code pieces:
# - `from __future__ import annotations`: lazy type hints, lets the file
#   reference types like `dict[str, Any]` cleanly on Python 3.11.
# - `Anthropic`: the official Python client class for the Claude API.
# - `TextBlockParam`: the typed shape of one cache-aware text block sent
#   in the `system` field.
# - `load_dotenv`: reads variables from a local `.env` file (which is
#   gitignored) into `os.environ` so `ANTHROPIC_API_KEY` is available.
import json
import os
import re
from typing import Any

from anthropic import Anthropic
from anthropic.types import TextBlockParam
from dotenv import load_dotenv

load_dotenv()  # picks up ANTHROPIC_API_KEY from a local .env (gitignored).

# --------------------------------------------------------------------------- #
# MODULE CONSTANTS AND THE PROCESS-LEVEL CLIENT
# --------------------------------------------------------------------------- #
# Simple explanation:
# Defaults shared by every Claude call: which model to use, how many tokens
# the response is allowed to take, and two small regular expressions that
# clean up `\`\`\`json` code fences Claude sometimes wraps around JSON.
# A single module-level `Anthropic` client is built once from the env-var
# key so that the common path does not rebuild the HTTP client per call.
#
# Important code pieces:
# - `DEFAULT_MODEL`: which Claude variant is used unless the caller passes
#   `model="..."`.
# - `DEFAULT_MAX_TOKENS`: the response token budget (a token is roughly
#   half a word).
# - `_FENCE_OPEN` / `_FENCE_CLOSE`: compiled regular expressions matching
#   the opening and closing triple-backtick fences. `re.IGNORECASE` lets
#   them match both `json` and `JSON`.
# - `_client`: a single shared `Anthropic` instance for the default
#   environment-key flow. Per-user saved keys instead get a fresh client
#   inside `call_claude` to avoid leaking the saved key into module state.
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 8192

# Code-fence stripping for JSON responses: tolerant to `json` / `JSON` /
# leading-space / trailing-whitespace variants Claude occasionally emits.
_FENCE_OPEN = re.compile(r"^```(?:json)?\s*", re.IGNORECASE)
_FENCE_CLOSE = re.compile(r"\s*```$")

# Module-level client for legacy/default calls. Saved-key flows pass a
# per-call key into call_claude(...) instead of mutating process state.
_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    expect_json: bool = False,
    cache_system: bool = True,
    api_key: str | None = None,
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
        api_key: optional per-call Anthropic key from the saved local user row.
            When provided, this call uses a temporary client for this key only.
            When omitted, existing environment-key behavior is preserved.

    Returns:
        Plain string by default, or a parsed dict when expect_json=True.
    """
    # --------------------------------------------------------------------- #
    # CALL_CLAUDE — BUILD ONE MESSAGES REQUEST AND NORMALIZE THE RESPONSE
    # --------------------------------------------------------------------- #
    # Simple explanation:
    # `call_claude` is the only place in Surf that calls Anthropic. It
    # wraps the system prompt in a cache-aware block (when caching is
    # on), sends the user message, and returns either a plain string or
    # a parsed JSON dict depending on `expect_json`.
    #
    # Important code pieces:
    # - `system_prompt: str`, `user_message: str`: the two pieces of text
    #   sent to Claude. The system prompt comes from a sibling `.md`
    #   file inside each specialist script's folder.
    # - `expect_json: bool`: when True, the response text is parsed as
    #   JSON after stripping any surrounding triple-backtick fence.
    # - `cache_system: bool`: when True the system block is tagged with
    #   `cache_control: ephemeral`, which lets Anthropic reuse a cached
    #   version of the long system prompt across calls in ~5 minutes.
    # - `api_key: str | None`: when set, a temporary `Anthropic` client
    #   is created for just this call. Used by the saved-per-user-key
    #   flow so the caller's key never leaks into module-level state.
    # - `next((b.text for b in ... if type == "text"), None)`: scans the
    #   response content blocks and returns the first text block's text,
    #   or `None` when no text block is present (defensive — current
    #   calls always return text, but tool-use mode could change that).
    # - `_FENCE_OPEN.sub(...)` / `_FENCE_CLOSE.sub(...)`: strip the
    #   ```json fences Claude occasionally wraps around JSON output.
    #
    # App connection:
    # Every Surf script that talks to Claude (factsheet cleaner, LO
    # extractor, MCQ generator, difficulty metadata critic) goes through
    # this function so prompt caching and the per-user-key contract stay
    # consistent.
    # Build one Messages API request and normalize the response shape.
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

    client = Anthropic(api_key=api_key) if api_key is not None else _client

    response = client.messages.create(
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


def validate_anthropic_key(api_key: str) -> bool:
    """Return True when Anthropic accepts the typed key.

    This function is intentionally scoped to the key passed by the caller. It
    never reads ``ANTHROPIC_API_KEY`` and never looks up the saved SQLite key,
    so P1/P7 can validate a newly typed replacement before deciding whether to
    store it.
    """
    # --------------------------------------------------------------------- #
    # VALIDATE_ANTHROPIC_KEY — CHEAP "IS THIS KEY GOOD?" CHECK
    # --------------------------------------------------------------------- #
    # Simple explanation:
    # Used by P1 signup and P7 settings before saving a typed key. It only
    # tests the key the caller passes in — it never reads the env var or
    # the SQLite-saved key, so a bad new key cannot overwrite a working
    # saved one.
    #
    # Important code pieces:
    # - `client.models.list(limit=1)`: the cheapest authenticated endpoint;
    #   if Anthropic accepts the key the call succeeds.
    # - `try` / `except Exception`: any error (network, 401, etc.) is
    #   treated as "invalid key" so callers can show a simple message.
    # Validate only the caller-provided key; never fall back to saved secrets.
    if not api_key.strip():
        return False

    client = Anthropic(api_key=api_key)
    try:
        client.models.list(limit=1)
    except Exception:
        return False
    return True

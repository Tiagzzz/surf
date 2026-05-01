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
from dotenv import load_dotenv

load_dotenv()  # picks up ANTHROPIC_API_KEY from a local .env (gitignored).

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

"""Surf — factsheet cleaner.

Sends a raw factsheet markdown (the output of pdf_to_md_v3.py) to Claude
with the cleaner system prompt, and returns strict cleaned JSON ready to
be saved to the database and rendered for the student.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.brain.claude_client import call_claude

# The prompt stays beside the Python caller so prompt changes do not touch wiring.
_SYSTEM_PROMPT_PATH = Path(__file__).with_name("factsheet_cleaner_system_prompt.md")


# Public cleaner used by the class-creation service after PDF extraction.
def clean_factsheet(raw_md: str, *, api_key: str) -> dict[str, Any]:
    """Clean a raw factsheet markdown into strict JSON via Claude.

    Args:
        raw_md: the markdown produced by pdf_to_md_v3.py from the user's
            uploaded factsheet PDF.
        api_key: the Anthropic API key saved for the active local user.

    Returns:
        Parsed JSON dict matching the schema defined in
        factsheet_cleaner_system_prompt.md.
    """
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("saved Anthropic API key is required for factsheet cleaning")

    system_prompt = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return call_claude(
        system_prompt=system_prompt,
        user_message=raw_md,
        expect_json=True,
        api_key=api_key,
    )

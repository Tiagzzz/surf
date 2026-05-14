"""Surf MCQ generator.

Calls Claude once for a batch of up to 10 slides and returns generated
question data. The wrapper does not loop, retry, or chunk; those concerns
live in the lecture-ingestion orchestrator.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.brain.claude_client import call_claude

_SYSTEM_PROMPT_PATH = Path(__file__).with_name("mcq_generator_system_prompt.md")
MAX_BATCH_SIZE = 10  # Keep batches small for prompt size and latency.


def generate_mcqs(
    slides_batch: list[dict[str, Any]], *, api_key: str | None = None
) -> dict[str, Any]:
    """Generate MCQs for a batch of slides.

    Args:
        slides_batch: list of ``{"page_number": int, "raw_md": str}`` records,
            length 1..MAX_BATCH_SIZE.

    Returns:
        dict with key ``by_slide`` — see system prompt for full schema.

    Raises:
        ValueError: when batch size is 0 or > MAX_BATCH_SIZE.
    """
    if not slides_batch:
        raise ValueError("slides_batch must contain at least 1 slide")
    if len(slides_batch) > MAX_BATCH_SIZE:
        raise ValueError(
            f"slides_batch must have at most {MAX_BATCH_SIZE} slides; "
            f"got {len(slides_batch)}"
        )
    user_message = json.dumps({"slides": slides_batch}, ensure_ascii=False)
    return call_claude(
        system_prompt=_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
        user_message=user_message,
        expect_json=True,
        api_key=api_key,
    )

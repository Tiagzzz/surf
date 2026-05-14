"""Surf — Learning-Objective extractor.

Calls Claude once per lecture with the full lecture markdown and a
7-key subset of the cleaned factsheet, returning learning objectives
(title + inclusive page range) and an ignored-page list with reasons.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.brain.claude_client import call_claude

_SYSTEM_PROMPT_PATH = Path(__file__).with_name("lo_extractor_system_prompt.md")


def extract_los(lecture_md: str, factsheet_subset: dict[str, Any]) -> dict[str, Any]:
    """Extract learning objectives and ignored pages from a lecture.

    Args:
        lecture_md: full markdown produced by pdf_to_md_v3.py (with
            ``--- PAGE N ---`` markers between slides).
        factsheet_subset: the 7-key factsheet subset curated by the orchestrator.
            Passing the full factsheet works but burns extra input tokens.

    Returns:
        dict with keys ``learning_objectives``, ``ignored_pages``, ``language``.
    """
    user_message = json.dumps(
        {"lecture_md": lecture_md, "factsheet_subset": factsheet_subset},
        ensure_ascii=False,
    )
    return call_claude(
        system_prompt=_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
        user_message=user_message,
        expect_json=True,
    )

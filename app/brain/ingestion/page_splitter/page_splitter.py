"""Surf — split lecture markdown on `--- PAGE N ---` markers and batch slides."""
from __future__ import annotations

import re

# D-4.1 (locked).
_PAGE_MARKER = re.compile(r"^---\s+PAGE\s+(\d+)\s+---\s*$", re.MULTILINE)

# D-4.3 (locked): max 10 slides per MCQ-generator call.
DEFAULT_BATCH_SIZE = 10


def split_lecture_md(md: str) -> list[dict]:
    """Split lecture markdown into per-slide records keyed by page number.

    Returns: [{"page_number": int, "raw_md": str}, ...].
    Drops any preamble before the first `--- PAGE 1 ---` marker.
    """
    if not md:
        return []
    matches = list(_PAGE_MARKER.finditer(md))
    if not matches:
        return []
    slides: list[dict] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        slides.append({
            "page_number": int(m.group(1)),
            "raw_md": md[start:end].strip(),
        })
    return slides


def batch_slides(slides: list[dict], size: int = DEFAULT_BATCH_SIZE) -> list[list[dict]]:
    """Group slides into max-`size` batches (D-4.3)."""
    if size < 1:
        raise ValueError("batch size must be >= 1")
    return [slides[i : i + size] for i in range(0, len(slides), size)]

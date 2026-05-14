"""Surf — split lecture markdown on `--- PAGE N ---` markers and batch slides."""
# Lecture ingestion utilities for page-aware slide batching.
from __future__ import annotations

import re

# Page markers come from the PDF-to-Markdown extractor and preserve source-page context.
_PAGE_MARKER = re.compile(r"^---\s+PAGE\s+(\d+)\s+---\s*$", re.MULTILINE)

# Keep generation batches small enough for one MCQ-generator request.
DEFAULT_BATCH_SIZE = 10


def split_lecture_md(md: str) -> list[dict]:
    """Split lecture markdown into per-slide records keyed by page number.

    Returns: [{"page_number": int, "raw_md": str}, ...].
    Drops any preamble before the first `--- PAGE 1 ---` marker.
    """
    # Keep only marked pages so downstream generation retains slide numbers.
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
    """Group slides into max-`size` batches for MCQ generation."""
    if size < 1:
        raise ValueError("batch size must be >= 1")
    return [slides[i : i + size] for i in range(0, len(slides), size)]

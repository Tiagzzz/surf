"""Surf — split lecture markdown on `--- PAGE N ---` markers and batch slides."""
# Lecture ingestion utilities for page-aware slide batching.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS AND MODULE CONSTANTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This file only needs Python's built-in `re` (regular expression) module.
# Two constants describe what a slide separator looks like and how big a
# batch of slides should be when we hand them to the MCQ generator.
#
# Important code pieces:
# - `_PAGE_MARKER`: a compiled regex matching lines like `--- PAGE 12 ---`.
#   These markers are inserted by the PDF-to-Markdown extractor so we know
#   exactly where one slide ends and the next begins.
# - `re.MULTILINE`: tells the regex engine that `^` and `$` match at every
#   line's start/end, not only at the very beginning/end of the input.
# - `DEFAULT_BATCH_SIZE = 10`: small enough that one MCQ-generator call to
#   Claude stays fast and stays under prompt-size limits.
import re

# Page markers come from the PDF-to-Markdown extractor and preserve source-page context.
_PAGE_MARKER = re.compile(r"^---\s+PAGE\s+(\d+)\s+---\s*$", re.MULTILINE)

# Keep generation batches small enough for one MCQ-generator request.
DEFAULT_BATCH_SIZE = 10


# --------------------------------------------------------------------------- #
# SPLIT_LECTURE_MD — TURN MARKED-UP LECTURE TEXT INTO PER-SLIDE RECORDS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Walks the lecture markdown and cuts it into one record per slide. Each
# record remembers its source page number and the markdown text on that
# slide. Anything before the first marker is dropped silently.
#
# Important code pieces:
# - `re.finditer(...)`: yields one match object per `--- PAGE N ---`
#   marker, in order.
# - `int(m.group(1))`: pulls the page number out of the marker.
# - `md[start:end].strip()`: slices the slide's text out of the full
#   markdown, between this marker and the next.
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


# --------------------------------------------------------------------------- #
# BATCH_SLIDES — CHUNK SLIDES INTO EVEN-SIZED BATCHES
# --------------------------------------------------------------------------- #
# Simple explanation:
# Groups the per-slide records into small lists so each MCQ-generator
# call receives at most `size` slides. This keeps each Claude call short
# and predictable in cost.
#
# Key detail:
# - `[slides[i : i + size] for i in range(0, len(slides), size)]`: a list
#   comprehension that walks the list `size` items at a time and slices
#   each chunk out.
def batch_slides(slides: list[dict], size: int = DEFAULT_BATCH_SIZE) -> list[list[dict]]:
    """Group slides into max-`size` batches for MCQ generation."""
    if size < 1:
        raise ValueError("batch size must be >= 1")
    return [slides[i : i + size] for i in range(0, len(slides), size)]

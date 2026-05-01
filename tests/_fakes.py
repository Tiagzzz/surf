"""Deterministic fakes for the Phase 1 smoke test.

Returns canned JSON matching the locked schemas in:
  - lo_extractor_system_prompt.md  (learning_objectives, ignored_pages, language)
  - mcq_generator_system_prompt.md (by_slide -> mcqs)

These fakes are pure functions; no network, no Anthropic SDK needed.
"""
from __future__ import annotations

from typing import Any


def fake_extract_los(lecture_md: str, factsheet_subset: dict[str, Any]) -> dict[str, Any]:
    """3-page sample: page 1 = ignored title, page 2 = LO 'Supply & Demand', page 3 = ignored sources."""
    return {
        "learning_objectives": [
            {"title": "Supply & Demand", "page_range": [2, 2]},
        ],
        "ignored_pages": [
            {"page_number": 1, "reason": "title page"},
            {"page_number": 3, "reason": "sources/references-only"},
        ],
        "language": "en",
    }


def fake_generate_mcqs(slides_batch: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a single MCQ for each slide in the batch; matches D-2.4 schema."""
    by_slide = []
    for s in slides_batch:
        page = s["page_number"]
        by_slide.append({
            "page_number": page,
            "mcqs": [
                {
                    "question": f"Test question for page {page}?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_indices": [0, 2],
                    "rationales_per_option": [
                        "A is correct because ...",
                        "B is wrong because ...",
                        "C is correct because ...",
                        "D is wrong because ...",
                    ],
                    "source_page": page,
                    "language": "en",
                }
            ],
        })
    return {"by_slide": by_slide}

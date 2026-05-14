"""Surf — pure exact-match grading and Swiss grade helpers.

Public surface:
    - ``is_exact_match(selected_indices, correct_indices, *, was_skipped=False)``
    - ``compute_swiss_grade(correct_count, total_count, pass_threshold_pct)``
    - ``compute_score_summary(correct_count, total_count, pass_threshold_pct)``

Rules enforced:
    - Exact match only; no partial credit; skipped is always wrong.
    - Swiss grade has 12 quarter-grade buckets below the class pass threshold
      (1.00 .. 3.75) and 9 quarter-grade buckets at/above the threshold
      (4.00 .. 6.00).
    - Duplicates in either selected_indices or correct_indices are invalid,
      so ``is_exact_match`` returns ``False``.

These helpers are dependency-free pure functions. They never read the DB,
never call Claude, and never log.
"""
# Pure grading helpers shared by attempts, review, and score summaries.
from __future__ import annotations

from typing import Sequence

__all__ = ["is_exact_match", "compute_swiss_grade", "compute_score_summary"]


def is_exact_match(
    selected_indices: Sequence[int],
    correct_indices: Sequence[int],
    *,
    was_skipped: bool = False,
) -> bool:
    """Return ``True`` iff the user's selection exactly matches the correct set.

    Rules:
      - If ``was_skipped`` is True, return False (skipped answers are wrong).
      - If either list contains duplicates, return False.
      - Otherwise return ``True`` iff ``set(selected) == set(correct)``.

    Order does not matter; sizes must match. No partial credit.
    """
    # Exact set match only; skipped or duplicate answers are always wrong.
    if was_skipped:
        return False
    if not _all_unique(selected_indices) or not _all_unique(correct_indices):
        return False
    return set(selected_indices) == set(correct_indices)


def compute_swiss_grade(
    correct_count: int,
    total_count: int,
    pass_threshold_pct: int,
) -> float:
    """Return a Swiss quarter-grade in [1.00, 6.00].

    Math:
      - ``score_pct = correct_count / total_count * 100``
      - Below threshold: linearly interpolated across 12 quarter-grade steps
        (1.00, 1.25, ..., 3.75). 0% -> 1.00, just-below-threshold -> 3.75.
      - At/above threshold: linearly interpolated across 9 quarter-grade
        steps (4.00, 4.25, ..., 6.00). At threshold -> 4.00, 100% -> 6.00.

    Raises ``ValueError`` if ``total_count`` is not positive or the threshold
    is outside ``(0, 100)``.
    """
    # Convert score percentage into the locked quarter-grade ladder.
    if total_count <= 0:
        raise ValueError("total_count must be > 0")
    if not (0 < pass_threshold_pct < 100):
        raise ValueError("pass_threshold_pct must be in (0, 100)")

    score_pct = (correct_count / total_count) * 100.0

    # Quarter-grade ladders
    below = [1.00 + 0.25 * i for i in range(12)]   # 1.00 .. 3.75 (12 steps)
    above = [4.00 + 0.25 * i for i in range(9)]    # 4.00 .. 6.00 (9 steps)

    if score_pct < pass_threshold_pct:
        # Map [0, threshold) -> 12 buckets via index based on relative position.
        ratio = score_pct / pass_threshold_pct
        idx = int(ratio * 12)
        if idx >= 12:
            idx = 11
        if idx < 0:
            idx = 0
        return below[idx]

    # At/above threshold: map [threshold, 100] -> 9 buckets.
    span = 100.0 - pass_threshold_pct
    if span <= 0:
        return 6.00  # threshold == 100 already rejected above; defensive only.
    ratio = (score_pct - pass_threshold_pct) / span
    idx = int(ratio * 9)
    if idx >= 9:
        idx = 8
    if idx < 0:
        idx = 0
    return above[idx]


def compute_score_summary(
    correct_count: int,
    total_count: int,
    pass_threshold_pct: int,
) -> dict:
    """Return the score-summary dict the P4 final-submit transaction stores.

    Keys: ``correct_count``, ``total_count``, ``score_pct``, ``swiss_grade``.
    ``score_pct`` is a plain float in [0, 100]. ``swiss_grade`` is a quarter
    grade in [1.00, 6.00] computed via :func:`compute_swiss_grade`.
    """
    # Package the values persisted with a completed attempt.
    if total_count <= 0:
        raise ValueError("total_count must be > 0")
    score_pct = (correct_count / total_count) * 100.0
    swiss_grade = compute_swiss_grade(correct_count, total_count, pass_threshold_pct)
    return {
        "correct_count": correct_count,
        "total_count": total_count,
        "score_pct": score_pct,
        "swiss_grade": swiss_grade,
    }


def _all_unique(seq: Sequence[int]) -> bool:
    """Helper: True iff `seq` contains no duplicates."""
    items = list(seq)
    return len(set(items)) == len(items)

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

# --------------------------------------------------------------------------- #
# IMPORTS AND PUBLIC EXPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Just the `Sequence` type hint and the `__all__` list. There are no DB,
# Streamlit, or Claude imports — every function in this file is a pure
# math/logic helper, which makes them trivial to unit-test.
#
# Important code pieces:
# - `Sequence[int]`: a type hint saying "any read-only sequence of ints"
#   (a list, tuple, etc.). It documents intent without locking the caller
#   into one container type.
# - `__all__`: the three names this module promises to expose.
from typing import Sequence

__all__ = ["is_exact_match", "compute_swiss_grade", "compute_score_summary"]


# --------------------------------------------------------------------------- #
# IS_EXACT_MATCH — EXACT-SET GRADING WITH NO PARTIAL CREDIT
# --------------------------------------------------------------------------- #
# Simple explanation:
# Returns True only when the user picked exactly the right answers — no
# extra, no missing, and they did not skip the question. Order does not
# matter because the comparison uses Python `set(...)`.
#
# Important code pieces:
# - `set(selected_indices) == set(correct_indices)`: turns both lists into
#   unordered sets and compares them; `{0, 2} == {2, 0}` is True.
# - `_all_unique(...)`: a tiny helper below that rejects duplicate indices
#   like `[0, 0]`, which the product lock forbids.
# - `was_skipped: bool = False`: keyword-only flag (the `*` in the
#   signature makes it keyword-only); skipped answers are always wrong.
#
# App connection:
# P4 take-mock final submit and P5 review both use this helper so the
# grading rule stays identical between live grading and re-display.


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
    # --------------------------------------------------------------------- #
    # COMPUTE_SWISS_GRADE — TURN A SCORE PERCENT INTO A SWISS QUARTER GRADE
    # --------------------------------------------------------------------- #
    # Simple explanation:
    # Surf displays grades the way Swiss universities do: a number between
    # 1.00 (worst) and 6.00 (best) in 0.25 steps. The teacher's pass mark
    # ("how many percent right counts as a grade 4") splits the range into
    # 12 fail buckets (1.00..3.75) and 9 pass buckets (4.00..6.00).
    #
    # Important code pieces:
    # - `score_pct = correct_count / total_count * 100`: percentage of
    #   right answers across the whole attempt.
    # - `below = [1.00 + 0.25 * i for i in range(12)]`: list comprehension
    #   that builds the 12-step fail ladder.
    # - `above = [4.00 + 0.25 * i for i in range(9)]`: the 9-step pass
    #   ladder.
    # - `raise ValueError(...)`: stop with a clear error when called with
    #   nonsense inputs instead of returning a garbage grade.
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
    # --------------------------------------------------------------------- #
    # COMPUTE_SCORE_SUMMARY — BUNDLE THE VALUES STORED WITH AN ATTEMPT
    # --------------------------------------------------------------------- #
    # Simple explanation:
    # P4 final submit calls this once at the end of an attempt to package
    # everything the attempt row needs: how many were correct, how many
    # total, the raw percent, and the Swiss grade.
    #
    # Key detail:
    # - Returns a `dict` (Python dictionary) with stable keys so the
    #   query helper that writes the attempt row can index it directly.
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

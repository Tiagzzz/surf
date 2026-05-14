"""P6 class-overview summary cards.

The functions here are deliberately small: they turn already-validated
aggregate payloads into equal-height Surf metric cards. They do not query the
DB, read Streamlit session state, or invent dashboard values.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# `dataclass` builds the small `SummaryCard` view model. `escape` keeps any
# dynamic card label or value from injecting HTML when rendered into custom
# markup. `Streamlit` provides the columns and HTML injector.
from dataclasses import dataclass
from html import escape
from typing import Any, Mapping

import streamlit as st

__all__ = ["SummaryCard", "build_summary_cards", "render_summary"]


# Each card is a tiny view model: text in, escaped HTML out. Keeping this
# immutable makes focused tests compare labels, values, helper copy, and dark-card
# styling without needing to parse Streamlit output.
@dataclass(frozen=True)
class SummaryCard:
    """Decorative metric card view model."""

    label: str
    value: str
    helper: str
    dark: bool = False


# Dashboard query helpers return plain dictionaries. These local coercion helpers
# keep old or malformed rows from crashing card rendering while still showing
# honest blanks instead of guessed grades.
def _as_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _format_grade(value: Any) -> str:
    grade = _as_float(value)
    if grade is None:
        return "—"
    return f"{grade:.2f}"


def _mock_basis_copy(mock_count: int) -> str:
    shown = min(max(mock_count, 0), 4)
    return f"Based on {shown} of 4 mocks"


# The top band mixes two approved aggregate sources: mock-only grade metrics and
# latest-answer coverage counts. This builder combines them without querying the
# database or inventing missing values.
# --------------------------------------------------------------------------- #
# SUMMARY CARD BUILDER AND RENDERER
# --------------------------------------------------------------------------- #
# Simple explanation:
# `build_summary_cards` assembles the four locked metric cards from the
# already-validated dashboard payload. `render_summary` places those cards
# inside Streamlit columns and returns the view models for tests.
#
# Important code pieces:
# - "Questions answered": dark card combining the latest-correct and
#   latest-wrong/skipped buckets out of `coverage_summary`.
# - "Completed mocks": total mock count (mock_kind == 'mock' only).
# - "Last 4 average": average Swiss grade over the last 4 completed mocks,
#   with `Based on N of 4 mocks` copy when N < 4.
# - "Last mock grade": Swiss grade of the most recent completed mock.
#
# Key detail:
# - Practice attempts are intentionally excluded from class average and
#   last grade (V1 lock). They still affect Study Next and weakness stats
#   elsewhere.
def build_summary_cards(
    *,
    mock_metrics: Mapping[str, Any] | None,
    coverage_summary: Mapping[str, Any] | None,
) -> list[SummaryCard]:
    """Return the locked top metric cards for P6 class overview.

    ``mock_metrics`` is the ``get_mock_grade_metrics`` payload from
    ``queries_dashboard``. It is mock-only by contract. ``coverage_summary`` is
    the latest-answer completion doughnut payload. Missing values are rendered
    as honest blanks/zeros rather than guessed numbers.
    """
    metrics = mock_metrics or {}
    coverage = coverage_summary or {}
    mock_count = _as_int(metrics.get("mock_count"))
    total_questions = _as_int(coverage.get("total_questions"))
    answered = _as_int(coverage.get("latest_correct")) + _as_int(
        coverage.get("latest_wrong_or_skipped")
    )
    return [
        SummaryCard(
            label="QUESTIONS ANSWERED",
            value=str(answered),
            helper=(
                f"{answered} of {total_questions} questions"
                if total_questions > 0
                else "Total"
            ),
            dark=True,
        ),
        SummaryCard(
            label="COMPLETED MOCKS",
            value=str(mock_count),
            helper="Total",
        ),
        SummaryCard(
            label="LAST 4 AVERAGE",
            value=_format_grade(metrics.get("class_average")),
            helper=_mock_basis_copy(mock_count),
        ),
        SummaryCard(
            label="LAST MOCK GRADE",
            value=_format_grade(metrics.get("last_grade")),
            helper="Mock exams only",
        ),
    ]


# Card markup is decorative, but all text still passes through `escape`. That
# keeps class/user-provided or future dynamic copy from becoming raw HTML.
def _card_html(card: SummaryCard) -> str:
    dark_class = " p6-metric-card--dark" if card.dark else ""
    return f"""
    <div class="p6-metric-card{dark_class}">
      <p class="surf-p6-card-title">{escape(card.label)}</p>
      <p class="surf-p6-metric">{escape(card.value)}</p>
      <p class="surf-p6-helper">{escape(card.helper)}</p>
    </div>
    """


# Rendering is intentionally thin: build the four card models first, then place
# them in Streamlit columns. Tests can assert the returned models without
# depending on browser rendering.
def render_summary(
    *,
    mock_metrics: Mapping[str, Any] | None,
    coverage_summary: Mapping[str, Any] | None,
    st_module: Any = st,
) -> list[SummaryCard]:
    """Render the equal-height metric band and return the view models."""
    cards = build_summary_cards(
        mock_metrics=mock_metrics,
        coverage_summary=coverage_summary,
    )
    cols = st_module.columns(4, gap="medium")
    for col, card in zip(cols, cards, strict=True):
        with col:
            st_module.html(_card_html(card))
    return cards

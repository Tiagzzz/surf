"""P6 latest-answer coverage doughnut.

The chart consumes only the ``get_completion_donut_summary`` payload. It never
uses preview fixtures, percentages invented in the renderer, or the old
"correct at least once" tie-break.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# `plotly.graph_objects` builds the Plotly doughnut figure used inside the
# Streamlit card. `escape` keeps any dynamic empty-state copy from injecting
# HTML when it lands inside custom card markup.
from html import escape
from typing import Any, Mapping

import plotly.graph_objects as go
import streamlit as st

__all__ = [
    "build_coverage_donut_figure",
    "coverage_empty_copy",
    "render_coverage_donut",
]

# The three colors map directly to the coverage buckets: green for latest
# correct, Surf accent red for latest wrong/skipped, and paper neutral for not
# covered. Keep this mapping stable so the chart matches the query payload.
PAPER_1 = "#EDE4D2"
PAPER_5 = "#28251F"
STATUS_OK = "#2D6A3F"
ACCENT = "#C8361D"


# Counts come from SQLite aggregate rows and focused tests may pass strings or
# missing values. Coerce locally so chart math stays safe without hiding the
# real bucket names.
def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _bucket_values(summary: Mapping[str, Any]) -> list[int]:
    return [
        _as_int(summary.get("latest_correct")),
        _as_int(summary.get("latest_wrong_or_skipped")),
        _as_int(summary.get("not_covered")),
    ]


def _completion_percent(summary: Mapping[str, Any]) -> int:
    total = _as_int(summary.get("total_questions"))
    if total <= 0:
        return 0
    completed = _as_int(summary.get("latest_correct")) + _as_int(
        summary.get("latest_wrong_or_skipped")
    )
    return round((completed / total) * 100)


def coverage_empty_copy(summary: Mapping[str, Any]) -> tuple[str, str] | None:
    """Return honest coverage copy for unavailable or all-unattempted states."""
    # Empty states explain the next user action: generate questions first, then
    # finish a mock or practice round. They never display pretend coverage just to
    # fill the card.
    total = _as_int(summary.get("total_questions"))
    if total <= 0:
        return (
            "No generated questions yet",
            "Upload a lecture and generate questions before Surf can calculate coverage.",
        )
    if _as_int(summary.get("latest_correct")) == 0 and _as_int(
        summary.get("latest_wrong_or_skipped")
    ) == 0:
        return (
            "Coverage is ready to start",
            "Questions are ready. Finish a mock or practice round to start covering them.",
        )
    return None


# --------------------------------------------------------------------------- #
# COVERAGE DOUGHNUT BUILDER AND RENDERER
# --------------------------------------------------------------------------- #
# Simple explanation:
# `build_coverage_donut_figure` produces the Plotly doughnut from the
# latest-answer summary, or `None` when there are no generated questions
# yet. `render_coverage_donut` is the keyed Streamlit container that places
# the chart or the honest empty-state copy plus the latest-answer note.
#
# Key detail:
# - "Latest answer wins" — each generated question contributes one slice
#   based on its most recent finished answer (mock or practice).
def build_coverage_donut_figure(summary: Mapping[str, Any]) -> go.Figure | None:
    """Build the latest-answer coverage doughnut or ``None`` if no questions exist."""
    # Build the doughnut from the stored latest-answer buckets only. The renderer
    # does not apply the older “correct at least once” rule and does not add sample
    # rows for a nicer-looking chart.
    if _as_int(summary.get("total_questions")) <= 0:
        return None

    fig = go.Figure(
        go.Pie(
            labels=["Latest correct", "Latest wrong/skipped", "Not covered"],
            values=_bucket_values(summary),
            hole=0.62,
            marker={
                "colors": [STATUS_OK, ACCENT, PAPER_1],
                "line": {"color": PAPER_5, "width": 1.5},
            },
            textinfo="label+percent",
            textposition="outside",
            automargin=True,
            hovertemplate="%{label}<br>%{value} questions<extra></extra>",
            sort=False,
        )
    )
    fig.update_layout(
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "JetBrains Mono, monospace", "color": PAPER_5, "size": 12},
        margin={"l": 24, "r": 72, "t": 22, "b": 34},
        showlegend=False,
    )
    fig.add_annotation(
        text=f"<b>{_completion_percent(summary)}%</b>",
        showarrow=False,
        font={"family": "Fraunces, Georgia, serif", "size": 30, "color": PAPER_5},
    )
    return fig


# Empty-state copy is normal user-facing text wrapped in custom card markup.
# Escape it before rendering so the styling layer stays separate from content.
def _empty_html(heading: str, body: str) -> str:
    return f"""
    <div class="surf-p6-empty-state">
      <p class="surf-p6-empty-heading">{escape(heading)}</p>
      <p class="surf-p6-helper">{escape(body)}</p>
    </div>
    """


# The renderer keeps the card title, chart or empty state, and helper note in
# one keyed Streamlit container. The note explains latest-answer semantics when
# real answers exist.
def render_coverage_donut(
    *,
    summary: Mapping[str, Any] | None,
    st_module: Any = st,
) -> go.Figure | None:
    """Render the coverage card using latest-answer buckets."""
    payload = summary or {}
    fig = build_coverage_donut_figure(payload)
    empty_copy = coverage_empty_copy(payload)
    with st_module.container(key="p6_coverage_doughnut_card"):
        st_module.html('<p class="surf-p6-card-title">KNOWLEDGE COVERAGE</p>')
        if fig is None:
            heading, body = empty_copy or ("No generated questions yet", "Upload lectures first.")
            st_module.html(_empty_html(heading, body))
        else:
            st_module.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False, "scrollZoom": False},
            )
            if empty_copy is not None:
                _heading, body = empty_copy
                st_module.html(f'<p class="surf-p6-chart-note">{escape(body)}</p>')
            else:
                st_module.html(
                    '<p class="surf-p6-chart-note">'
                    'Latest answer wins: correct, wrong/skipped, or not covered.'
                    '</p>'
                )
    return fig

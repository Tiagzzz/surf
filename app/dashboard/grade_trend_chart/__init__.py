"""P6 class grade trend chart renderer.

Consumes completed-attempt rows already fetched by the dashboard flow and draws
only stored mock-exam Swiss grades. Missing data renders an honest empty state.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# `plotly.graph_objects` draws the line chart with the grade-4 threshold
# annotation. `escape` keeps any dynamic empty-state copy safe inside custom
# card HTML. `Iterable` types the loose row sequence the renderer accepts.
from html import escape
from typing import Any, Iterable, Mapping

import plotly.graph_objects as go
import streamlit as st

__all__ = [
    "build_grade_trend_figure",
    "grade_trend_empty_copy",
    "render_grade_trend",
]

# These colors define the grade trend line, fill, grid, and grade-4 threshold.
# Keep them local to the chart so visual changes do not affect other dashboard
# cards.
PAPER_0 = "#F5EFE4"
PAPER_1 = "#EDE4D2"
PAPER_3 = "#6C6455"
PAPER_5 = "#28251F"
ACCENT = "#C8361D"
STATUS_OK = "#2D6A3F"


# Older or incomplete attempt rows may not have a usable `swiss_grade`. Reject
# those points instead of turning them into zeroes. An invented zero would make
# the trend look worse than the stored data.
def _coerce_grade(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


# The grade trend is a mock-exam metric. Filter out practice/unfinished rows and
# sort usable mock rows oldest-to-newest so improvement reads left-to-right.
def _mock_rows(rows: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []
    for row in rows:
        if row.get("mock_kind") not in (None, "mock"):
            continue
        if row.get("finished_at") is None:
            continue
        if _coerce_grade(row.get("swiss_grade")) is None:
            continue
        out.append(row)
    # The chart reads left-to-right oldest-to-newest. The production helper
    # returns newest first, but tests/previews may pass rows in another order.
    return sorted(out, key=lambda row: (str(row.get("finished_at")), int(row.get("id", 0))))


# Shared layout settings keep the Plotly chart visually inside the Surf card:
# transparent background, dashboard font, compact margins, and no legend noise.
def _base_layout(height: int) -> dict[str, Any]:
    return {
        "height": height,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "JetBrains Mono, monospace", "color": PAPER_5, "size": 12},
        "margin": {"l": 34, "r": 24, "t": 22, "b": 34},
        "showlegend": False,
    }


# Build a line only from real stored mock grades. If no usable grade points
# remain after filtering, return `None` so the renderer can show honest no-trend
# copy.
# --------------------------------------------------------------------------- #
# GRADE TREND BUILDER AND RENDERER
# --------------------------------------------------------------------------- #
# Simple explanation:
# `build_grade_trend_figure` plots the stored Swiss grades of completed
# mock attempts left-to-right oldest-to-newest, with a dashed grade-4
# threshold line. `render_grade_trend` wraps the chart in the keyed P6
# container and shows honest empty copy when there are no usable mock
# grade points yet.
#
# Key detail:
# - Only `mock_kind == 'mock'` rows with a stored `swiss_grade` are
#   included. Practice and unfinished rows are filtered out so the trend
#   matches the locked dashboard contract.
def build_grade_trend_figure(rows: Iterable[Mapping[str, Any]]) -> go.Figure | None:
    """Build a Plotly figure from stored completed mock grades.

    Returns ``None`` when no completed mock row has a usable Swiss grade.
    """
    points = _mock_rows(rows)
    if not points:
        return None

    labels = [f"Mock {idx}" for idx, _row in enumerate(points, start=1)]
    grades = [_coerce_grade(row.get("swiss_grade")) for row in points]
    fig = go.Figure(
        go.Scatter(
            x=labels,
            y=grades,
            mode="lines+markers",
            name="Mock grade",
            line={"color": ACCENT, "width": 4, "shape": "spline"},
            marker={"size": 10, "color": ACCENT, "line": {"color": PAPER_5, "width": 1}},
            fill="tozeroy",
            fillcolor="rgba(200, 54, 29, 0.18)",
            hovertemplate="%{x}<br>Grade %{y:.2f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=4,
        line_dash="dash",
        line_color=STATUS_OK,
        annotation_text="grade 4 threshold",
        annotation_position="top left",
    )
    fig.update_layout(**_base_layout(360))
    fig.update_yaxes(range=[1, 6], gridcolor=PAPER_1, title="Swiss grade")
    fig.update_xaxes(showgrid=False)
    return fig


# Empty copy tells users how the trend unlocks and keeps the last-four-mocks
# basis visible. This matters when a class has fewer than four completed mocks.
def grade_trend_empty_copy(*, mock_count: int) -> tuple[str, str]:
    """Return locked empty-state copy for no class mock trend."""
    if mock_count <= 0:
        return (
            "No mock trend yet",
            "Finish a mock exam so Surf can show your grade trend. Based on 0 of 4 mocks.",
        )
    return (
        "No mock trend yet",
        f"Surf found {mock_count} completed mock(s), but no stored grade trend points yet.",
    )


# Empty-state HTML is only a wrapper around copy. Escape heading and body text so
# future wording changes cannot inject markup.
def _empty_html(heading: str, body: str) -> str:
    return f"""
    <div class="surf-p6-empty-state">
      <p class="surf-p6-empty-heading">{escape(heading)}</p>
      <p class="surf-p6-helper">{escape(body)}</p>
    </div>
    """


# Rendering owns the Streamlit container and chart placement only. The function
# receives rows from dashboard flow, builds or skips the figure, and keeps the
# `Completed mock exams only.` note beside real charts.
def render_grade_trend(
    *,
    rows: Iterable[Mapping[str, Any]],
    mock_count: int,
    st_module: Any = st,
) -> go.Figure | None:
    """Render the class mock-grade trend card."""
    fig = build_grade_trend_figure(rows)
    with st_module.container(key="p6_grade_line_card"):
        st_module.html('<p class="surf-p6-card-title">GRADE TREND</p>')
        if fig is None:
            heading, body = grade_trend_empty_copy(mock_count=mock_count)
            st_module.html(_empty_html(heading, body))
        else:
            st_module.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False, "scrollZoom": False},
            )
            st_module.html(
                '<p class="surf-p6-chart-note">Completed mock exams only.</p>'
            )
    return fig

"""P6 real-data question-type performance chart renderer."""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# `Sequence` describes the row input passed by the dashboard flow. Plotly
# draws either the radar or the bar fallback. The shared question-type
# helpers map the canonical slug stored on each question to a display label.
from collections.abc import Sequence
from html import escape
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from app.brain.question_type import QUESTION_TYPE_LABELS, normalize_question_type

# Radar charts need enough real categories to form a meaningful shape. With one
# or two attempted types, use the bar fallback instead of padding missing types.
_MIN_RADAR_TYPES = 3


# Type rows with zero attempts are not evidence of performance. Coerce the
# attempted count safely and let zero-attempt rows fall out before charting.
def _attempted(row: dict) -> int:
    try:
        return int(row.get("attempted_count") or 0)
    except (TypeError, ValueError):
        return 0


def _accuracy_pct(row: dict) -> float:
    attempted = _attempted(row)
    if attempted <= 0:
        return 0.0
    accuracy = row.get("accuracy")
    if accuracy is None:
        try:
            accuracy = float(row.get("correct_count") or 0) / attempted
        except (TypeError, ValueError, ZeroDivisionError):
            accuracy = 0.0
    return round(float(accuracy) * 100.0, 2)


# Stored question types are normalized for display, but missing or unknown
# values remain visible. That makes data-quality problems obvious instead of
# silently mapping them to a fake category.
def question_type_label(value: object) -> str:
    """Return canonical, unknown, or missing type label without inventing rows."""
    slug = normalize_question_type(value)
    if not slug:
        return "Type unavailable"
    if slug in QUESTION_TYPE_LABELS:
        return QUESTION_TYPE_LABELS[slug]
    return f"Unknown type: {slug}"


# Filter to rows backed by completed answers. The chart should show what the
# student has actually attempted, not every possible taxonomy label.
def _real_rows(rows: Sequence[dict]) -> list[dict]:
    return [row for row in rows if _attempted(row) > 0]


def _labels_and_values(rows: Sequence[dict]) -> tuple[list[str], list[float]]:
    real_rows = _real_rows(rows)
    labels = [question_type_label(row.get("question_type")) for row in real_rows]
    values = [_accuracy_pct(row) for row in real_rows]
    return labels, values


# Build the radar from real attempted rows and close the polygon by repeating
# the first real point. Return `None` for sparse data so the fallback can render.
def build_question_type_radar_figure(rows: Sequence[dict]) -> go.Figure | None:
    """Build radar chart when at least three real type rows exist."""
    labels, values = _labels_and_values(rows)
    if len(labels) < _MIN_RADAR_TYPES:
        return None
    closed_labels = [*labels, labels[0]]
    closed_values = [*values, values[0]]
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=closed_values,
            theta=closed_labels,
            fill="toself",
            fillcolor="rgba(200, 54, 29, 0.18)",
            line={"color": "#C8361D", "width": 3},
            marker={"color": "#C8361D", "size": 7},
            name="Accuracy",
            hovertemplate="%{theta}: %{r:.0f}%<extra></extra>",
        )
    )
    fig.update_layout(
        height=320,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        polar={
            "bgcolor": "rgba(0,0,0,0)",
            "radialaxis": {"visible": True, "range": [0, 100], "gridcolor": "#D8CEBE"},
            "angularaxis": {"gridcolor": "#E6DDCF"},
        },
        showlegend=False,
        font={"family": "JetBrains Mono", "color": "#28251F", "size": 11},
    )
    return fig


# The bar chart is the honest sparse-data fallback. It uses the same real labels
# and accuracy values as the radar path, just in a simpler visual form.
def build_question_type_bar_fallback_figure(rows: Sequence[dict]) -> go.Figure | None:
    """Build the approved bar fallback from real type rows only."""
    labels, values = _labels_and_values(rows)
    if not labels:
        return None
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=values,
            marker={"color": "#C8361D", "line": {"color": "#28251F", "width": 1.5}},
            hovertemplate="%{x}: %{y:.0f}%<extra></extra>",
            name="Accuracy",
        )
    )
    fig.update_layout(
        height=300,
        margin={"l": 10, "r": 10, "t": 18, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        yaxis={"range": [0, 100], "title": "Accuracy %", "gridcolor": "#D8CEBE"},
        xaxis={"title": "Stored question type", "gridcolor": "#E6DDCF"},
        font={"family": "JetBrains Mono", "color": "#28251F", "size": 11},
    )
    return fig


# Empty copy tells users that completed answers need stored question types before
# this card can show performance. It does not mention model analysis or fake
# readiness scores.
def question_type_empty_copy() -> tuple[str, str]:
    return (
        "Not enough type data yet",
        "Surf will show this after completed answers have stored question types.",
    )


# Rendering follows the approved order: radar when enough real categories exist,
# bar fallback for sparse real data, and empty copy when no attempted type rows
# exist.
# --------------------------------------------------------------------------- #
# RENDER QUESTION-TYPE PERFORMANCE — RADAR WITH BAR FALLBACK
# --------------------------------------------------------------------------- #
# Simple explanation:
# Renders the P6 question-type accuracy card. When at least 3 real
# attempted types exist, a radar chart shows accuracy per type. With fewer
# real types, the renderer falls back to a horizontal bar chart so sparse
# data still reads honestly. With no attempted rows at all, an empty-state
# message explains the next step.
def render_question_type_performance(
    *,
    rows: Sequence[dict],
    st_module: Any = st,
    prefer_radar: bool = True,
) -> None:
    """Render radar-first question-type performance with an honest fallback."""
    with st_module.container(key="p6_question_type_card"):
        fig = build_question_type_radar_figure(rows) if prefer_radar else None
        if fig is None:
            fig = build_question_type_bar_fallback_figure(rows)
        if fig is None:
            heading, body = question_type_empty_copy()
            st_module.html(
                '<div class="surf-p6-empty-state">'
                f'<p class="surf-p6-empty-heading">{escape(heading)}</p>'
                f'<p class="surf-p6-helper">{escape(body)}</p></div>'
            )
            return
        st_module.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False, "scrollZoom": False},
        )


__all__ = [
    "build_question_type_bar_fallback_figure",
    "build_question_type_radar_figure",
    "question_type_empty_copy",
    "question_type_label",
    "render_question_type_performance",
]

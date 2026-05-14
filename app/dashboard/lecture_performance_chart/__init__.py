"""P6 lecture-specific performance chart renderer.

The dropdown source is all uploaded lectures for the selected class. The chart
uses only direct lecture-specific answer rows from completed mocks, passed in as
``list_lecture_performance_series(...)`` payloads.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from html import escape
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from app.db.queries_dashboard import list_lecture_performance_series, list_lectures_for_class

# The dropdown and the trend use separate query seams. Tests can replace each
# seam independently to prove uploaded lectures remain visible even when no
# completed mock has direct lecture performance yet.
LectureListFn = Callable[[int], list[dict]]
LectureSeriesFn = Callable[[int], list[dict]]


# Load all uploaded lectures for choices and direct performance rows for chart
# points as two streams. Combining them too early would hide lectures that still
# need completed mock answers.
def load_lecture_performance_payload(
    class_id: int,
    *,
    list_lectures_fn: LectureListFn = list_lectures_for_class,
    list_performance_fn: LectureSeriesFn = list_lecture_performance_series,
) -> dict[str, list[dict]]:
    """Load uploaded lectures and direct performance rows for a class."""
    return {
        "lectures": list_lectures_fn(class_id),
        "performance_series": list_performance_fn(class_id),
    }


# Lecture rows come from SQLite payloads and Streamlit selections. Normalize IDs
# defensively so malformed rows are ignored instead of becoming chart points.
def _lecture_id(row: dict) -> int | None:
    try:
        return int(row.get("lecture_id"))
    except (TypeError, ValueError):
        return None


def _series_by_lecture(performance_series: Sequence[dict]) -> dict[int, dict]:
    by_id: dict[int, dict] = {}
    for row in performance_series:
        lecture_id = _lecture_id(row)
        if lecture_id is not None:
            by_id[lecture_id] = row
    return by_id


def _average_grade(row: dict) -> float | None:
    grades: list[float] = []
    for point in row.get("performance") or []:
        try:
            grades.append(float(point["swiss_grade"]))
        except (KeyError, TypeError, ValueError):
            continue
    if not grades:
        return None
    return sum(grades) / len(grades)


# When real lecture performance exists, start with the lowest average Swiss
# grade so the dashboard points to the weakest lecture first. Without data, fall
# back to the first uploaded lecture for a stable empty state.
def select_default_lecture_id(
    lectures: Sequence[dict],
    performance_series: Sequence[dict],
) -> int | None:
    """Return weakest lecture by direct average, else first uploaded lecture."""
    series = _series_by_lecture(performance_series)
    candidates: list[tuple[float, int]] = []
    for lecture in lectures:
        lecture_id = _lecture_id(lecture)
        if lecture_id is None or lecture_id not in series:
            continue
        average = _average_grade(series[lecture_id])
        if average is not None:
            candidates.append((average, lecture_id))
    if candidates:
        return min(candidates, key=lambda item: (item[0], item[1]))[1]
    for lecture in lectures:
        lecture_id = _lecture_id(lecture)
        if lecture_id is not None:
            return lecture_id
    return None


# Build the line from one lecture's direct completed-mock points. Whole-mock
# grades or placeholder zeroes would overstate what the selected lecture actually
# explains.
def build_lecture_performance_figure(lecture_series: dict) -> go.Figure | None:
    """Build a Plotly line chart from one lecture's direct mock-grade rows."""
    points = list(lecture_series.get("performance") or [])
    if not points:
        return None

    x_values: list[str] = []
    y_values: list[float] = []
    hover_values: list[str] = []
    for point in points:
        try:
            grade = float(point["swiss_grade"])
        except (KeyError, TypeError, ValueError):
            continue
        attempt_position = point.get("attempt_position", len(x_values) + 1)
        x_values.append(f"Mock {attempt_position}")
        y_values.append(grade)
        percent = point.get("percent_correct")
        if percent is None:
            hover_values.append(f"Grade {grade:.2f}")
        else:
            hover_values.append(f"Grade {grade:.2f}<br>{float(percent):.0f}% correct")
    if not y_values:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(200, 54, 29, 0.16)",
            line={"color": "#C8361D", "width": 3},
            marker={"color": "#C8361D", "size": 8},
            text=hover_values,
            hovertemplate="%{text}<extra></extra>",
            name="Lecture grade",
        )
    )
    fig.update_layout(
        height=300,
        margin={"l": 10, "r": 10, "t": 18, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        yaxis={"range": [1, 6], "title": "Swiss grade", "gridcolor": "#D8CEBE"},
        xaxis={"title": "Last completed mocks", "gridcolor": "#E6DDCF"},
        font={"family": "JetBrains Mono", "color": "#28251F", "size": 11},
    )
    return fig


# The empty text separates two user situations: upload a lecture first, or take
# mocks that include this lecture. That keeps the card useful without fake trend
# points.
def lecture_empty_copy(*, has_lectures: bool) -> tuple[str, str]:
    """Return honest empty-state copy for the lecture focus section."""
    if not has_lectures:
        return (
            "No uploaded lectures yet",
            "Upload a lecture before Surf can show lecture-specific performance.",
        )
    return (
        "Lecture insights unlock after completed mocks include this lecture.",
        "This lecture is uploaded, but completed mocks have not answered its questions yet.",
    )


# Streamlit selectbox labels should always be readable. Use the stored lecture
# title when present and fall back to `Untitled lecture` for incomplete rows.
def _lecture_label(row: dict) -> str:
    title = str(row.get("title") or "Untitled lecture").strip() or "Untitled lecture"
    return title


# Render all uploaded lectures in the selectbox, then chart the selected
# lecture only if direct performance rows exist. This keeps the dashboard stable
# while the user is still building history.
def render_lecture_performance(
    *,
    lectures: Sequence[dict],
    performance_series: Sequence[dict],
    st_module: Any = st,
) -> None:
    """Render the P6 lecture dropdown and selected lecture trend."""
    lecture_rows = list(lectures or [])
    series = _series_by_lecture(performance_series or [])
    with st_module.container(key="p6_lecture_focus_card"):
        if not lecture_rows:
            heading, body = lecture_empty_copy(has_lectures=False)
            st_module.html(
                '<div class="surf-p6-empty-state">'
                f'<p class="surf-p6-empty-heading">{escape(heading)}</p>'
                f'<p class="surf-p6-helper">{escape(body)}</p></div>'
            )
            return

        default_id = select_default_lecture_id(lecture_rows, performance_series)
        default_index = 0
        for idx, row in enumerate(lecture_rows):
            if _lecture_id(row) == default_id:
                default_index = idx
                break
        selected = st_module.selectbox(
            "Lecture",
            lecture_rows,
            index=default_index,
            format_func=_lecture_label,
            key="p6_lecture_focus_select",
        )
        selected_id = _lecture_id(selected or {})
        selected_title = _lecture_label(selected or {})
        st_module.html(f'<p class="surf-p6-card-title">{escape(selected_title)}</p>')
        selected_series = series.get(selected_id) if selected_id is not None else None
        fig = build_lecture_performance_figure(selected_series or {})
        if fig is None:
            heading, body = lecture_empty_copy(has_lectures=True)
            st_module.html(
                f'<p class="surf-p6-empty-heading">{escape(heading)}</p>'
                f'<p class="surf-p6-helper">{escape(body)}</p>'
            )
            return
        average = _average_grade(selected_series or {})
        if average is not None:
            st_module.html(
                f'<p class="surf-p6-chart-note">Lecture average: {average:.2f} '
                'Swiss grade from direct lecture answers.</p>'
            )
        st_module.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False, "scrollZoom": False},
        )


__all__ = [
    "build_lecture_performance_figure",
    "lecture_empty_copy",
    "load_lecture_performance_payload",
    "render_lecture_performance",
    "select_default_lecture_id",
]

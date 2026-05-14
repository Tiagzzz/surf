"""P6 dashboard page flow seam.

This module owns the authenticated dashboard orchestration boundary:
selected class IDs from Streamlit session state are treated as untrusted,
validated against the signed-in user, and only then are dashboard aggregate
helpers called.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from html import escape
from typing import Any

import streamlit as st

from app.brain.page_header import render_page_header
from app.brain.page_layout import build_page_rail_css
from app.brain.topbar import render_topbar
from app.class_.study_next_launch import launch_study_next_practice
from app.db.queries_classes import get_class_by_id

# These aliases define the injectable seams used by focused tests: database
# aggregates, class lookup, topbar rendering, page switching, and layout rendering.
# Production uses the real defaults, while tests can replace one seam at a time.
AggregateFn = Callable[[int], Any]
AggregateMap = Mapping[str, AggregateFn]
GetClassFn = Callable[[int, int], Mapping[str, Any] | None]
LayoutFn = Callable[..., None]
TopbarFn = Callable[..., None]
SwitchPageFn = Callable[[str], None]


def _coerce_int(value: Any) -> int | None:
    """Return a positive-ish int from session state input, or None."""
    # Streamlit session state can hold stale strings, missing values, or values from
    # an old page visit. Coerce only safe integer-like IDs so invalid dashboard routes
    # show recovery copy before any class analytics are loaded.
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_owned_class(user_id: int, class_id: int) -> Mapping[str, Any] | None:
    """Default class lookup that rejects stale/foreign class IDs."""
    # The class row is loaded before any dashboard aggregate helper runs. Matching
    # `classes.user_id` to the saved user is the boundary that prevents a stale or
    # foreign `selected_class_id` from exposing another class's dashboard data.
    row = get_class_by_id(class_id)
    if row is None:
        return None
    if int(row.get("user_id", -1)) != int(user_id):
        return None
    return row


def _class_belongs_to_user(klass: Mapping[str, Any], user_id: int) -> bool:
    """Defensive second ownership check for injected class lookups."""
    # Some tests inject a class lookup instead of using SQLite. Keep a second
    # ownership check here so injected rows still follow the same rule as production
    # rows whenever they include a `user_id` field.
    if "user_id" not in klass:
        return True
    try:
        return int(klass["user_id"]) == int(user_id)
    except (TypeError, ValueError):
        return False


# The class name is display-only after ownership has been validated. Returning
# stripped text here keeps header/breadcrumb fallbacks simple without changing
# which class the dashboard queries.
def _class_name(klass: Mapping[str, Any]) -> str:
    return str(klass.get("name", "")).strip()


# `get_class_fn` validation in render_dashboard_page must happen before these imports.

def _default_aggregate_fns() -> dict[str, AggregateFn]:
    """Import dashboard aggregates lazily after class ownership validation."""
    # Dashboard aggregate imports stay lazy on purpose: `render_dashboard_page`
    # reaches this function only after class validation. That ordering keeps missing,
    # malformed, stale, or foreign class IDs away from analytics helpers.
    from app.db.queries_attempts import list_completed_attempts_for_class
    from app.db.queries_dashboard import (
        get_completion_donut_summary,
        get_mock_grade_metrics,
        get_question_type_performance_for_class,
        get_weakest_learning_objectives,
        list_lecture_performance_series,
        list_lectures_for_class,
    )

    return {
        "mock_grade_metrics": get_mock_grade_metrics,
        "completion_donut": get_completion_donut_summary,
        "mock_grade_trend": (
            lambda class_id: list_completed_attempts_for_class(
                class_id,
                mock_kind="mock",
                limit=4,
            )
        ),
        "lectures": list_lectures_for_class,
        "lecture_performance_series": list_lecture_performance_series,
        "question_type_performance": get_question_type_performance_for_class,
        "weakest_learning_objectives": get_weakest_learning_objectives,
    }


def _build_dashboard_payload(
    *,
    user: Mapping[str, Any],
    class_id: int,
    klass: Mapping[str, Any],
    aggregate_fns: AggregateMap,
) -> dict[str, Any]:
    """Call aggregate helpers for an already validated class."""
    # Build one payload from the already validated class ID. Each aggregate helper
    # receives that same ID, so charts and Study Next all describe the same selected
    # class instead of re-reading session state.
    aggregates = {
        name: fn(class_id)
        for name, fn in aggregate_fns.items()
    }
    return {
        "user": dict(user),
        "class_id": class_id,
        "class": dict(klass),
        "aggregates": aggregates,
    }


def _render_recovery(
    *,
    st_module: Any,
    switch_page_fn: SwitchPageFn,
) -> None:
    """Render honest no-class recovery copy without touching aggregates."""
    # Recovery handles the no-valid-class branch without touching aggregates. The
    # user gets one safe route back to My Classes, and the dashboard avoids guessing
    # which class should have been selected.
    st_module.html(_recovery_styles())
    with st_module.container(key="p6_dashboard_recovery"):
        st_module.markdown("## Class not found")
        st_module.markdown("Pick a class from your home to keep going.")
        if st_module.button("BACK TO MY CLASSES", key="p6_back_to_my_classes"):
            switch_page_fn("views/my_classes.py")


def _recovery_styles() -> str:
    """Return scoped P6 recovery button styling."""
    # This CSS targets only the stale/missing-class recovery container. It fixes the
    # visible `BACK TO MY CLASSES` button typography without affecting chart cards,
    # Study Next buttons, or other Streamlit controls.
    return """
<style>
.st-key-p6_dashboard_recovery [data-testid="stButton"] button {
  background: #FDF9F2 !important;
  border: 1.5px solid #28251F !important;
  border-radius: 3px !important;
  box-shadow: 4px 4px 0 #171512 !important;
  color: #28251F !important;
  font-family: "JetBrains Mono", ui-monospace, monospace !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  height: 44px !important;
  letter-spacing: 0.14em !important;
  padding: 0 18px !important;
  text-transform: uppercase !important;
  transition: transform 0.08s ease-out,
    box-shadow 0.08s ease-out,
    background 0.08s ease-out !important;
}
.st-key-p6_dashboard_recovery [data-testid="stButton"] button:hover {
  background: #F5EFE4 !important;
  box-shadow: 5px 5px 0 #171512 !important;
  transform: translate(-1px, -1px) !important;
}
.st-key-p6_dashboard_recovery [data-testid="stButton"] button:active {
  box-shadow: 0 0 0 #171512 !important;
  transform: translate(4px, 4px) !important;
}
@media (prefers-reduced-motion: reduce) {
  .st-key-p6_dashboard_recovery [data-testid="stButton"] button,
  .st-key-p6_dashboard_recovery [data-testid="stButton"] button:hover,
  .st-key-p6_dashboard_recovery [data-testid="stButton"] button:active {
    transform: none !important;
    transition: background 0.08s ease-out !important;
  }
}
</style>
"""


def _styles() -> str:
    """Return scoped P6 class-overview styling."""
    # These styles define dashboard chrome: section labels, metric cards, chart
    # cards, and empty states. They should not encode numbers or business rules;
    # values still come only from the validated aggregate payload.
    return """
<style>
.st-key-p6_dashboard_page [data-testid="stVerticalBlock"] { gap: 16px !important; }
.surf-p6-kicker, .surf-p6-section-label, .surf-p6-card-title,
.surf-p6-helper, .surf-p6-chart-note {
  font-family: "JetBrains Mono", ui-monospace, monospace;
}
.surf-p6-kicker, .surf-p6-section-label, .surf-p6-card-title {
  color: #3B362C;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  margin: 0 0 6px;
  text-transform: uppercase;
}
.surf-p6-title, .surf-p6-section-heading, .surf-p6-metric, .surf-p6-empty-heading {
  color: #28251F;
  font-family: "Fraunces", Georgia, serif;
  font-style: italic;
  letter-spacing: -0.035em;
}
.surf-p6-title { font-size: 48px; font-weight: 650; line-height: 1.0; margin: 0 0 8px; }
.surf-p6-subtitle, .surf-p6-helper, .surf-p6-chart-note {
  color: #6C6455;
  font-size: 12px;
  line-height: 1.5;
}
.surf-p6-subtitle { font-size: 13px; margin: 0 0 16px; max-width: 760px; }
.surf-p6-section { margin: 14px 0 4px; }
.surf-p6-section-heading { font-size: 28px; font-weight: 650; line-height: 1.05; margin: 0; }
.p6-metric-card {
  background: #F5EFE4;
  border: 1.5px solid #28251F;
  border-radius: 4px;
  box-shadow: 3px 3px 0 #171512;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  height: 156px;
  justify-content: space-between;
  padding: 22px 24px;
}
.p6-metric-card--dark { background: #28251F; color: #FDF9F2; }
.p6-metric-card--dark .surf-p6-card-title, .p6-metric-card--dark .surf-p6-helper { color: #EDE4D2; }
.p6-metric-card--dark .surf-p6-metric { color: #FDF9F2; }
.surf-p6-metric { font-size: 42px; font-weight: 700; line-height: 1; margin: 0; }
.st-key-p6_grade_line_card, .st-key-p6_coverage_doughnut_card, .st-key-p6_future_section {
  background: #F5EFE4;
  border: 1.5px solid #28251F;
  border-radius: 4px;
  box-shadow: 3px 3px 0 #171512;
  box-sizing: border-box;
  padding: 20px;
}
.surf-p6-empty-state {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.surf-p6-empty-heading { font-size: 24px; font-weight: 650; margin: 0 0 8px; }
</style>
"""


# Section headings are decorative HTML but their copy may include page text.
# Escape both label and heading so styling cannot accidentally turn dynamic text
# into markup.
def _section_html(label: str, heading: str) -> str:
    return f"""
    <div class="surf-p6-section">
      <p class="surf-p6-section-label">{escape(label)}</p>
      <h2 class="surf-p6-section-heading">{escape(heading)}</h2>
    </div>
    """


def _dashboard_study_next_view_models(
    *,
    weak_los: list[Mapping[str, Any]],
    lectures: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build P6 Study Next rows with the shared P3 view-model contract."""
    # Study Next on the dashboard reuses the Class Hub view-model shape. That keeps
    # lecture labels, ready counts, and practice-launch session keys aligned between
    # P3 and P6 instead of creating a dashboard-only contract.
    from app.class_.class_hub import build_study_next_view_models

    lecture_labels = {
        int(lecture.get("lecture_id") or lecture.get("id")): f"L{index + 1:02d}"
        for index, lecture in enumerate(lectures)
        if lecture.get("lecture_id") is not None or lecture.get("id") is not None
    }
    prepared_rows: list[dict[str, Any]] = []
    ready_counts: dict[int, int] = {}
    for row in weak_los:
        prepared = dict(row)
        lo_id = int(prepared["lo_id"])
        lecture_id = prepared.get("lecture_id")
        if "lecture_label" not in prepared and lecture_id is not None:
            prepared["lecture_label"] = lecture_labels.get(int(lecture_id))
        ready_counts[lo_id] = int(
            prepared.get("questions_ready")
            or prepared.get("ready_count")
            or prepared.get("answered_count")
            or 0
        )
        prepared_rows.append(prepared)
    return build_study_next_view_models(
        prepared_rows,
        ready_counts_by_lo_id=ready_counts,
    )


def _render_future_sections(*, st_module: Any) -> None:
    """Render placeholder dashboard section anchors in the approved order."""
    # This placeholder renderer remains for older focused tests that assert section
    # ordering. The active dashboard layout below renders the real lecture, question
    # type, and Study Next sections from aggregate data.
    for label, heading, body in (
        (
            "LECTURE FOCUS",
            "Pick a lecture to see its trend.",
            "Lecture insights unlock after completed mocks include this lecture.",
        ),
        (
            "QUESTION TYPES",
            "Where your answers are strongest.",
            "Surf will show this after completed answers have stored question types.",
        ),
        (
            "STUDY NEXT",
            "Where Surf thinks you should focus.",
            "Take a mock or practice round so Surf can spot weak topics.",
        ),
    ):
        st_module.html(_section_html(label, heading))
        with st_module.container(key=f"p6_future_{label.lower().replace(' ', '_')}"):
            st_module.html(f'<p class="surf-p6-helper">{escape(body)}</p>')


def _default_render_layout(payload: dict[str, Any], *, st_module: Any = st) -> None:
    """Render the P6 class overview from a validated aggregate payload."""
    # The layout receives a prepared payload after route validation. It renders the
    # header, cards, charts, and Study Next from that payload only, so rendering code
    # cannot accidentally bypass the ownership guard by reading session state again.
    from app.class_.class_hub import TAKE_MOCK_VIEW_PATH, render_study_next_section
    from app.dashboard.coverage_donut import render_coverage_donut
    from app.dashboard.grade_trend_chart import render_grade_trend
    from app.dashboard.lecture_performance_chart import render_lecture_performance
    from app.dashboard.question_type_performance_chart import render_question_type_performance
    from app.dashboard.summary_cards import render_summary

    klass = payload["class"]
    aggregates = payload.get("aggregates", {})
    mock_metrics = aggregates.get("mock_grade_metrics", {})
    coverage_summary = aggregates.get("completion_donut", {})
    mock_trend = aggregates.get("mock_grade_trend", [])
    lectures = aggregates.get("lectures", [])
    lecture_series = aggregates.get("lecture_performance_series", [])
    question_type_rows = aggregates.get("question_type_performance", [])
    weak_los = aggregates.get("weakest_learning_objectives", [])
    mock_count = 0
    try:
        mock_count = int(mock_metrics.get("mock_count", 0))
    except (TypeError, ValueError, AttributeError):
        mock_count = 0

    st_module.html(_styles())
    st_module.html(build_page_rail_css("p6_dashboard_page"))
    with st_module.container(key="p6_dashboard_page"):
        render_page_header(
            kicker="SURFBOARD",
            title=f"{_class_name(klass) or 'Class'} dashboard",
            helper="Real progress from completed mocks and practice rounds.",
            key="p6_page_header",
            st_module=st_module,
        )
        st_module.html(_section_html("CLASS OVERVIEW", "Your progress at a glance."))
        render_summary(
            mock_metrics=mock_metrics,
            coverage_summary=coverage_summary,
            st_module=st_module,
        )
        render_grade_trend(
            rows=mock_trend,
            mock_count=mock_count,
            st_module=st_module,
        )
        render_coverage_donut(summary=coverage_summary, st_module=st_module)
        st_module.html(_section_html("LECTURE FOCUS", "Pick a lecture to see its trend."))
        render_lecture_performance(
            lectures=lectures,
            performance_series=lecture_series,
            st_module=st_module,
        )
        st_module.html(_section_html("QUESTION TYPES", "Where your answers are strongest."))
        render_question_type_performance(rows=question_type_rows, st_module=st_module)
        study_next = _dashboard_study_next_view_models(
            weak_los=list(weak_los or []),
            lectures=list(lectures or []),
        )
        practiced_lo_id = render_study_next_section(
            study_next,
            st_module=st_module,
            key_prefix="p6",
        )
        if practiced_lo_id is not None:
            launch_study_next_practice(
                class_id=int(payload["class_id"]),
                class_name=_class_name(klass) or None,
                learning_objective_id=practiced_lo_id,
                session_state=st_module.session_state,
            )
            st_module.switch_page(TAKE_MOCK_VIEW_PATH)


# Public entry point for `views/dashboard.py`. It owns the route-level decision:
# recover before aggregates when IDs are bad, otherwise validate ownership, load
# real dashboard data, and delegate visual rendering.
def render_dashboard_page(
    *,
    user: Mapping[str, Any],
    selected_class_id: int | str | None,
    get_class_fn: GetClassFn = _get_owned_class,
    topbar_fn: TopbarFn = render_topbar,
    switch_page_fn: SwitchPageFn | None = None,
    render_layout_fn: LayoutFn = _default_render_layout,
    aggregate_fns: AggregateMap | None = None,
    st_module: Any = st,
) -> None:
    """Render the P6 dashboard after validating class ownership.

    ``selected_class_id`` comes from Streamlit session state and is therefore
    untrusted. Missing, malformed, stale, or foreign class IDs render honest
    recovery copy and return before any dashboard aggregate helper can run.
    """
    switch_page = switch_page_fn or st_module.switch_page
    user_id = _coerce_int(user.get("id"))
    class_id = _coerce_int(selected_class_id)

    if user_id is None or class_id is None:
        topbar_fn("dashboard", class_name=None)
        _render_recovery(st_module=st_module, switch_page_fn=switch_page)
        return

    klass = get_class_fn(user_id, class_id)
    if klass is None or not _class_belongs_to_user(klass, user_id):
        topbar_fn("dashboard", class_name=None)
        _render_recovery(st_module=st_module, switch_page_fn=switch_page)
        return

    topbar_fn("dashboard", class_name=_class_name(klass) or None)
    payload = _build_dashboard_payload(
        user=user,
        class_id=class_id,
        klass=klass,
        aggregate_fns=aggregate_fns or _default_aggregate_fns(),
    )
    if render_layout_fn is _default_render_layout:
        render_layout_fn(payload, st_module=st_module)
    else:
        render_layout_fn(payload)


__all__ = ["render_dashboard_page"]

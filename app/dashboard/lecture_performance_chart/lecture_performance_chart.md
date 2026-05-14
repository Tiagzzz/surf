# `app/dashboard/lecture_performance_chart/` — lecture focus chart

This module renders the Lecture Focus section. The dropdown lists all uploaded lectures for the validated class, and the chart shows direct lecture-specific Swiss-grade points from completed mock attempts when available.

## Public surface

- `load_lecture_performance_payload(...)` loads uploaded lectures and performance series through injectable query seams.
- `select_default_lecture_id(...)` picks the weakest lecture by direct average when real data exists, otherwise the first uploaded lecture.
- `build_lecture_performance_figure(...)` builds the selected lecture line chart.
- `lecture_empty_copy(...)` returns honest unlock copy.
- `render_lecture_performance(...)` renders the dropdown, selected lecture title, average note, chart, or empty state.

## Data flow

`dashboard_flow` passes `lectures` and `lecture_performance_series` payloads into the renderer. The renderer maps performance rows by lecture ID, keeps uploaded lectures visible even if they do not yet have performance rows, and charts only direct points for the selected lecture.

## Connected code and tools

- `app.db.queries_dashboard.list_lectures_for_class` supplies uploaded lecture options.
- `app.db.queries_dashboard.list_lecture_performance_series` supplies direct lecture performance rows.
- `app.dashboard.dashboard_flow` passes both payloads into this renderer.
- Plotly draws the line chart; Streamlit renders the selectbox and card.

## Code walkthrough

### Module docstring, imports, and query seams

The top block documents the direct lecture-performance boundary, imports Plotly/Streamlit, and exposes type aliases for injectable lecture-list and performance-list functions.

### `load_lecture_performance_payload(...)`

Calls the lecture-list and performance-list functions separately. This prevents uploaded lectures with no completed-mock answers from disappearing from the dropdown.

### ID and average helpers

`_lecture_id(...)`, `_series_by_lecture(...)`, and `_average_grade(...)` normalize row dictionaries and skip malformed data rather than inventing grades.

### `select_default_lecture_id(...)`

Defaults to the lowest average direct Swiss grade when real performance exists. If no lecture has trend data, it picks the first uploaded lecture so the empty state still has a stable selection.

### `build_lecture_performance_figure(...)`

Builds a Plotly line chart from one lecture's direct `performance` points. Each point already represents only that lecture's answers in a completed mock.

### `lecture_empty_copy(...)`

Returns separate copy for no uploaded lectures and uploaded-but-no-performance states.

### `_lecture_label(...)`

Builds safe selectbox labels from lecture titles, falling back to `Untitled lecture`.

### `render_lecture_performance(...)`

Renders the lecture selector, selected lecture title, optional average note, figure, or unlock copy. It keeps the section visible even before trend data exists.

## Testing notes

`tests/test_dashboard_render_contract.py` and `tests/test_dashboard_chart_components.py` cover uploaded-lecture dropdown behavior, default selection, and direct performance plotting.

## What could break if changed

- Building dropdown options from performance rows would hide uploaded lectures with no completed-mock data yet.
- Using whole-mock grades instead of direct lecture answer rows would misrepresent lecture performance.
- Adding sample rows or zero-filled points would create fake analytics.

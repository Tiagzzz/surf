# `app/dashboard/grade_trend_chart/` — P6 class grade trend chart

This module renders the class-level Grade Trend card from completed mock attempts. It draws only stored Swiss grades from mock exams and uses honest copy when no trend can be drawn.

## Inputs / outputs

- `rows`: completed attempt rows, normally from `list_completed_attempts_for_class(class_id, mock_kind="mock", limit=4)`.
- `mock_count`: completed mock count from `get_mock_grade_metrics(...)`.
- Output: a Plotly line/area figure or honest empty-state HTML.

## Data flow

`dashboard_flow` validates class ownership, fetches the last completed mock rows, and passes them to `render_grade_trend(...)`. This module filters to completed mock rows with usable `swiss_grade`, sorts oldest-to-newest, and draws the Swiss-grade line.

## Connected code and tools

- `app.db.queries_attempts.list_completed_attempts_for_class` supplies mock trend rows.
- `app.db.queries_dashboard.get_mock_grade_metrics` supplies `mock_count` for empty copy.
- `app.dashboard.dashboard_flow._default_render_layout` renders this card.
- Plotly draws the chart; Streamlit displays it.

## Constraints

- Completed mock attempts only.
- No practice grades, unfinished attempts, invented class averages, or preview fixtures.
- Y-axis stays on Swiss grade range 1–6 with a grade-4 threshold line.
- Empty state keeps the `Based on 0 of 4 mocks` basis when no mocks exist.

## Code walkthrough

### Module docstring, imports, and `__all__`

The top block declares the mock-only grade boundary, imports Plotly/Streamlit, and exposes only builder/copy/render functions.

### Color constants

The constants keep the chart line, grid, fill, and threshold aligned with the dashboard palette.

### `_coerce_grade(...)`

Converts stored `swiss_grade` values to floats and rejects missing or malformed values so old/incomplete rows do not become fake chart points.

### `_mock_rows(...)`

Filters incoming rows to completed mock attempts with grades and sorts them from oldest to newest. The production query returns newest first, so this helper makes the visual read naturally left-to-right.

### `_base_layout(...)`

Returns the transparent Plotly layout shared by the card.

### `build_grade_trend_figure(...)`

Builds the filled line chart with a grade-4 threshold. It returns `None` when no usable mock-grade rows exist.

### `grade_trend_empty_copy(...)`

Centralizes the no-trend copy. It distinguishes no completed mocks from completed mocks that still lack usable grade points.

### `_empty_html(...)`

Escapes empty-state copy before rendering decorative HTML.

### `render_grade_trend(...)`

Renders the card title, chart or empty copy, and the `Completed mock exams only.` note.

## Testing notes

`tests/test_dashboard_chart_components.py` covers mock filtering, sorting, empty copy, and figure construction.

## What could break if changed

- Including practice rows would make the class trend disagree with the mock-only grade contract.
- Sorting newest-to-oldest would make improvement look backwards.
- Returning a fake zero chart for no data would violate the real-data-only rule.

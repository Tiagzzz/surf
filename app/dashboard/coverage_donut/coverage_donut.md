# `app/dashboard/coverage_donut/` — P6 latest-answer coverage doughnut

This module renders the Knowledge Coverage card from the `get_completion_donut_summary(...)` payload. It shows what share of generated questions has a latest completed answer and whether that latest answer was correct or wrong/skipped.

## Inputs / outputs

- Input: `summary`, a dictionary with `latest_correct`, `latest_wrong_or_skipped`, `not_covered`, and `total_questions`.
- Output: a Plotly doughnut figure, an honest empty state, or an all-not-covered chart with unlock copy.
- Rendered by: `dashboard_flow._default_render_layout(...)`.

## Data flow

`dashboard_flow` validates class ownership, calls `get_completion_donut_summary(class_id)`, and passes the payload into `render_coverage_donut(...)`. This module coerces counts, preserves the three bucket order, computes the center percentage, and renders either Plotly or escaped empty-state HTML.

## Connected code and tools

- `app.db.queries_dashboard.get_completion_donut_summary` defines the latest-answer buckets.
- `app.dashboard.dashboard_flow` passes the payload into this renderer.
- Plotly draws the doughnut; Streamlit displays the figure/card.

## Constraints

- Buckets are exactly `Latest correct`, `Latest wrong/skipped`, and `Not covered`.
- Latest completed mock/practice answer wins.
- No generated questions returns copy instead of a fake chart.
- Generated questions with no completed answers can draw an all-not-covered chart and must explain what unlocks coverage.
- The center annotation is the completion percentage only.

## Code walkthrough

### Module docstring, imports, and `__all__`

The module declares its latest-answer boundary, imports Plotly and Streamlit, and exposes only the builder/copy/render functions used by tests and dashboard flow.

### Surf color constants

Constants define paper colors, dark text, success green, and Surf accent red for wrong/skipped answers.

### `_as_int(...)`, `_bucket_values(...)`, and `_completion_percent(...)`

These helpers coerce query payload values, keep bucket order stable, and calculate the center percentage from latest-correct plus latest-wrong/skipped over total generated questions.

### `coverage_empty_copy(...)`

Returns clear copy for no generated questions and generated-but-unattempted questions. It returns `None` after at least one completed answer exists.

### `build_coverage_donut_figure(...)`

Builds the Plotly pie/doughnut. It returns `None` only when there are no generated questions. It uses outside labels, fixed colors, no sorting, transparent background, and the percentage center annotation.

### `_empty_html(...)`

Escapes heading/body copy and wraps it in Surf empty-state markup.

### `render_coverage_donut(...)`

Renders the card title, figure or empty state, and helper note. The helper note explains latest-answer semantics when answers exist.

## Testing notes

`tests/test_dashboard_chart_components.py` covers figure buckets, center percentage, wrong/skipped color, and empty-state behavior.

## What could break if changed

- Changing labels or bucket order would make the UI disagree with `get_completion_donut_summary`.
- Using fixture/demo values here would create fake production analytics.
- Removing the percentage center or latest-answer note would make the dashboard harder to explain.
- Recoloring wrong/skipped away from Surf accent red would regress the approved visual contract.

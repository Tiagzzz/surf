# `app/dashboard/question_type_performance_chart/` — question-type performance chart

This module renders the Question Types section from real completed-answer rows grouped by stored `questions.question_type`. Radar is the preferred view when enough real categories exist; a bar chart handles sparse data.

## Public surface

- `question_type_label(value)` returns canonical, missing, or unknown type labels.
- `build_question_type_radar_figure(rows)` builds a radar chart only when at least three real attempted type rows exist.
- `build_question_type_bar_fallback_figure(rows)` builds a bar fallback from real attempted rows.
- `question_type_empty_copy()` explains when type analytics unlock.
- `render_question_type_performance(...)` tries radar, then bar, then empty copy.

## Data flow

`dashboard_flow` passes rows from `get_question_type_performance_for_class(...)` into this renderer. Each row represents stored answer performance for a question type. The module filters to rows with attempts, normalizes labels for display, and never pads missing taxonomy categories.

## Connected code and tools

- `app.db.queries_dashboard.get_question_type_performance_for_class` supplies the aggregate rows.
- `app.brain.question_type.normalize_question_type` and `QUESTION_TYPE_LABELS` define canonical labels.
- `app.dashboard.dashboard_flow` renders this section after class validation.
- Plotly draws radar/bar charts; Streamlit displays the card.

## Code walkthrough

### Module docstring, imports, and `_MIN_RADAR_TYPES`

The top block defines the real-data boundary and imports Plotly, Streamlit, and the central question-type taxonomy. `_MIN_RADAR_TYPES = 3` prevents a fake radar shape from sparse data.

### `_attempted(...)` and `_accuracy_pct(...)`

These helpers convert aggregate row counts into safe attempted counts and percentages. Missing or malformed values become zero rather than crashes.

### `question_type_label(...)`

Normalizes stored values. Known slugs get friendly labels, missing values become `Type unavailable`, and unsupported stored values remain visible as `Unknown type: ...`.

### `_real_rows(...)` and `_labels_and_values(...)`

Filter to attempted rows and produce label/value arrays for both chart builders. No missing categories are added.

### `build_question_type_radar_figure(...)`

Builds a `go.Scatterpolar` radar only when at least three real rows exist. It closes the polygon by repeating the first real point.

### `build_question_type_bar_fallback_figure(...)`

Builds a separate `go.Bar` fallback from the same real rows. This is the readable path for one or two stored categories.

### `question_type_empty_copy(...)`

Returns the honest empty-state copy for no type data.

### `render_question_type_performance(...)`

Renders radar first, then bar fallback, then empty copy. It does not call any model-analysis code.

## Testing notes

`tests/test_dashboard_chart_components.py`, `tests/test_dashboard_render_contract.py`, `tests/test_queries_dashboard.py`, and `tests/test_question_type.py` cover labels, radar/bar fallback, and real aggregate rows.

## What could break if changed

- Padding missing taxonomy categories would create fake analytics.
- Treating unknown or missing stored values as canonical slugs would hide data-quality problems.
- Removing the bar fallback would make sparse real data harder to read.
- Adding difficulty-profile fields here would exceed the current no-model-analysis boundary.

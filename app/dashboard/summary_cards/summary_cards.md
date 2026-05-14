# `app/dashboard/summary_cards/` — P6 class overview metric band

This module renders the first metric band on the dashboard. It consumes already-validated aggregate payloads and turns them into four equal-height Surf metric cards.

## Inputs / outputs

- `mock_metrics`: dictionary from `get_mock_grade_metrics(class_id)`, mock-only by contract.
- `coverage_summary`: dictionary from `get_completion_donut_summary(class_id)`, latest-answer based.
- Output: four `SummaryCard` view models and their rendered HTML cards.

## Data flow

`dashboard_flow` validates class ownership and passes aggregate dictionaries to `render_summary(...)`. `build_summary_cards(...)` computes display values from those dictionaries, then `render_summary(...)` lays them out in Streamlit columns.

## Connected code and tools

- `app.db.queries_dashboard.get_mock_grade_metrics` supplies completed mock count, last grade, and last-four average.
- `app.db.queries_dashboard.get_completion_donut_summary` supplies generated/answered coverage counts.
- `app.dashboard.dashboard_flow` renders the summary band before chart sections.
- Streamlit columns display the four cards.

## Constraints

- Last grade and class average are mock-only.
- Questions answered comes from latest correct plus latest wrong/skipped answers.
- Missing grade values display as `—`, not guessed values.
- Last-four average helper copy remains `Based on N of 4 mocks`.

## Code walkthrough

### Module docstring, imports, and `__all__`

The top block states that this module renders from already-validated payloads only. It imports `dataclass`, escaping, Streamlit, and type helpers.

### `SummaryCard`

A small immutable view model for card label, value, helper copy, and dark-card styling.

### `_as_int(...)`, `_as_float(...)`, and `_format_grade(...)`

Local coercion helpers keep dashboard cards robust when old rows or tests provide missing values.

### `_mock_basis_copy(...)`

Builds the visible `Based on N of 4 mocks` helper while capping the shown count at four.

### `build_summary_cards(...)`

Creates the four locked card models: questions answered, completed mocks, last-four average, and last mock grade. It uses only aggregate values and does not query the database.

### `_card_html(...)`

Escapes card text and wraps it in Surf card markup.

### `render_summary(...)`

Builds cards, renders four Streamlit columns, and returns the card models for tests.

## Testing notes

`tests/test_dashboard_render_contract.py` and `tests/test_dashboard_chart_components.py` cover card values, helper copy, and rendering contracts.

## What could break if changed

- Using practice attempts for grade cards would violate the mock-only grade contract.
- Guessing missing grades would make the dashboard look more complete than the data is.
- Changing the `Based on N of 4 mocks` copy can make partial averages unclear.
- Moving Study Next into the top band would break the approved section order.

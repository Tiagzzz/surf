# `app/dashboard/dashboard_flow/` — dashboard page flow seam

This module is the route guard and renderer coordinator for P6. It proves that the selected class belongs to the saved user before any dashboard aggregate can run, then renders the real dashboard sections and Study Next handoff.

## What this code does

`render_dashboard_page(...)` receives a saved user and a `selected_class_id` from the Streamlit wrapper. It rejects missing, malformed, stale, or foreign classes with recovery copy. For a valid class, it calls the dashboard aggregate helpers and passes their plain dictionary/list payloads to the renderer.

## Inputs / outputs

| Function | Inputs | Output / effect |
|---|---|---|
| `render_dashboard_page(...)` | saved user mapping, selected class ID, injectable seams | Renders recovery or the full dashboard. |
| `_default_aggregate_fns()` | none | Returns the real aggregate helper map after validation. |
| `_build_dashboard_payload(...)` | user, validated class ID, class row, aggregate map | Returns a payload with `user`, `class_id`, `class`, and `aggregates`. |
| `_default_render_layout(...)` | validated payload | Renders header, charts, and Study Next. |
| `_dashboard_study_next_view_models(...)` | weakness rows and lecture rows | Returns the shared Study Next row shape used by Class Hub. |

## Data flow

1. Coerce `user["id"]` and `selected_class_id` to integers.
2. Render `Class not found` recovery if either ID is missing or malformed.
3. Look up the class and confirm `classes.user_id` matches the saved user.
4. Render the dashboard topbar with the validated class name.
5. Lazily import aggregate helpers and call each helper with the validated class ID.
6. Render class overview, grade trend, latest-answer coverage, lecture focus, question types, and Study Next.
7. If a Study Next row is clicked, write session-only practice launch state and switch to `views/take_mock_exam.py`.

## Connected code and tools

- Calls `app.db.queries_classes.get_class_by_id` for ownership validation.
- Calls `app.db.queries_dashboard` helpers for mock metrics, coverage, lectures, lecture trends, question-type performance, and weakest learning objectives.
- Calls `app.db.queries_attempts.list_completed_attempts_for_class(..., mock_kind="mock", limit=4)` for grade trend rows.
- Calls dashboard chart/render modules for visual sections.
- Reuses `app.class_.class_hub.render_study_next_section` and `app.class_.study_next_launch.launch_study_next_practice` for practice launch.
- Uses Streamlit for rendering and navigation only after the data boundary is clear.

## Code walkthrough

### Module docstring, imports, and type aliases

The top of the file explains the ownership boundary, imports shared UI helpers and class lookup, and defines injectable type aliases for aggregate functions, class lookup, layout rendering, topbar rendering, and page switching.

### `_coerce_int(...)`

Converts session/user values into usable integer IDs. It rejects `None`, booleans, and malformed strings so bad route state recovers before any database aggregate can run.

### `_get_owned_class(...)`

Loads a class by ID and checks that the row belongs to the signed-in user. This is the production data-isolation guard.

### `_class_belongs_to_user(...)`

Repeats the ownership check for injected class rows. Tests and preview seams can supply custom rows, so this keeps the same safety rule visible.

### `_class_name(...)`

Extracts the display class name from a validated class row. Empty names fall back later to generic dashboard copy.

### `_default_aggregate_fns(...)`

Imports aggregate helpers inside the function. Because `render_dashboard_page(...)` calls this only after validation, stale or foreign IDs cannot trigger analytics queries.

### `_build_dashboard_payload(...)`

Calls every aggregate helper with the same validated class ID and groups the results into one payload for the layout renderer.

### `_render_recovery(...)` and `_recovery_styles()`

Render honest recovery copy and the `BACK TO MY CLASSES` button when the dashboard has no valid class. The scoped CSS styles only this recovery button.

### `_styles()` and `_section_html(...)`

Return dashboard-local CSS and escaped section-heading markup. These helpers control chrome only; they do not create or alter dashboard data.

### `_dashboard_study_next_view_models(...)`

Adapts real weakness rows into the Class Hub Study Next view-model shape. It keeps generated/answered counts from the aggregate row and fills lecture labels from uploaded lecture order when needed.

### `_render_future_sections(...)`

Keeps older focused tests harmless by rendering placeholder section anchors. The main layout now renders the real lecture, type, and Study Next sections.

### `_default_render_layout(...)`

Renders the full dashboard from the validated payload. It injects scoped CSS, renders the shared header, draws each dashboard section in order, then launches Study Next practice through the shared session-state helper when a practice arrow is clicked.

### `render_dashboard_page(...)`

Public entry point. It ties together ID coercion, class ownership validation, recovery, topbar rendering, aggregate loading, and layout delegation.

## Testing notes

Key focused tests:

- `tests/test_dashboard_view_wrapper.py` checks the wrapper/auth route.
- `tests/test_dashboard_render_contract.py` checks layout, validation, and aggregate order.
- `tests/test_dashboard_study_next_reuse.py` checks shared Study Next behavior.
- `tests/test_dashboard_chart_components.py` checks chart builders.
- `tests/test_queries_dashboard.py` checks the underlying formulas.

## What could break if changed

- Moving `_default_aggregate_fns()` before ownership validation can leak class analytics.
- Trusting `selected_class_id` directly can show a stale or foreign class.
- Removing the mock-only `mock_kind="mock"` trend call can mix practice into grade charts.
- Forking Study Next launch state here can break P4 practice startup.
- Adding fallback demo numbers or padded question-type rows would create fake analytics.

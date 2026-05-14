# `views/dashboard.py` — Dashboard page wrapper

This Streamlit page is the thin route wrapper for P6. It checks whether a saved local user exists, reads the selected class ID from session state, and delegates all dashboard validation and rendering to `app.dashboard.render_dashboard_page(...)`.

## Page overview

The dashboard shows a signed-in student class progress view: summary cards, mock-grade trend, latest-answer coverage, lecture focus, question-type performance, and Study Next guidance. The wrapper itself does not calculate analytics.

## Route and session context

| State / route item | Meaning |
|---|---|
| `get_saved_user()` | Loads the saved local user. If it returns `None`, the page routes back to signup. |
| `st.session_state["selected_class_id"]` | The class selected from My Classes or Class Hub. It is treated as untrusted until `dashboard_flow` validates ownership. |
| `views/signup.py` | Recovery route for anonymous users. |
| `app.dashboard.render_dashboard_page(...)` | The bucket entry point that validates class ownership and renders the dashboard. |

## On-screen elements

The visible sections are rendered by `app/dashboard/`, not by this wrapper:

| Section | Source |
|---|---|
| Shared topbar and page header | `dashboard_flow` through shared brain helpers. |
| Summary cards | `summary_cards` from mock metrics and latest-answer coverage. |
| Grade trend | `grade_trend_chart` from completed mock attempts only. |
| Knowledge coverage | `coverage_donut` from latest completed mock/practice answers. |
| Lecture focus | `lecture_performance_chart` from uploaded lectures and direct lecture-specific mock rows. |
| Question types | `question_type_performance_chart` from stored `questions.question_type` rows. |
| Study Next | Shared Class Hub Study Next renderer plus practice launch handoff. |

## User interactions

- Anonymous users are redirected to signup before dashboard code runs.
- A stale or missing selected class shows recovery copy inside `dashboard_flow` and offers `BACK TO MY CLASSES`.
- Study Next practice clicks are handled by the dashboard bucket through the shared practice launch helper, then route to `views/take_mock_exam.py`.

## Data sources

The wrapper reads only saved-user state and Streamlit session state. Dashboard data comes from `app.db.queries_dashboard`, `app.db.queries_attempts`, and `app.db.queries_classes` after class ownership validation.

## Connected buckets

- `app/brain/` for saved user, topbar, page header, and shared page rail.
- `app/dashboard/` for route guard, analytics rendering, and chart modules.
- `app/class_/` for the shared Study Next renderer and practice launch state.
- `app/db/` for class ownership and aggregate query helpers.

## Code walkthrough

### Module docstring and imports

The docstring explains that this page is intentionally thin. Imports are limited to Streamlit, saved-user lookup, and the dashboard bucket entry point.

### Saved-user check

`_user = get_saved_user()` decides whether a local user exists. If not, Streamlit switches to `views/signup.py` before any class dashboard code runs.

### Dashboard delegation

For signed-in users, the wrapper reads `selected_class_id` from `st.session_state` and calls `render_dashboard_page(...)`. The dashboard bucket, not this file, validates the class and renders analytics.

## Testing notes

`tests/test_dashboard_view_wrapper.py` covers the wrapper behavior. Use the wider dashboard test group when the wrapper or dashboard bucket changes.

## What could break if changed

- Reading dashboard aggregates in this wrapper would bypass the ownership guard.
- Trusting `selected_class_id` here would duplicate validation and risk drift.
- Changing the anonymous redirect can strand first-time users outside signup.

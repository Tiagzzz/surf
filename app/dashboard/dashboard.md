# `app/dashboard/` — P6 dashboard bucket

This bucket renders the authenticated class dashboard. It starts from the class selected in Streamlit session state, proves that the class belongs to the saved user, and then shows real progress from completed mocks, practice answers, uploaded lectures, stored question types, and Study Next weaknesses.

## What lives in this folder

| File / folder | What it does |
|---|---|
| `__init__.py` | Re-exports `render_dashboard_page` so `views/dashboard.py` stays a thin page wrapper. |
| `dashboard_flow/` | Owns route validation, recovery copy, aggregate-call order, page header, section order, and Study Next launch handoff. |
| `summary_cards/` | Builds the four top metric cards: questions answered, completed mocks, last-four average, and last mock grade. |
| `grade_trend_chart/` | Draws the mock-only Swiss-grade trend from stored completed mock attempts. |
| `coverage_donut/` | Draws latest-answer coverage: latest correct, latest wrong/skipped, and not covered. |
| `lecture_performance_chart/` | Shows all uploaded lectures in a dropdown and direct lecture-specific mock performance for the selected lecture. |
| `question_type_performance_chart/` | Shows real performance by stored `questions.question_type`, using radar first and a bar fallback for sparse data. |
| `radar_chart/` | Reserved Phase 7 scaffold that points active type rendering to `question_type_performance_chart/`; kept so future ML/radar work has an explicit seam without fake analytics. |

## How the pieces interact

```text
views/dashboard.py
        │
        ├── get_saved_user() redirects anonymous users to signup
        ├── reads st.session_state["selected_class_id"]
        ▼
app.dashboard.render_dashboard_page(...)
        │
        ├── validates class ownership through get_class_by_id
        ├── renders recovery if the selected class is missing, stale, malformed, or foreign
        ├── calls dashboard aggregate helpers only after validation
        ├── renders summary, grade, coverage, lecture, and type sections
        └── reuses the Class Hub Study Next renderer and practice-launch handoff
```

## Data flow

1. The page wrapper passes the saved user and `selected_class_id` into `render_dashboard_page(...)`.
2. `dashboard_flow` coerces IDs and validates `classes.user_id` before importing or calling aggregate helpers.
3. Aggregate helpers return plain dictionaries/lists from stored SQLite rows. They do not return pandas objects and do not read demo fixtures.
4. Chart modules convert those payloads into Plotly figures or honest empty states.
5. Study Next rows use weakest learning-objective payloads and the same session-only practice launch path as Class Hub.

## Connected code and tools

- `views/dashboard.py` is the Streamlit route wrapper.
- `app.brain.session.get_saved_user()` is the authentication boundary.
- `app.brain.topbar.render_topbar()` and `app.brain.page_header.render_page_header()` provide shared shell/header chrome.
- `app.db.queries_classes.get_class_by_id()` enforces class ownership.
- `app.db.queries_dashboard` supplies coverage, grade, lecture, type, and weakness payloads.
- `app.db.queries_attempts.list_completed_attempts_for_class(..., mock_kind="mock", limit=4)` supplies grade trend rows.
- `app.class_.class_hub.render_study_next_section()` and `app.class_.study_next_launch.launch_study_next_practice()` keep P6 practice launch state aligned with P3.

## Code walkthrough

### `__init__.py`

Imports `render_dashboard_page` from `dashboard_flow` and exposes it through `__all__`. This keeps the public dashboard import stable even if internal chart modules change.

### `dashboard_flow/__init__.py`

Coordinates the page. It validates route/session input, renders recovery when needed, loads aggregates only after ownership is proven, injects scoped dashboard styles, renders the real dashboard sections in order, and launches Study Next practice through the shared session-state helper.

### `summary_cards/__init__.py`

Builds simple immutable card view models from `mock_grade_metrics` and `completion_donut` payloads, then renders the four-card metric band. It keeps grade metrics mock-only and coverage counts latest-answer based.

### `grade_trend_chart/__init__.py`

Filters incoming rows to completed mock attempts with stored `swiss_grade`, sorts them oldest-to-newest, and draws a Swiss-grade Plotly line chart. Empty data stays honest instead of becoming a fake zero line.

### `coverage_donut/__init__.py`

Reads the three latest-answer buckets and builds the doughnut with a percentage center annotation. It explains no-question and generated-but-unattempted states without inventing coverage.

### `lecture_performance_chart/__init__.py`

Keeps uploaded lecture options separate from performance rows, defaults to the weakest lecture when real data exists, and renders direct lecture-specific mock trends or unlock copy.

### `question_type_performance_chart/__init__.py`

Normalizes stored question-type slugs for labels, filters to attempted rows, draws radar only when at least three real categories exist, and falls back to a bar chart for sparse real data.

### Reserved scaffold module

`radar_chart` is kept as the only reserved dashboard scaffold because future Phase 7 ML/radar work may need an explicit seam. The old empty `completion_chart`, `lecture_avg_chart`, and `score_evolution_chart` folders were deleted on 2026-05-13; active production rendering already lives in `coverage_donut`, `lecture_performance_chart`, and `grade_trend_chart`.

## Testing notes

Use focused dashboard checks after touching this bucket:

```bash
python -m pytest -q tests/test_dashboard* tests/test_queries_dashboard* tests/test_no_secrets_committed.py tests/test_no_real_db.py
python -m ruff check app/dashboard views/dashboard.py --no-cache
python -m compileall app/dashboard views/dashboard.py
```

## What could break if changed

- Calling aggregate helpers before class ownership validation can expose another class's dashboard data.
- Mixing practice rows into grade metrics would break the mock-only grade contract.
- Padding missing question types would create fake analytics.
- Changing Streamlit keys can break tests, Study Next state, or styled dashboard cards.
- Adding dashboard-local shell/header code can drift from shared topbar and page-header behavior.

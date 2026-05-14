# `app/brain/topbar/` — shared authenticated topbar

Surf's authenticated chrome. The public entry point is
`render_topbar(current_page, *, class_name=None, mode_label=None)`. P2-P7 call it
near the top of their renderers; Signup stays unauthenticated and does not use
this module.

## Purpose

- Render the fixed white topbar with Surf logo, breadcrumb, Home, and Settings
  controls.
- Keep authenticated page body content below the fixed bar.
- Keep topbar inner content aligned with the shared 880px page rail.
- Route logo/Home to My Classes and Settings gear to Settings.

## What lives in this folder

| File | What it does |
|---|---|
| `__init__.py` | Constants, SVG loading, data-URI conversion, scoped CSS, breadcrumb HTML, and `render_topbar(...)` |
| `topbar.md` | This teammate-facing walkthrough |

## Inputs / outputs

| Function / constant | Purpose |
|---|---|
| `BREADCRUMB_SEPARATOR` | Locked ` › ` separator between breadcrumb segments |
| `PAGE_TO_BREADCRUMB` | Static breadcrumb parent segments per page key |
| `PAGE_TO_VIEW` | `st.switch_page` target per page key |
| `render_topbar(current_page, class_name=None, mode_label=None)` | Renders the topbar and handles click routing |

Dynamic `class_name` values are escaped before rendering. Missing dashboard class
names degrade to the My Classes parent breadcrumb so stale class labels are not
shown.

## Data flow

```text
page renderer
  → render_topbar(current_page="class_view", class_name=class_name)
      → _topbar_styles() loads local SVGs as data URIs
      → _breadcrumb_html(...) escapes dynamic breadcrumb text
      → Streamlit buttons call st.switch_page(...)
```

The topbar reads local SVG assets only. It does not read SQLite, session state,
API keys, environment variables, or Anthropic state.

## Connected pages and tools

- P2 My Classes: `MY CLASSES`.
- P3 Class Hub: `MY CLASSES › <CLASS NAME>` when a class is available.
- P4 Take Mock: `MY CLASSES › <CLASS NAME> › MOCK EXAM` or `PRACTICE`.
- P5 Review: `MY CLASSES › <CLASS NAME> › REVIEW`.
- P6 Dashboard: `MY CLASSES › <CLASS NAME> › DASHBOARD` after class ownership
  validation.
- P7 Settings: `MY CLASSES › SETTINGS`.
- Assets: `assets/brand/surf-logo.svg`, `assets/icons/home.svg`, and
  `assets/icons/settings.svg`.
- Streamlit: `st.html`, `st.container`, `st.columns`, `st.button`, and
  `st.switch_page`.

## Code walkthrough

### Module docstring

Summarizes the public contract: authenticated-only topbar, logo/breadcrumb/icon
layout, routes, and no DB/API reads.

### Locked content constants

`BREADCRUMB_SEPARATOR`, `GEAR_ARIA_LABEL`, `HOME_ARIA_LABEL`,
`LOGO_NAV_ARIA_LABEL`, `PAGE_TO_BREADCRUMB`, and `PAGE_TO_VIEW` define route,
copy, and accessibility contracts in one place.

### Asset path constants

`_REPO_ROOT` locates the project root from the module path. `_LOGO_ASSET`,
`_HOME_ICON_ASSET`, and `_SETTINGS_ICON_ASSET` point to local SVG assets.

### SVG loader helpers

`_read_svg(...)` reads an asset safely, `_svg_to_data_uri(...)` base64-encodes
it, and the three cached data-URI helpers reuse the result for the process.
The data-URI pattern avoids Streamlit stripping raw inline SVG.

### `_topbar_styles()`

Builds scoped CSS for the fixed topbar, hidden Streamlit chrome, page-body top
offset, logo button, breadcrumb text, Home/Settings stamped icon buttons, focus
states, and reduced-motion behavior. It imports the shared rail constants so the
inner row aligns with page content.

### `_breadcrumb_html(...)`

Starts from `PAGE_TO_BREADCRUMB`, appends dynamic class/mode leaves for
class-scoped pages, escapes all text, joins segments with the locked separator,
and returns a single HTML string.

### `render_topbar(...)`

Injects CSS, opens the `surf_topbar` container, lays out logo/breadcrumb/actions,
renders the three buttons, and calls `st.switch_page(...)` when a navigation
button is clicked.

### `__all__`

Exports constants and `render_topbar(...)` for tests and page renderers.

## Testing notes

```bash
python -m pytest -q tests/test_topbar.py tests/test_topbar_dashboard_breadcrumb.py
ruff check app/brain/topbar --no-cache
```

## What could break if changed

- Moving or renaming `render_topbar` breaks authenticated page imports.
- Calling it from Signup would show authenticated chrome on the setup page.
- Removing dynamic escaping can let user-created class names inject markup.
- Inlining raw SVG through `st.html` can make icons disappear.
- Removing the fixed-body offset can let page content slide underneath the bar.
- Changing route targets can strand Home or Settings navigation.

## Button-label note

The logo, Home, and Settings controls are icon-only Streamlit buttons with hidden
labels and help text. The visible breadcrumb remains JetBrains Mono. No shared
button-font behavior lives here.

# `app/brain/page_header` — shared authenticated page header

Renders the small header family used by authenticated pages: Mono all-caps
kicker, Fraunces italic title, and optional helper line. Callers provide copy;
this helper escapes it and paints it inside the caller's page rail.

## Purpose

- Keep page headers visually consistent across My Classes, Class Hub, Dashboard,
  and Settings.
- Escape dynamic title/helper strings, including user-created class names.
- Avoid duplicating header CSS in each page bucket.
- Preserve injectable rendering for tests and dashboard-style fake Streamlit
  modules.

## Inputs / outputs

| Function | Input | Output |
|---|---|---|
| `build_page_header_css(header_key)` | Streamlit container key | Scoped `<style>` string |
| `build_page_header_html(kicker, title, helper)` | Header copy | Escaped HTML string |
| `render_page_header(...)` | Copy, key, optional `st_module` seam | Renders CSS and HTML inside a keyed Streamlit container |

The helper reads no DB rows, session state, API keys, uploaded files, or
Anthropic state.

## Connected code and tools

- My Classes, Class Hub, Dashboard, and Settings render this helper inside the
  shared page rail.
- `app.brain.page_layout` owns the width and horizontal padding.
- `app.brain.topbar` owns the authenticated top offset.
- Tests use the optional `st_module` seam to record rendered CSS/HTML.

## Code walkthrough

### Constants

`PAGE_HEADER_DEFAULT_KEY` is the fallback container key. The class-name
constants identify the kicker, title, and helper nodes in the generated HTML so
CSS and tests share stable hooks.

### `build_page_header_css(...)`

Rejects an empty key, then returns CSS scoped to `.st-key-<header_key>`. It
sets the shared spacing, Mono uppercase kicker, Fraunces italic title, and quiet
helper line. Typography rules use `!important` because Streamlit theme wrappers
can otherwise override custom Markdown HTML.

### `build_page_header_html(...)`

Builds a simple `<div role="group">` header and escapes every copy string with
`html.escape`. It avoids semantic heading tags because the current Streamlit
rendering path is more reliable with simple div markup.

### `_render_html(...)`

Uses `st.markdown(..., unsafe_allow_html=True)` when available, falling back to
`st.html(...)` for small test fakes.

### `render_page_header(...)`

Imports Streamlit lazily when no injected module is provided, injects scoped CSS,
opens a keyed container, and renders the escaped header HTML.

## Testing notes

```bash
python -m pytest -q tests/test_page_header_contract.py
ruff check app/brain/page_header --no-cache
```

## What could break if changed

- Removing escaping can allow user-created class names to inject markup.
- Broad CSS selectors can change unrelated page text.
- Adding width or top padding here can fight `page_layout` and `topbar`.
- Removing the injected renderer seam can force testable pages to hand-roll
  their own header HTML.

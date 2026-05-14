# `app/brain/page_layout` — shared page rail helper

Defines Surf's authenticated-page content rail. It is not a renderer; it only
provides a scoped CSS rule and a small `st.container(...)` convenience wrapper.

## Purpose

- Lock the shared content width to `880px`, anchored to the Take Mock card rail.
- Lock authenticated page horizontal padding to `32px`.
- Keep top offset ownership with `app.brain.topbar`; this helper must not add
  top padding.
- Give page renderers one reusable ruler for cards, forms, headers, and chart
  panels.

## Inputs / outputs

| Function / constant | Purpose |
|---|---|
| `SURF_CONTENT_MAX_WIDTH_PX = 880` | Shared authenticated page rail width |
| `SURF_AUTH_PAGE_X_PADDING_PX = 32` | Shared horizontal page padding |
| `SURF_TOPBAR_OWNS_TOP_PADDING = True` | Contract flag showing topbar owns top offset |
| `D02_ALIGNMENT_SURFACES` | Named page surfaces that should use or match the shared rail |
| `build_page_rail_css(rail_key)` | Returns scoped CSS for one keyed rail |
| `render_page_rail_styles(rail_key)` | Injects the CSS in Streamlit |
| `page_rail(rail_key)` | Injects CSS and returns `st.container(key=rail_key)` |

## Data flow

The helper receives only a Streamlit container key. It reads no DB rows, no
session state, no API keys, no Anthropic state, and no route state.

## Connected code and tools

- Page renderers wrap authenticated content with `page_rail(...)` or inject
  `build_page_rail_css(...)` through their renderer seam.
- `app.brain.topbar` imports the width and padding constants so topbar actions
  align with page content.
- `app.brain.page_header` expects callers to render it inside this rail.

## Code walkthrough

### Constants

`SURF_CONTENT_MAX_WIDTH_PX`, `SURF_AUTH_PAGE_X_PADDING_PX`, and
`SURF_TOPBAR_OWNS_TOP_PADDING` are readable contract values for tests and page
renderers. `D02_ALIGNMENT_SURFACES` names the surfaces that should align on the
same invisible rail.

### `build_page_rail_css(...)`

Validates that the key is non-empty, then returns CSS scoped to
`.st-key-<rail_key>`. The outer keyed container gets horizontal and bottom
padding; the direct Streamlit vertical block is centered at `max-width: 880px`.
The CSS intentionally contains no top padding.

### `render_page_rail_styles(...)`

Imports Streamlit lazily and injects the CSS via `st.html(...)`.

### `page_rail(...)`

A thin convenience helper: inject the styles, then return
`st.container(key=rail_key)` for use as a context manager.

## Testing notes

```bash
python -m pytest -q tests/test_page_layout_contract.py
ruff check app/brain/page_layout --no-cache
```

## What could break if changed

- Changing the width or padding can make authenticated pages and topbar actions
  drift out of alignment.
- Adding top padding here can double-count the fixed topbar offset.
- Targeting broad Streamlit selectors here can unexpectedly affect unrelated
  pages.

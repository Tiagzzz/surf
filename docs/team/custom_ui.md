# Custom UI Guide

Surf uses Streamlit widgets plus scoped CSS/HTML to reach the approved visual style. The goal is not to replace Streamlit; it is to wrap Streamlit carefully where the default widgets do not match the app identity.

## Visual language

- Paper-like white cards and stamped controls.
- JetBrains Mono for button labels and compact UI text.
- Fraunces-style display text where page identity needs a stronger headline.
- Full-width page shells with a centered content rail.
- Shared topbar for authenticated pages.

## Scoped CSS pattern

Most custom UI is scoped by Streamlit container keys. Example idea:

```python
with st.container(key="p2_add_class_form_card"):
    st.html("<div class='surf-p2-form-title'>Add Class</div>")
```

The CSS targets the keyed wrapper instead of the whole app. That keeps a button fix on My Classes from accidentally changing Review or Dashboard.

## Shared layout pieces

| Piece | Purpose |
|---|---|
| `app.brain.page_layout.page_rail(...)` | centers page content on the common width. |
| `app.brain.page_header.render_page_header(...)` | shared kicker/title/helper copy for standard pages. |
| `app.brain.topbar.render_topbar(...)` | fixed authenticated topbar with logo, breadcrumbs, Home, and Settings. |
| Page bucket styles | page-specific cards, buttons, upload zones, dialogs, and grids. |

## Current custom surfaces

- Class Hub has a red stamped `CUSTOM MOCK >` button directly under `DASHBOARD >`. It uses the same width/rhythm as the neighboring action buttons but a red accent fill so the personal-difficulty mock is easy to find.
- P5 Review can show a `Difficulty for you: X/100` flag/badge on review cards. The badge is the only visible personal-difficulty UI on P5.
- P5 intentionally does **not** show the six Claude metadata fields as a student-facing breakdown, and Dashboard intentionally does **not** show a fake ML widget.

## Button and upload guidance

- Visible button labels should use the intended mono font.
- Icon-only controls still need accessible help/labels.
- File upload controls must stay clickable; do not hide the native upload button unless the replacement remains accessible and tested.
- Destructive actions use a confirmation dialog before deleting local data.

## What can break

- Broad CSS selectors can affect unrelated pages.
- Streamlit markup can change between versions, so selectors based on `data-testid` need focused checks after upgrades.
- Using `st.html` for very large style blocks can behave differently from `st.markdown(..., unsafe_allow_html=True)`; existing page sidecars document the chosen path.

## External tools and functions

- Streamlit containers/buttons/dialogs/uploaders.
- `html.escape` for user-provided class or lecture text before custom HTML.
- Shared Surf helpers: `render_topbar`, `render_page_header`, `page_rail`.
- Local previews under `previews/` may be used by maintainers until final cleanup removes or excludes that scaffolding.

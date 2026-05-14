# `views/my_classes.py` — P2 My Classes page wrapper

This page wrapper is intentionally thin. It resolves the saved local user and then delegates all P2 My Classes rendering to `app.my_classes.class_list_render.render_my_classes_page(...)`.

## Page overview

`views/my_classes.py` is the authenticated entry point for the My Classes page. If a saved user is available, the wrapper renders the page with that user mapping. If no saved user is available, it sends the browser back to `views/signup.py` so the user can complete local setup first.

## Session-state and routing context

| Key or route | Owner | Purpose |
|---|---|---|
| `get_saved_user()` | `app.brain.session` | Reads the local saved-user/auth state without exposing the stored Anthropic key. |
| `views/signup.py` | Streamlit page route | Recovery route when no saved user exists. |
| `render_my_classes_page(user=...)` | `app.my_classes.class_list_render` | Draws the My Classes page, Add Class form, class cards, and class-delete dialog. |
| `selected_class_id` | `class_list_render.handle_open_class` | Set later when the user enters a class from a card; the wrapper does not write it directly. |

## On-screen elements

This wrapper does not draw visible components itself. The delegated renderer owns:

| Element | Source |
|---|---|
| Shared topbar and page header | `app.brain.topbar.render_topbar` and `app.brain.page_header.render_page_header`, called from `class_list_render`. |
| `ADD CLASS` form | `class_list_render._render_add_class_form`, which calls the class-creation service only after a factsheet file is present. |
| Class cards and stats | `class_list_render.build_class_card_view_models` using classes and stats from query helpers. |
| `ENTER CLASS >` navigation | `class_list_render.handle_open_class`, which sets `selected_class_id` and switches to `views/class_view.py`. |
| `DELETE CLASS` confirmation | `class_list_render._render_delete_dialog` plus `app.my_classes.class_delete.delete_class_after_confirmation`. |

## User interactions

1. Browser opens `views/my_classes.py`.
2. The wrapper calls `get_saved_user()`.
3. If no saved user exists, `st.switch_page("views/signup.py")` returns the user to setup.
4. If a user exists, the wrapper calls `render_my_classes_page(user=_user)`.
5. The renderer handles all later P2 actions: class creation, class-card navigation, stats display, and confirmation-gated deletion.

## Data sources and connected buckets

- `app.brain.session` supplies the saved local user.
- `app.my_classes.class_list_render` owns all P2 rendering and service dispatch.
- `app.my_classes.class_create` creates a class only after factsheet extraction and cleaning succeed.
- `app.my_classes.class_delete` guards destructive deletion behind explicit confirmation.
- `app.db.queries_classes`, `app.db.queries_dashboard`, and `app.db.queries_lectures` provide class rows and card stats through the renderer, not through this wrapper.

## Code walkthrough

### Module docstring

Explains that this is a P2 wrapper and that the real page logic lives in `app.my_classes.class_list_render`.

### Imports

```python
import streamlit as st

from app.brain.session import get_saved_user
from app.my_classes.class_list_render import render_my_classes_page
```

The wrapper imports only Streamlit routing, the saved-user helper, and the P2 renderer. It does not import database query helpers, factsheet cleaning, or delete services directly.

### Saved-user branch

```python
_user = get_saved_user()
if _user is None:
    st.switch_page("views/signup.py")
else:
    render_my_classes_page(user=_user)
```

The branch keeps the authentication boundary simple: unauthenticated users return to setup, and authenticated users enter the P2 renderer with their saved-user mapping. No key value is printed, logged, or passed outside the app bucket.

## Testing notes

- `tests/test_class_list_render.py::test_thin_view_wrapper` checks that the wrapper delegates correctly.
- P2 behavior is primarily covered through `tests/test_class_create.py`, `tests/test_class_delete.py`, `tests/test_class_list_render.py`, and query tests used by the card stats provider.
- Leak guards such as `tests/test_no_secrets_committed.py` and `tests/test_no_real_db.py` help ensure this page surface does not commit local DB content or keys.

## What could break if changed

- Bypassing `get_saved_user()` could render P2 for a user with no saved local setup.
- Importing query helpers or services into this wrapper would make it less clear which bucket owns P2 behavior.
- Routing unauthenticated users somewhere other than `views/signup.py` could strand first-time users.
- Passing anything other than the saved-user mapping into `render_my_classes_page` could break P2 ownership checks and class-card stats.

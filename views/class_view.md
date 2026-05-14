# `views/class_view.py` — Class Hub page wrapper

This page wrapper keeps route setup thin. It resolves the saved local user, reads the selected class id from Streamlit session state, and hands rendering to `app.class_.class_hub.render_class_hub_page(...)`.

## Route context

- **Route file:** `views/class_view.py`
- **Main renderer:** `app.class_.class_hub.render_class_hub_page`
- **Required session key:** `selected_class_id` when a class has been chosen from My Classes.
- **Unauthenticated recovery:** if no saved user exists, route to `views/signup.py`.
- **Missing-class recovery:** the renderer shows `Class not found` and `BACK TO MY CLASSES`.

## On-screen elements owned by the renderer

- Shared topbar and class-name page header.
- `DASHBOARD >` navigation.
- Lecture chooser grid and selected-lecture state.
- `ADD LECTURE` form with mandatory lecture title and PDF upload.
- Study Next rows and `>` practice launch buttons.
- `TAKE MOCK >` selected-lecture launch.
- Narrow `DELETE LECTURE` / `UNDO` flow with destructive confirmation.
- Attempt History toggle and review arrows after completed attempts exist.

## Data flow

```text
views/class_view.py
        │
        ├── get_saved_user()
        ├── st.session_state.get("selected_class_id")
        └── render_class_hub_page(user=_user, class_id=_class_id)
```

All lecture upload, generation, Study Next, mock launch, attempt history, dashboard routing, and safe deletion behavior lives in the class bucket.

## Code walkthrough

### Module docstring and imports
The wrapper documents its two responsibilities, imports Streamlit, imports the saved-user helper, and imports the Class Hub renderer.

### Saved-user gate
`get_saved_user()` reads the local signed-in user. If no user exists, the wrapper switches to signup and does not render class content.

### Selected-class handoff
When a user exists, the wrapper reads `selected_class_id` from session state and passes it to the renderer. The renderer owns stale/missing class recovery so the wrapper does not duplicate class lookup logic.

## Testing notes

```bash
python -m ruff check views/class_view.py --no-cache
python -m pytest -q tests/test_class_hub_render_contract.py
```

## What could break if changed

- Bypassing `get_saved_user()` would let unauthenticated sessions reach class data.
- Renaming `selected_class_id` would break the My Classes → Class Hub handoff and dashboard route.
- Moving Class Hub logic into the wrapper would make tests harder and duplicate renderer recovery behavior.

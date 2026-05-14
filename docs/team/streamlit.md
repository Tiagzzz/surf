# Streamlit Guide

Streamlit is the UI framework for Surf. It renders Python code as a browser app, rerunning the page script when users click buttons, submit forms, or change state.

## Entry point and pages

`streamlit_app.py` decides which page list to show:

```python
if is_authenticated():
    pages = [st.Page("views/my_classes.py", title="My Classes", default=True), ...]
else:
    pages = [st.Page("views/signup.py", title="Sign Up", default=True)]

st.navigation(pages).run()
```

This keeps routing centralized. The `views/` files are thin wrappers; the larger page behavior lives under `app/` buckets.

## Page wrappers

A typical wrapper checks whether setup exists, reads route state, and delegates:

```python
if not is_authenticated():
    st.switch_page("views/signup.py")

class_id = st.session_state.get("selected_class_id")
render_class_hub(class_id=class_id)
```

That pattern keeps app behavior in reusable functions and keeps Streamlit pages easy to scan.

## Session state

`st.session_state` stores browser-session choices such as:

- selected class id;
- selected lecture ids for a mock;
- Custom Mock launch state after the red `CUSTOM MOCK >` button chooses the top personal-difficulty questions;
- current attempt id;
- open/closed form flags;
- in-progress answers before final submit.

Draft mock answers are session-only until final submit. Final submit writes attempts and answer rows to SQLite in one transaction.

## UI primitives used by Surf

- `st.Page` and `st.navigation` for multipage routing.
- `st.switch_page` for page-to-page actions.
- `st.session_state` for session choices.
- `st.container`, `st.columns`, and forms/dialogs for layout.
- `st.html` and `st.markdown(..., unsafe_allow_html=True)` for scoped custom UI where native widgets cannot match the design.
- `st.dialog` for destructive confirmation flows.
- `st.fragment(run_every=...)` where timer-style refresh behavior is feasible.

## Current Phase 7/7.1 surfaces

- Class Hub renders `DASHBOARD >` and then the red `CUSTOM MOCK >` button. Custom Mock uses the existing P4 mock flow; it does not create a separate attempt type.
- Review cards can render a `Difficulty for you: X/100` badge. P5 recalculates that score when the review screen opens or refreshes.
- The hidden scoring inputs are not displayed as a student-facing six-feature breakdown.
- Dashboard remains real-data-only. It can chart stored attempt performance, but it must not add fake ML widgets or placeholder analytics.

## External functions to know

- `app.brain.session.is_authenticated()` gates signup vs app pages.
- `app.brain.topbar.render_topbar(...)` renders authenticated navigation chrome.
- `app.brain.page_header.render_page_header(...)` renders shared page headers.
- `app.brain.page_layout.page_rail(...)` centers page content on the shared rail.

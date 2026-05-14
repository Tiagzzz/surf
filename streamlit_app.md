# `streamlit_app.py` — Streamlit entry point and router

This file is the app entry point. It decides whether the user should see Sign Up or the authenticated app pages, sends a fresh signed-in browser session to My Classes, then asks Streamlit to run the selected page.

## What this file owns

- One saved-user check through `app.brain.session.is_authenticated()`.
- The Streamlit page list for the unauthenticated route.
- The Streamlit page list for the authenticated app shell.
- The one-time signed-in reload redirect to My Classes.
- The final `st.navigation(pages).run()` call.

It does not render page content, open the live database at import time, validate API keys, calculate dashboard metrics, or run ML code.

## Route list

| State | Page file | Sidebar title | Default |
|---|---|---|---|
| Not signed in | `views/signup.py` | Sign Up | Yes |
| Signed in | `views/my_classes.py` | My Classes | Yes |
| Signed in | `views/class_view.py` | Class | No |
| Signed in | `views/take_mock_exam.py` | Take Mock Exam | No |
| Signed in | `views/review_mock_exam.py` | Review Mock Exam | No |
| Signed in | `views/dashboard.py` | Dashboard | No |
| Signed in | `views/settings.py` | Settings | No |

## Why the auth check queries saved user state

A real signed-in Surf session means the local `users` table contains a row with a non-blank Anthropic key. The entry point asks `is_authenticated()` for that answer instead of checking whether the SQLite file exists. A file can exist before setup is complete, so file-existence alone would send some first-time users to the wrong page.

Importing the session helper does not create the live DB by itself. Database work happens later through the app's lazy connection layer when a query helper is actually called.

## Why routes live in `views/`, not `pages/`

Streamlit can auto-discover a top-level `pages/` folder. Surf does not use that folder because this file already controls navigation with `st.navigation`. Keeping route files in `views/` prevents duplicate sidebar entries and keeps this router as the single source of truth.

## Connected files

| File or bucket | Relationship |
|---|---|
| `app/brain/session/__init__.py` | Owns `is_authenticated()`. |
| `app/db/connection.py` | Provides lazy SQLite access used by session queries. |
| `app/db/queries_users/__init__.py` | Checks whether a saved user with a key exists. |
| `views/signup.py` | Unauthenticated page. |
| `views/my_classes.py` | Authenticated default page. |
| `views/class_view.py` | Class Hub route. |
| `views/take_mock_exam.py` | Mock/practice attempt route. |
| `views/review_mock_exam.py` | Review route. |
| `views/dashboard.py` | Dashboard route. |
| `views/settings.py` | Settings route. |

## Code walkthrough

### Router comments

```python
# Surf app entry point.
# The router shows Sign Up until a saved local user with a non-blank Anthropic key exists.
# Authenticated users get the six approved app pages through Streamlit navigation.
# Route files live in views/ so Streamlit's pages/ auto-discovery stays off.
```

The opening comments explain the whole file without changing runtime behavior. They are comments, not app copy, so users do not see them.

### Imports and reload constants

```python
import streamlit as st

from app.brain.session import is_authenticated

AUTHENTICATED_HOME_VIEW = "views/my_classes.py"
AUTHENTICATED_HOME_REDIRECT_KEY = "_surf_authenticated_home_redirect_done"
```

The entry point imports Streamlit and the one auth helper. It does not import page buckets, database query helpers, or ML modules. The constants name the signed-in home page and the private session flag used to avoid redirecting every in-app click.

### One-time authenticated home redirect helper

```python
def should_redirect_authenticated_session_home(session_state) -> bool:
    if session_state.get(AUTHENTICATED_HOME_REDIRECT_KEY):
        return False
    session_state[AUTHENTICATED_HOME_REDIRECT_KEY] = True
    return True
```

A browser reload starts a fresh Streamlit session. On that first signed-in run, the helper returns `True` and marks the redirect as done. Later in-app navigation in the same session keeps working normally, so clicking Settings, Dashboard, Class, or Review does not bounce back to My Classes.

### Authenticated page list

```python
if authenticated:
    pages = [
        st.Page(AUTHENTICATED_HOME_VIEW, title="My Classes", default=True),
        st.Page("views/class_view.py", title="Class"),
        st.Page("views/take_mock_exam.py", title="Take Mock Exam"),
        st.Page("views/review_mock_exam.py", title="Review Mock Exam"),
        st.Page("views/dashboard.py", title="Dashboard"),
        st.Page("views/settings.py", title="Settings"),
    ]
```

When setup is complete, the app exposes the six authenticated pages. My Classes is the default because it is the student's home base.

### Signup-only page list

```python
else:
    pages = [st.Page("views/signup.py", title="Sign Up", default=True)]
```

When setup is incomplete, Sign Up is the only route. This keeps the user from reaching class data or settings before a local user/key exists.

### Register navigation, redirect fresh signed-in sessions, then run

```python
navigation = st.navigation(pages)

if authenticated and should_redirect_authenticated_session_home(st.session_state):
    st.switch_page(AUTHENTICATED_HOME_VIEW)

navigation.run()
```

Streamlit first receives the allowed page list. If this is the first run of a signed-in browser session, the app switches to My Classes. Otherwise, Streamlit runs whichever allowed page is active.

## What could break if changed

- Replacing `is_authenticated()` with a file-existence check can route first-time users incorrectly.
- Adding a top-level `pages/` folder can duplicate sidebar entries.
- Removing the one-time redirect flag can trap signed-in users on Settings/Dashboard after browser reloads, or can overcorrect and bounce every in-app navigation back to My Classes.
- Reordering the authenticated list changes the first page the user sees after signup.
- Importing page buckets or ML code here can make startup slower and harder to test.

## Verification

```bash
python -m pytest tests/test_streamlit_app_router.py -q
python -m ruff check streamlit_app.py views tests/test_streamlit_app_router.py --no-cache
python -m compileall streamlit_app.py views app
python - <<'PY_INNER'
from pathlib import Path
text = Path("streamlit_app.py").read_text()
required = [
    'AUTHENTICATED_HOME_VIEW = "views/my_classes.py"',
    'st.Page(AUTHENTICATED_HOME_VIEW, title="My Classes", default=True)',
    'st.switch_page(AUTHENTICATED_HOME_VIEW)',
    'st.Page("views/class_view.py", title="Class")',
    'st.Page("views/take_mock_exam.py", title="Take Mock Exam")',
    'st.Page("views/review_mock_exam.py", title="Review Mock Exam")',
    'st.Page("views/dashboard.py", title="Dashboard")',
    'st.Page("views/settings.py", title="Settings")',
    'st.Page("views/signup.py", title="Sign Up", default=True)',
]
missing = [item for item in required if item not in text]
raise SystemExit(f"Missing router entries: {missing}" if missing else 0)
PY_INNER
```

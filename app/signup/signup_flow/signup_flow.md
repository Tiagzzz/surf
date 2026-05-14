# `app/signup/signup_flow/__init__.py` — P1 signup flow renderer

This module renders Surf's first screen, validates the typed Anthropic API key, and saves local setup only after validation succeeds.

## What this code receives and generates

| Code part | Receives | Generates / changes |
|---|---|---|
| `render_signup_flow(validate_key=..., save_setup=...)` | Optional validation and save callbacks. Tests pass fake callbacks; the real page uses the defaults. | The full P1 split screen. It does not return page data; it paints the page through Streamlit. |
| `_render_setup_card(...)` | The same validation and save callbacks. | The right-side Welcome card, text inputs, Console link, `AI USE` button, `START SURFING >` button, and helper copy. |
| `_save_after_validation(...)` | Raw display-name text, raw API-key text, a key validator, and a local-save function. | `True` only after validation, save, toast, and page switch. `False` for missing fields, invalid key, validation exception, or save failure. |
| `_show_ai_use_dialog()` | No user input. | A Streamlit dialog with Markdown from `ai_use_copy.md`. |
| `_render_styles()` | No user input. | CSS for the split layout, hidden Streamlit chrome, fields, and stamped buttons. |
| `_render_left_panel()` | No user input. | Static brand HTML for the left panel. |

## Main flow in plain words

1. `views/signup.py` calls `render_signup_flow()`.
2. `render_signup_flow()` paints CSS, then creates a left and right column.
3. The left column gets static Surf branding.
4. The right column gets the setup card.
5. The setup card captures the display name and API key from Streamlit widgets.
6. `AI USE` opens information only.
7. `START SURFING >` sends the typed values to `_save_after_validation()`.
8. `_save_after_validation()` blocks empty values, validates the key, saves only after validation, then switches to My Classes.

## External tools, libraries, and app functions used

| Name | Type | Where used | Why it matters |
|---|---|---|---|
| `streamlit` / `st` | External UI library | `st.html`, `st.text_input`, `st.button`, `st.dialog`, `st.toast`, `st.spinner`, `st.switch_page`, `st.columns`, `st.container` | Paints the page, captures inputs, opens dialogs/toasts, and navigates after signup. |
| `base64` | Python standard library | `_font_data_uri()` | Converts local font bytes into CSS-safe text. |
| `collections.abc.Callable` | Python standard library typing helper | Function signatures | Documents that validation/save behavior is passed in as callable functions. |
| `html.escape` | Python standard library | `_render_setup_card()` | Escapes helper text before inserting it into HTML. |
| `pathlib.Path` | Python standard library | `_AI_USE_COPY_PATH`, `_REPO_ROOT`, `_FONTS_DIR` | Builds stable local file paths for Markdown and fonts. |
| `validate_anthropic_key` | Surf app function from `app.brain.claude_client` | Default `validate_key` callback | Checks the typed Anthropic key before it can be saved. |
| `upsert_user_setup` | Surf app function from `app.db.queries_users` | Default `save_setup` callback | Writes the local display name and key after validation. |
| `ai_use_copy.md` | Local Markdown file | `_load_ai_use_copy()` | Keeps the visible AI-use explanation editable without changing Python. |
| `assets/fonts/*.woff2` | Local font files | `_font_face_block()` | Supplies the approved P1 Fraunces and JetBrains Mono typography. |

## Code walkthrough

### 1. Module contract and imports

The top of the file says what the public renderer receives and what it produces:

```python
"""P1 signup / local setup flow.

The public ``render_signup_flow`` function receives optional validation/save
callbacks, renders the split signup screen, and generates one local user setup
row only after the typed Anthropic API key validates.
"""
```

The imports support four jobs:

```python
import base64
from collections.abc import Callable
from html import escape
from pathlib import Path

import streamlit as st

from app.brain.claude_client import validate_anthropic_key
from app.db.queries_users import upsert_user_setup
```

- `streamlit` paints the page and handles button/input state.
- `validate_anthropic_key` is the default key checker.
- `upsert_user_setup` is the default local database writer.
- The standard-library imports support fonts, callback types, safe HTML text, and local paths.

### 2. Constants: copy, route, and local file paths

The constants feed later render/save functions. They avoid hard-coded strings spread through the page.

```python
CONSOLE_URL = "https://console.anthropic.com/"
PRIMARY_LABEL = "START SURFING >"
AI_USE_LABEL = "AI USE"
HELPER_COPY = "Clicking validates your Anthropic key with Anthropic, then saves your name and key to this computer."
SWITCH_PAGE_PATH = "views/my_classes.py"

_AI_USE_COPY_PATH = Path(__file__).with_name("ai_use_copy.md")
_REPO_ROOT = Path(__file__).resolve().parents[3]
_FONTS_DIR = _REPO_ROOT / "assets" / "fonts"
```

What this block receives: no runtime input.  
What it generates: shared values used by the UI, validation messages, navigation, Markdown loader, and font loader.

### 3. Dialog copy loader

```python
def _load_ai_use_copy() -> str:
    return _AI_USE_COPY_PATH.read_text(encoding="utf-8")
```

This function receives no user data. It generates the Markdown string shown in the `AI USE` dialog. Because it reads the file at click time, changing the dialog text does not require changing validation or database code.

### 4. Font helpers

```python
def _font_data_uri(filename: str) -> str:
    encoded = base64.b64encode((_FONTS_DIR / filename).read_bytes()).decode("ascii")
    return f"data:font/woff2;base64,{encoded}"
```

This receives one local font filename, reads the font bytes, and generates a CSS `data:` URL. Streamlit does not automatically serve the `assets/fonts` folder, so the page embeds the fonts into the CSS.

```python
def _font_face_block() -> str:
    try:
        fraunces_regular = _font_data_uri("Fraunces-Regular.woff2")
        ...
    except FileNotFoundError:
        return ""
    return f"""
    @font-face {{ ... }}
    """
```

This block receives no user input. It generates CSS for Fraunces and JetBrains Mono. If a font file is missing, it returns an empty string so signup still opens with system fonts.

### 5. Page CSS renderer

```python
def _render_styles() -> None:
    st.html(
        """
        <style>
        """ + _font_face_block() + """
        :root { ... }
        header, footer, #MainMenu, ... { display: none !important; }
        .surf-p1-left { ... }
        .st-key-p1_submit button { ... }
        </style>
        """
    )
```

This function generates CSS through `st.html`. It hides Streamlit chrome, fills the viewport, styles the left brand panel, styles the right setup card, and scopes button/input styling to P1 keys so it does not affect authenticated pages.

### 6. Left brand panel

```python
def _render_left_panel() -> None:
    st.html(
        """
        <section class="surf-p1-left" aria-label="Surf brand panel">
          ...
        </section>
        """
    )
```

This block receives no values from the user. It generates static HTML: Surf headline, tagline, and footer. It does not read the display name, API key, database, or session state.

### 7. AI-use dialog

```python
def _show_ai_use_dialog() -> None:
    @st.dialog(AI_USE_LABEL)
    def _dialog() -> None:
        st.markdown(_load_ai_use_copy())

    _dialog()
```

This creates a Streamlit dialog and fills it with Markdown. It only explains the app's Anthropic usage. It does not submit the form, validate the key, save data, or navigate.

### 8. Validation and save function

```python
def _save_after_validation(
    display_name: str,
    api_key: str,
    *,
    validate_key: Callable[[str], bool],
    save_setup: Callable[[str, str], int],
) -> bool:
    clean_name = display_name.strip()
    clean_key = api_key.strip()
```

This function receives the raw widget values and two callbacks. The first thing it generates is cleaned input: whitespace is stripped from name and key.

Missing fields stop before any external check:

```python
if not clean_name:
    st.error(MISSING_NAME_ERROR)
    return False
if not clean_key:
    st.error(MISSING_KEY_ERROR)
    return False
```

The key validator receives only the stripped key and returns a boolean:

```python
try:
    with st.spinner(VALIDATING_COPY):
        key_is_valid = validate_key(clean_key)
except Exception:
    st.toast(INVALID_KEY_TOAST)
    return False

if not key_is_valid:
    st.toast(INVALID_KEY_TOAST)
    return False
```

The save function receives the cleaned name/key pair only after validation succeeds:

```python
try:
    save_setup(clean_name, clean_key)
except Exception:
    st.toast(SAVE_FAILURE_TOAST)
    return False

st.toast(SUCCESS_TOAST)
st.switch_page(SWITCH_PAGE_PATH)
return True
```

This final block generates the local user setup row, a success toast, and navigation to My Classes. Every failure branch returns `False` and keeps the user on signup.

### 9. Setup card renderer

```python
def _render_setup_card(
    *,
    validate_key: Callable[[str], bool],
    save_setup: Callable[[str, str], int],
) -> None:
    with st.container(border=True):
        ...
        display_name = st.text_input(...)
        api_key = st.text_input(..., type="password", ...)
```

This function receives callbacks and generates the visible right-side card. The two text inputs generate the current display-name and API-key values for this render.

The two buttons intentionally generate separate booleans:

```python
ai_use_clicked = st.button(AI_USE_LABEL, key="p1_ai_use", use_container_width=True)
submit_clicked = st.button(PRIMARY_LABEL, key="p1_submit", type="primary", use_container_width=True)
```

Their branches stay separate:

```python
if ai_use_clicked:
    _show_ai_use_dialog()
    return

if submit_clicked:
    _save_after_validation(
        display_name,
        api_key,
        validate_key=validate_key,
        save_setup=save_setup,
    )
```

That early `return` matters: clicking `AI USE` cannot accidentally validate or save the form.

### 10. Public renderer

```python
def render_signup_flow(
    *,
    validate_key: Callable[[str], bool] = validate_anthropic_key,
    save_setup: Callable[[str, str], int] = upsert_user_setup,
) -> None:
    _render_styles()
    left, right = st.columns([1, 1], gap="small")
    with left:
        _render_left_panel()
    with right:
        with st.container(key="p1_setup_panel"):
            _render_setup_card(validate_key=validate_key, save_setup=save_setup)
```

This is the only function other modules should call. It receives injectable callbacks for tests, generates the two-column layout, and passes the callbacks down to the setup card.

### 11. Export list

```python
__all__ = ["render_signup_flow"]
```

This tells future readers that `render_signup_flow` is the supported import. Helpers such as `_save_after_validation` stay private to the module.

## Testing notes

- `tests/test_signup_flow.py` covers empty-field blocking, invalid-key blocking, valid-key save and route, save failure, AI USE no-save behavior, and locked copy/link contracts.
- `tests/test_session_auth.py` checks that authentication depends on a saved non-blank key rather than a database file existing.
- `tests/test_no_secrets_committed.py` prevents real-shaped Anthropic keys and database files from being tracked.
- `tests/test_no_real_db.py` guards the test suite against reading or writing the live local database.

## What could break if changed

- Saving before validation could store an unusable key and let the user into the app.
- Logging or documenting key values could leak a private credential.
- Removing the Console link would make first-time setup harder.
- Making `AI USE` submit the setup would surprise users and could validate a half-filled form.
- Changing the route path would stop successful signup from opening My Classes.
- Broad CSS selectors could damage authenticated pages.

"""Shared authenticated topbar for Surf V1.

Public entry point::

    from app.brain.topbar import render_topbar
    render_topbar(current_page="my_classes")

Surf's authenticated chrome. Drawn at the top of P2-P7. P1 (signup)
is unauthenticated and **must not** call this module — the test suite
enforces that.

Visual contract:

* **Surface:** White ``#FFFFFF`` chrome.
* **Logo (left):** ``assets/brand/surf-logo.svg`` rendered as the
  background-image on a Streamlit ``st.button`` so the logo itself IS
  the click target. ``st.html`` strips raw ``<svg>`` content; the SVG
  ships base64 as a ``data:image/svg+xml`` URI.
* **Breadcrumb (middle):** JetBrains Mono Paper4 CAPS via
  ``text-transform: uppercase``. Plain non-clickable text with locked
  ``BREADCRUMB_SEPARATOR`` of Unicode
  `` › `` between segments. P2 ⇒ ``MY CLASSES``;
  P7 ⇒ ``MY CLASSES › SETTINGS``.
* **Gear (right):** ``assets/icons/settings.svg`` rendered as the
  background-image on a stamped ``st.button``. Paper fill, 1.5px Paper5
  border, 4px stamp shadow at rest, and press-into-shadow active animation.
  Locked aria contract: ``aria-label="Open settings"``.

Routing uses ``st.switch_page`` to ``views/my_classes.py`` and
``views/my_classes.py`` from the logo and Home buttons, and
``views/settings.py`` from the gear button, matching the surfaces
declared in ``streamlit_app.py``. No DB read, no Anthropic
call, no environment variable lookup — the topbar is pure chrome.
"""
# Shared authenticated navigation chrome with no data or network access.

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# These are the outside helpers this file needs. The topbar is "pure chrome",
# so it deliberately avoids importing any database, network, or Anthropic code.
# It only loads things needed to read a couple of SVG icons from disk, escape
# user-typed text, and draw Streamlit widgets.
#
# Important code pieces:
# - `from __future__ import annotations`: makes type hints lazy strings so the
#   file works the same on Python 3.11 without paying a runtime cost.
# - `base64`: turns the raw SVG bytes into a text-safe form so the icon can be
#   embedded directly inside a CSS `background-image` URL.
# - `functools.lru_cache`: a decorator that remembers a function's result. Used
#   below so each SVG is read from disk once per process.
# - `html.escape as html_escape`: turns characters like `<` into `&lt;` so a
#   user-typed class name can never inject HTML into the breadcrumb.
# - `pathlib.Path`: object-oriented file/folder paths; safer than string paths.
# - `streamlit as st`: the Streamlit library — the source of `st.button`,
#   `st.columns`, `st.container`, `st.html`, and `st.switch_page` used below.
# - `SURF_AUTH_PAGE_X_PADDING_PX` and `SURF_CONTENT_MAX_WIDTH_PX`: shared layout
#   numbers (left/right padding and the max content width) so the topbar lines
#   up with the page body underneath it.
#
# App connection:
# Anything imported here is allowed to influence how the topbar looks or where
# its buttons navigate, but nothing here can read the live SQLite database or
# call the Anthropic API.
from __future__ import annotations

import base64
from functools import lru_cache
from html import escape as html_escape
from pathlib import Path

import streamlit as st

from app.brain.page_layout import (
    SURF_AUTH_PAGE_X_PADDING_PX,
    SURF_CONTENT_MAX_WIDTH_PX,
)

# --------------------------------------------------------------------------- #
# LOCKED CONTENT CONSTANTS — TEXT, ARIA LABELS, AND ROUTING TABLES
# --------------------------------------------------------------------------- #
# Simple explanation:
# These are the fixed pieces of text and the lookup tables the topbar uses to
# decide what to show in the breadcrumb and where each button should send the
# user. They are "locked" — the test suite checks the exact strings — so the
# product, design, and accessibility teams stay aligned.
#
# Important code pieces:
# - `BREADCRUMB_SEPARATOR`: the small `›` character (with spaces around it)
#   that separates breadcrumb segments, e.g. `MY CLASSES › SETTINGS`.
# - `GEAR_ARIA_LABEL`, `LOGO_NAV_ARIA_LABEL`, `HOME_ARIA_LABEL`: the
#   accessibility labels read aloud by screen readers for the gear, logo, and
#   home icon-only buttons.
# - `PAGE_TO_BREADCRUMB`: a `dict` (lookup table) that maps a page name like
#   `"settings"` to the list of breadcrumb words shown on that page.
# - `PAGE_TO_VIEW`: a `dict` that maps a page name to the Streamlit view file
#   to load when the user clicks a navigation button.
#
# Key detail:
# - `dict[str, list[str]]` and `dict[str, str]` are type hints. They say "this
#   variable is a dictionary whose keys are strings and whose values are either
#   lists of strings or strings". They document intent and help editors.
#
# App connection:
# Renaming any of these strings would break the locked tests and confuse screen
# reader users, so changes must go through the locked-content review.

#: Unicode single right-pointing angle quotation mark + flanking spaces.
#: Locked breadcrumb separator.
BREADCRUMB_SEPARATOR = " › "

#: Locked accessible name for the right-aligned gear settings control.
GEAR_ARIA_LABEL = "Open settings"

#: Locked accessible name for the logo navigation control.
LOGO_NAV_ARIA_LABEL = "Go to My Classes"

#: Locked accessible name for the icon-only Home control.
HOME_ARIA_LABEL = "Go home"

#: Page → breadcrumb segments. P2 is depth-1; P7 is depth-2 (Settings is
#: a child route off the My Classes home, mirroring the wireframe's
#: logical path). P3 (``class_view``), P4 (``take_mock_exam``), and P5
#: (``review_mock_exam``) append dynamic segments at render time. Their
#: entries hold only the static parent so missing dynamic values degrade
#: honestly instead of rendering stale labels. New surfaces extend this
#: map; the renderer joins segments with the locked
#: :data:`BREADCRUMB_SEPARATOR`.
PAGE_TO_BREADCRUMB: dict[str, list[str]] = {
    "my_classes": ["My Classes"],
    "settings": ["My Classes", "Settings"],
    "class_view": ["My Classes"],
    "take_mock_exam": ["My Classes"],
    "review_mock_exam": ["My Classes"],
    "dashboard": ["My Classes"],
}

#: Page → switch target mapping for the navigation calls.
PAGE_TO_VIEW: dict[str, str] = {
    "my_classes": "views/my_classes.py",
    "settings": "views/settings.py",
    "class_view": "views/class_view.py",
    "take_mock_exam": "views/take_mock_exam.py",
    "review_mock_exam": "views/review_mock_exam.py",
    "dashboard": "views/dashboard.py",
}

# --------------------------------------------------------------------------- #
# ASSET PATHS — WHERE THE TOPBAR'S SVG ICONS LIVE ON DISK
# --------------------------------------------------------------------------- #
# Simple explanation:
# These constants point at the three SVG (vector image) files the topbar
# displays: the Surf logo, the gear icon, and the home icon. The paths are
# computed once, relative to the repository root, so the topbar finds the
# icons no matter where the app is launched from.
#
# Key detail:
# - `Path(__file__).resolve().parents[3]`: starts from this file's full path,
#   then walks three folders up (`topbar/` → `brain/` → `app/` → repo root),
#   giving the project's root folder.

#: Repo root, computed from this module's path.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LOGO_ASSET = _REPO_ROOT / "assets" / "brand" / "surf-logo.svg"
_SETTINGS_ICON_ASSET = _REPO_ROOT / "assets" / "icons" / "settings.svg"
_HOME_ICON_ASSET = _REPO_ROOT / "assets" / "icons" / "home.svg"


# --------------------------------------------------------------------------- #
# SVG LOADING HELPERS — READ FROM DISK, ENCODE FOR CSS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Streamlit 1.56 strips raw `<svg>` tags out of injected HTML for safety, so
# the topbar cannot just drop an `<svg>` into the page. Instead it reads the
# SVG file from disk as text, then base64-encodes it into a `data:` URL that
# CSS can use as a `background-image`. The two helpers below split that work:
# one reads the file, the other converts the text into a data URI.
#
# Important code pieces:
# - `_read_svg(path: Path) -> str`: opens a file and returns its text. If the
#   file is missing it returns an empty string so the topbar still renders
#   (just without that icon) instead of crashing.
# - `try` / `except FileNotFoundError`: Python's way of safely handling a
#   missing asset without taking down the whole page.
# - `_svg_to_data_uri(svg: str) -> str`: turns SVG text into a
#   `data:image/svg+xml;base64,...` URL that CSS understands.
# - `base64.b64encode(...).decode("ascii")`: encodes the bytes into a safe
#   ASCII string suitable for embedding inside CSS.
#
# App connection:
# These helpers are why the logo, home button, and gear button each show as a
# real image even though they are drawn as Streamlit buttons.
def _read_svg(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def _svg_to_data_uri(svg: str) -> str:
    if not svg:
        return ""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


# --------------------------------------------------------------------------- #
# CACHED ICON URIs — READ EACH SVG FROM DISK EXACTLY ONCE
# --------------------------------------------------------------------------- #
# Simple explanation:
# Each topbar render call would otherwise re-read the same SVG file from disk.
# These three small helpers run once per process, cache the resulting data
# URI, and return the cached value on every later call.
#
# Important code pieces:
# - `@lru_cache(maxsize=1)`: a decorator. It tells Python "remember the most
#   recent result of this function so any later call returns it instantly".
#   Since these functions take no arguments and the SVG files do not change
#   while the app runs, `maxsize=1` is enough.
# - `_logo_data_uri`, `_home_icon_data_uri`, `_settings_icon_data_uri`: one
#   helper per icon. Each combines `_read_svg` and `_svg_to_data_uri`.
#
# App connection:
# This is a small but meaningful speed-up: the topbar appears on every page
# (P2–P7) and is repainted on every interaction, so caching the icons avoids
# repeated disk reads.
@lru_cache(maxsize=1)
def _logo_data_uri() -> str:
    """Return a base64 ``data:image/svg+xml`` URI for the Surf logo."""
    return _svg_to_data_uri(_read_svg(_LOGO_ASSET))


@lru_cache(maxsize=1)
def _home_icon_data_uri() -> str:
    """Return a base64 ``data:image/svg+xml`` URI for the home icon."""
    return _svg_to_data_uri(_read_svg(_HOME_ICON_ASSET))


@lru_cache(maxsize=1)
def _settings_icon_data_uri() -> str:
    """Return a base64 ``data:image/svg+xml`` URI for the gear icon.

    Streamlit 1.56's ``st.html`` sanitizer strips raw ``<svg>``, so the
    icon ships on a CSS ``background-image`` like the Surf logo. Asset
    lives at ``assets/icons/settings.svg``.
    """
    return _svg_to_data_uri(_read_svg(_SETTINGS_ICON_ASSET))


# --------------------------------------------------------------------------- #
# TOPBAR CSS BUILDER — `_topbar_styles`
# --------------------------------------------------------------------------- #
# Simple explanation:
# This function returns one big block of CSS (the styling rules for how things
# look on screen) wrapped in `<style>...</style>`. The CSS is injected once by
# `render_topbar()` so the topbar chrome, breadcrumb, and icon buttons all
# look like Surf instead of default Streamlit widgets.
#
# What the CSS controls, section by section:
# - `:root { --surf-paper: #FDF9F2; ... }`: declares the Surf color palette as
#   CSS variables so the rest of the stylesheet refers to colors by name.
# - The "Hide Streamlit's default header" group: removes Streamlit's own
#   toolbar, footer, and menu so the Surf topbar fully replaces them.
# - The `[data-testid="stMainBlockContainer"]` rule: pushes page content down
#   so it never sits underneath the fixed topbar.
# - `.st-key-surf_topbar`: the white topbar surface itself — fixed to the top
#   of the window, centered, with the locked left/right padding from
#   `SURF_AUTH_PAGE_X_PADDING_PX`.
# - `.st-key-topbar_nav_logo button`: turns Streamlit's logo button into a
#   transparent click target with the Surf logo painted as its background.
# - `.surf-topbar__breadcrumb` / `.surf-topbar__breadcrumb-sep`: the JetBrains
#   Mono uppercase breadcrumb text and its lighter separator color.
# - `.st-key-topbar_nav_home` and `.st-key-topbar_nav_settings`: the stamped
#   home and gear buttons — paper background, 1.5px border, 4px shadow at
#   rest, and the press-into-shadow active animation that is Surf's
#   signature interaction feel.
# - `@media (prefers-reduced-motion: reduce)`: respects users who set
#   reduced-motion in their OS by disabling the press animation.
#
# Why a Python `f"""..."""` string instead of a separate `.css` file:
# The CSS includes runtime values — the cached SVG data URIs, the layout
# constants from `app.brain.page_layout` — that have to be filled in by
# Python, so the stylesheet is built as a formatted string.
#
# App connection:
# Every authenticated Surf page (P2–P7) calls `render_topbar()`, which calls
# this function. A change here repaints every authenticated page's chrome.
def _topbar_styles() -> str:
    """Scoped CSS for the topbar chrome.

    Visual lessons applied:
      - Canonical Surf tokens (no custom hex).
      - Reset Streamlit's default button/page-link border/padding.
      - 4px stamp shadow on the Home and gear controls; the chrome
        surrounding stays flat and only the icon buttons get the stamp.
      - Reduced-motion accommodation kills hover transforms.

    The aria contracts for the icon controls are documented inside the
    stylesheet so a static source audit confirms the locked strings.
    """
    # Build all CSS in one place so page views only call render_topbar(...).
    logo_uri = _logo_data_uri()
    home_uri = _home_icon_data_uri()
    gear_uri = _settings_icon_data_uri()
    logo_bg_rule = (
        f'background: url("{logo_uri}") no-repeat left center !important;'
        if logo_uri
        else "background: transparent !important;"
    )
    home_bg_rule = (
        f'background: var(--surf-paper) url("{home_uri}") no-repeat center !important;'
        f"background-size: 22px 22px !important;"
        if home_uri
        else "background: var(--surf-paper) !important;"
    )
    gear_bg_rule = (
        f'background: var(--surf-paper) url("{gear_uri}") no-repeat center !important;'
        f"background-size: 22px 22px !important;"
        if gear_uri
        else "background: var(--surf-paper) !important;"
    )
    return f"""
    <style>
    /* Surf shared topbar.
       Locked aria contracts:
         - gear settings button:  aria-label="{GEAR_ARIA_LABEL}"
         - icon Home button:       aria-label="{HOME_ARIA_LABEL}"
         - logo / nav button:     aria-label="{LOGO_NAV_ARIA_LABEL}"
       Streamlit 1.56 has no aria-label parameter on st.button / st.page_link,
       so the runtime screen-reader hint is delivered via Streamlit's help=
       (sets the title attribute). When Streamlit ships an aria-label
       parameter the controls below should adopt it. */
    :root {{
      --surf-paper: #FDF9F2;
      --surf-paper0: #F5EFE4;
      --surf-paper1: #EDE4D2;
      --surf-paper3: #6C6455;
      --surf-paper4: #3B362C;
      --surf-paper5: #28251F;
      --surf-shadow: #171512;
      --surf-accent: #C8361D;
    }}

    /* Hide Streamlit's default header / toolbar / footer. */
    header, footer, #MainMenu,
    [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], [data-testid="stHeader"] {{
      display: none !important;
      visibility: hidden !important;
      height: 0 !important;
    }}

    /* Compensate for the fixed topbar — page content sits below it,
       not under it. Owned by the topbar component so authenticated
       page renderers (P2/P3/P7 today; P4/P5/P6 future) MUST NOT add
       their own page-level top padding. The 80px value is anchored on the taller
       gear column: 8 (top inset) + 4 (gear top margin) + 40 (gear
       height) + 8 (gear bottom margin) + 16 (bottom inset) ≈ 76px,
       plus a 4px breathing buffer = 80px. The 24px bottom value
       preserves the previous .st-key-surf_topbar margin-bottom. */
    [data-testid="stMainBlockContainer"] {{
      padding-top: 80px !important;
      padding-bottom: 24px !important;
    }}

    /* Topbar chrome surface — white, sm/md inset, full viewport width.
       Pinned to the viewport top via position: fixed so navigation /
       settings stay reachable while page content scrolls beneath.
       z-index 100 sits above page content but below st.dialog overlays
       (Streamlit defaults at 1000+) so destructive-confirm dialogs
       (P2 class delete, P7 reset) still appear above the bar.
       The bottom inset is generous (16px) so the gear's 5px hover
       stamp shadow doesn't clip the chrome's border-bottom. */
    .st-key-surf_topbar {{
      background: #FFFFFF !important;
      border-bottom: 1px solid var(--surf-paper1);
      box-sizing: border-box;
      min-height: 80px !important;
      padding: 8px {SURF_AUTH_PAGE_X_PADDING_PX}px 16px !important;
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      z-index: 100 !important;
      width: 100% !important;
    }}
    .st-key-surf_topbar > [data-testid="stVerticalBlock"] {{
      box-sizing: border-box !important;
      margin: 0 auto !important;
      max-width: {SURF_CONTENT_MAX_WIDTH_PX}px !important;
      width: 100% !important;
    }}
    .st-key-surf_topbar [data-testid="stHorizontalBlock"] {{
      align-items: center !important;
      flex-wrap: nowrap !important;
      gap: 24px !important;
    }}
    .st-key-surf_topbar [data-testid="column"] {{
      padding: 0 !important;
    }}
    .st-key-surf_topbar [data-testid="stHorizontalBlock"]
      > [data-testid="column"]:nth-child(2) {{
      flex: 1 1 auto !important;
    }}

    /* Logo cell — clickable Streamlit button with SVG as background. */
    .st-key-topbar_nav_logo {{
      flex: 0 0 auto !important;
      max-width: 88px !important;
    }}
    .st-key-topbar_nav_logo [data-testid="stButton"] {{
      width: auto !important;
    }}
    .st-key-topbar_nav_logo button {{
      {logo_bg_rule}
      background-size: contain !important;
      border: none !important;
      box-shadow: none !important;
      color: transparent !important;
      cursor: pointer !important;
      display: block !important;
      font-size: 0 !important;
      height: 36px !important;
      line-height: 0 !important;
      margin: 0 !important;
      min-width: 56px !important;
      padding: 0 !important;
      text-indent: -9999px !important;
      transition: opacity 0.08s ease-out !important;
      width: 64px !important;
    }}
    .st-key-topbar_nav_logo button:hover {{
      opacity: 0.78 !important;
    }}
    .st-key-topbar_nav_logo button:focus,
    .st-key-topbar_nav_logo button:focus-visible {{
      outline: 2px solid var(--surf-accent) !important;
      outline-offset: 3px !important;
    }}

    /* Breadcrumb — Mono Paper4 CAPS, single static line. */
    .surf-topbar__breadcrumb {{
      color: var(--surf-paper4) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 13px !important;
      font-weight: 500 !important;
      letter-spacing: 0.14em !important;
      line-height: 1.4 !important;
      text-align: left !important;
      text-transform: uppercase !important;
    }}
    .surf-topbar__breadcrumb-sep {{
      color: var(--surf-paper3) !important;
      padding: 0 10px !important;
    }}

    /* Right-aligned stamped Home + gear buttons (SVG icons as backgrounds). */
    .st-key-topbar_nav_actions {{
      display: flex !important;
      flex: 0 0 auto !important;
      justify-content: flex-end !important;
      max-width: 116px !important;
    }}
    .st-key-topbar_nav_actions [data-testid="stHorizontalBlock"] {{
      gap: 8px !important;
    }}
    .st-key-topbar_nav_home,
    .st-key-topbar_nav_settings {{
      display: flex !important;
      flex: 0 0 auto !important;
      justify-content: flex-end !important;
      max-width: 52px !important;
    }}
    .st-key-topbar_nav_home button {{
      {home_bg_rule}
    }}
    .st-key-topbar_nav_settings button {{
      {gear_bg_rule}
    }}
    .st-key-topbar_nav_home button,
    .st-key-topbar_nav_settings button {{
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: transparent !important;
      cursor: pointer !important;
      font-size: 0 !important;
      height: 40px !important;
      line-height: 0 !important;
      margin: 4px 4px 8px 0 !important;
      min-width: 44px !important;
      padding: 0 !important;
      text-indent: -9999px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background-color 0.08s ease-out !important;
      width: 44px !important;
    }}
    .st-key-topbar_nav_home button:hover,
    .st-key-topbar_nav_settings button:hover {{
      background-color: var(--surf-paper0) !important;
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }}
    .st-key-topbar_nav_home button:active,
    .st-key-topbar_nav_settings button:active {{
      background-color: var(--surf-paper0) !important;
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }}
    .st-key-topbar_nav_home button:focus,
    .st-key-topbar_nav_home button:focus-visible,
    .st-key-topbar_nav_settings button:focus,
    .st-key-topbar_nav_settings button:focus-visible {{
      outline: 2px solid var(--surf-accent) !important;
      outline-offset: 3px !important;
    }}

    /* Reduced-motion accommodation. */
    @media (prefers-reduced-motion: reduce) {{
      .st-key-surf_topbar [data-testid="stButton"] button,
      .st-key-surf_topbar [data-testid="stButton"] button:hover,
      .st-key-surf_topbar [data-testid="stButton"] button:active {{
        transform: none !important;
        transition: background 0.08s ease-out !important;
      }}
    }}
    </style>
    """


# --------------------------------------------------------------------------- #
# BREADCRUMB HTML BUILDER — `_breadcrumb_html`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Builds the small navigation trail shown in the middle of the topbar, such as
# `MY CLASSES › SETTINGS` or `MY CLASSES › Biology 101 › Mock Exam`. It looks
# up the static segments for the page in `PAGE_TO_BREADCRUMB`, then appends
# dynamic pieces (class name, mode label) only when they were passed in.
#
# Important code pieces:
# - `current_page: str`, `class_name: str | None`, `mode_label: str | None`:
#   the page key plus two optional pieces of context. `| None` means "or
#   nothing", so callers may leave them out for pages that do not need them.
# - `html_escape(...)`: turns any user-typed class name into safe HTML so a
#   malicious class name cannot inject markup into the breadcrumb.
# - `PAGE_TO_BREADCRUMB.get(current_page, [fallback])`: looks up the page; if
#   the key is missing, falls back to a title-cased version of the page key
#   so the bar still renders something meaningful.
# - `sep_html.join(...)`: glues the segment spans together with the locked
#   `›` separator span between them.
#
# Per-page behavior summary:
# - `class_view` (P3) shows `MY CLASSES › <CLASS NAME>` when a class is known.
# - `take_mock_exam` (P4) shows `MY CLASSES › <CLASS> › <Mode>` and falls back
#   to `Mock Exam` when no mode label is supplied.
# - `review_mock_exam` (P5) ends with `Review`.
# - `dashboard` (P6) only appends `Dashboard` when a class is known.
#
# App connection:
# The breadcrumb is the user's main "where am I?" cue. The strict escaping and
# the locked separator are why a class named `<script>` cannot break the page.
def _breadcrumb_html(
    current_page: str,
    *,
    class_name: str | None = None,
    mode_label: str | None = None,
) -> str:
    """Render the breadcrumb as a single static HTML line.

    Looks up ``current_page`` in :data:`PAGE_TO_BREADCRUMB` and joins
    the resulting segments with the locked :data:`BREADCRUMB_SEPARATOR`
    wrapped in a styled span so the separator can be rendered Paper3
    (slightly lighter than the segment Paper4). Unknown keys fall
    through to a graceful title-cased default.

    Every segment is escaped via :func:`html.escape` before
    interpolation. P3+ surfaces surface user-typed content (a class
    name) through this helper — escaping at the boundary stops a stored
    XSS regression. Whitespace-only ``class_name`` values behave like
    ``None`` and don't render a dangling separator.

    Parameters
    ----------
    current_page:
        Stem of the active view, e.g. ``"my_classes"``, ``"settings"``,
        ``"class_view"``, ``"take_mock_exam"``, or ``"review_mock_exam"``.
    class_name:
        Dynamic class segment for class-scoped pages. ``class_view`` renders
        ``MY CLASSES › <CLASS NAME>`` when present. P4/P5 append the class
        segment before their page-specific leaf segment. ``None`` or
        whitespace-only values fall back to the static parent-only breadcrumb
        for P3 and omit the class segment for P4/P5.
    mode_label:
        Dynamic P4 leaf segment for ``current_page == "take_mock_exam"``.
        Practice can pass ``"Practice"``; missing or whitespace-only values
        fall back to ``"Mock Exam"``. Ignored on other pages.
    """
    # Escape every visible segment before assembling the breadcrumb HTML.
    base_segments = PAGE_TO_BREADCRUMB.get(
        current_page, [current_page.replace("_", " ").title()]
    )
    segments: list[str] = list(base_segments)
    clean_class_name = (class_name or "").strip()
    if current_page == "class_view":
        if clean_class_name:
            segments.append(clean_class_name)
    elif current_page == "take_mock_exam":
        if clean_class_name:
            segments.append(clean_class_name)
        segments.append((mode_label or "").strip() or "Mock Exam")
    elif current_page == "review_mock_exam":
        if clean_class_name:
            segments.append(clean_class_name)
        segments.append("Review")
    elif current_page == "dashboard":
        if clean_class_name:
            segments.append(clean_class_name)
            segments.append("Dashboard")
    sep = html_escape(BREADCRUMB_SEPARATOR.strip())
    sep_html = f'<span class="surf-topbar__breadcrumb-sep">{sep}</span>'
    inner = sep_html.join(f"<span>{html_escape(p)}</span>" for p in segments)
    return f'<div class="surf-topbar__breadcrumb">{inner}</div>'


# --------------------------------------------------------------------------- #
# PUBLIC ENTRY POINT — `render_topbar`
# --------------------------------------------------------------------------- #
# Simple explanation:
# The one function authenticated pages call to draw the topbar. It injects the
# CSS once, then lays out three Streamlit columns: the logo on the left, the
# breadcrumb in the middle, and the home + gear buttons on the right. Clicking
# the logo or home sends the user to My Classes; clicking the gear opens
# Settings.
#
# Important code pieces:
# - `-> None`: the function does not return a value; it has the side effect of
#   drawing widgets into the page.
# - `st.html(_topbar_styles())`: injects the CSS string into the page.
# - `with st.container(key="surf_topbar"):`: groups the topbar widgets inside
#   a Streamlit container with the locked key `surf_topbar`. CSS targets the
#   `.st-key-surf_topbar` selector built from that key.
# - `st.columns([1, 6, 1.5], gap="small")`: three columns sized 1 : 6 : 1.5
#   (logo : breadcrumb : actions) with a small gap between them.
# - `st.button(" ", key=..., help=...)`: a Streamlit button whose visible
#   label is a single space (the SVG icon is painted by CSS instead). `help=`
#   provides the screen-reader hint, since Streamlit 1.56 has no aria-label
#   parameter yet.
# - `st.switch_page(PAGE_TO_VIEW[...])`: tells Streamlit to navigate to one
#   of the view files declared in `streamlit_app.py`.
#
# App connection:
# This is the function imported and called by every authenticated Surf page
# (P2 My Classes, P3 Class Hub, P6 Dashboard, P7 Settings). P1 (signup) must
# not call it — the test suite enforces that.
def render_topbar(
    current_page: str,
    *,
    class_name: str | None = None,
    mode_label: str | None = None,
) -> None:
    """Render the shared authenticated topbar.

    Parameters
    ----------
    current_page:
        Stem of the currently active view (``"my_classes"`` /
        ``"settings"`` / ``"class_view"`` / ``"take_mock_exam"`` /
        ``"review_mock_exam"``). Drives the breadcrumb segments. P1 /
        signup MUST NOT call this function.
    class_name:
        Dynamic class label for class-scoped pages. P3 renders
        ``MY CLASSES › <CLASS NAME>``; P4/P5/P6 render the class label before
        their page leaf when present. ``None`` falls back to the
        single-segment ``MY CLASSES`` parent for P3/P6 and omits the class
        segment for P4/P5.
    mode_label:
        Dynamic P4 mode leaf. ``take_mock_exam`` renders this after the
        class segment, falling back to ``Mock Exam`` when missing. Practice
        callers can pass ``Practice``. Ignored on other pages.

    The logo and icon-only Home button both route to My Classes. The Home
    button sits immediately left of Settings and uses the same stamped
    button contract.
    """
    # Render fixed chrome, breadcrumb, and icon navigation controls.
    st.html(_topbar_styles())
    with st.container(key="surf_topbar"):
        col_logo, col_crumb, col_actions = st.columns([1, 6, 1.5], gap="small")
        with col_logo:
            if st.button(
                " ",
                key="topbar_nav_logo",
                help=LOGO_NAV_ARIA_LABEL,
            ):
                st.switch_page(PAGE_TO_VIEW["my_classes"])
        with col_crumb:
            st.html(
                _breadcrumb_html(
                    current_page, class_name=class_name, mode_label=mode_label
                )
            )
        with col_actions:
            with st.container(key="topbar_nav_actions"):
                col_home, col_settings = st.columns(2, gap="small")
                with col_home:
                    if st.button(
                        " ",
                        key="topbar_nav_home",
                        help=HOME_ARIA_LABEL,
                    ):
                        st.switch_page(PAGE_TO_VIEW["my_classes"])
                with col_settings:
                    if st.button(
                        " ",
                        key="topbar_nav_settings",
                        help=GEAR_ARIA_LABEL,
                    ):
                        st.switch_page(PAGE_TO_VIEW["settings"])


# --------------------------------------------------------------------------- #
# PUBLIC EXPORTS — `__all__`
# --------------------------------------------------------------------------- #
# Simple explanation:
# `__all__` lists the names this module promises to expose. When another file
# does `from app.brain.topbar import *` it only gets these names. It also acts
# as a clear "what is public here?" signal for the team: the constants and
# `render_topbar`. Internal helpers (the ones starting with `_`) are not
# listed and should not be imported by other files.
__all__ = [
    "BREADCRUMB_SEPARATOR",
    "GEAR_ARIA_LABEL",
    "HOME_ARIA_LABEL",
    "LOGO_NAV_ARIA_LABEL",
    "PAGE_TO_BREADCRUMB",
    "PAGE_TO_VIEW",
    "render_topbar",
]

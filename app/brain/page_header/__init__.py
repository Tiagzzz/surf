"""Shared Surf authenticated-page header helper."""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS AND HEADER CSS CLASS CONSTANTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This module renders the big page header block (kicker word + italic
# title + helper sentence) shared by My Classes (P2), Class Hub (P3),
# Dashboard (P6), and Settings (P7). It only depends on `html.escape`
# (to keep user-typed text from injecting HTML) and `typing.Any`.
#
# Important code pieces:
# - `escape`: turns `<` into `&lt;` etc. when interpolating user-supplied
#   strings into the header markup.
# - `PAGE_HEADER_DEFAULT_KEY`: the Streamlit container key the CSS scopes
#   to, so the styles only affect this header instance.
# - `PAGE_HEADER_KICKER_CLASS` / `PAGE_HEADER_TITLE_CLASS` /
#   `PAGE_HEADER_HELPER_CLASS`: stable CSS class names referenced by both
#   the CSS builder and the HTML builder below.
from html import escape
from typing import Any

PAGE_HEADER_DEFAULT_KEY = "surf_page_header"
PAGE_HEADER_KICKER_CLASS = "surf-page-header-kicker"
PAGE_HEADER_TITLE_CLASS = "surf-page-header-title"
PAGE_HEADER_HELPER_CLASS = "surf-page-header-helper"


# --------------------------------------------------------------------------- #
# BUILD_PAGE_HEADER_CSS — SCOPED STYLES FOR ONE KEYED CONTAINER
# --------------------------------------------------------------------------- #
# Simple explanation:
# Returns the CSS string that styles the kicker (small caps line above
# the title), the italic Fraunces title, and the helper paragraph. The
# CSS is scoped via the `.st-key-<key>` selector that Streamlit emits for
# `st.container(key=...)`, so other widgets on the page do not inherit it.
#
# Key detail:
# - In Surf, page-level CSS must be injected via
#   `st.markdown(..., unsafe_allow_html=True)`, not `st.html(...)`. The
#   `_render_html` helper below picks the right Streamlit call.
def build_page_header_css(header_key: str = PAGE_HEADER_DEFAULT_KEY) -> str:
    """Return scoped CSS for one keyed Surf page-header container."""
    if not header_key:
        raise ValueError("header_key must be a non-empty Streamlit container key")
    return f"""
<style>
.st-key-{header_key} .surf-page-header {{
  box-sizing: border-box !important;
  margin: 0 0 24px !important;
  width: 100% !important;
}}
.st-key-{header_key} .{PAGE_HEADER_KICKER_CLASS} {{
  color: #3B362C !important;
  font-family: "JetBrains Mono", ui-monospace, monospace !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  letter-spacing: 0.16em !important;
  line-height: 1.2 !important;
  margin: 0 0 6px !important;
  text-transform: uppercase !important;
}}
.st-key-{header_key} .{PAGE_HEADER_TITLE_CLASS} {{
  color: #28251F !important;
  font-family: "Fraunces", Georgia, serif !important;
  font-size: 48px !important;
  font-style: italic !important;
  font-weight: 650 !important;
  letter-spacing: -0.035em !important;
  line-height: 1 !important;
  margin: 0 0 8px !important;
}}
.st-key-{header_key} .{PAGE_HEADER_HELPER_CLASS} {{
  color: #6C6455 !important;
  font-family: "Fraunces", Georgia, serif !important;
  font-size: 15px !important;
  font-weight: 400 !important;
  line-height: 1.5 !important;
  margin: 0 !important;
  max-width: 760px !important;
}}
</style>
""".strip()


# --------------------------------------------------------------------------- #
# BUILD_PAGE_HEADER_HTML — ESCAPED MARKUP FOR THE HEADER BLOCK
# --------------------------------------------------------------------------- #
# Simple explanation:
# Returns the actual HTML for the three-line header. Every visible string
# is passed through `escape(...)` so a class or page title that happens
# to contain `<` or `&` cannot inject markup or break the layout.
def build_page_header_html(*, kicker: str, title: str, helper: str) -> str:
    """Return escaped Surf page-header markup."""
    return (
        '<div class="surf-page-header" role="group" aria-label="Page header">'
        f'<div class="{PAGE_HEADER_KICKER_CLASS}">{escape(kicker)}</div>'
        f'<div class="{PAGE_HEADER_TITLE_CLASS}">{escape(title)}</div>'
        f'<div class="{PAGE_HEADER_HELPER_CLASS}">{escape(helper)}</div>'
        "</div>"
    )


# --------------------------------------------------------------------------- #
# _RENDER_HTML — PICK THE STREAMLIT RENDER CALL THAT ACTUALLY WORKS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Page-level CSS and HTML in Surf must be drawn with
# `st.markdown(..., unsafe_allow_html=True)` because `st.html` can
# silently strip large style blocks. This helper uses `getattr(...)` to
# prefer `markdown` when available and falls back to `st.html` otherwise
# (useful for testing with a fake `st_module`).
def _render_html(st_module: Any, body: str) -> None:
    """Render HTML through the most reliable Streamlit-compatible API."""
    markdown = getattr(st_module, "markdown", None)
    if callable(markdown):
        markdown(body, unsafe_allow_html=True)
        return
    st_module.html(body)


# --------------------------------------------------------------------------- #
# RENDER_PAGE_HEADER — PUBLIC ENTRY POINT FOR P2/P3/P6/P7 HEADERS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This is the function pages call to draw the shared header. It injects
# the scoped CSS, opens a keyed `st.container`, and renders the escaped
# header HTML inside it. The header is intentionally NOT used by P4
# (Take Mock) or P5 (Review) — those pages have their own chrome.
#
# Important code pieces:
# - `*` in the signature: forces every argument after it to be passed by
#   keyword, e.g. `render_page_header(kicker=..., title=..., helper=...)`.
# - `st_module: Any | None = None`: tests can inject a fake Streamlit;
#   production code lets it default to the real `import streamlit as st`.
def render_page_header(
    *,
    kicker: str,
    title: str,
    helper: str,
    key: str = PAGE_HEADER_DEFAULT_KEY,
    st_module: Any | None = None,
) -> None:
    """Render Surf's shared authenticated page-header pattern."""
    if st_module is None:
        import streamlit as st

        st_module = st

    _render_html(st_module, build_page_header_css(key))
    with st_module.container(key=key):
        _render_html(
            st_module,
            build_page_header_html(kicker=kicker, title=title, helper=helper),
        )


__all__ = [
    "PAGE_HEADER_DEFAULT_KEY",
    "PAGE_HEADER_HELPER_CLASS",
    "PAGE_HEADER_KICKER_CLASS",
    "PAGE_HEADER_TITLE_CLASS",
    "build_page_header_css",
    "build_page_header_html",
    "render_page_header",
]

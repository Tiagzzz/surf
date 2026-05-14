"""Shared Surf authenticated-page header helper."""
from __future__ import annotations

from html import escape
from typing import Any

PAGE_HEADER_DEFAULT_KEY = "surf_page_header"
PAGE_HEADER_KICKER_CLASS = "surf-page-header-kicker"
PAGE_HEADER_TITLE_CLASS = "surf-page-header-title"
PAGE_HEADER_HELPER_CLASS = "surf-page-header-helper"


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


def build_page_header_html(*, kicker: str, title: str, helper: str) -> str:
    """Return escaped Surf page-header markup."""
    return (
        '<div class="surf-page-header" role="group" aria-label="Page header">'
        f'<div class="{PAGE_HEADER_KICKER_CLASS}">{escape(kicker)}</div>'
        f'<div class="{PAGE_HEADER_TITLE_CLASS}">{escape(title)}</div>'
        f'<div class="{PAGE_HEADER_HELPER_CLASS}">{escape(helper)}</div>'
        "</div>"
    )


def _render_html(st_module: Any, body: str) -> None:
    """Render HTML through the most reliable Streamlit-compatible API."""
    markdown = getattr(st_module, "markdown", None)
    if callable(markdown):
        markdown(body, unsafe_allow_html=True)
        return
    st_module.html(body)


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

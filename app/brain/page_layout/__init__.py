"""Shared authenticated-page rail helpers for Surf UI."""
# Shared width and padding helpers for authenticated page content.
from __future__ import annotations

SURF_CONTENT_MAX_WIDTH_PX = 880
"""Shared content rail width anchored to the P4 Take Mock question card."""

SURF_AUTH_PAGE_X_PADDING_PX = 32
"""Authenticated page horizontal padding from the Surf design-system spacing lock."""

SURF_TOPBAR_OWNS_TOP_PADDING = True
"""Boundary flag: the fixed topbar owns authenticated page top offset."""

D02_ALIGNMENT_SURFACES = (
    "P2 My Classes wrappers/cards/forms",
    "P3 Class Hub wrappers/cards/forms",
    "P4 Take Mock attempt content",
    "P5 Review content",
    "P6 Dashboard wrappers/cards",
    "P7 Settings wrappers/cards",
    "Shared page headers",
    "Topbar inner content/actions",
)
"""Named authenticated surfaces that must share this rail or document evidence."""


def build_page_rail_css(
    rail_key: str,
    *,
    max_width_px: int = SURF_CONTENT_MAX_WIDTH_PX,
    x_padding_px: int = SURF_AUTH_PAGE_X_PADDING_PX,
) -> str:
    """Return scoped CSS for a keyed authenticated-page rail container.

    Use with ``st.container(key=rail_key)``. The helper intentionally does not
    add vertical offset because ``app.brain.topbar`` owns the fixed-topbar
    spacing on authenticated pages.
    """
    # Scope rail CSS by Streamlit key so pages can opt in without global bleed.
    if not rail_key:
        raise ValueError("rail_key must be a non-empty Streamlit container key")

    return f"""
<style>
.st-key-{rail_key} {{
  box-sizing: border-box;
  padding: 0 {x_padding_px}px 32px !important;
  width: 100% !important;
}}
.st-key-{rail_key} > [data-testid="stVerticalBlock"] {{
  box-sizing: border-box;
  margin: 0 auto !important;
  max-width: {max_width_px}px !important;
  width: 100% !important;
}}
</style>
""".strip()


def render_page_rail_styles(rail_key: str) -> None:
    """Inject the shared page-rail CSS for ``rail_key`` into Streamlit."""
    import streamlit as st

    st.html(build_page_rail_css(rail_key))


def page_rail(rail_key: str):
    """Return a keyed Streamlit container styled as Surf's shared page rail."""
    import streamlit as st

    render_page_rail_styles(rail_key)
    return st.container(key=rail_key)


__all__ = [
    "D02_ALIGNMENT_SURFACES",
    "SURF_AUTH_PAGE_X_PADDING_PX",
    "SURF_CONTENT_MAX_WIDTH_PX",
    "SURF_TOPBAR_OWNS_TOP_PADDING",
    "build_page_rail_css",
    "page_rail",
    "render_page_rail_styles",
]

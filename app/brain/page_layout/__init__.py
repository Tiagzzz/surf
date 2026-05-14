"""Shared authenticated-page rail helpers for Surf UI."""
# Shared width and padding helpers for authenticated page content.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# SHARED RAIL CONSTANTS — WIDTHS, PADDING, AND OWNERSHIP FLAGS
# --------------------------------------------------------------------------- #
# Simple explanation:
# These constants are the single source of truth for how wide the
# centered content column on every authenticated page is, how much
# horizontal padding it has, and the fact that the topbar (not each
# page) owns the top vertical offset. Touching them changes the rail
# everywhere at once.
#
# Important code pieces:
# - `SURF_CONTENT_MAX_WIDTH_PX = 880`: the locked content rail width,
#   anchored to the P4 Take Mock question card.
# - `SURF_AUTH_PAGE_X_PADDING_PX = 32`: left/right padding inside the
#   rail.
# - `SURF_TOPBAR_OWNS_TOP_PADDING = True`: a documentation flag —
#   authenticated pages must NOT add their own top padding because the
#   fixed topbar already reserves space below it.
# - `D02_ALIGNMENT_SURFACES`: a tuple listing every authenticated
#   surface that must share this rail. The design-system review uses it
#   to make sure no page silently drifts off the shared width.
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


# --------------------------------------------------------------------------- #
# BUILD_PAGE_RAIL_CSS — SCOPED RAIL STYLE FOR ONE STREAMLIT CONTAINER
# --------------------------------------------------------------------------- #
# Simple explanation:
# Returns a CSS `<style>` block that centers and constrains the content
# inside a Streamlit container with the given `rail_key`. Each page gets
# its own key so styles never bleed between pages.
#
# Important code pieces:
# - `.st-key-<rail_key>`: the CSS selector Streamlit emits when you pass
#   `key=rail_key` to `st.container(...)`.
# - `max-width: {max_width_px}px`: caps the content to the shared rail.
# - `margin: 0 auto`: centers the rail horizontally inside the page.
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


# --------------------------------------------------------------------------- #
# RENDER_PAGE_RAIL_STYLES / PAGE_RAIL — RAIL INJECTION HELPERS
# --------------------------------------------------------------------------- #
# Simple explanation:
# `render_page_rail_styles` just drops the rail CSS into the page.
# `page_rail` does both: it injects the CSS and returns a
# `st.container(key=rail_key)` that the page can use as a `with` block
# for everything that should sit inside the rail.
#
# Key detail:
# - `import streamlit as st` is done lazily inside the function so the
#   module stays cheap to import in pure unit tests.
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

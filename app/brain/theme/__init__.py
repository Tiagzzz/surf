"""Surf design system — public API.

Re-exports the 11 callables from `theme.py` so callers write::

    from app.brain.theme import inject_theme
    inject_theme()

instead of reaching into the module path.
"""

from .theme import (
    caption,
    chip,
    chips_row,
    empty_state_text,
    eyebrow,
    heading_h2,
    inject_theme,
    meta,
    score,
    stat_card,
    steps,
)

__all__ = [
    "inject_theme",
    "heading_h2",
    "eyebrow",
    "caption",
    "meta",
    "score",
    "chip",
    "chips_row",
    "steps",
    "stat_card",
    "empty_state_text",
]

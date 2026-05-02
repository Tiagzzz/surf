"""Difficulty-stars display (D-2.24, Figma node 4028:141).

Renders a 5-slot star display with `n` filled and `5 - n` empty, where
`n = clamp(round(score * 5), 1, 5)`. SVG bytes are read once at module
load and inlined into `st.html` — no `<img>` tags (DOM-ordering quirks
per CONTEXT D-2.24).

Phase 2 ships placeholder behavior at the call site: when
`difficulty_score IS NULL` the caller renders the chip with the dashed
border + "—" text instead of calling this function. When the Phase 4
ML model lands, this function lights up automatically.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

_ICONS_DIR = Path(__file__).resolve().parents[3] / "assets" / "icons"
_FILLED_SVG = (_ICONS_DIR / "star_filled.svg").read_text(encoding="utf-8")
_EMPTY_SVG = (_ICONS_DIR / "star_empty.svg").read_text(encoding="utf-8")


def difficulty_stars(score: float) -> None:
    """Render a 5-slot star display for the given difficulty score.

    Args:
        score: Float in [0.0, 1.0]. Values outside the range are clamped.

    Maps `score` to an integer level `n ∈ [1, 5]` via `round(score * 5)`
    clamped to the allowed range, then renders `n` filled stars followed
    by `5 - n` empty stars inside a single span (gap 1 px, matches the
    Figma chip's inter-star spacing).
    """
    n = max(1, min(5, round(score * 5)))
    inner = (_FILLED_SVG * n) + (_EMPTY_SVG * (5 - n))
    st.html(
        '<span style="display: inline-flex; gap: 1px; align-items: center;">'
        f'{inner}'
        '</span>'
    )

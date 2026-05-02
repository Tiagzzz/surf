"""Smoke tests for app/brain/theme/theme.py.

Asserts the public API is importable and that the embedded `_CSS`
contains the markers Plan 02-01 D-2.12..D-2.24 require:

  - `@font-face` (D-2.16, self-hosted fonts)
  - `--paper` (D-2.12 Paper ladder token)
  - `prefers-reduced-motion` (D-2.15 accessibility)
  - `st-key-mcq-opt` (D-2.20 rebuilt MCQ option scoping)
  - no `TBD` substring (the file shipped, no placeholders)
"""

from __future__ import annotations

import pathlib

_THEME_PATH = pathlib.Path(__file__).resolve().parent.parent / "app" / "brain" / "theme" / "theme.py"


def test_inject_theme_importable() -> None:
    from app.brain.theme import inject_theme
    assert callable(inject_theme)


def test_helpers_all_callable() -> None:
    from app.brain.theme import (
        caption,
        chip,
        chips_row,
        empty_state_text,
        eyebrow,
        meta,
        score,
        stat_card,
        steps,
    )
    for fn in [eyebrow, caption, meta, score, chip, chips_row, steps, stat_card, empty_state_text]:
        assert callable(fn), fn


def test_css_contains_required_markers() -> None:
    src = _THEME_PATH.read_text(encoding="utf-8")
    assert "@font-face" in src, "self-hosted fonts (D-2.16) missing"
    assert "--paper" in src, "Paper ladder token (D-2.12) missing"
    assert "prefers-reduced-motion" in src, "reduced-motion block (D-2.15) missing"
    assert "st-key-mcq-opt" in src, "MCQ option scoping (D-2.20) missing"


def test_css_no_tbd_placeholder() -> None:
    src = _THEME_PATH.read_text(encoding="utf-8")
    assert "TBD" not in src, "found TBD placeholder — file did not ship"


def test_css_no_google_fonts_import() -> None:
    """D-2.16 mandates self-hosted fonts; the Google Fonts @import is gone."""
    src = _THEME_PATH.read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in src, "Google Fonts @import still present"


def test_helpers_html_escape_user_text() -> None:
    """D-2.19 hardening: helpers must call html.escape on user-supplied text."""
    src = _THEME_PATH.read_text(encoding="utf-8")
    assert "html.escape" in src, "html.escape missing — XSS hardening incomplete"

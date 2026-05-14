"""P5 — Review Mock / Practice page renderer.

This page is read-only. It renders persisted attempt results with Surf's
Streamlit-connected custom UI: real Streamlit buttons for navigation, scoped
CSS for the Figma-like review surface, and escaped decorative HTML for result
cards and option/rationale rows.
"""
# Paints saved P5 results without recalculating or rewriting attempts.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Streamlit plus a handful of stdlib helpers, the shared topbar, the
# read-only attempt queries, the Phase 7 personal-difficulty scorer, and
# the pure helpers from `rationale_display`. Everything that could mutate
# the database is excluded — P5 is strictly a read-only review surface.
#
# Important code pieces:
# - `zoneinfo.ZoneInfo`: Python's standard timezone helper, used so the
#   "finished at" timestamp displays in Swiss local time regardless of
#   how it was stored.
# - `score_questions`: imported from `app.ml.personal_difficulty` and
#   called fresh on every render. The resulting difficulty number is
#   never written back to SQLite.
import base64
import json
from datetime import datetime, timezone
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from app.brain.topbar import render_topbar
from app.db.queries_attempts import (
    get_attempt_review_rows,
    get_attempt_summary,
    list_personal_difficulty_examples_for_class,
)
from app.db.queries_classes import get_class_by_id, get_class_pass_threshold
from app.ml.personal_difficulty import score_questions
from app.mock_review.rationale_display import (
    classify_option_state,
    format_question_type_chip_label,
    format_rationale_text,
    parse_review_row,
    result_stamp_for_attempt,
)

__all__ = ["render_review_mock_page"]

# --------------------------------------------------------------------------- #
# LOCKED COPY AND DIFFICULTY-EXPLAINER CONTENT
# --------------------------------------------------------------------------- #
# Simple explanation:
# Fixed strings the review page falls back on when an attempt row is
# missing a label, plus the multi-paragraph explainer the user sees when
# they expand "Understand your difficulty score". Keeping the copy as
# module constants lets the test suite assert the exact wording.
#
# Important code pieces:
# - `_DIFFICULTY_EXPLAINER_BODY`: the longer body shown inside the
#   collapsible explainer card.
# - `_DIFFICULTY_FEATURE_KEYS`: the difficulty_* columns the renderer
#   forwards into the scoring view passed to `score_questions(...)`.
_TYPE_UNAVAILABLE_COPY = "Type unavailable"
_RATIONALE_UNAVAILABLE_COPY = "Rationale unavailable."
_MISSED_LOCKED_COPY = "MISSED"
_LECTURE_UNAVAILABLE_COPY = "Lecture unavailable."
_PRACTICE_DISCLAIMER_COPY = "Practice does not count toward class average."
_DIFFICULTY_EXPLAINER_LABEL = "Understand your difficulty score"
_DIFFICULTY_EXPLAINER_OPEN_KEY = "p5_difficulty_explainer_open"
_DIFFICULTY_EXPLAINER_BODY = (
    "Your difficulty score tells you how hard a question really is, on a scale "
    "from 1 to 100.\n\n"
    "Lower numbers are gentler questions that most students get right. Higher "
    "numbers are the ones that catch people out, even after solid prep. A 20 "
    "is a warm-up. An 80 is the kind of question that decides grades.\n\n"
    "Surf builds the score from signals in the question itself, like how "
    "layered the wording is, how close the wrong answers look to the right one, "
    "and how much lecture material you need to hold in your head at once. As "
    "you answer more questions, your own track record feeds into the score too, "
    "so it gets sharper over time.\n\n"
    "Think of the number as a heads-up, not a verdict. Nailing a 75 is worth "
    "celebrating. Missing a 25 is worth a second look before the exam."
)
_SWISS_TZ = ZoneInfo("Europe/Zurich")
_DIFFICULTY_FEATURE_KEYS = (
    "difficulty_word_count",
    "difficulty_readability",
    "difficulty_distractor_similarity",
    "difficulty_conceptual_density",
    "difficulty_distractor_derivation",
    "difficulty_reasoning_steps",
    "difficulty_wording_complexity",
    "difficulty_wording_clarity_issue",
)


@lru_cache(maxsize=None)
def _font_data_uri(filename: str) -> str:
    path = Path(__file__).resolve().parents[3] / "assets" / "fonts" / filename
    data = path.read_bytes()
    return f"data:font/woff2;base64,{base64.b64encode(data).decode('ascii')}"


def _font_face_block() -> str:
    fraunces_regular = _font_data_uri("Fraunces-Regular.woff2")
    fraunces_semibold_italic = _font_data_uri("Fraunces-SemiBoldItalic.woff2")
    fraunces_black_italic = _font_data_uri("Fraunces-BlackItalic.woff2")
    mono_regular = _font_data_uri("JetBrainsMono-Regular.woff2")
    mono_medium = _font_data_uri("JetBrainsMono-Medium.woff2")
    return f"""
    @font-face {{
      font-family: "Fraunces";
      src: url({fraunces_regular!r}) format("woff2");
      font-weight: 400; font-style: normal; font-display: swap;
    }}
    @font-face {{
      font-family: "Fraunces";
      src: url({fraunces_semibold_italic!r}) format("woff2");
      font-weight: 600; font-style: italic; font-display: swap;
    }}
    @font-face {{
      font-family: "Fraunces";
      src: url({fraunces_black_italic!r}) format("woff2");
      font-weight: 900; font-style: italic; font-display: swap;
    }}
    @font-face {{
      font-family: "JetBrains Mono";
      src: url({mono_regular!r}) format("woff2");
      font-weight: 400; font-style: normal; font-display: swap;
    }}
    @font-face {{
      font-family: "JetBrains Mono";
      src: url({mono_medium!r}) format("woff2");
      font-weight: 500; font-style: normal; font-display: swap;
    }}
    """


# --------------------------------------------------------------------------- #
# PAGE CSS BUILDER — `_styles`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Returns one big block of scoped CSS as a Python string. Injected via
# `st.markdown(_styles(), unsafe_allow_html=True)` rather than `st.html(...)`
# because large style payloads have been observed to silently drop when
# passed to `st.html`. The CSS owns: hero band, summary card grid, the
# Phase 7 personal-difficulty flag silhouette pinned to each card's
# top-right edge (V-notch via `clip-path`, tier color via the
# `--flag-color` custom property), the per-option correct/wrong/missed
# styling, the rationale feedback row, and the two action buttons.
#
# Important code pieces:
# - `.surf-personal-difficulty-flag` and its `::before` / `::after`
#   pseudo-elements: paint the colored flag and a 4px offset shadow
#   silhouette without `filter: drop-shadow` (which has been unreliable
#   inside Streamlit's wrapper hierarchy).
# - `.surf-personal-difficulty-flag--ok` / `--warn` / `--risk`: tier
#   modifier classes corresponding to the low/medium/high score bands.
def _styles() -> str:
    return (
        "<style>\n"
        + _font_face_block()
        + """
    :root {
      --surf-paper: #FDF9F2;
      --surf-paper0: #F5EFE4;
      --surf-paper1: #EDE4D2;
      --surf-paper3: #6C6455;
      --surf-paper4: #3B362C;
      --surf-paper5: #28251F;
      --surf-shadow: #171512;
      --surf-accent: #C8361D;
      --surf-accent-deep: #9D2815;
      --surf-status-warn: #B5851F;
      --surf-status-ok: #1F6F4A;
      --surf-accent-wash: #F3C8BE;
      --surf-status-ok-wash: #A7CDB1;
      --surf-status-ok-soft: #D8E9D8;
    }
    .stApp { background: var(--surf-paper) !important; }
    .st-key-p5_review_mock_page [data-testid="stButton"] button {
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      letter-spacing: 0.14em !important;
      text-transform: uppercase !important;
    }
    .st-key-p5_review_mock_page {
      box-sizing: border-box;
      padding: 0 32px 32px !important;
    }
    .surf-p5-hero {
      align-items: center;
      background: var(--surf-paper1);
      border-bottom: 2px solid var(--surf-shadow);
      box-sizing: border-box;
      display: flex;
      justify-content: space-between;
      margin: 0 calc(50% - 50vw) 48px;
      min-height: 110px;
      padding: 10px max(32px, calc((100vw - 1280px) / 2 + 80px));
      width: 100vw;
    }
    .surf-p5-title,
    .surf-p5-grade-value {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 34px;
      font-style: italic;
      font-weight: 900;
      letter-spacing: -0.02em;
      line-height: 0.95;
      margin: 0 0 10px;
    }
    .surf-p5-grade-value { color: var(--surf-accent-deep); font-size: 64px; margin: 0; }
    .surf-p5-date,
    .surf-p5-grade-label {
      color: var(--surf-paper5);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.16em;
      margin: 0;
      text-transform: uppercase;
    }
    .surf-p5-date { font-size: 19px; font-weight: 500; }
    .st-key-p5_summary_card {
      background: var(--surf-paper) !important;
      border: 2px solid var(--surf-paper5) !important;
      border-radius: 4px !important;
      box-shadow: 8px 8px 0 var(--surf-shadow) !important;
      box-sizing: border-box;
      margin: 0 auto 42px !important;
      max-width: 720px !important;
      padding: 28px 34px !important;
      width: 100% !important;
    }
    .st-key-p5_difficulty_score_explainer {
      margin: 0 auto 18px !important;
      max-width: 880px !important;
      width: 100% !important;
    }
    .st-key-p5_difficulty_score_explainer button,
    .st-key-p5_difficulty_score_explainer [data-testid="stButton"] button,
    .st-key-p5_difficulty_score_explainer button * {
      align-items: center !important;
      background: transparent !important;
      border: 0 !important;
      box-shadow: none !important;
      color: var(--surf-paper4) !important;
      display: inline-flex !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 16px !important;
      font-style: italic !important;
      font-weight: 600 !important;
      height: auto !important;
      justify-content: flex-start !important;
      letter-spacing: 0 !important;
      line-height: 1.25 !important;
      margin: 0 !important;
      padding: 0 !important;
      text-align: left !important;
      text-transform: none !important;
      transition: color 0.08s ease-out !important;
      width: auto !important;
    }
    .st-key-p5_difficulty_score_explainer button:hover,
    .st-key-p5_difficulty_score_explainer button:hover * {
      background: transparent !important;
      box-shadow: none !important;
      color: var(--surf-accent) !important;
      transform: none !important;
      text-decoration: underline !important;
      text-underline-offset: 3px !important;
    }
    .st-key-p5_difficulty_score_explainer_card {
      background: var(--surf-paper0);
      border: 1.5px dashed var(--surf-paper3);
      border-radius: 4px;
      box-sizing: border-box;
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 15px;
      font-style: italic;
      line-height: 1.5;
      margin: -4px auto 32px;
      max-width: 880px;
      padding: 18px 20px;
      width: 100%;
    }
    .surf-p5-difficulty-explainer-body {
      margin: 0;
      white-space: pre-line;
    }
    .surf-p5-summary-grid {
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    .surf-p5-stat-label {
      color: var(--surf-paper4);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 10px;
      font-weight: 500;
      letter-spacing: 0.14em;
      margin: 0 0 6px;
      text-transform: uppercase;
    }
    .surf-p5-stat-value {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 28px;
      font-style: italic;
      font-weight: 600;
      line-height: 1.1;
      margin: 0;
    }
    .surf-p5-practice-note,
    .surf-p5-threshold {
      color: var(--surf-paper4);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      letter-spacing: 0.08em;
      margin: 16px 0 0;
      text-transform: uppercase;
    }
    [class*="st-key-p5_review_row_"] {
      background: var(--surf-paper) !important;
      border: 3px solid var(--surf-shadow) !important;
      border-radius: 8px !important;
      box-shadow: 7px 7px 0 var(--surf-shadow) !important;
      box-sizing: border-box;
      margin: 0 auto 48px !important;
      max-width: 880px !important;
      padding: 30px 32px 28px !important;
      position: relative !important;
      width: 100% !important;
    }
    .surf-question-type-chip {
      align-items: center;
      background: var(--surf-paper1);
      border: 3px solid var(--surf-shadow);
      border-radius: 8px;
      box-shadow: 4px 4px 0 var(--surf-shadow);
      color: var(--surf-accent-deep);
      display: inline-flex;
      font-family: "Fraunces", Georgia, serif;
      font-size: 18px;
      font-style: italic;
      font-weight: 900;
      height: 36px;
      justify-content: center;
      letter-spacing: -0.02em;
      margin: 0 0 22px;
      min-width: 220px;
      padding: 4px 18px 6px;
    }
    /* Phase 7: personal difficulty flag anchored to the top-right of
       every P5 review card. Vertical ribbon with stacked
       DIFFICULTY FOR YOU label and the italic-serif score; V-notch at
       the bottom via clip-path. The fill color is the score tier — see
       the three modifier classes below. Score is recalculated on every
       render and never persisted (Phase 7 D-16/D-17). */
    /* The parent has NO clip-path itself — it just provides the box,
       text content, and tier color via the `--flag-color` custom
       property. Two pseudo-elements paint the silhouette and the
       stamp shadow: ::before is the colored flag, ::after is the
       dark silhouette offset 4px 4px. Both use the same V-notch
       clip-path. Earlier attempts used `filter: drop-shadow` on the
       parent — that turned out unreliable inside Streamlit's wrapper
       hierarchy (some browsers apply the filter before the clip and
       the shadow disappears). */
    .surf-personal-difficulty-flag {
      position: absolute;
      top: 0;
      /* Flag sits right next to the card: its left edge is flush
         against the card's OUTER right border. The card has a 3px
         border, so `right: 0` puts a child at the padding-box right
         edge (= inner border edge). Push out by `width + 3px` so the
         flag's left edge touches the outer border edge cleanly. */
      right: -111px;
      width: 108px;
      height: 130px;
      /* Asymmetric padding: extra room on the right keeps the label
         and score off the notched right edge. */
      padding: 16px 26px 16px 10px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      gap: 8px;
      text-align: center;
      z-index: 2;
    }
    .surf-personal-difficulty-flag::before,
    .surf-personal-difficulty-flag::after {
      content: "";
      position: absolute;
      inset: 0;
      /* V-notch on the right side, pointing left into the flag. */
      clip-path: polygon(0 0, 100% 0, 78% 50%, 100% 100%, 0 100%);
    }
    /* Hard offset stamp silhouette. */
    .surf-personal-difficulty-flag::after {
      background: var(--surf-shadow);
      transform: translate(4px, 4px);
      z-index: -2;
    }
    /* Colored flag silhouette, sits on top of the shadow. */
    .surf-personal-difficulty-flag::before {
      background: var(--flag-color, var(--surf-status-ok));
      z-index: -1;
    }
    /* Ensure the text content paints above the silhouette pseudo-elements. */
    .surf-personal-difficulty-flag-label,
    .surf-personal-difficulty-flag-score {
      position: relative;
      z-index: 1;
    }
    .surf-personal-difficulty-flag-label {
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.14em;
      line-height: 1.15;
      margin: 0;
      text-transform: uppercase;
    }
    .surf-personal-difficulty-flag-score {
      font-family: "Fraunces", Georgia, serif;
      font-size: 44px;
      font-style: italic;
      font-weight: 700;
      line-height: 1;
      margin: 0;
    }
    /* Tier — green when score < 33 (low personal risk). */
    .surf-personal-difficulty-flag--ok {
      --flag-color: var(--surf-status-ok);
      color: var(--surf-paper);
    }
    /* Tier — yellow when 33 ≤ score ≤ 66 (medium personal risk). */
    .surf-personal-difficulty-flag--warn {
      --flag-color: var(--surf-status-warn);
      color: var(--surf-paper);
    }
    /* Tier — red when score > 66 (high personal risk). */
    .surf-personal-difficulty-flag--risk {
      --flag-color: var(--surf-accent-deep);
      color: var(--surf-paper);
    }
    /* No right-padding reservation is needed any more — the flag now
       hangs off the card's right edge, so LO and question text wrap to
       the natural card width. */
    .surf-p5-lo {
      color: #1A1814;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.22em;
      margin: 0 0 22px;
      text-transform: uppercase;
    }
    .surf-p5-question-text {
      color: #1A1814;
      font-family: "Fraunces", Georgia, serif;
      font-size: 27px;
      font-style: italic;
      font-weight: 600;
      letter-spacing: -0.01em;
      line-height: 1.08;
      margin: 0 0 28px;
    }
    .surf-p5-result-stamp {
      color: var(--surf-paper4);
      display: inline-block;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.16em;
      margin: 0 0 12px;
      text-transform: uppercase;
    }
    .surf-p5-result-stamp.correct { color: var(--surf-status-ok); }
    .surf-p5-result-stamp.wrong { color: var(--surf-accent-deep); }
    .surf-p5-result-stamp.skipped { color: var(--surf-paper4); }
    [class*="st-key-p5_review_option_"] {
      border: 2px solid var(--surf-shadow) !important;
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      box-sizing: border-box;
      margin: 0 0 10px !important;
      padding: 0 !important;
      width: 100% !important;
    }
    [class*="st-key-p5_review_option_correct_"] {
      background: var(--surf-status-ok-wash) !important;
      border-color: var(--surf-shadow) !important;
    }
    [class*="st-key-p5_review_option_wrong_"] {
      background: #E8A798 !important;
      border-color: var(--surf-shadow) !important;
    }
    [class*="st-key-p5_review_option_missed_"] {
      background: #E8A798 !important;
      border-color: var(--surf-shadow) !important;
    }
    [class*="st-key-p5_review_option_skipped_"] {
      background: var(--surf-status-ok-wash) !important;
      border-color: var(--surf-shadow) !important;
    }
    [class*="st-key-p5_review_option_neutral_"] {
      background: var(--surf-status-ok-wash) !important;
      border-color: var(--surf-shadow) !important;
    }
    .surf-p5-option-row {
      align-items: center;
      display: flex;
      gap: 18px;
      min-height: 72px;
      padding: 16px 22px;
    }
    .surf-p5-option-checkbox {
      background: var(--surf-paper);
      border: 3px solid var(--surf-paper5);
      border-radius: 5px;
      display: inline-block;
      flex: 0 0 auto;
      height: 28px;
      margin-top: 0;
      position: relative;
      width: 28px;
    }
    .surf-p5-option-checkbox.is-selected { background: var(--surf-paper5); }
    .surf-p5-option-checkbox.is-selected::before {
      color: var(--surf-paper);
      content: "✓";
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 18px;
      font-weight: 700;
      left: 5px;
      line-height: 1;
      position: absolute;
      top: 2px;
    }
    .surf-p5-option-text {
      color: var(--surf-paper5);
      flex: 1 1 auto;
      font-family: "Fraunces", Georgia, serif;
      font-size: 18px;
      line-height: 1.22;
      min-width: 0;
      overflow-wrap: anywhere;
    }
    .surf-p5-feedback-row {
      align-items: center;
      background: color-mix(in srgb, var(--surf-paper) 86%, white);
      border: 2px solid var(--surf-paper3);
      border-radius: 4px;
      box-sizing: border-box;
      display: flex;
      gap: 18px;
      margin: 10px 0 18px;
      min-height: 72px;
      padding: 14px 18px;
    }
    .surf-p5-feedback-row.ok .surf-p5-feedback-symbol { color: var(--surf-status-ok); }
    .surf-p5-feedback-row.bad .surf-p5-feedback-symbol { color: var(--surf-accent-deep); }
    .surf-p5-feedback-symbol {
      flex: 0 0 auto;
      font-family: "Fraunces", Georgia, serif;
      font-size: 34px;
      font-style: italic;
      font-weight: 900;
      line-height: 1;
    }
    .surf-p5-feedback-copy {
      color: var(--surf-paper5);
      display: flex;
      flex-direction: column;
      gap: 6px;
      min-width: 0;
      overflow-wrap: anywhere;
    }
    .surf-p5-feedback-label {
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.16em;
      line-height: 1.5;
      text-transform: uppercase;
    }
    .surf-p5-feedback-reason {
      font-family: "Fraunces", Georgia, serif;
      font-size: 18px;
      font-weight: 400;
      letter-spacing: 0;
      line-height: 1.28;
      text-transform: none;
    }
    div[class*="st-key-p5_back_to_class"] button,
    div[class*="st-key-p5_open_dashboard"] button,
    div[class*="st-key-p5_recovery_back_to_class"] button {
      background: var(--surf-paper) !important;
      border: 2px solid var(--surf-shadow) !important;
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
      font-size: 11px !important;
      font-weight: 700 !important;
      min-height: 44px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
    }
    div[class*="st-key-p5_back_to_class"] button:hover,
    div[class*="st-key-p5_open_dashboard"] button:hover,
    div[class*="st-key-p5_recovery_back_to_class"] button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    div[class*="st-key-p5_back_to_class"] button:active,
    div[class*="st-key-p5_open_dashboard"] button:active,
    div[class*="st-key-p5_recovery_back_to_class"] button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }
    @media (prefers-reduced-motion: reduce) {
      .st-key-p5_review_mock_page button,
      .st-key-p5_review_mock_page button:hover,
      .st-key-p5_review_mock_page button:active {
        transform: none !important;
        transition: background 0.08s ease-out !important;
      }
    }
    """
        + "\n</style>"
    )


def format_finished_at(value: Any) -> str:
    """Format a stored attempt timestamp as Swiss-local `dd MMM YYYY · HH:MM`.

    Naive values are treated as UTC (matches SQLite ``datetime('now')``);
    tz-aware values keep their offset. Shared by P5 review hero and P3
    attempt cards so both surfaces show identical Swiss-local time.
    """
    if value is None:
        return "Date unavailable"
    text = str(value)
    normalized = text.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        parsed = None
    if parsed is None:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(
                    text[:19] if "T" in text else text[:19],
                    fmt,
                )
                break
            except ValueError:
                continue
    if parsed is None:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(_SWISS_TZ).strftime("%d %b %Y · %H:%M")


def _lookup_class_name(class_id: int | None) -> str | None:
    if class_id is None:
        return None
    class_row = get_class_by_id(class_id)
    if not class_row:
        return None
    name = class_row.get("name")
    return str(name) if name else None


def _class_name(summary: dict, class_id: int | None) -> str:
    for key in ("class_name", "name"):
        value = summary.get(key)
        if value:
            return str(value)
    looked_up = _lookup_class_name(class_id)
    if looked_up:
        return looked_up
    if class_id is not None:
        return f"Class {class_id}"
    return "Class unavailable"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _grade_value(summary: dict) -> str:
    grade = summary.get("swiss_grade")
    if grade is None:
        return "X.dd"
    try:
        return f"{float(grade):.2f}"
    except (TypeError, ValueError):
        return "X.dd"


def _hero_html(*, title: str, finished_at: str, grade: str | None) -> str:
    grade_block = ""
    if grade is not None:
        grade_block = (
            '<div><p class="surf-p5-grade-label">Grade</p>'
            f'<p class="surf-p5-grade-value">{escape(grade)}</p></div>'
        )
    return (
        '<div class="surf-p5-hero">'
        '<div>'
        f'<p class="surf-p5-title">{escape(title)}</p>'
        f'<p class="surf-p5-date">{escape(finished_at)}</p>'
        '</div>'
        f'{grade_block}'
        '</div>'
    )


def _threshold_status(score_pct: float, threshold: int) -> str:
    status = "passed" if score_pct >= threshold else "below threshold"
    return f"Grade-4 threshold: {threshold}% — {status}"


def _recovery_state() -> None:
    st.markdown(_styles(), unsafe_allow_html=True)
    with st.container(key="p5_review_mock_page"):
        st.html(
            '<div class="surf-p5-hero"><div><p class="surf-p5-title">No attempt selected.</p>'
            '<p class="surf-p5-date">Return to class and choose a completed '
            'attempt.</p></div></div>'
        )
        with st.container(key="p5_recovery_back_to_class"):
            if st.button("BACK TO CLASS", use_container_width=True):
                st.switch_page("views/class_view.py")


def _summary_html(
    summary: dict,
    *,
    threshold: int | None,
    skipped_count: int | None = None,
) -> str:
    mock_kind = str(summary.get("mock_kind") or "mock").lower()
    is_practice = mock_kind == "practice"
    correct_count = _safe_int(summary.get("correct_count"))
    total_count = _safe_int(summary.get("total_count"))
    if skipped_count is None:
        skipped_count = _safe_int(summary.get("skipped_count"))
    score_pct = _safe_float(summary.get("raw_score_pct"))
    grade_text = "Practice" if is_practice else _grade_value(summary)
    threshold_html = ""
    if is_practice:
        threshold_html = (
            '<p class="surf-p5-practice-note">'
            f'{escape(_PRACTICE_DISCLAIMER_COPY)}</p>'
        )
    elif threshold is not None:
        threshold_html = (
            f'<p class="surf-p5-threshold">'
            f'{escape(_threshold_status(score_pct, threshold))}</p>'
        )
    return (
        '<div class="surf-p5-summary-grid">'
        '<div><p class="surf-p5-stat-label">Result</p>'
        f'<p class="surf-p5-stat-value">{escape(str(grade_text))}</p></div>'
        '<div><p class="surf-p5-stat-label">Score</p>'
        f'<p class="surf-p5-stat-value">{correct_count}/{total_count}</p></div>'
        '<div><p class="surf-p5-stat-label">Percent</p>'
        f'<p class="surf-p5-stat-value">{score_pct:.0f}%</p></div>'
        '<div><p class="surf-p5-stat-label">Skipped</p>'
        f'<p class="surf-p5-stat-value">{skipped_count}</p></div>'
        '</div>'
        f'{threshold_html}'
    )


def _result_state(result_stamp: str) -> str:
    return result_stamp.lower() if result_stamp in {"CORRECT", "WRONG", "SKIPPED"} else "wrong"


def _difficulty_flag_tier(score: int) -> str:
    """Return the tier class suffix (`ok`/`warn`/`risk`) for a clamped score.

    - score < 33 → ``ok`` (green) — low personal risk.
    - 33 ≤ score ≤ 66 → ``warn`` (yellow) — medium personal risk.
    - score > 66 → ``risk`` (red) — high personal risk.
    """
    if score < 33:
        return "ok"
    if score <= 66:
        return "warn"
    return "risk"


def _decode_json_list(value: object) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
        except ValueError:
            return []
        if isinstance(parsed, list):
            return parsed
    return []


def _review_card_header_html(
    *,
    stamp: str,
    objective: str,
    type_label: str,
    question: str,
    difficulty_score: int | None = None,
) -> str:
    _ = stamp
    difficulty_flag = ""
    if difficulty_score is not None:
        try:
            score_int = int(difficulty_score)
        except (TypeError, ValueError):
            score_int = None
        if score_int is not None and 0 <= score_int <= 100:
            tier = _difficulty_flag_tier(score_int)
            difficulty_flag = (
                f'<div class="surf-personal-difficulty-flag '
                f'surf-personal-difficulty-flag--{tier}" '
                f'aria-label="Difficulty for you: {score_int}/100">'
                '<span class="surf-personal-difficulty-flag-label">'
                "DIFFICULTY<br>FOR YOU"
                "</span>"
                '<span class="surf-personal-difficulty-flag-score">'
                f"{escape(str(score_int))}"
                "</span>"
                "</div>"
            )
    return (
        f"{difficulty_flag}"
        f'<div class="surf-question-type-chip">{escape(type_label or _TYPE_UNAVAILABLE_COPY)}</div>'
        f'<div class="surf-p5-lo">{escape(objective)}</div>'
        f'<div class="surf-p5-question-text">{escape(question)}</div>'
    )


def _scoring_view_from_review_row(row: dict) -> dict:
    """Build the plain-dict view passed to `score_questions(...)`."""
    qid = row.get("question_id", row.get("id"))
    view = {
        "id": qid,
        "question_id": qid,
        "stem": row.get("question_text"),
        "question_text": row.get("question_text"),
        "options": _decode_json_list(row.get("options_json", row.get("options"))),
        "correct_indices": _decode_json_list(row.get("correct_indices")),
        "question_type": row.get("question_type"),
        "lo_title": row.get("learning_objective_title")
        or row.get("learning_objective")
        or row.get("lo_title"),
    }
    for key in _DIFFICULTY_FEATURE_KEYS:
        view[key] = row.get(key)
    return view


def _example_view_from_review_row(row: dict) -> dict:
    """Build a completed-answer example view for `score_questions(...)`."""
    view = _scoring_view_from_review_row(row)
    view["selected_indices"] = _decode_json_list(row.get("selected_indices"))
    view["is_correct"] = bool(row.get("is_correct"))
    view["is_skipped"] = bool(row.get("is_skipped") or row.get("was_skipped"))
    return view


def _difficulty_score_map_for_review(
    class_id: int | None,
    review_rows: list[dict],
    *,
    examples_fn=list_personal_difficulty_examples_for_class,
    score_questions_fn=score_questions,
) -> dict[int, int]:
    """Compute `{question_id: score}` for the review rows on each render.

    The map is recomputed on every page load (D-16). No score is written
    to SQLite or to attempt rows. Any failure path returns an empty map
    so the review page renders without the badge rather than crashing.
    """
    if not review_rows:
        return {}
    if not isinstance(class_id, int) or class_id <= 0:
        return {}
    try:
        examples = [
            _example_view_from_review_row(row)
            for row in list(examples_fn(class_id) or [])
        ]
    except Exception:
        examples = []
    scoring_inputs = [_scoring_view_from_review_row(row) for row in review_rows]
    try:
        results = score_questions_fn(scoring_inputs, examples=examples)
    except Exception:
        return {}
    if len(results) != len(review_rows):
        return {}
    score_map: dict[int, int] = {}
    for row, result in zip(review_rows, results):
        qid = row.get("question_id")
        if isinstance(qid, int):
            try:
                score_map[qid] = int(result.score)
            except (AttributeError, TypeError, ValueError):
                continue
    return score_map


def _option_html(*, option: object, selected: bool) -> str:
    checkbox_class = (
        "surf-p5-option-checkbox is-selected"
        if selected
        else "surf-p5-option-checkbox"
    )
    return (
        '<div class="surf-p5-option-row">'
        f'<span class="{checkbox_class}"></span>'
        f'<span class="surf-p5-option-text">{escape(str(option))}</span>'
        '</div>'
    )


def _feedback_html(*, state_class: str, rationale: object) -> str:
    is_ok = state_class in {"correct", "neutral"}
    symbol = "✓" if is_ok else "✗"
    label_by_state = {
        "correct": "Correct!",
        "wrong": "Not quite ...",
        "missed": "You missed this option ...",
        "skipped": "Skipped question.",
        "neutral": "Good catch! This option was wrong!",
    }
    label = label_by_state.get(state_class, "Review note")
    text = format_rationale_text(rationale)
    return (
        f'<div class="surf-p5-feedback-row {"ok" if is_ok else "bad"}">'
        f'<span class="surf-p5-feedback-symbol">{symbol}</span>'
        '<span class="surf-p5-feedback-copy">'
        f'<span class="surf-p5-feedback-label">{escape(label)}</span>'
        '<span class="surf-p5-feedback-reason">'
        f'{escape(text or _RATIONALE_UNAVAILABLE_COPY)}'
        '</span>'
        '</span></div>'
    )


def _render_review_row(raw_row: dict, *, difficulty_score: int | None = None) -> None:
    row = parse_review_row(raw_row)
    question_id = _safe_int(row.get("question_id"))
    selected_indices = set(row.get("selected_indices") or [])
    correct_indices = set(row.get("correct_indices") or [])
    was_skipped = bool(row.get("was_skipped"))
    is_correct = bool(row.get("is_correct"))
    result_stamp = result_stamp_for_attempt(
        was_skipped=was_skipped,
        is_correct=is_correct,
    )
    result_state = _result_state(result_stamp)
    options = list(row.get("options_json") or [])
    rationales = list(row.get("rationales_per_option_json") or [])
    objective = (
        row.get("learning_objective")
        or row.get("learning_objective_title")
        or row.get("lo_title")
        or "Learning objective unavailable."
    )
    type_label = format_question_type_chip_label(row.get("question_type"))
    question_text = str(row.get("question_text") or "Question unavailable.")

    with st.container(key=f"p5_review_row_{result_state}_{question_id}"):
        st.html(
            _review_card_header_html(
                stamp=result_stamp,
                objective=str(objective),
                type_label=type_label,
                question=question_text,
                difficulty_score=difficulty_score,
            )
        )
        for index, option in enumerate(options[:4]):
            state_class = classify_option_state(
                index,
                selected_indices=selected_indices,
                correct_indices=correct_indices,
                was_skipped=was_skipped,
            )
            rationale = rationales[index] if index < len(rationales) else None
            with st.container(key=f"p5_review_option_{state_class}_{question_id}_{index}"):
                st.html(_option_html(option=option, selected=index in selected_indices))
            feedback_markup = _feedback_html(state_class=state_class, rationale=rationale)
            if feedback_markup:
                st.html(feedback_markup)


def _render_difficulty_score_explainer() -> None:
    """Render the text-only P5 difficulty-score explanation toggle."""
    is_open = bool(st.session_state.get(_DIFFICULTY_EXPLAINER_OPEN_KEY, False))
    with st.container(key="p5_difficulty_score_explainer"):
        if st.button(
            _DIFFICULTY_EXPLAINER_LABEL,
            key="p5_difficulty_score_explainer_action",
        ):
            st.session_state[_DIFFICULTY_EXPLAINER_OPEN_KEY] = not is_open
    if st.session_state.get(_DIFFICULTY_EXPLAINER_OPEN_KEY, False):
        with st.container(key="p5_difficulty_score_explainer_card"):
            st.html(
                '<p class="surf-p5-difficulty-explainer-body">'
                f"{escape(_DIFFICULTY_EXPLAINER_BODY)}"
                "</p>"
            )


def _render_actions(*, class_id: int | None) -> None:
    left, right = st.columns(2)
    with left:
        with st.container(key="p5_back_to_class"):
            if st.button("BACK TO CLASS", key="p5_back_to_class_button", use_container_width=True):
                st.switch_page("views/class_view.py")
    with right:
        with st.container(key="p5_open_dashboard"):
            if st.button(
                "OPEN DASHBOARD",
                key="p5_open_dashboard_button",
                use_container_width=True,
            ):
                if class_id is not None:
                    st.session_state["selected_class_id"] = class_id
                st.switch_page("views/dashboard.py")


# --------------------------------------------------------------------------- #
# PUBLIC ENTRY POINT — `render_review_mock_page`
# --------------------------------------------------------------------------- #
# Simple explanation:
# The one function `views/review_mock_exam.py` calls. It loads the saved
# attempt summary plus the per-question review rows, recovers gracefully
# when either is missing, renders the shared topbar with the class
# breadcrumb segment, draws the hero band and four-stat summary card, and
# then loops every review row through `_render_review_row` with the
# freshly-computed difficulty flag score. No write happens here — the
# function is strictly read-only.
def render_review_mock_page(
    *,
    user: dict,
    class_id: int | None,
    attempt_id: int | None,
) -> None:
    """Render the read-only P5 review page."""
    # Loads persisted attempt rows and renders recovery if they are missing.
    _ = user
    if attempt_id is None:
        _recovery_state()
        return

    summary = get_attempt_summary(attempt_id, class_id)
    if summary is None:
        _recovery_state()
        return

    review_rows = get_attempt_review_rows(attempt_id)
    if not review_rows:
        _recovery_state()
        return

    resolved_class_name = _class_name(summary, class_id)
    render_topbar(current_page="review_mock_exam", class_name=resolved_class_name)
    st.markdown(_styles(), unsafe_allow_html=True)

    mock_kind = str(summary.get("mock_kind") or "mock").lower()
    is_practice = mock_kind == "practice"
    title = "Practice Review" if is_practice else "Mock Review"
    finished_at = format_finished_at(summary.get("finished_at"))
    threshold = get_class_pass_threshold(class_id) if class_id is not None else None
    skipped_count = sum(1 for row in review_rows if bool(row.get("was_skipped")))

    with st.container(key="p5_review_mock_page"):
        st.html(
            _hero_html(
                title=title,
                finished_at=finished_at,
                grade=None if is_practice else _grade_value(summary),
            )
        )
        with st.container(key="p5_summary_card"):
            st.html(
                _summary_html(
                    summary,
                    threshold=threshold,
                    skipped_count=skipped_count,
                )
            )
        _render_difficulty_score_explainer()
        difficulty_score_map = _difficulty_score_map_for_review(
            class_id,
            review_rows,
        )
        for row in review_rows:
            qid = _safe_int(row.get("question_id"))
            _render_review_row(
                row,
                difficulty_score=difficulty_score_map.get(qid),
            )
        _render_actions(class_id=class_id)

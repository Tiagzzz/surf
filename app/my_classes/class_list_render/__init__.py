"""P2 — My Classes page renderer.

Public entry point::

    from app.my_classes.class_list_render import render_my_classes_page
    render_my_classes_page(user=user_dict)

The module owns three responsibilities:

* **View-model construction.** :func:`build_class_card_view_models` turns
  ``(classes, stats_by_class_id)`` into the locked list of card
  payloads the renderer reads — never hardcoded demo data.
* **Service-layer dispatch.** :func:`submit_add_class_form` blocks when
  the required factsheet is missing and otherwise delegates to
  :func:`app.my_classes.class_create.create_class_from_factsheet`.
* **Streamlit rendering.** :func:`render_my_classes_page` composes the
  shared topbar, page chrome, inline ADD CLASS form, class cards, and
  destructive delete dialog using injectable services so tests and the
  preview sandbox can stand in fakes.

The visual layout keeps the approved class-card refinement: the
title-row's last-4-mock average is color-coded by tier, the four stat
lines are arranged in two stacked mini-columns, and the bottom action
row uses full-width stamped ``DELETE CLASS`` and ``ENTER CLASS >``
buttons. The copy registry, threshold slider, factsheet requirement,
delete dialog copy, ``selected_class_id`` session-state contract, and
``OPEN CLASS`` compatibility token (preserved as ``OPEN_CLASS_LABEL``)
remain centralized here.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path
from time import sleep
from typing import Any, Callable, Iterable, Mapping

import streamlit as st

from app.brain.page_header import render_page_header
from app.brain.page_layout import page_rail
from app.brain.processing_popup import show_processing_popup
from app.brain.topbar import render_topbar
from app.db.queries_classes import list_classes_for_user
from app.db.queries_dashboard import (
    get_coverage_summary,
    get_mock_grade_metrics,
)
from app.db.queries_lectures import list_lectures_for_class
from app.my_classes.class_create import create_class_from_factsheet
from app.my_classes.class_delete import (
    DELETE_LABEL,
    DELETE_SUCCESS_TOAST,
    DELETE_TRIGGER_LABEL,
    DIALOG_TITLE,
    KEEP_LABEL,
    delete_class_after_confirmation,
    format_dialog_body,
)

# --------------------------------------------------------------------------- #
# Copy, validation, session, and routing constants used by the P2 renderer.
# --------------------------------------------------------------------------- #

PAGE_TITLE = "My Classes"
HELPER_PARAGRAPH = (
    "Each class holds your lectures, generated questions, mocks, and stats."
)

ADD_CLASS_LABEL = "ADD CLASS"
CLASS_NAME_LABEL = "CLASS NAME"
GRADE_THRESHOLD_LABEL = "GRADE-4 THRESHOLD (%)"
GRADE_THRESHOLD_HELPER = (
    "Example: if 50% of exam points gives a 4.0, leave this at 50%."
)
FACTSHEET_LABEL = "CLASS FACTSHEET (PDF)"
FACTSHEET_HELPER = (
    "Upload the official course factsheet so Surf can ground its answers."
)
DISCARD_DRAFT_LABEL = "DISCARD CLASS DRAFT"
CREATE_CLASS_LABEL = "CREATE CLASS"
OPEN_CLASS_LABEL = "OPEN CLASS"
ENTER_CLASS_LABEL = "ENTER CLASS >"
EMPTY_STATE_COPY = "Nothing here yet. Add a class and upload your first lecture."

PROCESSING_TOAST = "Reading your factsheet…"
PROCESS_FAIL_TITLE = "Couldn't process the factsheet"
PROCESS_FAIL_BODY = (
    "Something went wrong reading your factsheet. "
    "Try again, or check your API key in Settings."
)
SAVE_SUCCESS_TOAST = "Saved."
DELETE_SUCCESS_COPY = DELETE_SUCCESS_TOAST  # re-export for renderer convenience

MISSING_FACTSHEET_ERROR = (
    "Attach the class factsheet PDF to create this class."
)
MISSING_NAME_ERROR = "Add a class name to continue."
INVALID_NAME_ERROR = "Class name must be 80 characters or fewer."
MISSING_API_KEY_ERROR = (
    "Add your Anthropic API key in Settings before creating a class."
)

#: Grade-4 threshold slider range shown during class setup.
GRADE_THRESHOLD_MIN = 20
GRADE_THRESHOLD_MAX = 80
GRADE_THRESHOLD_DEFAULT = 50
GRADE_THRESHOLD_STEP = 1

#: Session-state keys owned by the My Classes page.
ADD_CLASS_OPEN_KEY = "p2_add_class_open"
ADD_CLASS_STATUS_KEY = "p2_add_class_status"
DELETE_PENDING_KEY = "p2_delete_class_id"
SELECTED_CLASS_KEY = "selected_class_id"

#: Routing target for the class-card ENTER action.
CLASS_VIEW_PATH = "views/class_view.py"

#: Maximum class-name length accepted by the page form.
CLASS_NAME_MAX_LENGTH = 80

#: Last-4 mock average labels shown on class cards.
AVG_SCORE_LABEL_FULL = "Last 4 Mock Avg"
AVG_SCORE_LABEL_PARTIAL_TEMPLATE = "Last 4 Mock Avg ({n} of 4)"

__all__ = [
    "PAGE_TITLE",
    "HELPER_PARAGRAPH",
    "ADD_CLASS_LABEL",
    "CLASS_NAME_LABEL",
    "GRADE_THRESHOLD_LABEL",
    "GRADE_THRESHOLD_HELPER",
    "GRADE_THRESHOLD_MIN",
    "GRADE_THRESHOLD_MAX",
    "GRADE_THRESHOLD_DEFAULT",
    "GRADE_THRESHOLD_STEP",
    "FACTSHEET_LABEL",
    "FACTSHEET_HELPER",
    "DISCARD_DRAFT_LABEL",
    "CREATE_CLASS_LABEL",
    "OPEN_CLASS_LABEL",
    "ENTER_CLASS_LABEL",
    "EMPTY_STATE_COPY",
    "PROCESSING_TOAST",
    "PROCESS_FAIL_TITLE",
    "PROCESS_FAIL_BODY",
    "SAVE_SUCCESS_TOAST",
    "MISSING_FACTSHEET_ERROR",
    "MISSING_NAME_ERROR",
    "INVALID_NAME_ERROR",
    "MISSING_API_KEY_ERROR",
    "ADD_CLASS_OPEN_KEY",
    "ADD_CLASS_STATUS_KEY",
    "DELETE_PENDING_KEY",
    "SELECTED_CLASS_KEY",
    "CLASS_VIEW_PATH",
    "AVG_SCORE_LABEL_FULL",
    "AVG_SCORE_LABEL_PARTIAL_TEMPLATE",
    "build_class_card_view_models",
    "submit_add_class_form",
    "handle_open_class",
    "render_my_classes_page",
]


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #


def _format_grade_value(grade: float | int | None) -> str:
    if grade is None:
        return "—"
    return f"{float(grade):.2f}"


def _grade_tier(grade: float | int | None) -> str:
    """Return the visual tier for the last-4 mock average.

    * ``empty`` — no completed mock yet.
    * ``fail`` — < 4.0 (Accent/Deep / red).
    * ``borderline`` — 4.0 ≤ avg < 5.0 (Status/Warn / gold).
    * ``pass`` — ≥ 5.0 (Status/OK / green).
    """
    if grade is None:
        return "empty"
    value = float(grade)
    if value < 4.0:
        return "fail"
    if value < 5.0:
        return "borderline"
    return "pass"


def _format_avg_score_label(completed_mock_count: int) -> str:
    if completed_mock_count >= 4 or completed_mock_count <= 0:
        return AVG_SCORE_LABEL_FULL
    return AVG_SCORE_LABEL_PARTIAL_TEMPLATE.format(n=completed_mock_count)


def _format_coverage(coverage_pct: int | float | None) -> str:
    if coverage_pct is None:
        return "— Covered"
    return f"{int(round(coverage_pct))}% Covered"


def _format_last_grade(last_grade: float | int | None) -> str:
    if last_grade is None:
        return "— last grade"
    return f"{float(last_grade):.2f} last grade"


def build_class_card_view_models(
    classes: Iterable[Mapping[str, Any]],
    stats_by_class_id: Mapping[int, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build view-model dicts for each class card.

    Every numeric stat must come from ``stats_by_class_id``; this
    function never fabricates demo data. Missing stats fall through to
    locked honest placeholders defined in 03-UI-SPEC §3.3.
    """
    if not isinstance(classes, (list, tuple)):
        raise TypeError(
            "classes must be a list or tuple of class dicts; got "
            f"{type(classes).__name__}"
        )

    view_models: list[dict[str, Any]] = []
    for class_row in classes:
        class_id = class_row["id"]
        class_name = str(class_row.get("name", "")).strip() or "Untitled class"
        stats = stats_by_class_id.get(class_id, {}) or {}

        lectures_count = int(stats.get("lectures_count") or 0)
        questions_count = int(stats.get("questions_count") or 0)
        coverage_pct = stats.get("coverage_pct")
        last_grade = stats.get("last_grade")
        last_4_mock_avg = stats.get("last_4_mock_avg")
        completed_mock_count = int(stats.get("completed_mock_count") or 0)

        view_models.append(
            {
                "class_id": class_id,
                "class_name": class_name,
                "avg_score_value": _format_grade_value(last_4_mock_avg),
                "avg_score_tier": _grade_tier(last_4_mock_avg),
                "avg_score_label": _format_avg_score_label(completed_mock_count),
                "left_stats": [
                    f"{lectures_count} lectures",
                    f"{questions_count} Questions",
                ],
                "right_stats": [
                    _format_coverage(coverage_pct),
                    _format_last_grade(last_grade),
                ],
            }
        )
    return view_models


def submit_add_class_form(
    *,
    user_id: int,
    class_name: str,
    grade4_threshold_percent: int,
    factsheet_file: Any,
    create_fn: Callable[..., dict[str, Any]] = create_class_from_factsheet,
) -> dict[str, Any]:
    """Service-layer wrapper for ``CREATE CLASS``.

    Returns ``{"ok": False, "error": "missing_factsheet"}`` when the
    page submitted without a PDF; otherwise delegates to ``create_fn``
    and returns its status dict verbatim.
    """
    if factsheet_file in (None, b"", ""):
        return {"ok": False, "error": "missing_factsheet"}
    return create_fn(
        user_id=user_id,
        class_name=class_name,
        grade4_threshold_percent=grade4_threshold_percent,
        factsheet_file_or_bytes=factsheet_file,
    )


def handle_open_class(
    *,
    class_id: int,
    state: dict[str, Any],
    switch_page_fn: Callable[[str], None],
) -> None:
    """Record the selection and navigate to the class hub view."""
    state[SELECTED_CLASS_KEY] = class_id
    switch_page_fn(CLASS_VIEW_PATH)


def _default_list_class_stats(user_id: int) -> dict[int, dict[str, Any]]:
    """Default stats provider — wires real per-class metrics for P2 cards.

    Walks every class owned by ``user_id`` and assembles a stats dict
    keyed by class id with the six fields ``build_class_card_view_models``
    consumes. All numbers come from existing query helpers; no SQL lives
    in this module and pandas is intentionally not imported.

    Per-field wiring:

    * ``lectures_count`` — ``len(list_lectures_for_class(class_id))``.
    * ``questions_count`` — ``get_coverage_summary(class_id)["total_questions"]``.
    * ``coverage_pct`` — ``(correct_at_least_once + attempted_never_correct)
      / total_questions * 100``, rounded to int. ``None`` when there are
      no questions yet (honest fallback so the renderer prints ``— Covered``).
      Coverage counts mock + practice per the V1 lock.
    * ``last_grade`` — ``get_mock_grade_metrics(class_id)["last_grade"]``.
      Mock-only by definition of the helper; ``None`` when no completed
      mocks exist.
    * ``last_4_mock_avg`` — ``get_mock_grade_metrics(class_id)["class_average"]``.
      Mock-only; averages exactly the last 4 completed mocks (or fewer
      if 1–3 exist); ``None`` when none exist.
    * ``completed_mock_count`` — ``get_mock_grade_metrics(class_id)["mock_count"]``.
      Practice attempts do not increment this.
    """
    classes = list_classes_for_user(user_id) or []
    stats: dict[int, dict[str, Any]] = {}
    for class_row in classes:
        class_id = int(class_row["id"])

        lectures_count = len(list_lectures_for_class(class_id))

        coverage = get_coverage_summary(class_id)
        total_questions = int(coverage["total_questions"])
        attempted = int(coverage["correct_at_least_once"]) + int(
            coverage["attempted_never_correct"]
        )
        if total_questions == 0:
            coverage_pct: int | None = None
        else:
            coverage_pct = int(round(attempted / total_questions * 100))

        mock_metrics = get_mock_grade_metrics(class_id)

        stats[class_id] = {
            "lectures_count": lectures_count,
            "questions_count": total_questions,
            "coverage_pct": coverage_pct,
            "last_grade": mock_metrics["last_grade"],
            "last_4_mock_avg": mock_metrics["class_average"],
            "completed_mock_count": int(mock_metrics["mock_count"]),
        }
    return stats


# --------------------------------------------------------------------------- #
# Streamlit rendering
# --------------------------------------------------------------------------- #

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FONTS_DIR = _REPO_ROOT / "assets" / "fonts"
_DROPBOX_FILE_ICON_DATA_URI = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='64' height='76' viewBox='0 0 64 76' fill='none'%3E"
    "%3Cpath d='M14 4h27l13 13v51a4 4 0 0 1-4 4H14"
    "a4 4 0 0 1-4-4V8a4 4 0 0 1 4-4Z' stroke='%236C6455' "
    "stroke-width='6' stroke-linejoin='round'/%3E"
    "%3Cpath d='M40 5v16h16' stroke='%236C6455' stroke-width='6' "
    "stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"
)


def _font_data_uri(filename: str) -> str:
    """Return a base64 ``data:font/woff2`` URI for an asset font file.

    Embedding the WOFF2 inline avoids Streamlit's static-file-serving
    requirement so the font registers no matter which surface the
    user landed on first. Same pattern used by P1 signup and the
    P1/P7 preview sandboxes.
    """
    encoded = base64.b64encode((_FONTS_DIR / filename).read_bytes()).decode("ascii")
    return f"data:font/woff2;base64,{encoded}"


@lru_cache(maxsize=1)
def _font_face_block() -> str:
    """Inline ``@font-face`` declarations for Fraunces + JetBrains Mono.

    Every authenticated surface that renders Fraunces or JetBrains
    Mono needs its own ``@font-face`` block — the browser does not
    keep custom-font registrations across ``st.switch_page`` boundaries
    in a multi-page Streamlit app.
    """
    try:
        fraunces_regular = _font_data_uri("Fraunces-Regular.woff2")
        fraunces_medium = _font_data_uri("Fraunces-Medium.woff2")
        fraunces_semibold_italic = _font_data_uri(
            "Fraunces-SemiBoldItalic.woff2"
        )
        mono_regular = _font_data_uri("JetBrainsMono-Regular.woff2")
        mono_medium = _font_data_uri("JetBrainsMono-Medium.woff2")
    except FileNotFoundError:
        return ""
    return f"""
    @font-face {{
      font-family: "Fraunces";
      src: url({fraunces_regular!r}) format("woff2");
      font-weight: 400; font-style: normal; font-display: swap;
    }}
    @font-face {{
      font-family: "Fraunces";
      src: url({fraunces_medium!r}) format("woff2");
      font-weight: 500; font-style: normal; font-display: swap;
    }}
    @font-face {{
      font-family: "Fraunces";
      src: url({fraunces_semibold_italic!r}) format("woff2");
      font-weight: 600; font-style: italic; font-display: swap;
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
    }

    .stApp { background: var(--surf-paper) !important; }

    /* P2 button font only — scoped to the My Classes rail plus the
       P2 delete-dialog buttons, which Streamlit renders in a portal
       outside `.st-key-p2_my_classes_page`. Surf's button label style
       uses the Surf stamped-button label style; this must
       not sweep unrelated pages or non-button copy. */
    .st-key-p2_my_classes_page [data-testid="stButton"] button,
    .st-key-p2_my_classes_page [data-testid="stFormSubmitButton"] button,
    .st-key-p2_my_classes_page [data-testid="stBaseButton-primary"],
    .st-key-p2_my_classes_page [data-testid="stBaseButton-secondary"],
    .st-key-p2_my_classes_page [data-testid="stBaseButton-primaryFormSubmit"],
    .st-key-p2_my_classes_page [data-testid="stBaseButton-secondaryFormSubmit"],
    .st-key-p2_my_classes_page [data-testid="stButton"] button *,
    .st-key-p2_my_classes_page [data-testid="stFormSubmitButton"] button *,
    .st-key-p2_my_classes_page [data-testid="stBaseButton-primary"] *,
    .st-key-p2_my_classes_page [data-testid="stBaseButton-secondary"] *,
    .st-key-p2_my_classes_page [data-testid="stBaseButton-primaryFormSubmit"] *,
    .st-key-p2_my_classes_page [data-testid="stBaseButton-secondaryFormSubmit"] *,
    div[class*="st-key-p2_delete_keep"] button,
    div[class*="st-key-p2_delete_confirm"] button,
    div[class*="st-key-p2_delete_keep"] button *,
    div[class*="st-key-p2_delete_confirm"] button * {
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      letter-spacing: 0.14em !important;
      text-transform: uppercase !important;
    }

    /* Destructive delete dialog — KEEP CLASS (neutral) +
       DELETE CLASS (Accent/Deep destructive). Dialogs render in a
       Streamlit portal outside `.st-key-p2_my_classes_page`, so these
       rules are scoped by the per-button keys instead. */
    div[class*="st-key-p2_delete_keep"] button {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 3px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      height: 44px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
    }
    div[class*="st-key-p2_delete_confirm"] button {
      background: var(--surf-accent-deep) !important;
      border: 1.5px solid var(--surf-accent-deep) !important;
      border-radius: 3px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      height: 44px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
    }
    div[class*="st-key-p2_delete_keep"] button:hover,
    div[class*="st-key-p2_delete_confirm"] button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    div[class*="st-key-p2_delete_keep"] button:active,
    div[class*="st-key-p2_delete_confirm"] button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }
    div[class*="st-key-p2_delete_confirm"] button:hover {
      background: var(--surf-accent) !important;
      border-color: var(--surf-accent) !important;
    }

    .st-key-p2_my_classes_page {
      box-sizing: border-box;
      padding: 0 32px 24px !important;
    }

    .surf-p2-page-title {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 32px;
      font-weight: 500;
      letter-spacing: -0.01em;
      line-height: 1.15;
      margin: 0 0 12px;
    }
    .surf-p2-helper {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 17px;
      font-weight: 400;
      line-height: 1.5;
      margin: 0 0 24px;
    }

    /* Universal stamped buttons (03-UI-SPEC §2.5.a). */
    .st-key-p2_my_classes_page [data-testid="stButton"] button {
      border-radius: 3px !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      letter-spacing: 0.14em !important;
      padding: 0 18px !important;
      text-transform: uppercase !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
    }

    .st-key-p2_add_class_button button {
      background: var(--surf-paper5) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
      height: 48px !important;
      width: 100% !important;
    }
    .st-key-p2_add_class_button button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .st-key-p2_add_class_button button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }

    /* Add Class form card (when expanded) — one dashed outer draft surface. */
    .st-key-p2_add_class_form_card {
      background: var(--surf-paper) !important;
      border: 2px dashed var(--surf-paper5) !important;
      border-radius: 6px !important;
      box-shadow: none !important;
      box-sizing: border-box !important;
      margin: 24px 0 !important;
      padding: 32px 40px !important;
      width: 100% !important;
    }
    .st-key-p2_add_class_form_card [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-p2_add_class_form_card > [data-testid="stLayoutWrapper"]
      > [data-testid="stVerticalBlock"] {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      padding: 0 !important;
    }
    .surf-p2-form-title {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 28px;
      font-style: italic;
      font-weight: 700;
      letter-spacing: -0.01em;
      margin: 0 0 28px;
      text-align: center;
    }

    /* Field labels (Mono/Field Label). */
    .surf-p2-field-label {
      color: var(--surf-paper4) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 500 !important;
      letter-spacing: 0.08em !important;
      margin: 16px 0 8px !important;
      text-transform: uppercase !important;
    }
    .surf-p2-field-label:first-child { margin-top: 0 !important; }
    .surf-p2-field-helper {
      color: var(--surf-paper4) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 14px !important;
      font-style: italic !important;
      line-height: 1.4 !important;
      margin: 8px 0 16px !important;
    }

    /* Text input — wide, rounded, thick black border. */
    .st-key-p2_my_classes_page [data-testid="stTextInput"] label {
      display: none !important;
    }
    .st-key-p2_my_classes_page [data-testid="stTextInput"],
    .st-key-p2_my_classes_page [data-testid="stTextInput"] > div {
      width: 100% !important;
    }
    .st-key-p2_my_classes_page [data-testid="stTextInputRootElement"] {
      background: var(--surf-paper) !important;
      border: none !important;
      box-shadow: none !important;
      padding: 0 !important;
      width: 100% !important;
    }
    .st-key-p2_my_classes_page [data-testid="stTextInput"] > div > div {
      background: var(--surf-paper) !important;
      border: 2px solid var(--surf-paper5) !important;
      border-radius: 6px !important;
      box-shadow: none !important;
      width: 100% !important;
    }
    .st-key-p2_my_classes_page [data-testid="stTextInput"] input {
      background: transparent !important;
      color: var(--surf-paper5) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 17px !important;
      font-style: italic !important;
      min-height: 48px !important;
      padding: 12px 18px !important;
      width: 100% !important;
    }
    .st-key-p2_my_classes_page [data-testid="stTextInput"] input::placeholder {
      color: rgba(40, 37, 31, 0.36) !important;
      font-style: italic !important;
    }
    .st-key-p2_my_classes_page [data-testid="stTextInput"] input:focus {
      outline: none !important;
    }

    /* Slider — Paper1 base track, Accent/Vibrant fill, Paper5 thumb. */
    .st-key-p2_my_classes_page [data-testid="stSlider"] label {
      display: none !important;
    }
    .st-key-p2_my_classes_page [data-testid="stSlider"] [data-baseweb="slider"] {
      padding-top: 28px !important;
    }
    /* BaseWeb slider track (background) */
    .st-key-p2_my_classes_page [data-testid="stSlider"]
      [data-baseweb="slider"] > div > div {
      background: var(--surf-paper1) !important;
    }
    /* Filled portion */
    .st-key-p2_my_classes_page [data-testid="stSlider"]
      [data-baseweb="slider"] > div > div > div {
      background: var(--surf-accent) !important;
    }
    /* Thumb */
    .st-key-p2_my_classes_page [data-testid="stSlider"] [role="slider"] {
      background: var(--surf-paper5) !important;
      border: none !important;
      box-shadow: none !important;
      color: transparent !important;
    }
    /* Floating value bubble above the thumb. */
    .st-key-p2_my_classes_page [data-testid="stSlider"]
      [data-testid="stThumbValue"],
    .st-key-p2_my_classes_page [data-testid="stSlider"] [role="slider"]
      > div {
      background: transparent !important;
      color: var(--surf-accent-deep) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 20px !important;
      font-style: italic !important;
      font-weight: 700 !important;
      opacity: 1 !important;
      visibility: visible !important;
    }
    /* Hide the min/max tick labels (we don't show 20/80). */
    .st-key-p2_my_classes_page [data-testid="stSlider"]
      [data-testid="stTickBar"],
    .st-key-p2_my_classes_page [data-testid="stSlider"]
      [data-testid="stTickBarMin"],
    .st-key-p2_my_classes_page [data-testid="stSlider"]
      [data-testid="stTickBarMax"] {
      display: none !important;
    }

    /* File uploader — the native Streamlit dropzone is the full visual
       Dropbox target. The real button is stretched invisibly over the
       dashed area, so clicks still open the file picker without the
       small stamped button/extra solid line showing inside the zone. */
    .st-key-p2_factsheet_dropbox {
      box-sizing: border-box !important;
      margin: 0 0 8px !important;
      min-height: 260px !important;
      position: relative !important;
      text-align: center !important;
      width: 100% !important;
    }
    .st-key-p2_factsheet_dropbox [data-testid="stElementContainer"],
    .st-key-p2_factsheet_dropbox .stElementContainer {
      position: static !important;
    }
    .surf-p2-dropbox-visual {
      align-items: center;
      display: flex;
      flex-direction: column;
      gap: 14px;
      left: 50%;
      pointer-events: none;
      position: absolute;
      top: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      z-index: 3;
    }
    .surf-p2-dropbox-icon {
      background-image: url("""
        + _DROPBOX_FILE_ICON_DATA_URI
        + """");
      background-position: center;
      background-repeat: no-repeat;
      background-size: contain;
      display: block;
      height: 54px;
      width: 46px;
    }
    .surf-p2-dropbox-title {
      color: var(--surf-paper3);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 46px;
      font-style: normal;
      font-weight: 500;
      letter-spacing: 0.16em;
      line-height: 1;
      margin: 0;
      text-transform: uppercase;
    }
    .surf-p2-dropbox-helper,
    .surf-p2-dropbox-ready {
      color: rgba(108, 100, 85, 0.42);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 24px;
      font-weight: 400;
      letter-spacing: 0.16em;
      line-height: 1.2;
      margin: 0;
      text-transform: uppercase;
    }
    .surf-p2-dropbox-ready {
      bottom: 18px;
      color: var(--surf-status-ok);
      font-size: 12px;
      left: 24px;
      position: absolute;
      right: 24px;
      z-index: 4;
    }
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploader"],
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploader"] > section {
      width: 100% !important;
    }
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploader"] label {
      display: none !important;
    }
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploaderDropzone"] {
      background: var(--surf-paper0) !important;
      border: 2.5px dashed var(--surf-paper3) !important;
      border-radius: 6px !important;
      box-shadow: none !important;
      box-sizing: border-box !important;
      display: block !important;
      min-height: 260px !important;
      outline: 0 !important;
      padding: 0 !important;
      position: relative !important;
      width: 100% !important;
    }
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploaderDropzone"]
      [data-testid="stFileUploaderDropzoneInstructions"] {
      display: none !important;
    }
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploaderDropzone"]
      [data-testid="stBaseButton-secondary"],
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploaderDropzone"] button {
      background: transparent !important;
      border: 0 !important;
      border-radius: 6px !important;
      box-shadow: none !important;
      color: transparent !important;
      cursor: pointer !important;
      height: 100% !important;
      inset: 0 !important;
      min-height: 260px !important;
      opacity: 0 !important;
      padding: 0 !important;
      position: absolute !important;
      width: 100% !important;
      z-index: 2 !important;
    }
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploaderDropzone"] button *,
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploaderDropzone"]
      [data-testid="stBaseButton-secondary"] * {
      color: transparent !important;
      opacity: 0 !important;
    }
    .st-key-p2_factsheet_dropbox [data-testid="stFileUploaderFile"] {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 3px !important;
      color: var(--surf-paper5) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      margin: 10px auto 0 !important;
      max-width: calc(100% - 48px) !important;
      position: relative !important;
      z-index: 4 !important;
    }

    /* Form submit buttons — DISCARD CLASS DRAFT (neutral) + CREATE CLASS (primary). */
    .st-key-p2_add_class_form_card [data-testid="stFormSubmitButton"] button {
      border-radius: 3px !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      height: 48px !important;
      letter-spacing: 0.14em !important;
      padding: 0 18px !important;
      text-transform: uppercase !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
      width: 100% !important;
    }
    /* Neutral default for form submit */
    .st-key-p2_add_class_form_card [data-testid="stFormSubmitButton"] button {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
    }
    /* Primary form submit (kind="primary" / kind="primaryFormSubmit"). */
    .st-key-p2_add_class_form_card
      [data-testid="stFormSubmitButton"] button[kind="primary"],
    .st-key-p2_add_class_form_card
      [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] {
      background: var(--surf-paper5) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      color: var(--surf-paper) !important;
    }
    .st-key-p2_add_class_form_card
      [data-testid="stFormSubmitButton"] button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .st-key-p2_add_class_form_card
      [data-testid="stFormSubmitButton"] button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }

    /* Class cards — hard-stamp 3px (§2.5.b regular). Styled directly
       on the keyed container so we don't depend on Streamlit's
       border-wrapper DOM. The key is unique per class
       (`p2_class_card_{id}`); the prefix selector matches every card. */
    [class*="st-key-p2_class_card_"] {
      background: var(--surf-paper0) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 4px !important;
      box-shadow: 3px 3px 0 var(--surf-shadow) !important;
      margin: 0 0 16px !important;
      padding: 24px 28px !important;
    }

    .surf-p2-card-row {
      align-items: center;
      display: flex;
      gap: 32px;
      justify-content: space-between;
      width: 100%;
    }

    .surf-p2-card-name {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 32px;
      font-style: italic;
      font-weight: 600;
      letter-spacing: -0.01em;
      line-height: 1.05;
      margin: 0 0 16px;
    }

    .surf-p2-card-statgroup {
      color: var(--surf-paper4);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 13px;
      font-weight: 400;
      letter-spacing: 0.04em;
      line-height: 1.6;
      text-transform: lowercase;
    }

    /* Title-row right cell: avg score + sub-label */
    .surf-p2-card-avg {
      align-items: flex-end;
      display: flex;
      flex-direction: column;
      flex: 0 0 auto;
      gap: 4px;
      min-width: 200px;
    }
    .surf-p2-card-avg-value {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 56px;
      font-style: italic;
      font-weight: 700;
      letter-spacing: -0.02em;
      line-height: 1;
      text-align: right;
    }
    .surf-p2-card-avg-value.tier-fail { color: var(--surf-accent-deep); }
    .surf-p2-card-avg-value.tier-borderline { color: var(--surf-status-warn); }
    .surf-p2-card-avg-value.tier-pass { color: var(--surf-status-ok); }
    .surf-p2-card-avg-value.tier-empty { color: var(--surf-paper3); }
    .surf-p2-card-avg-label {
      color: var(--surf-paper4);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      font-weight: 400;
      letter-spacing: 0.06em;
      text-transform: lowercase;
    }

    /* Card action row — full-width DELETE CLASS (neutral) +
       ENTER CLASS > (primary), both stamped 4px (§2.5.a).
       Per-class button keys: `delete_class_{id}` / `open_class_{id}`. */
    div[class*="st-key-delete_class_"] button,
    div[class*="st-key-open_class_"] button {
      border-radius: 3px !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      height: 48px !important;
      letter-spacing: 0.14em !important;
      margin-top: 16px !important;
      padding: 0 18px !important;
      text-transform: uppercase !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
      width: 100% !important;
    }
    /* Neutral DELETE CLASS variant. */
    div[class*="st-key-delete_class_"] button {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
    }
    /* Primary ENTER CLASS > variant (Streamlit type="primary"). */
    div[class*="st-key-open_class_"] button,
    div[class*="st-key-open_class_"] button[kind="primary"] {
      background: var(--surf-paper5) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
    }
    div[class*="st-key-delete_class_"] button:hover,
    div[class*="st-key-open_class_"] button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    div[class*="st-key-delete_class_"] button:active,
    div[class*="st-key-open_class_"] button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }

    /* Empty state card */
    .st-key-p2_empty_state_card [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-p2_empty_state_card > [data-testid="stLayoutWrapper"]
      > [data-testid="stVerticalBlock"] {
      background: var(--surf-paper0) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 4px !important;
      box-shadow: 3px 3px 0 var(--surf-shadow) !important;
      margin: 0 !important;
      padding: 32px 28px !important;
      text-align: center !important;
    }
    .surf-p2-empty-text {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 17px;
      font-weight: 400;
      line-height: 1.5;
      margin: 0;
      text-align: center;
    }

    /* Reduced-motion accommodation. */
    @media (prefers-reduced-motion: reduce) {
      .st-key-p2_my_classes_page [data-testid="stButton"] button,
      .st-key-p2_my_classes_page [data-testid="stButton"] button:hover,
      .st-key-p2_my_classes_page [data-testid="stButton"] button:active {
        transform: none !important;
        transition: background 0.08s ease-out !important;
      }
    }
    </style>
    """
    )


def _render_class_card(view_model: dict[str, Any], *, switch_page_fn) -> None:
    class_id = view_model["class_id"]
    class_name = view_model["class_name"]

    with st.container(key=f"p2_class_card_{class_id}"):
        # Row 1: title + stats on the left, big colored avg score on the right.
        row_col_left, row_col_right = st.columns([3, 2], gap="medium")
        with row_col_left:
            st.html(
                f'<div class="surf-p2-card-name">{escape(class_name)}</div>'
            )
            stat_left, stat_right = st.columns(2, gap="medium")
            with stat_left:
                left_html = "<br>".join(
                    escape(line) for line in view_model["left_stats"]
                )
                st.html(
                    f'<div class="surf-p2-card-statgroup">{left_html}</div>'
                )
            with stat_right:
                right_html = "<br>".join(
                    escape(line) for line in view_model["right_stats"]
                )
                st.html(
                    f'<div class="surf-p2-card-statgroup">{right_html}</div>'
                )
        with row_col_right:
            tier_class = f'tier-{view_model["avg_score_tier"]}'
            st.html(
                f'<div class="surf-p2-card-avg">'
                f'<span class="surf-p2-card-avg-value {tier_class}">'
                f"{escape(view_model['avg_score_value'])}"
                "</span>"
                f'<span class="surf-p2-card-avg-label">'
                f"{escape(view_model['avg_score_label'])}"
                "</span>"
                "</div>"
            )

        # Row 2: full-width DELETE CLASS (neutral) + ENTER CLASS > (primary).
        action_left, action_right = st.columns(2, gap="medium")
        with action_left:
            if st.button(
                DELETE_TRIGGER_LABEL,
                key=f"delete_class_{class_id}",
                help=f"Delete class {class_name}",
                use_container_width=True,
            ):
                st.session_state[DELETE_PENDING_KEY] = class_id
        with action_right:
            if st.button(
                ENTER_CLASS_LABEL,
                key=f"open_class_{class_id}",
                help=f"Open class {class_name}",
                type="primary",
                use_container_width=True,
            ):
                handle_open_class(
                    class_id=class_id,
                    state=st.session_state,
                    switch_page_fn=switch_page_fn,
                )


def _render_delete_dialog(
    *,
    class_id: int,
    class_name: str,
    delete_after_confirm_fn: Callable[..., dict[str, Any]],
    user_id: int,
) -> None:
    @st.dialog(DIALOG_TITLE)
    def _dialog() -> None:
        st.html(
            '<p class="surf-p2-helper">'
            f"{escape(format_dialog_body(class_name))}"
            "</p>"
        )
        col_keep, col_delete = st.columns(2, gap="small")
        with col_keep:
            keep_clicked = st.button(
                KEEP_LABEL,
                key="p2_delete_keep",
                use_container_width=True,
            )
        with col_delete:
            confirm_clicked = st.button(
                DELETE_LABEL,
                key="p2_delete_confirm",
                use_container_width=True,
            )

        if keep_clicked:
            st.session_state.pop(DELETE_PENDING_KEY, None)
            st.rerun()
        if confirm_clicked:
            result = delete_after_confirm_fn(
                user_id=user_id,
                class_id=class_id,
                confirmed=True,
            )
            st.session_state.pop(DELETE_PENDING_KEY, None)
            if result["status"] == "deleted":
                st.toast(DELETE_SUCCESS_TOAST)
            elif result["status"] == "not_owned":
                st.toast(
                    "Couldn't delete that class — it isn't on this account."
                )
            else:
                st.toast(
                    "Couldn't delete that class. Try again, or check your "
                    "local data file in Settings."
                )
            st.rerun()

    _dialog()


def _render_add_class_form(
    *,
    user_id: int,
    submit_fn: Callable[..., dict[str, Any]],
) -> None:
    with (
        st.container(key="p2_add_class_form_card"),
        st.form("p2_add_class_form", clear_on_submit=False),
    ):
        st.html('<div class="surf-p2-form-title">Add Class</div>')
        st.html(f'<div class="surf-p2-field-label">{escape(CLASS_NAME_LABEL)}</div>')
        class_name = st.text_input(
            CLASS_NAME_LABEL,
            key="p2_add_class_name",
            label_visibility="collapsed",
            max_chars=CLASS_NAME_MAX_LENGTH,
            placeholder="Type here",
        )
        st.html(
            f'<div class="surf-p2-field-label">{escape(GRADE_THRESHOLD_LABEL)}</div>'
        )
        threshold = st.slider(
            GRADE_THRESHOLD_LABEL,
            min_value=GRADE_THRESHOLD_MIN,
            max_value=GRADE_THRESHOLD_MAX,
            value=GRADE_THRESHOLD_DEFAULT,
            step=GRADE_THRESHOLD_STEP,
            key="p2_add_class_threshold",
            label_visibility="collapsed",
            format="%d%%",
        )
        st.html(
            f'<p class="surf-p2-field-helper">{escape(GRADE_THRESHOLD_HELPER)}</p>'
        )
        st.html(f'<div class="surf-p2-field-label">{escape(FACTSHEET_LABEL)}</div>')
        with st.container(key="p2_factsheet_dropbox"):
            st.html(
                '<div class="surf-p2-dropbox-visual">'
                '<span class="surf-p2-dropbox-icon" aria-hidden="true"></span>'
                '<div class="surf-p2-dropbox-title">DROPBOX</div>'
                '<p class="surf-p2-dropbox-helper">UPLOAD YOUR FACTSHEET</p>'
                '</div>'
            )
            factsheet_file = st.file_uploader(
                FACTSHEET_LABEL,
                type=["pdf"],
                key="p2_add_class_factsheet",
                label_visibility="collapsed",
            )
            if factsheet_file is not None:
                st.html(
                    '<p class="surf-p2-dropbox-ready">READY: '
                    f'{escape(getattr(factsheet_file, "name", "factsheet.pdf"))}'
                    '</p>'
                )
        st.html(
            f'<p class="surf-p2-field-helper">{escape(FACTSHEET_HELPER)}</p>'
        )

        col_discard, col_create = st.columns([2, 3], gap="small")
        with col_discard:
            discard_clicked = st.form_submit_button(
                DISCARD_DRAFT_LABEL,
                use_container_width=True,
            )
        with col_create:
            create_clicked = st.form_submit_button(
                CREATE_CLASS_LABEL,
                type="primary",
                use_container_width=True,
            )

    if discard_clicked:
        st.session_state[ADD_CLASS_OPEN_KEY] = False
        for stale in (
            "p2_add_class_name",
            "p2_add_class_threshold",
            "p2_add_class_factsheet",
        ):
            st.session_state.pop(stale, None)
        st.rerun()
    elif create_clicked:
        cleaned_name = (class_name or "").strip()
        if not cleaned_name:
            st.error(MISSING_NAME_ERROR)
            return
        if len(cleaned_name) > CLASS_NAME_MAX_LENGTH:
            st.error(INVALID_NAME_ERROR)
            return
        if factsheet_file is None:
            st.error(MISSING_FACTSHEET_ERROR)
            return
        popup = st.empty()
        show_processing_popup(popup, state="processing")
        with st.spinner(PROCESSING_TOAST):
            result = submit_fn(
                user_id=user_id,
                class_name=cleaned_name,
                grade4_threshold_percent=int(threshold),
                factsheet_file=factsheet_file,
            )
        if result.get("ok"):
            show_processing_popup(popup, state="done")
            sleep(0.75)
            st.toast(SAVE_SUCCESS_TOAST)
            st.session_state[ADD_CLASS_OPEN_KEY] = False
            for stale in (
                "p2_add_class_name",
                "p2_add_class_threshold",
                "p2_add_class_factsheet",
            ):
                st.session_state.pop(stale, None)
            st.rerun()
        elif result.get("error") == "missing_factsheet":
            popup.empty()
            st.error(MISSING_FACTSHEET_ERROR)
        elif result.get("error") == "missing_api_key":
            popup.empty()
            st.error(MISSING_API_KEY_ERROR)
        else:
            popup.empty()
            st.toast(f"{PROCESS_FAIL_TITLE} — {PROCESS_FAIL_BODY}")


def _default_layout_renderer(payload: dict[str, Any]) -> None:
    """Default Streamlit renderer for :func:`render_my_classes_page`."""
    user = payload["user"]
    submit_fn = payload["submit_fn"]
    delete_after_confirm_fn = payload["delete_after_confirm_fn"]
    switch_page_fn = payload["switch_page_fn"]
    card_view_models = payload["card_view_models"]
    name_by_class_id = payload["name_by_class_id"]

    st.html(_styles())
    with page_rail("p2_my_classes_page"):
        render_page_header(
            kicker="SURFBOARD",
            title=payload["page_title"],
            helper=payload["helper_paragraph"],
            key="p2_page_header",
        )

        if st.button(
            ADD_CLASS_LABEL,
            key="p2_add_class_button",
            use_container_width=True,
        ):
            current = bool(st.session_state.get(ADD_CLASS_OPEN_KEY, False))
            st.session_state[ADD_CLASS_OPEN_KEY] = not current
            st.rerun()

        if st.session_state.get(ADD_CLASS_OPEN_KEY, False):
            _render_add_class_form(
                user_id=int(user["id"]),
                submit_fn=submit_fn,
            )

        if not card_view_models:
            with (
                st.container(key="p2_empty_state_card"),
                st.container(border=True),
            ):
                st.html(
                    f'<p class="surf-p2-empty-text">'
                    f"{escape(EMPTY_STATE_COPY)}"
                    "</p>"
                )
        else:
            for view_model in card_view_models:
                _render_class_card(view_model, switch_page_fn=switch_page_fn)

        # Pop (not get): clearing the pending id as we hand it to the
        # dialog prevents an unrelated rerun (e.g. user clicking
        # ADD CLASS) from re-opening the modal after the user
        # dismissed it via the X. Streamlit's @st.dialog keeps the
        # modal alive on its own — once the user closes or confirms
        # this code path won't re-trigger.
        pending_id = st.session_state.pop(DELETE_PENDING_KEY, None)
        if pending_id is not None and pending_id in name_by_class_id:
            _render_delete_dialog(
                class_id=pending_id,
                class_name=name_by_class_id[pending_id],
                delete_after_confirm_fn=delete_after_confirm_fn,
                user_id=int(user["id"]),
            )


def render_my_classes_page(
    *,
    user: Mapping[str, Any],
    topbar_fn: Callable[[str], None] = render_topbar,
    list_classes_fn: Callable[[int], list[dict[str, Any]]] = list_classes_for_user,
    list_class_stats_fn: Callable[[int], dict[int, dict[str, Any]]] = _default_list_class_stats,
    submit_fn: Callable[..., dict[str, Any]] = submit_add_class_form,
    delete_after_confirm_fn: Callable[..., dict[str, Any]] = delete_class_after_confirmation,
    switch_page_fn: Callable[[str], None] | None = None,
    render_layout_fn: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Render P2 — My Classes.

    Composes the shared topbar, page chrome, ADD CLASS form, class
    cards, and destructive delete dialog. All side-effect entry points
    (topbar, queries, services, navigation, layout) are injectable so
    tests and the preview sandbox can run with fakes.
    """
    topbar_fn("my_classes")

    classes = list_classes_fn(int(user["id"])) or []
    stats = list_class_stats_fn(int(user["id"])) or {}
    card_view_models = build_class_card_view_models(classes, stats)
    name_by_class_id = {c["id"]: c.get("name", "") for c in classes}

    payload: dict[str, Any] = {
        "page_title": PAGE_TITLE,
        "helper_paragraph": HELPER_PARAGRAPH,
        "user": dict(user),
        "card_view_models": card_view_models,
        "name_by_class_id": name_by_class_id,
        "submit_fn": submit_fn,
        "delete_after_confirm_fn": delete_after_confirm_fn,
        "switch_page_fn": switch_page_fn or st.switch_page,
        "add_class_open": bool(
            st.session_state.get(ADD_CLASS_OPEN_KEY, False)
        ) if hasattr(st, "session_state") else False,
    }

    layout = render_layout_fn or _default_layout_renderer
    layout(payload)

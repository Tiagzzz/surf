"""P4 — Take Mock / Practice page renderer.

The renderer keeps answer state in Streamlit session only until the final
submit boundary. Visual chrome follows Surf's Streamlit-connected custom UI
pattern: real Streamlit buttons provide behavior and scoped CSS/HTML overlays
provide the Figma-like card appearance.
"""
# Renders P4 while leaving answers session-only until final submit.
from __future__ import annotations

import base64
from collections.abc import Mapping
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

import app.mock_take.answer_capture as answer_capture
from app.brain.question_type import QUESTION_TYPE_LABELS, normalize_question_type
from app.brain.topbar import render_topbar
from app.class_.mock_standard_launch import (
    FROZEN_QUESTION_IDS_KEY,
    MOCK_KIND_KEY,
    P4_LAUNCH_STATE_KEY,
    QUESTION_PAYLOADS_KEY,
    SELECTED_LECTURE_IDS_KEY,
)
from app.db.queries_classes import get_class_by_id
from app.db.queries_questions import get_question_display_context
from app.mock_take.attempt_save import submit_attempt

__all__ = ["P4_SHOW_SUBMIT_DIALOG_KEY", "render_take_mock_page"]

# Submit-dialog flag shared with the final confirmation renderer.
# The literal string is part of the session-state contract and MUST NOT drift.
P4_SHOW_SUBMIT_DIALOG_KEY = "p4_show_submit_dialog"

_ATTEMPT_STATE_FALLBACK_KEY = "p4_attempt_in_progress"
_SUBMIT_DIALOG_FALLBACK = "open_submit_dialog"
_HELPER_TEXT_LEGACY_SENTINEL = "Select an option or press SKIP"
_CHECKMARK_DATA_URI = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'>"
    "<path d='M3 8l3 3 7-7' stroke='%23FDF9F2' stroke-width='2.5' "
    "fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>"
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


def _styles() -> str:
    return (
        "<style>\n"
        + _font_face_block()
        + f"""
    :root {{
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
      --surf-accent-wash: #F7D9D1;
      --surf-status-ok-wash: #9EC7AA;
    }}
    .stApp {{ background: var(--surf-paper) !important; }}
    .st-key-p4_take_mock_page [data-testid="stButton"] button,
    .stDialog .st-key-p4_dialog_keep_answering button,
    .stDialog .st-key-p4_dialog_finish_mock button {{
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      letter-spacing: 0.14em !important;
      text-transform: uppercase !important;
    }}
    [data-testid="stMainBlockContainer"] {{
      max-width: none !important;
    }}
    .st-key-p4_take_mock_page {{
      box-sizing: border-box;
      padding: 0 32px 32px !important;
    }}
    .surf-p4-hero {{
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
    }}
    .surf-p4-hero-left {{ align-items: center; display: flex; gap: 32px; }}
    .surf-p4-counter-label,
    .surf-p4-lo-large,
    .surf-p4-lo,
    .surf-p4-helper {{
      font-family: "JetBrains Mono", ui-monospace, monospace;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }}
    .surf-p4-counter-label {{
      color: var(--surf-paper5); font-size: 11px; font-weight: 700; margin: 0 0 4px;
    }}
    .surf-p4-counter {{
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 64px;
      font-style: italic;
      font-weight: 900;
      letter-spacing: -0.02em;
      line-height: 0.95;
      margin: 0;
    }}
    .surf-p4-counter .current {{ color: var(--surf-accent-deep); }}
    .surf-p4-mode {{
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 42px;
      font-style: italic;
      font-weight: 900;
      letter-spacing: -0.02em;
      line-height: 0.95;
      margin: 0 0 10px;
    }}
    .surf-p4-lo-large {{
      color: var(--surf-paper5); font-size: 19px; font-weight: 500; margin: 0;
    }}
    .st-key-p4_question_card {{
      background: var(--surf-paper) !important;
      border: 3px solid var(--surf-shadow) !important;
      border-radius: 8px !important;
      box-shadow: 7px 7px 0 var(--surf-shadow) !important;
      box-sizing: border-box;
      margin: 0 auto !important;
      max-width: 880px !important;
      padding: 30px 32px 28px !important;
      width: 100% !important;
    }}
    .surf-question-type-chip {{
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
    }}
    .surf-p4-lo {{ color: #1A1814; font-size: 11px; font-weight: 700; margin: 0 0 22px; }}
    .surf-p4-question-text {{
      color: #1A1814;
      font-family: "Fraunces", Georgia, serif;
      font-size: 27px;
      font-style: italic;
      font-weight: 600;
      letter-spacing: -0.01em;
      line-height: 1.08;
      margin: 0 0 28px;
    }}
    [class*="st-key-p4_option_pick_"] {{
      border-radius: 5px !important;
      box-sizing: border-box;
      margin: 0 0 16px;
      overflow: hidden;
      position: relative;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out,
        border-color 0.08s ease-out;
    }}
    [class*="st-key-p4_option_pick_selected_"] {{
      background: var(--surf-paper) !important;
      border: 2px solid var(--surf-shadow) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
    }}
    [class*="st-key-p4_option_pick_selected_"]:hover {{
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }}
    [class*="st-key-p4_option_pick_unselected_"] {{
      background: var(--surf-paper1) !important;
      border: 2px solid var(--surf-shadow) !important;
      box-shadow: none !important;
    }}
    [class*="st-key-p4_option_pick_unselected_"]:hover {{
      background: var(--surf-paper) !important;
      transform: translate(-1px, -1px) !important;
    }}
    [class*="st-key-p4_option_pick_"]:active {{
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }}
    [class*="st-key-p4_option_btn_"] {{
      bottom: 0 !important;
      height: 100% !important;
      left: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      position: absolute !important;
      right: 0 !important;
      top: 0 !important;
      width: 100% !important;
      z-index: 3 !important;
    }}
    [class*="st-key-p4_option_btn_"] [data-testid="stElementContainer"],
    [class*="st-key-p4_option_btn_"] [data-testid="stButton"],
    [class*="st-key-p4_option_btn_"] .stButton {{
      height: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      width: 100% !important;
    }}
    [class*="st-key-p4_option_pick_"] [data-testid="stButton"] button {{
      background: transparent !important;
      border: 0 !important;
      border-radius: 5px !important;
      box-shadow: none !important;
      box-sizing: border-box !important;
      color: transparent !important;
      cursor: pointer !important;
      font-size: 0 !important;
      height: 100% !important;
      line-height: 0 !important;
      margin: 0 !important;
      min-height: 100% !important;
      padding: 0 !important;
      text-indent: -9999px !important;
      width: 100% !important;
    }}
    .surf-p4-option-overlay {{
      align-items: center;
      box-sizing: border-box;
      display: flex;
      gap: 18px;
      min-height: 72px;
      padding: 16px 22px;
      pointer-events: none;
      position: relative;
      z-index: 1;
    }}
    .surf-p4-option-checkbox {{
      background: var(--surf-paper);
      border: 3px solid var(--surf-paper5);
      border-radius: 5px;
      display: inline-block;
      flex: 0 0 auto;
      height: 28px;
      margin-top: 0;
      position: relative;
      width: 28px;
    }}
    .surf-p4-option-checkbox.is-selected {{ background: var(--surf-paper5); }}
    .surf-p4-option-checkbox.is-selected::before {{
      background-image: url("{_CHECKMARK_DATA_URI}");
      background-position: center;
      background-repeat: no-repeat;
      background-size: 15px 15px;
      content: "";
      inset: 0;
      position: absolute;
    }}
    .surf-p4-option-text {{
      color: var(--surf-paper5);
      flex: 1 1 auto;
      font-family: "Fraunces", Georgia, serif;
      font-size: 18px;
      font-weight: 400;
      line-height: 1.22;
      min-width: 0;
      overflow-wrap: anywhere;
      white-space: normal;
    }}
    .surf-p4-helper {{
      color: var(--surf-paper4);
      font-size: 10px;
      font-weight: 400;
      margin: 12px 0 0;
    }}
    .st-key-p4_question_card [data-testid="stHorizontalBlock"] {{
      gap: 18px !important;
      margin-top: 20px !important;
    }}
    div[class*="st-key-p4_skip"] button,
    div[class*="st-key-p4_recovery_back_to_class"] button,
    div[class*="st-key-p4_recovery_my_classes"] button {{
      background: var(--surf-paper) !important;
      border: 2px solid var(--surf-shadow) !important;
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
      font-size: 11px !important;
      font-weight: 700 !important;
      min-height: 58px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
    }}
    div[class*="st-key-p4_next"] button,
    div[class*="st-key-p4_finish_mock"] button {{
      background: var(--surf-paper5) !important;
      border: 2px solid var(--surf-shadow) !important;
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
      font-size: 11px !important;
      font-weight: 700 !important;
      min-height: 58px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
    }}
    div[class*="st-key-p4_skip"] button:hover,
    div[class*="st-key-p4_recovery_back_to_class"] button:hover,
    div[class*="st-key-p4_recovery_my_classes"] button:hover,
    div[class*="st-key-p4_next"] button:hover,
    div[class*="st-key-p4_finish_mock"] button:hover {{
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }}
    div[class*="st-key-p4_skip"] button:active,
    div[class*="st-key-p4_recovery_back_to_class"] button:active,
    div[class*="st-key-p4_recovery_my_classes"] button:active,
    div[class*="st-key-p4_next"] button:active,
    div[class*="st-key-p4_finish_mock"] button:active {{
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }}
    div[class*="st-key-p4_next"] button:disabled,
    div[class*="st-key-p4_finish_mock"] button:disabled {{
      background: var(--surf-paper1) !important;
      border-color: var(--surf-paper3) !important;
      box-shadow: none !important;
      color: var(--surf-paper3) !important;
      cursor: not-allowed !important;
      transform: none !important;
    }}
    .stDialog {{
      align-items: center !important;
      backdrop-filter: blur(2px) !important;
      background: rgba(40, 37, 31, 0.32) !important;
      display: flex !important;
      justify-content: center !important;
    }}
    .stDialog > div {{
      align-items: center !important;
      justify-content: center !important;
    }}
    .stDialog [role="dialog"] {{
      background: var(--surf-paper) !important;
      border: 2px solid var(--surf-paper5) !important;
      border-radius: 6px !important;
      box-shadow: 6px 6px 0 var(--surf-shadow) !important;
      max-width: 480px !important;
      padding: 26px 30px !important;
    }}
    .stDialog [data-testid="stDialogTitle"],
    .stDialog h2 {{
      color: var(--surf-paper5) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 22px !important;
      font-style: italic !important;
      font-weight: 700 !important;
      letter-spacing: -0.01em !important;
      margin: 0 0 16px !important;
    }}
    .stDialog .st-key-p4_dialog_keep_answering button {{
      background: var(--surf-paper) !important;
      border: 2px solid var(--surf-paper5) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
      min-height: 52px !important;
    }}
    .stDialog .st-key-p4_dialog_finish_mock button {{
      background: var(--surf-paper5) !important;
      border: 2px solid var(--surf-shadow) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
      min-height: 52px !important;
    }}
    .stDialog .st-key-p4_dialog_keep_answering button:hover,
    .stDialog .st-key-p4_dialog_finish_mock button:hover {{
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }}
    .stDialog .st-key-p4_dialog_keep_answering button:active,
    .stDialog .st-key-p4_dialog_finish_mock button:active {{
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }}
    .stDialog .st-key-p4_dialog_keep_answering button:disabled,
    .stDialog .st-key-p4_dialog_finish_mock button:disabled {{
      background: var(--surf-paper1) !important;
      border-color: var(--surf-paper3) !important;
      color: var(--surf-paper3) !important;
      cursor: not-allowed !important;
      transform: none !important;
    }}
    .surf-p4-submit-error {{
      color: var(--surf-accent-deep) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 13px !important;
      font-weight: 400 !important;
      letter-spacing: 0.01em !important;
      line-height: 1.34 !important;
      margin: 12px 0 0 !important;
    }}
    @media (prefers-reduced-motion: reduce) {{
      .st-key-p4_take_mock_page button,
      .st-key-p4_take_mock_page button:hover,
      .st-key-p4_take_mock_page button:active,
      .stDialog .st-key-p4_dialog_keep_answering button,
      .stDialog .st-key-p4_dialog_keep_answering button:hover,
      .stDialog .st-key-p4_dialog_keep_answering button:active,
      .stDialog .st-key-p4_dialog_finish_mock button,
      .stDialog .st-key-p4_dialog_finish_mock button:hover,
      .stDialog .st-key-p4_dialog_finish_mock button:active {{
        transform: none !important;
        transition: background 0.08s ease-out !important;
      }}
    }}
    """
        + "\n</style>"
    )


def _attempt_state_key() -> str:
    return str(getattr(answer_capture, "P4_IN_PROGRESS_KEY", _ATTEMPT_STATE_FALLBACK_KEY))


def _new_attempt_state(launch_state: Mapping[str, Any]) -> dict[str, Any]:
    if hasattr(answer_capture, "init_attempt_state"):
        try:
            return answer_capture.init_attempt_state(dict(launch_state))
        except TypeError:
            return answer_capture.init_attempt_state()
    return {
        "selected_indices_by_qid": {},
        "skipped_qids": set(),
        "current_index": 0,
        "started_at": None,
        "submit_in_flight": False,
        "submitted_attempt_id": None,
    }


def _get_attempt_state(launch_state: Mapping[str, Any]) -> dict[str, Any]:
    key = _attempt_state_key()
    state = st.session_state.get(key)
    if not isinstance(state, dict):
        state = _new_attempt_state(launch_state)
        st.session_state[key] = state
    return state


def _selected_indices(state: Mapping[str, Any], qid: int) -> list[int]:
    selected_by_qid = state.get("selected_indices_by_qid")
    if not isinstance(selected_by_qid, Mapping):
        return []
    values = selected_by_qid.get(qid, selected_by_qid.get(str(qid), []))
    if not isinstance(values, list):
        return []
    return [int(value) for value in values]


def _toggle_option(state: dict[str, Any], qid: int, option_index: int) -> None:
    if hasattr(answer_capture, "toggle_option"):
        try:
            answer_capture.toggle_option(state, question_id=qid, option_index=option_index)
        except TypeError:
            answer_capture.toggle_option(state, qid, option_index)
        return
    skipped = state.setdefault("skipped_qids", set())
    if hasattr(skipped, "discard"):
        skipped.discard(qid)
    selected_by_qid = state.setdefault("selected_indices_by_qid", {})
    current = list(selected_by_qid.get(qid, []))
    if option_index in current:
        current = [value for value in current if value != option_index]
    else:
        current = sorted({*current, option_index})
    selected_by_qid[qid] = current


def _mark_skipped(state: dict[str, Any], qid: int) -> None:
    if hasattr(answer_capture, "mark_skipped"):
        try:
            answer_capture.mark_skipped(state, question_id=qid)
        except TypeError:
            answer_capture.mark_skipped(state, qid)
        return
    state.setdefault("selected_indices_by_qid", {})[qid] = []
    state.setdefault("skipped_qids", set()).add(qid)


def _can_advance(state: dict[str, Any], qid: int) -> bool:
    if hasattr(answer_capture, "can_advance"):
        try:
            return bool(answer_capture.can_advance(state, question_id=qid))
        except TypeError:
            return bool(answer_capture.can_advance(state, qid))
    skipped = state.get("skipped_qids", set())
    return qid in skipped or bool(_selected_indices(state, qid))


def _advance(state: dict[str, Any], total_questions: int) -> str | None:
    if hasattr(answer_capture, "advance"):
        try:
            return answer_capture.advance(state, total_questions=total_questions)
        except TypeError:
            return answer_capture.advance(state, total_questions)
    state["current_index"] = int(state.get("current_index", 0)) + 1
    if state["current_index"] >= total_questions:
        return str(getattr(answer_capture, "SUBMIT_DIALOG_SENTINEL", _SUBMIT_DIALOG_FALLBACK))
    return None


def _question_type_label(value: object) -> str:
    slug = normalize_question_type(value)
    return QUESTION_TYPE_LABELS.get(slug, "Type unavailable")


def _mode_label(mock_kind: object) -> str:
    return "Practice" if mock_kind == "practice" else "Mock Exam"


def _question_id(question: Mapping[str, Any], fallback: int) -> int:
    try:
        return int(question.get("id", fallback))
    except (TypeError, ValueError):
        return fallback


def _question_payloads(launch_state: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    payloads = launch_state.get("question_payloads", [])
    if not isinstance(payloads, list):
        return []
    return [payload for payload in payloads if isinstance(payload, Mapping)]


def _render_topbar(*, class_name: object, mode_label: str) -> None:
    clean_class_name = class_name if isinstance(class_name, str) and class_name.strip() else None
    try:
        render_topbar(
            current_page="take_mock_exam",
            class_name=clean_class_name,
            mode_label=mode_label,
        )
    except TypeError:
        render_topbar(current_page="take_mock_exam", class_name=clean_class_name)


def _recovery_html() -> str:
    return (
        '<div class="surf-p4-hero"><div class="surf-p4-hero-left"><div>'
        '<p class="surf-p4-mode">No mock in progress.</p>'
        '<p class="surf-p4-lo-large">Return to class and launch a mock or practice.</p>'
        '</div></div></div>'
    )


def _render_submit_dialog_body(
    *,
    launch_state: Mapping[str, Any],
    attempt_state: dict[str, Any],
    total_count: int,
    mock_kind: object,
) -> None:
    _ = total_count
    title = "Finish practice?" if mock_kind == "practice" else "Finish mock?"
    finish_label = "FINISH PRACTICE" if mock_kind == "practice" else "FINISH MOCK"

    frozen_qids = launch_state.get("frozen_question_ids", [])
    if not isinstance(frozen_qids, list):
        frozen_qids = []
    skipped_qids = attempt_state.get("skipped_qids", set())
    if isinstance(skipped_qids, list):
        skipped_qids = set(skipped_qids)
    if not isinstance(skipped_qids, set):
        skipped_qids = set()

    selected_by_qid = attempt_state.get("selected_indices_by_qid", {})
    if not isinstance(selected_by_qid, Mapping):
        selected_by_qid = {}

    answered_count = 0
    try:
        for raw_qid in frozen_qids:
            qid = int(raw_qid)
            selected_values = selected_by_qid.get(qid, selected_by_qid.get(str(qid), []))
            if (
                qid not in skipped_qids
                and isinstance(selected_values, list)
                and len(selected_values) > 0
            ):
                answered_count += 1
    except (TypeError, ValueError):
        answered_count = 0

    skipped_count = len(skipped_qids)

    _ = title
    st.markdown(
        f"Answered: {answered_count} · Skipped: {skipped_count}", unsafe_allow_html=True
    )
    if skipped_count > 0:
        st.markdown("Skipped questions count as wrong.", unsafe_allow_html=True)

    action_col, finish_col = st.columns(2)
    with action_col:
        with st.container(key="p4_dialog_keep_answering"):
            if st.button("KEEP ANSWERING", use_container_width=True):
                st.session_state[P4_SHOW_SUBMIT_DIALOG_KEY] = False
                st.rerun()

    with finish_col:
        with st.container(key="p4_dialog_finish_mock"):
            if st.button(
                finish_label,
                use_container_width=True,
                disabled=attempt_state.get("submit_in_flight", False),
            ):
                status = submit_attempt(
                    launch_state=dict(launch_state), attempt_state=attempt_state
                )
                status_type = status.get("status")
                if status_type == "submitted":
                    result = status.get("result", {})
                    attempt_id = result.get("attempt_id")
                    if isinstance(attempt_id, int):
                        st.session_state["current_attempt_id"] = attempt_id
                    st.session_state.pop(P4_LAUNCH_STATE_KEY, None)
                    st.session_state.pop(FROZEN_QUESTION_IDS_KEY, None)
                    st.session_state.pop(QUESTION_PAYLOADS_KEY, None)
                    st.session_state.pop(MOCK_KIND_KEY, None)
                    st.session_state.pop(SELECTED_LECTURE_IDS_KEY, None)
                    st.session_state.pop(_attempt_state_key(), None)
                    st.session_state[P4_SHOW_SUBMIT_DIALOG_KEY] = False
                    st.switch_page("views/review_mock_exam.py")
                elif status_type == "already_submitted":
                    attempt_id = status.get("attempt_id")
                    if isinstance(attempt_id, int):
                        st.session_state["current_attempt_id"] = attempt_id
                    st.session_state.pop(P4_SHOW_SUBMIT_DIALOG_KEY, None)
                    st.switch_page("views/review_mock_exam.py")
                elif status_type == "in_flight":
                    # Defensive branch; the FINISH button is disabled while in-flight.
                    pass
                elif status_type in {"mock-confirming", "practice-confirming"}:
                    # These are dialog-open pre-submit states in the broader contract.
                    # The renderer should normally never receive them directly.
                    pass
                elif status_type in {"validation_error", "error"}:
                    st.markdown(
                        '<div class="surf-p4-submit-error">'
                        "Couldn't finish your attempt — your answers are still here. "
                        "Try again."
                        "</div>",
                        unsafe_allow_html=True,
                    )
                # in_flight and any unexpected branches are no-ops here on purpose.


@st.dialog("Finish mock?")
def _render_mock_submit_dialog(
    *,
    launch_state: Mapping[str, Any],
    attempt_state: dict[str, Any],
    total_count: int,
) -> None:
    _render_submit_dialog_body(
        launch_state=launch_state,
        attempt_state=attempt_state,
        total_count=total_count,
        mock_kind="mock",
    )


@st.dialog("Finish practice?")
def _render_practice_submit_dialog(
    *,
    launch_state: Mapping[str, Any],
    attempt_state: dict[str, Any],
    total_count: int,
) -> None:
    _render_submit_dialog_body(
        launch_state=launch_state,
        attempt_state=attempt_state,
        total_count=total_count,
        mock_kind="practice",
    )


def _render_submit_dialog(
    *,
    launch_state: Mapping[str, Any],
    attempt_state: dict[str, Any],
    total_count: int,
    mock_kind: object,
) -> None:
    if mock_kind == "practice":
        _render_practice_submit_dialog(
            launch_state=launch_state,
            attempt_state=attempt_state,
            total_count=total_count,
        )
        return
    _render_mock_submit_dialog(
        launch_state=launch_state,
        attempt_state=attempt_state,
        total_count=total_count,
    )


def _render_recovery(*, class_id: int | None) -> None:
    st.markdown(_styles(), unsafe_allow_html=True)
    with st.container(key="p4_take_mock_page"):
        st.html(_recovery_html())
        if class_id is not None:
            with st.container(key="p4_recovery_back_to_class"):
                if st.button(
                    "BACK TO CLASS",
                    key="p4_recovery_back_to_class_button",
                    use_container_width=True,
                ):
                    st.switch_page("views/class_view.py")
        else:
            with st.container(key="p4_recovery_my_classes"):
                if st.button(
                    "MY CLASSES",
                    key="p4_recovery_my_classes_button",
                    use_container_width=True,
                ):
                    st.switch_page("views/my_classes.py")


def _class_name_from_launch(launch_state: Mapping[str, Any], class_id: int | None) -> str | None:
    raw_name = launch_state.get("class_name")
    if isinstance(raw_name, str) and raw_name.strip():
        return raw_name.strip()
    raw_id = launch_state.get("class_id", class_id)
    try:
        resolved_id = int(raw_id)
    except (TypeError, ValueError):
        return None
    try:
        row = get_class_by_id(resolved_id)
    except Exception:
        return None
    if not isinstance(row, Mapping):
        return None
    name = row.get("name")
    return name.strip() if isinstance(name, str) and name.strip() else None


def _display_context_for_question(question: Mapping[str, Any], qid: int) -> dict[str, Any]:
    context: dict[str, Any] = {}
    lo_title = question.get("learning_objective_title") or question.get(
        "learning_objective_label"
    )
    if lo_title:
        context["learning_objective_title"] = lo_title
    if question.get("question_type"):
        context["question_type"] = question.get("question_type")
    if context.get("learning_objective_title") and context.get("question_type"):
        return context
    try:
        row = get_question_display_context(qid)
    except Exception:
        row = None
    if isinstance(row, Mapping):
        context.setdefault("learning_objective_title", row.get("learning_objective_title"))
        context.setdefault("question_type", row.get("question_type"))
    return context


def _hero_html(*, mode_label: str, current: int, total: int, lo_label: object) -> str:
    lo = str(lo_label or "Learning Objective")
    return (
        '<div class="surf-p4-hero">'
        '<div class="surf-p4-hero-left">'
        '<div>'
        '<p class="surf-p4-counter-label">Question</p>'
        f'<p class="surf-p4-counter"><span class="current">{current}</span>/{total}</p>'
        '</div>'
        '<div>'
        f'<p class="surf-p4-mode">{escape(mode_label)}</p>'
        f'<p class="surf-p4-lo-large">{escape(lo)}</p>'
        '</div>'
        '</div>'
        '</div>'
    )


def _question_html(*, lo_label: object, question_type_label: str, question_text: object) -> str:
    lo = str(lo_label or "Learning Objective")
    question = str(question_text or "Question unavailable.")
    return (
        f'<div class="surf-question-type-chip">{escape(question_type_label)}</div>'
        f'<div class="surf-p4-lo">{escape(lo)}</div>'
        f'<div class="surf-p4-question-text">{escape(question)}</div>'
    )


def _option_overlay_html(option_text: object, *, is_selected: bool) -> str:
    checkbox_class = (
        "surf-p4-option-checkbox is-selected" if is_selected else "surf-p4-option-checkbox"
    )
    return (
        '<div class="surf-p4-option-overlay">'
        f'<span class="{checkbox_class}"></span>'
        f'<span class="surf-p4-option-text">{escape(str(option_text))}</span>'
        '</div>'
    )


def render_take_mock_page(*, user: dict, class_id: int | None) -> None:
    """Render the P4 take-mock/practice page from session launch state."""
    # Coordinates recovery, answer controls, navigation, and submit dialogs.
    _ = user
    launch_state = st.session_state.get(P4_LAUNCH_STATE_KEY)
    if not isinstance(launch_state, Mapping) or not launch_state:
        _render_recovery(class_id=class_id)
        return

    mode_label = _mode_label(launch_state.get("mock_kind"))
    _render_topbar(
        class_name=_class_name_from_launch(launch_state, class_id),
        mode_label=mode_label,
    )
    st.markdown(_styles(), unsafe_allow_html=True)

    questions = _question_payloads(launch_state)
    if not questions:
        _render_recovery(class_id=class_id)
        return

    state = _get_attempt_state(launch_state)
    total_questions = len(questions)
    current_index = int(state.get("current_index", 0) or 0)
    current_index = max(0, min(current_index, total_questions - 1))
    state["current_index"] = current_index
    question = questions[current_index]
    qid = _question_id(question, current_index + 1)
    is_final_question = current_index == total_questions - 1
    display_context = _display_context_for_question(question, qid)
    lo_label = display_context.get("learning_objective_title")

    with st.container(key="p4_take_mock_page"):
        st.html(
            _hero_html(
                mode_label=mode_label,
                current=current_index + 1,
                total=total_questions,
                lo_label=lo_label,
            )
        )

        with st.container(key="p4_question_card"):
            st.html(
                _question_html(
                    lo_label=lo_label,
                    question_type_label=_question_type_label(display_context.get("question_type")),
                    question_text=question.get("question_text"),
                )
            )

            options = question.get("options")
            if not isinstance(options, list):
                options = []
            selected = set(_selected_indices(state, qid))
            for option_index, option_text in enumerate(options[:4]):
                option_state = "selected" if option_index in selected else "unselected"
                with st.container(key=f"p4_option_pick_{option_state}_{qid}_{option_index}"):
                    with st.container(key=f"p4_option_btn_{qid}_{option_index}"):
                        if st.button(
                            str(option_text),
                            key=f"p4_option_button_{qid}_{option_index}",
                            use_container_width=True,
                        ):
                            _toggle_option(state, qid, option_index)
                            st.rerun()
                    st.html(
                        _option_overlay_html(
                            option_text,
                            is_selected=option_index in selected,
                        )
                    )

            can_move_forward = _can_advance(state, qid)
            if not can_move_forward:
                st.html(
                    '<div class="surf-p4-helper">Select at least one option, or press SKIP.</div>'
                )

            skip_col, next_col = st.columns(2)
            with skip_col:
                with st.container(key="p4_skip"):
                    if st.button("SKIP", key="p4_skip_button", use_container_width=True):
                        _mark_skipped(state, qid)
                        signal = _advance(state, total_questions)
                        if signal == getattr(
                            answer_capture,
                            "SUBMIT_DIALOG_SENTINEL",
                            _SUBMIT_DIALOG_FALLBACK,
                        ):
                            st.session_state[P4_SHOW_SUBMIT_DIALOG_KEY] = True
                        st.rerun()
            with next_col:
                if is_final_question:
                    finish_label = "FINISH PRACTICE" if mode_label == "Practice" else "FINISH MOCK"
                    with st.container(key="p4_finish_mock"):
                        if st.button(
                            finish_label,
                            key="p4_finish_mock_button",
                            disabled=not can_move_forward,
                            use_container_width=True,
                        ):
                            st.session_state[P4_SHOW_SUBMIT_DIALOG_KEY] = True
                            st.rerun()
                else:
                    with st.container(key="p4_next"):
                        if st.button(
                            "NEXT >",
                            key="p4_next_button",
                            disabled=not can_move_forward,
                            use_container_width=True,
                        ):
                            signal = _advance(state, total_questions)
                            if signal == getattr(
                                answer_capture,
                                "SUBMIT_DIALOG_SENTINEL",
                                _SUBMIT_DIALOG_FALLBACK,
                            ):
                                st.session_state[P4_SHOW_SUBMIT_DIALOG_KEY] = True
                            st.rerun()

    if st.session_state.get(P4_SHOW_SUBMIT_DIALOG_KEY):
        _render_submit_dialog(
            launch_state=launch_state,
            attempt_state=state,
            total_count=total_questions,
            mock_kind=launch_state.get("mock_kind"),
        )

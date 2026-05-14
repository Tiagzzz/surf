"""Surf P7 — Settings page renderer.

Three-card layout locked for Surf V1:

  1. **Profile** — display-name update via :mod:`app.settings.username_save`.
  2. **Anthropic API key** — replace-only-after-validation via
     :mod:`app.settings.api_key_save`. The saved key value is never
     rendered. The ``AI USE`` button reuses the same markdown copy as
     P1 (``app/signup/signup_flow/ai_use_copy.md``) so the explanation
     stays single-sourced.
  3. **Reset app data** — typed ``DELETE`` confirmation gates the
     destructive call to
     :func:`app.settings.reset_account.reset_local_account_data`. After
     a confirmed reset the page clears ``st.session_state`` and reruns
     through the app router so the user lands on Sign Up.

The render function takes the current user dict and the local DB path,
plus injectable services so tests and the preview sandbox can run with
fakes (no real Anthropic call, no live SQLite write).

Visual conventions use Surf stamped buttons, hard-stamp cards, and the
12px / 16px spacing rhythm. Both SVGs (logo + gear) come from the shared
topbar component; nothing in this module touches the asset paths directly.
"""
# --------------------------------------------------------------------------- #
# MODULE OVERVIEW — P7 SETTINGS PAGE
# --------------------------------------------------------------------------- #
# Simple explanation:
# Surf V1 Settings has three cards on one screen: change display name,
# replace the Anthropic API key, and reset all local data. The shared
# topbar is shown at the top of this page. Every sensitive action is
# isolated in its own service module so the renderer never touches SQLite
# or the Anthropic SDK directly.
#
# Important code pieces:
# - Locked copy constants for every visible string (titles, labels,
#   privacy reminders, dialog copy) so the team can audit wording in one
#   place.
# - `is_reset_confirmation_armed`: returns True only when the user types
#   the exact word `DELETE` (case-sensitive); the destructive button
#   stays disabled otherwise.
# - `_render_profile_card` / `_render_api_key_card` / `_render_reset_card`:
#   one helper per card; each takes injectable services.
# - `render_settings_page`: the public entry point called by the view.
#
# App connection (privacy):
# The Anthropic API key is stored locally in plaintext SQLite on this
# user's computer; this is a Surf V1 approved decision. Surf never
# transmits the key anywhere except to Anthropic (via the shared
# `call_claude` wrapper) and never displays it back to the user. The
# Reset card wipes the local SQLite contents, including the saved key,
# and signs the user out.
# Renders the Settings cards while keeping sensitive account actions isolated.
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Callable

import streamlit as st

from app.brain.page_header import render_page_header
from app.brain.page_layout import page_rail
from app.brain.topbar import render_topbar
from app.db.queries_users import get_local_db_path
from app.settings.api_key_save import replace_api_key_after_validation
from app.settings.reset_account import reset_local_account_data
from app.settings.username_save import save_display_name

# --------------------------------------------------------------------------- #
# Locked content strings for the P7 Settings surface
# --------------------------------------------------------------------------- #

PAGE_TITLE = "Settings"
TOPBAR_PAGE_KEY = "settings"

# Profile card
PROFILE_CARD_TITLE = "Profile"
PROFILE_FIELD_LABEL = "NEW DISPLAY NAME"
PROFILE_PRIMARY_LABEL = "SAVE NAME"
PROFILE_CURRENT_NAME_TEMPLATE = "Current name: {display_name}"
PROFILE_SAVE_SUCCESS_TOAST = "Saved."

# API key card
API_KEY_CARD_TITLE = "Anthropic API key"
API_KEY_STATUS_SAVED = "API key saved"
API_KEY_PRIVACY_REMINDER = (
    "Your key is saved only on this computer, in a local SQLite file. "
    "Surf never shows it back to you."
)
API_KEY_FIELD_LABEL = "NEW API KEY"
API_KEY_HELPER = (
    "If the new key fails to validate, your old key stays unchanged."
)
API_KEY_PRIMARY_LABEL = "REPLACE API KEY"
API_KEY_AI_USE_LABEL = "AI USE"
API_KEY_VALIDATING_COPY = "Checking your Anthropic key…"
API_KEY_REPLACE_SUCCESS_TOAST = "Saved."

# Reset card
RESET_CARD_TITLE = "Reset app data"
RESET_PATH_TEMPLATE = "Surf stores everything for this account at {path}"
RESET_PRIVACY_EXPLANATION = (
    "Your display name, Anthropic API key, classes, lectures, generated "
    "questions, attempts, and answers all live in that file on this "
    "computer. Nothing is uploaded."
)
RESET_WARNING = (
    "Resetting deletes that file's contents and signs you out. This "
    "cannot be undone."
)
RESET_BUTTON_LABEL = "RESET APP DATA"
RESET_DIALOG_TITLE = "Delete all local Surf data?"
RESET_DIALOG_BODY = (
    "This deletes your classes, lectures, questions, attempts, answers, "
    "and saved API key from this computer. Type DELETE to confirm."
)
RESET_DIALOG_FIELD_LABEL = "TYPE DELETE TO CONFIRM"
RESET_DIALOG_HELPER_MISMATCH = (
    "Type DELETE in capital letters to enable the delete button."
)
RESET_DIALOG_KEEP_LABEL = "KEEP DATA"
RESET_DIALOG_CONFIRM_LABEL = "DELETE ALL LOCAL DATA"
RESET_TYPED_TOKEN = "DELETE"
RESET_SUCCESS_TOAST = "Local data deleted."

# Routing target after confirmed reset.
SIGNUP_VIEW_PATH = "views/signup.py"

# Shared AI-use markdown copy lives next to the signup flow. P1 and P7
# both read this same path so the explanation never drifts.
_AI_USE_COPY_PATH = (
    Path(__file__).resolve().parents[1] / "signup" / "signup_flow" / "ai_use_copy.md"
)


# --------------------------------------------------------------------------- #
# Pure helpers (testable without Streamlit state)
# --------------------------------------------------------------------------- #


def is_reset_confirmation_armed(typed_value: str) -> bool:
    """Return True iff the typed value matches the locked DELETE token.

    The reset destructive button stays disabled until this returns True.
    Comparison is exact (case-sensitive); ``"delete"`` and ``"DELETE "``
    both fail.
    """
    # Gates destructive reset behind the exact confirmation word.
    return typed_value == RESET_TYPED_TOKEN


def get_ai_use_copy_path() -> Path:
    """Return the locked path to the shared AI-use markdown copy.

    Both P1 and P7 read this exact file so the explanation is
    single-sourced. Tests use this to confirm the path target.
    """
    # Keeps the usage explanation shared with signup.
    return _AI_USE_COPY_PATH


def load_ai_use_copy() -> str:
    """Read the shared AI-use markdown content."""
    try:
        return _AI_USE_COPY_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


# --------------------------------------------------------------------------- #
# Scoped CSS — applies the 03-UI-SPEC §2.5 universal rules.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# PAGE-SCOPED CSS — `_settings_styles`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Returns the CSS block that styles every P7 surface: cards, inputs,
# stamped buttons, and the destructive reset button (Accent/Deep red).
# Scoped to `.st-key-p7_settings_page` plus the explicit dialog button
# keys (`p7_reset_keep`, `p7_reset_confirm`, `p7_ai_use_close`) which
# Streamlit renders in a portal outside the page container.
#
# Key detail:
# - The reset confirm button uses the destructive variant (`Accent/Deep`
#   fill) and is disabled until the user types `DELETE` exactly.
def _settings_styles() -> str:
    return """
    <style>
    /* P7 Settings page.
       Visual conventions: stamped buttons, hard-stamp cards, 12px gap
       inside cards, and 16px between cards. */
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
    }

    .stApp { background: var(--surf-paper) !important; }

    /* Page outer padding: 32px horizontal, 24px vertical. */
    .st-key-p7_settings_page {
      box-sizing: border-box;
      padding: 0 32px 24px !important;
    }

    /* Page title. */
    .surf-p7-page-title {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 32px;
      font-weight: 500;
      letter-spacing: -0.01em;
      line-height: 1.15;
      margin: 0 0 24px;
    }

    /* Cards use the regular Surf hard-stamp shadow. */
    .st-key-p7_profile_card [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-p7_profile_card > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"],
    .st-key-p7_api_key_card [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-p7_api_key_card > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"],
    .st-key-p7_reset_card [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-p7_reset_card > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] {
      background: var(--surf-paper0) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 4px !important;
      box-shadow: 3px 3px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
      padding: 24px 28px !important;
    }

    /* 16px gap between cards. */
    .st-key-p7_settings_page [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {
      margin-bottom: 0 !important;
    }
    .st-key-p7_profile_card,
    .st-key-p7_api_key_card,
    .st-key-p7_reset_card {
      margin-bottom: 16px !important;
    }
    .st-key-p7_reset_card { margin-bottom: 0 !important; }

    /* Card title. */
    .surf-p7-card-title {
      color: var(--surf-paper5) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 22px !important;
      font-weight: 500 !important;
      letter-spacing: -0.005em !important;
      line-height: 1.25 !important;
      margin: 0 0 12px !important;
    }
    .surf-p7-card-meta {
      color: var(--surf-paper4) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 13px !important;
      font-weight: 400 !important;
      letter-spacing: 0.01em !important;
      margin: 0 0 16px !important;
    }
    .surf-p7-card-body {
      color: var(--surf-paper5) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 17px !important;
      font-weight: 400 !important;
      line-height: 1.5 !important;
      margin: 0 0 12px !important;
    }
    .surf-p7-card-helper {
      color: var(--surf-paper4) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 13px !important;
      font-weight: 400 !important;
      letter-spacing: 0.01em !important;
      line-height: 1.4 !important;
      margin: 0 0 16px !important;
    }
    .surf-p7-card-path {
      background: var(--surf-paper) !important;
      border: 1px solid var(--surf-paper1) !important;
      border-radius: 3px !important;
      color: var(--surf-paper5) !important;
      display: inline-block !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      letter-spacing: 0.01em !important;
      padding: 2px 6px !important;
      word-break: break-all !important;
    }
    .surf-p7-field-label {
      color: var(--surf-paper4) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 500 !important;
      letter-spacing: 0.08em !important;
      margin: 0 0 6px !important;
      text-transform: uppercase !important;
    }

    /* Input — same outer-border reset as P1 to avoid Streamlit's default
       light-gray double border. The width:100% chain on every wrapper
       layer is mandatory: Streamlit's intermediate divs default to
       content-width otherwise, leaving a sliver of card padding visible
       past the input's right edge. */
    .st-key-p7_settings_page [data-testid="stTextInput"] label {
      display: none !important;
    }
    .st-key-p7_settings_page [data-testid="stTextInput"],
    .st-key-p7_settings_page [data-testid="stTextInput"] > div {
      width: 100% !important;
    }
    .st-key-p7_settings_page [data-testid="stTextInputRootElement"] {
      background: var(--surf-paper) !important;
      border: none !important;
      box-shadow: none !important;
      padding: 0 !important;
      width: 100% !important;
    }
    .st-key-p7_settings_page [data-testid="stTextInput"] > div > div {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 3px !important;
      box-shadow: none !important;
      width: 100% !important;
    }
    .st-key-p7_settings_page [data-testid="stTextInput"] input {
      background: transparent !important;
      color: var(--surf-paper5) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 15px !important;
      font-weight: 400 !important;
      letter-spacing: 0.01em !important;
      min-height: 44px !important;
      padding: 10px 14px !important;
      width: 100% !important;
    }
    .st-key-p7_settings_page [data-testid="stTextInput"] input::placeholder {
      color: rgba(40, 37, 31, 0.34) !important;
    }
    .st-key-p7_settings_page [data-testid="stTextInput"] input:focus {
      outline: none !important;
    }

    /* Universal stamped buttons. */
    .st-key-p7_settings_page [data-testid="stButton"] button,
    .st-key-p7_profile_save button,
    .st-key-p7_api_key_replace button,
    .st-key-p7_api_key_ai_use button,
    .st-key-p7_reset_open button {
      border-radius: 3px !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      height: 44px !important;
      letter-spacing: 0.14em !important;
      margin: 4px 4px 8px 0 !important;
      padding: 0 18px !important;
      text-transform: uppercase !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
      width: calc(100% - 4px) !important;
    }
    .st-key-p7_settings_page [data-testid="stButton"] button *,
    .st-key-p7_profile_save button *,
    .st-key-p7_api_key_replace button *,
    .st-key-p7_api_key_ai_use button *,
    .st-key-p7_reset_open button * {
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      letter-spacing: 0.14em !important;
      line-height: 1 !important;
      margin: 0 !important;
      text-transform: uppercase !important;
      white-space: nowrap !important;
    }

    /* Dialog buttons render outside `.st-key-p7_settings_page`, so the
       visible labels need the same Mono/Button Label contract by key. */
    .st-key-p7_reset_keep button,
    .st-key-p7_reset_confirm button,
    .st-key-p7_ai_use_close button {
      border-radius: 3px !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      height: 44px !important;
      letter-spacing: 0.14em !important;
      margin: 4px 4px 8px 0 !important;
      padding: 0 18px !important;
      text-transform: uppercase !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
      width: calc(100% - 4px) !important;
    }
    .st-key-p7_reset_keep button *,
    .st-key-p7_reset_confirm button *,
    .st-key-p7_ai_use_close button * {
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      letter-spacing: 0.14em !important;
      line-height: 1 !important;
      margin: 0 !important;
      text-transform: uppercase !important;
      white-space: nowrap !important;
    }

    /* Neutral variant — Paper surface, ink ink. */
    .st-key-p7_profile_save button,
    .st-key-p7_api_key_replace button,
    .st-key-p7_api_key_ai_use button,
    .st-key-p7_reset_open button,
    .st-key-p7_reset_keep button,
    .st-key-p7_ai_use_close button {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
    }
    .st-key-p7_profile_save button:hover,
    .st-key-p7_api_key_replace button:hover,
    .st-key-p7_api_key_ai_use button:hover,
    .st-key-p7_reset_open button:hover,
    .st-key-p7_reset_keep button:hover,
    .st-key-p7_ai_use_close button:hover {
      background: var(--surf-paper0) !important;
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .st-key-p7_profile_save button:active,
    .st-key-p7_api_key_replace button:active,
    .st-key-p7_api_key_ai_use button:active,
    .st-key-p7_reset_open button:active,
    .st-key-p7_reset_keep button:active,
    .st-key-p7_ai_use_close button:active {
      background: var(--surf-paper0) !important;
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }

    /* Primary variant on Profile / API key. */
    .st-key-p7_profile_save button[kind="primary"],
    .st-key-p7_api_key_replace button[kind="primary"] {
      background: var(--surf-paper5) !important;
      border-color: var(--surf-paper5) !important;
      color: var(--surf-paper) !important;
    }
    .st-key-p7_profile_save button[kind="primary"]:hover,
    .st-key-p7_api_key_replace button[kind="primary"]:hover {
      background: var(--surf-paper4) !important;
    }

    /* Destructive variant — reset confirm button. Accent/Deep fill. */
    .st-key-p7_reset_confirm button {
      background: var(--surf-accent-deep) !important;
      border: 1.5px solid var(--surf-accent-deep) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
    }
    .st-key-p7_reset_confirm button:hover:not(:disabled) {
      background: var(--surf-accent) !important;
      border-color: var(--surf-accent) !important;
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .st-key-p7_reset_confirm button:active:not(:disabled) {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }
    .st-key-p7_reset_confirm button:disabled {
      background: var(--surf-paper1) !important;
      border-color: var(--surf-paper3) !important;
      color: var(--surf-paper3) !important;
      cursor: not-allowed !important;
      opacity: 0.6 !important;
    }

    /* 12px gap between adjacent buttons in a card row. */
    .st-key-p7_settings_page [data-testid="stHorizontalBlock"] {
      gap: 12px !important;
    }
    .st-key-p7_settings_page [data-testid="column"] {
      padding: 0 !important;
    }

    /* Reduced-motion accommodation. */
    @media (prefers-reduced-motion: reduce) {
      .st-key-p7_settings_page [data-testid="stButton"] button,
      .st-key-p7_settings_page [data-testid="stButton"] button:hover,
      .st-key-p7_settings_page [data-testid="stButton"] button:active,
      .st-key-p7_reset_keep button,
      .st-key-p7_reset_keep button:hover,
      .st-key-p7_reset_keep button:active,
      .st-key-p7_reset_confirm button,
      .st-key-p7_reset_confirm button:hover,
      .st-key-p7_reset_confirm button:active,
      .st-key-p7_ai_use_close button,
      .st-key-p7_ai_use_close button:hover,
      .st-key-p7_ai_use_close button:active {
        transform: none !important;
        transition: background 0.08s ease-out !important;
      }
    }
    </style>
    """


# --------------------------------------------------------------------------- #
# Card renderers
# --------------------------------------------------------------------------- #


def _render_profile_card(
    *,
    user_id: int,
    display_name: str,
    save_name_fn: Callable[..., dict[str, Any]],
) -> None:
    with st.container(key="p7_profile_card"), st.container(border=True):
        st.html(f'<h2 class="surf-p7-card-title">{escape(PROFILE_CARD_TITLE)}</h2>')
        st.html(
            f'<p class="surf-p7-card-meta">'
            f"{escape(PROFILE_CURRENT_NAME_TEMPLATE.format(display_name=display_name))}"
            "</p>"
        )
        st.html(f'<div class="surf-p7-field-label">{escape(PROFILE_FIELD_LABEL)}</div>')
        new_name = st.text_input(
            PROFILE_FIELD_LABEL,
            key="p7_profile_input",
            label_visibility="collapsed",
            placeholder="Type the new display name",
        )
        clicked = st.button(
            PROFILE_PRIMARY_LABEL,
            key="p7_profile_save",
            type="primary",
            use_container_width=True,
        )
        if clicked:
            result = save_name_fn(user_id, new_name)
            if result["status"] == "saved":
                st.toast(PROFILE_SAVE_SUCCESS_TOAST)
                st.rerun()
            elif result.get("kind") == "missing_name":
                st.error(result["message"])
            else:
                st.toast(f"{result['title']} — {result['body']}")


def _render_ai_use_dialog() -> None:
    # Dialog title matches P1's `AI USE` label. Using the card title here
    # would put `Anthropic API key` in the modal header, which is wrong.
    @st.dialog(API_KEY_AI_USE_LABEL)
    def _dialog() -> None:
        st.markdown(load_ai_use_copy())
        if st.button(
            "CLOSE AI INFO",
            key="p7_ai_use_close",
            use_container_width=True,
        ):
            st.rerun()

    _dialog()


def _render_api_key_card(
    *,
    user_id: int,
    has_saved_key: bool,
    replace_key_fn: Callable[..., dict[str, Any]],
) -> None:
    with st.container(key="p7_api_key_card"), st.container(border=True):
        st.html(f'<h2 class="surf-p7-card-title">{escape(API_KEY_CARD_TITLE)}</h2>')
        if has_saved_key:
            st.html(
                f'<p class="surf-p7-card-meta">{escape(API_KEY_STATUS_SAVED)}</p>'
            )
        st.html(
            f'<p class="surf-p7-card-body">{escape(API_KEY_PRIVACY_REMINDER)}</p>'
        )
        st.html(f'<div class="surf-p7-field-label">{escape(API_KEY_FIELD_LABEL)}</div>')
        new_key = st.text_input(
            API_KEY_FIELD_LABEL,
            key="p7_api_key_input",
            type="password",
            label_visibility="collapsed",
            placeholder="••••••••",
        )
        st.html(f'<p class="surf-p7-card-helper">{escape(API_KEY_HELPER)}</p>')
        col_replace, col_ai_use = st.columns(2, gap="small")
        with col_replace:
            replace_clicked = st.button(
                API_KEY_PRIMARY_LABEL,
                key="p7_api_key_replace",
                type="primary",
                use_container_width=True,
            )
        with col_ai_use:
            ai_use_clicked = st.button(
                API_KEY_AI_USE_LABEL,
                key="p7_api_key_ai_use",
                use_container_width=True,
            )

        if ai_use_clicked:
            _render_ai_use_dialog()
            return

        if replace_clicked:
            # No try/except: `replace_api_key_after_validation` always
            # returns a status dict — the validate/persist exception
            # branches are caught inside the service and surfaced as
            # `kind: invalid` / `kind: save_failure` so the page only
            # has to switch on the status field.
            with st.spinner(API_KEY_VALIDATING_COPY):
                result = replace_key_fn(user_id, new_key)
            if result["status"] == "replaced":
                st.toast(API_KEY_REPLACE_SUCCESS_TOAST)
                st.rerun()
            elif result.get("kind") == "blank":
                st.error(result["message"])
            else:
                st.toast(f"{result['title']} — {result['body']}")


def _render_reset_dialog(
    *,
    reset_fn: Callable[..., dict[str, Any]],
) -> None:
    @st.dialog(RESET_DIALOG_TITLE)
    def _dialog() -> None:
        st.html(f'<p class="surf-p7-card-body">{escape(RESET_DIALOG_BODY)}</p>')
        st.html(
            f'<div class="surf-p7-field-label">{escape(RESET_DIALOG_FIELD_LABEL)}</div>'
        )
        typed = st.text_input(
            RESET_DIALOG_FIELD_LABEL,
            key="p7_reset_typed",
            label_visibility="collapsed",
            placeholder=RESET_TYPED_TOKEN,
        )
        armed = is_reset_confirmation_armed(typed)
        if not armed:
            st.html(
                f'<p class="surf-p7-card-helper">'
                f"{escape(RESET_DIALOG_HELPER_MISMATCH)}"
                "</p>"
            )
        col_keep, col_confirm = st.columns(2, gap="small")
        with col_keep:
            keep_clicked = st.button(
                RESET_DIALOG_KEEP_LABEL,
                key="p7_reset_keep",
                use_container_width=True,
            )
        with col_confirm:
            confirm_clicked = st.button(
                RESET_DIALOG_CONFIRM_LABEL,
                key="p7_reset_confirm",
                disabled=not armed,
                use_container_width=True,
            )

        if keep_clicked:
            st.rerun()
        if confirm_clicked and armed:
            reset_fn()
            st.session_state.clear()
            st.toast(RESET_SUCCESS_TOAST)
            st.rerun()

    _dialog()


def _render_reset_card(
    *,
    db_path: str,
    reset_fn: Callable[..., dict[str, Any]],
) -> None:
    with st.container(key="p7_reset_card"), st.container(border=True):
        st.html(f'<h2 class="surf-p7-card-title">{escape(RESET_CARD_TITLE)}</h2>')
        st.html(
            f'<p class="surf-p7-card-body">'
            f"{escape(RESET_PATH_TEMPLATE.split('{path}')[0])}"
            f'<span class="surf-p7-card-path">{escape(db_path)}</span>'
            "</p>"
        )
        st.html(
            f'<p class="surf-p7-card-body">{escape(RESET_PRIVACY_EXPLANATION)}</p>'
        )
        st.html(f'<p class="surf-p7-card-body">{escape(RESET_WARNING)}</p>')
        open_clicked = st.button(
            RESET_BUTTON_LABEL,
            key="p7_reset_open",
            use_container_width=True,
        )
        if open_clicked:
            _render_reset_dialog(reset_fn=reset_fn)


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #


def render_settings_page(
    *,
    user: dict[str, Any],
    db_path: str | None = None,
    save_name_fn: Callable[..., dict[str, Any]] = save_display_name,
    replace_key_fn: Callable[..., dict[str, Any]] = replace_api_key_after_validation,
    reset_fn: Callable[..., dict[str, Any]] = reset_local_account_data,
    show_topbar_fn: Callable[[str], None] = render_topbar,
) -> None:
    """Render P7 — three-card Settings page.

    Parameters
    ----------
    user:
        ``{"id": int, "username": str, "anthropic_api_key": str | None}``.
        Only ``id`` and ``username`` are read; the saved key value is
        never displayed (only its presence is reflected via
        ``API key saved`` status).
    db_path:
        Local DB path string for the Reset card. Defaults to
        :func:`app.db.queries_users.get_local_db_path`.
    save_name_fn / replace_key_fn / reset_fn / show_topbar_fn:
        Injectable for testing and the preview sandbox so the function
        can run without real Anthropic, real SQLite writes, or the live
        topbar import path.
    """
    # Orchestrates the profile, key replacement, and reset cards.
    show_topbar_fn(TOPBAR_PAGE_KEY)
    st.html(_settings_styles())
    with page_rail("p7_settings_page"):
        render_page_header(
            kicker="SURFBOARD",
            title=PAGE_TITLE,
            helper="",
            key="p7_page_header",
        )
        _render_profile_card(
            user_id=int(user["id"]),
            display_name=str(user.get("username", "")),
            save_name_fn=save_name_fn,
        )
        _render_api_key_card(
            user_id=int(user["id"]),
            has_saved_key=bool(user.get("anthropic_api_key")),
            replace_key_fn=replace_key_fn,
        )
        resolved_path = db_path if db_path is not None else get_local_db_path()
        _render_reset_card(db_path=resolved_path, reset_fn=reset_fn)


__all__ = [
    "PAGE_TITLE",
    "PROFILE_CARD_TITLE",
    "API_KEY_CARD_TITLE",
    "RESET_CARD_TITLE",
    "RESET_TYPED_TOKEN",
    "SIGNUP_VIEW_PATH",
    "get_ai_use_copy_path",
    "is_reset_confirmation_armed",
    "load_ai_use_copy",
    "render_settings_page",
]

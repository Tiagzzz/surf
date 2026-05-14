"""P3 — Class Hub renderer.

Public entry point::

    from app.class_.class_hub import render_class_hub_page
    render_class_hub_page(user=user_dict, class_id=class_id)

The module owns four responsibilities:

* **Pure view-model construction.** :func:`build_lecture_grid_view_models`,
  :func:`compute_take_mock_state`, :func:`build_study_next_view_models`,
  :func:`build_attempt_history_view_models`, and
  :func:`attempt_history_is_visible` turn raw query rows into the locked
  page payloads. None of them touch Streamlit.
* **Service-layer dispatch.** :func:`submit_add_lecture_form` validates the
  Add Lecture inputs, fetches the saved per-user Anthropic API key, and
  delegates to :func:`app.class_.lecture_ingest.ingest_lecture`.
  :func:`handle_lecture_delete` routes through
  :func:`app.class_.lecture_delete.delete_lecture_after_confirmation`.
* **Streamlit rendering.** :func:`render_class_hub_page` composes the
  shared topbar, dashboard navigation button, lecture chooser grid,
  inline Add Lecture form, Study Next card, destructive lecture-delete
  dialog, and the (visibility-gated) Attempt History toggle/section.
* **Honest boundaries.** No fake difficulty metadata is emitted; the
  `question_type` slug is stored question metadata. The
  renderer never reads ``ANTHROPIC_API_KEY`` from the environment.

Visual layout follows the approved P3 composition and wording:

* Launch CTA reads ``TAKE MOCK >`` (lock).
* Attempt History (the lock forbids new production `quiz` labels) is
  hidden until the first completed mock or practice attempt exists
  for the class.
* Dashboard button opens the real P6 dashboard route.
* Safe lecture delete is offered only for failed, pending, or
  never-attempted lectures, behind the destructive-dialog confirmation
  pattern.
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
from app.class_.lecture_delete import delete_lecture_after_confirmation
from app.class_.lecture_ingest import ingest_lecture as _ingest_lecture
from app.class_.mock_custom_launch import launch_mock_custom
from app.class_.mock_standard_launch import launch_mock_standard
from app.class_.study_next_launch import launch_study_next_practice
from app.db.queries_attempts import list_completed_attempts_for_class
from app.db.queries_classes import get_class_by_id
from app.db.queries_dashboard import (
    get_weakest_learning_objectives,
)
from app.db.queries_lectures import list_lectures_for_class
from app.db.queries_questions import (
    list_ready_questions_for_lecture,
    ready_question_count_for_lecture,
)
from app.db.queries_users import get_saved_anthropic_api_key
from app.mock_review.results_render import format_finished_at

# --------------------------------------------------------------------------- #
# Locked content constants
# --------------------------------------------------------------------------- #

PAGE_TITLE = "Class Hub"

DASHBOARD_LABEL = "DASHBOARD >"
CUSTOM_MOCK_LABEL = "CUSTOM MOCK >"
CUSTOM_MOCK_EMPTY_TOAST = (
    "No ready questions for Custom Mock yet. Generate or import questions first."
)
CUSTOM_MOCK_HELP_LABEL = "How does it work? learn more"
CUSTOM_MOCK_HELP_HIDE_LABEL = "How does it work? hide"
CUSTOM_MOCK_HELP_BODY = (
    'Custom Mock is your "hit me with the hard ones" button.\n\n'
    "Surf scans the questions already prepared for this class and picks the "
    "ones most likely to trip you up today. It looks at three things: how "
    "tricky the question itself is, what the lecture covers, and how you've "
    "done on similar questions before.\n\n"
    "Just starting out? Surf leans on each question's difficulty rating. The "
    "more you practice, the more personal it gets, your own weak spots start "
    "shaping the picks.\n\n"
    "You'll get up to 10 of the toughest, most useful questions dropped "
    "straight into the normal mock exam screen. Nothing new is generated ! "
    "Custom Mock only re-shuffles what's already there, so it's instant."
)

BUILD_MOCK_SECTION_LABEL = "Build a mock exam"
BUILD_MOCK_HEADING = "Pick the lectures you want to be tested on."

ADD_LECTURE_LABEL = "ADD LECTURE"
TAKE_MOCK_LABEL = "TAKE MOCK >"
TAKE_MOCK_DISABLED_HELP = (
    "Pick at least one ready lecture to start a mock."
)
TAKE_MOCK_SHORT_HELP_TEMPLATE = (
    "Only {ready} ready questions across the picked lectures — Surf will "
    "build a shorter mock with whatever's ready."
)

EMPTY_LECTURE_CELL_LABEL = "NO LECTURE UPLOADED YET"

LECTURE_DELETE_TRIGGER_LABEL = "Delete lecture"
LECTURE_DELETE_DIALOG_TITLE = "Delete this lecture?"
LECTURE_DELETE_DIALOG_BODY_TEMPLATE = (
    "{title} will be removed from {class_name}. This can't be undone."
)
LECTURE_DELETE_KEEP_LABEL = "KEEP LECTURE"
LECTURE_DELETE_CONFIRM_LABEL = "DELETE LECTURE"
LECTURE_DELETE_BLOCKED_TOAST = (
    "Surf can't delete this lecture — it has attempt history. "
    "Lectures with completed mock or practice answers stay around so "
    "your reviews keep working."
)
LECTURE_DELETE_NOT_OWNED_TOAST = (
    "Couldn't delete that lecture — it isn't on this account."
)
LECTURE_DELETE_SUCCESS_TOAST = "Lecture removed."

# Action-row delete mode replaces per-cell delete controls.
DELETE_LECTURE_BUTTON_LABEL = "DELETE LECTURE"
DELETE_LECTURE_UNDO_LABEL = "UNDO"
DELETE_LECTURE_DISABLED_HELP = (
    "No lectures are available to delete right now."
)
DELETE_LECTURE_PROMPT_HELP = (
    "Pick a lecture to delete, or press UNDO to cancel."
)

ADD_LECTURE_FORM_TITLE = "Add Lecture"
LECTURE_NAME_LABEL = "LECTURE NAME"
LECTURE_NAME_PLACEHOLDER = "Type here"
UPLOAD_SLIDES_LABEL = "UPLOAD SLIDES"
UPLOAD_SLIDES_HELPER = (
    "Upload your Lecture Slides, Question Generation will start Automatically"
)
LECTURE_DROPBOX_TITLE = "DROPBOX"
LECTURE_DROPBOX_HELPER = "UPLOAD YOUR LECTURE"
DISCARD_LECTURE_DRAFT_LABEL = "DISCARD CARD & CLOSE FORM"

ADD_LECTURE_MISSING_TITLE = "Type a lecture name to continue."
ADD_LECTURE_MISSING_PDF = "Attach a slides PDF to continue."
ADD_LECTURE_MISSING_API_KEY = (
    "Add your Anthropic API key in Settings before uploading a lecture."
)
ADD_LECTURE_INGEST_FAIL_TITLE = "Couldn't process the slides"
ADD_LECTURE_INGEST_PARTIAL_TITLE = "Lecture saved with some failures"
ADD_LECTURE_PROCESSING_TOAST = "Reading your slides…"
ADD_LECTURE_SAVED_READY_TOAST = (
    "Lecture saved. Surf is generating questions in the background."
)
ADD_LECTURE_SAVED_FAILED_TOAST = (
    "Lecture saved but Surf couldn't extract usable content. "
    "Check the slides PDF and re-upload."
)

STUDY_NEXT_SECTION_LABEL = "Study Next"
STUDY_NEXT_HEADING = "Where Surf thinks you should focus."
# Study Next uses a small `>` arrow at each LO row's right edge.
# The literal is hard-coded at the call site; no exported constant needed.
STUDY_NEXT_EMPTY_COPY = (
    "Take a mock or practice round so Surf can spot weak topics."
)

ATTEMPT_HISTORY_OPEN_LABEL = "ATTEMPT HISTORY"
ATTEMPT_HISTORY_CLOSE_LABEL = "COLLAPSE ATTEMPT HISTORY"
ATTEMPT_HISTORY_PRACTICE_KIND_LABEL = "Practice"
ATTEMPT_HISTORY_MOCK_KIND_LABEL = "Mock Exam"

RECOVERY_NO_CLASS_TITLE = "Class not found"
RECOVERY_NO_CLASS_BODY = (
    "Pick a class from your home to keep going."
)
RECOVERY_BACK_TO_HOME_LABEL = "BACK TO MY CLASSES"

#: Default mock target — 5 ready questions per selected lecture.
DEFAULT_MOCK_TARGET_PER_LECTURE = 5

#: Lecture grid is 3 columns × 4 rows in the Class Hub layout.
LECTURE_GRID_COLUMNS = 3
LECTURE_GRID_ROWS = 4
LECTURE_GRID_SIZE = LECTURE_GRID_COLUMNS * LECTURE_GRID_ROWS

#: Routing targets for the take, review, dashboard, and class-list pages.
TAKE_MOCK_VIEW_PATH = "views/take_mock_exam.py"
REVIEW_MOCK_VIEW_PATH = "views/review_mock_exam.py"
DASHBOARD_VIEW_PATH = "views/dashboard.py"
MY_CLASSES_VIEW_PATH = "views/my_classes.py"

#: Session-state keys owned by the Class Hub route.
SELECTED_CLASS_KEY = "selected_class_id"
ADD_LECTURE_OPEN_KEY = "p3_add_lecture_open"
SELECTED_LECTURES_KEY = "p3_selected_lecture_ids"
ATTEMPT_HISTORY_OPEN_KEY = "p3_attempt_history_open"
DELETE_PENDING_LECTURE_KEY = "p3_delete_lecture_id"
DELETE_MODE_KEY = "p3_delete_mode_active"
CUSTOM_MOCK_HELP_OPEN_KEY = "p3_custom_mock_help_open"

#: Inline SVG checkmark used by the selected-state lecture-pick
#: checkbox visual. Lives as a module constant so the CSS line in
#: `_styles()` stays inside the 100-col limit (the URI is intentionally
#: long because it carries the SVG inline).
_DROPBOX_FILE_ICON_DATA_URI = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='64' height='76' viewBox='0 0 64 76' fill='none'%3E"
    "%3Cpath d='M14 4h27l13 13v51a4 4 0 0 1-4 4H14"
    "a4 4 0 0 1-4-4V8a4 4 0 0 1 4-4Z' stroke='%236C6455' "
    "stroke-width='6' stroke-linejoin='round'/%3E"
    "%3Cpath d='M40 5v16h16' stroke='%236C6455' stroke-width='6' "
    "stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"
)

_CHECKMARK_DATA_URI = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'>"
    "<path d='M3 8l3 3 7-7' stroke='%23FDF9F2' stroke-width='2.5' "
    "fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>"
)

__all__ = [
    "PAGE_TITLE",
    "DASHBOARD_LABEL",
    "CUSTOM_MOCK_LABEL",
    "CUSTOM_MOCK_EMPTY_TOAST",
    "CUSTOM_MOCK_HELP_LABEL",
    "CUSTOM_MOCK_HELP_HIDE_LABEL",
    "CUSTOM_MOCK_HELP_BODY",
    "BUILD_MOCK_SECTION_LABEL",
    "BUILD_MOCK_HEADING",
    "ADD_LECTURE_LABEL",
    "TAKE_MOCK_LABEL",
    "EMPTY_LECTURE_CELL_LABEL",
    "ADD_LECTURE_FORM_TITLE",
    "LECTURE_NAME_LABEL",
    "UPLOAD_SLIDES_LABEL",
    "UPLOAD_SLIDES_HELPER",
    "LECTURE_DROPBOX_TITLE",
    "LECTURE_DROPBOX_HELPER",
    "DISCARD_LECTURE_DRAFT_LABEL",
    "STUDY_NEXT_SECTION_LABEL",
    "STUDY_NEXT_HEADING",
    "ATTEMPT_HISTORY_OPEN_LABEL",
    "ATTEMPT_HISTORY_CLOSE_LABEL",
    "DEFAULT_MOCK_TARGET_PER_LECTURE",
    "LECTURE_GRID_COLUMNS",
    "LECTURE_GRID_ROWS",
    "LECTURE_GRID_SIZE",
    "TAKE_MOCK_VIEW_PATH",
    "REVIEW_MOCK_VIEW_PATH",
    "DASHBOARD_VIEW_PATH",
    "MY_CLASSES_VIEW_PATH",
    "SELECTED_CLASS_KEY",
    "ADD_LECTURE_OPEN_KEY",
    "SELECTED_LECTURES_KEY",
    "ATTEMPT_HISTORY_OPEN_KEY",
    "DELETE_PENDING_LECTURE_KEY",
    "DELETE_MODE_KEY",
    "CUSTOM_MOCK_HELP_OPEN_KEY",
    "DELETE_LECTURE_BUTTON_LABEL",
    "DELETE_LECTURE_UNDO_LABEL",
    "build_lecture_grid_view_models",
    "compute_take_mock_state",
    "build_study_next_view_models",
    "build_attempt_history_view_models",
    "attempt_history_is_visible",
    "render_study_next_section",
    "submit_add_lecture_form",
    "handle_lecture_delete",
    "render_class_hub_page",
]


# --------------------------------------------------------------------------- #
# Pure helpers (testable without Streamlit)
# --------------------------------------------------------------------------- #


def build_lecture_grid_view_models(
    lectures: Iterable[Mapping[str, Any]],
    *,
    ready_counts_by_lecture_id: Mapping[int, int],
    attempted_lecture_ids: Iterable[int],
    grid_size: int = LECTURE_GRID_SIZE,
) -> list[dict[str, Any]]:
    """Build the 3×4 lecture grid view-models.

    Real lecture cells fill in insertion order (`L01`, `L02`, ...).
    Remaining cells render the locked `NO LECTURE UPLOADED YET` placeholder.

    A lecture is **selectable** only when its status is ``ready`` — that's
    what the lecture chooser uses to gate the TAKE MOCK > button. A lecture
    exposes the **safe-delete affordance** when its status is ``failed``
    or ``pending``, OR it is ``ready`` but no completed attempt has ever
    answered one of its questions. Lectures that have
    answered attempt history are intentionally NOT deletable in V1.
    """
    if not isinstance(grid_size, int) or grid_size <= 0:
        raise ValueError("grid_size must be a positive integer.")
    attempted = set(attempted_lecture_ids)
    cells: list[dict[str, Any]] = []
    for index, lecture in enumerate(list(lectures)[:grid_size]):
        lecture_id = int(lecture["id"])
        title = str(lecture.get("title", "")).strip() or "Untitled lecture"
        status = str(lecture.get("status") or "pending").lower()
        ready_count = int(ready_counts_by_lecture_id.get(lecture_id, 0) or 0)
        is_attempted = lecture_id in attempted
        selectable = status == "ready"
        if status in ("failed", "pending"):
            deletable = True
        elif status == "ready" and not is_attempted:
            deletable = True
        else:
            deletable = False
        cells.append(
            {
                "kind": "lecture",
                "lecture_id": lecture_id,
                "label": f"L{index + 1:02d}",
                "title": title,
                "status": status,
                "selectable": selectable,
                "deletable": deletable,
                "ready_question_count": ready_count,
            }
        )
    while len(cells) < grid_size:
        cells.append(
            {
                "kind": "empty",
                "lecture_id": None,
                "label": "",
                "title": EMPTY_LECTURE_CELL_LABEL,
                "status": "empty",
                "selectable": False,
                "deletable": False,
                "ready_question_count": None,
            }
        )
    return cells


def compute_take_mock_state(
    selected_lecture_ids: Iterable[int],
    *,
    ready_counts_by_lecture_id: Mapping[int, int],
    target_question_count: int | None = None,
) -> dict[str, Any]:
    """Compute the TAKE MOCK > button state.

    Disabled when no lectures are selected. Enabled with honest
    shorter-mock copy when fewer ready questions are available than the
    target; otherwise enabled with no extra copy.
    """
    selected = list(selected_lecture_ids)
    target = (
        int(target_question_count)
        if target_question_count is not None
        else DEFAULT_MOCK_TARGET_PER_LECTURE * len(selected)
    )
    total_ready = sum(
        int(ready_counts_by_lecture_id.get(lid, 0) or 0) for lid in selected
    )
    if not selected or total_ready == 0:
        return {
            "enabled": False,
            "honest_short_copy": None,
            "total_ready": 0,
            "target": target,
        }
    if total_ready < target:
        return {
            "enabled": True,
            "honest_short_copy": TAKE_MOCK_SHORT_HELP_TEMPLATE.format(
                ready=total_ready
            ),
            "total_ready": total_ready,
            "target": target,
        }
    return {
        "enabled": True,
        "honest_short_copy": None,
        "total_ready": total_ready,
        "target": target,
    }


def build_study_next_view_models(
    weak_los: Iterable[Mapping[str, Any]],
    *,
    ready_counts_by_lo_id: Mapping[int, int] | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Up to ``limit`` weakest LOs ordered worst-first."""
    rows = list(weak_los)[:limit]
    counts = ready_counts_by_lo_id or {}
    view_models: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        lo_id = int(row["lo_id"])
        view_models.append(
            {
                "rank": index + 1,
                "lo_id": lo_id,
                "lo_title": str(row.get("lo_title", "")).strip()
                or "Learning objective",
                "lecture_id": row.get("lecture_id"),
                "lecture_label": row.get("lecture_label"),
                "questions_ready": int(counts.get(lo_id, 0) or 0),
                "error_rate": row.get("error_rate"),
            }
        )
    return view_models


def build_attempt_history_view_models(
    attempts: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Most-recent-first attempt rows for the Attempt History list.

    Each row carries a ``kind_label`` ("Mock Exam" or "Practice"), a
    formatted date, the question/correct counts, the lecture labels
    tested, and the Swiss grade with a tier (fail/borderline/pass) so
    the renderer can color-code consistently with P2.
    """
    rows = list(attempts)
    view_models: list[dict[str, Any]] = []
    for row in rows:
        kind = (row.get("kind") or "").lower()
        kind_label = (
            ATTEMPT_HISTORY_PRACTICE_KIND_LABEL
            if kind == "practice"
            else ATTEMPT_HISTORY_MOCK_KIND_LABEL
        )
        grade = row.get("swiss_grade")
        tier = _grade_tier(grade)
        view_models.append(
            {
                "attempt_id": int(row["id"]),
                "kind": kind or "mock",
                "kind_label": kind_label,
                "finished_at": row.get("finished_at"),
                "question_count": int(row.get("question_count") or 0),
                "correct_count": int(row.get("correct_count") or 0),
                "lecture_labels": list(row.get("lecture_labels") or []),
                "swiss_grade": grade,
                "swiss_grade_tier": tier,
                "lo_title": row.get("lo_title"),
            }
        )
    return view_models


def attempt_history_is_visible(
    attempts: Iterable[Mapping[str, Any]],
) -> bool:
    """Hide the Attempt History toggle/section until the first completed
    attempt exists for the class.
    """
    return any(
        (row.get("finished_at") is not None) for row in attempts
    )


def _grade_tier(grade: float | int | None) -> str:
    if grade is None:
        return "empty"
    value = float(grade)
    if value < 4.0:
        return "fail"
    if value < 5.0:
        return "borderline"
    return "pass"


def _validate_pdf_arg(slide_pdf_file: Any) -> bool:
    """Reject empty / falsy PDF arguments.

    Streamlit's ``UploadedFile`` is truthy when populated; raw bytes are
    truthy when non-empty; ``None`` and empty bytes are explicitly
    invalid.
    """
    if slide_pdf_file is None:
        return False
    if isinstance(slide_pdf_file, (bytes, bytearray)) and len(slide_pdf_file) == 0:
        return False
    if isinstance(slide_pdf_file, str) and not slide_pdf_file.strip():
        return False
    return True


def submit_add_lecture_form(
    *,
    user_id: int,
    class_id: int,
    lecture_title: str,
    slide_pdf_file: Any,
    get_api_key_fn: Callable[[int], str | None] = get_saved_anthropic_api_key,
    ingest_fn: Callable[..., int] = _ingest_lecture,
) -> dict[str, Any]:
    """Validate Add Lecture inputs and dispatch to the ingestion helper.

    Returns a small status dict the renderer can render directly:

    - ``{"ok": False, "error": "missing_title"}``
    - ``{"ok": False, "error": "missing_pdf"}``
    - ``{"ok": False, "error": "missing_api_key"}``
    - ``{"ok": False, "error": "ingest_failed", "detail": "<message>"}``
    - ``{"ok": True, "lecture_id": <int>}``

    The function NEVER reads ``ANTHROPIC_API_KEY`` from the environment;
    the saved per-user key from
    :func:`app.db.queries_users.get_saved_anthropic_api_key` is the only
    accepted source (CLAUDE.md API-key consent rule).

    The ``slide_pdf_file`` argument is forwarded to ``ingest_fn`` as a
    ``Path`` when it's already a path-like object; raw bytes are written
    to a Python ``tempfile`` first because :func:`ingest_lecture`
    expects a filesystem path.
    """
    cleaned_title = (lecture_title or "").strip()
    if not cleaned_title:
        return {"ok": False, "error": "missing_title"}
    if not _validate_pdf_arg(slide_pdf_file):
        return {"ok": False, "error": "missing_pdf"}
    api_key = get_api_key_fn(int(user_id))
    if api_key is None or not str(api_key).strip():
        return {"ok": False, "error": "missing_api_key"}

    pdf_path = _materialize_pdf_arg(slide_pdf_file)
    try:
        lecture_id = ingest_fn(
            int(class_id),
            pdf_path,
            title=cleaned_title,
            api_key=str(api_key),
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": "ingest_failed",
            "detail": str(exc),
        }
    return {"ok": True, "lecture_id": int(lecture_id)}


def _materialize_pdf_arg(slide_pdf_file: Any) -> Any:
    """Coerce ``slide_pdf_file`` into something :func:`ingest_lecture`
    can read.

    - ``Path`` / ``str`` paths are returned unchanged.
    - ``bytes`` / ``bytearray`` are written to a tempfile and the path
      is returned. The temp file is left on disk for the ingest helper
      to clean up; ``ingest_lecture`` reads it once and the OS reclaims
      it on next sweep.
    - Streamlit's ``UploadedFile`` (anything with ``getvalue()``) is
      treated as the bytes case.
    """
    if isinstance(slide_pdf_file, Path):
        return slide_pdf_file
    if isinstance(slide_pdf_file, str):
        return Path(slide_pdf_file)
    if hasattr(slide_pdf_file, "getvalue") and callable(slide_pdf_file.getvalue):
        data = slide_pdf_file.getvalue()
    elif isinstance(slide_pdf_file, (bytes, bytearray)):
        data = bytes(slide_pdf_file)
    else:
        return slide_pdf_file
    import tempfile

    suffix = ".pdf"
    fp = tempfile.NamedTemporaryFile(  # noqa: SIM115
        suffix=suffix, delete=False
    )
    fp.write(data)
    fp.flush()
    fp.close()
    return Path(fp.name)


def handle_lecture_delete(
    *,
    user_id: int,
    class_id: int,
    lecture_id: int,
    confirmed: bool,
    delete_fn: Callable[..., dict[str, Any]] = delete_lecture_after_confirmation,
) -> dict[str, Any]:
    """Single seam the renderer calls to delete a lecture.

    The renderer never invokes
    :func:`app.db.queries_lectures.delete_lecture_for_user` directly;
    every delete goes through this helper. When ``confirmed`` is
    ``False`` the helper short-circuits to a ``cancelled`` status
    *before* dispatching to ``delete_fn``. The downstream
    :func:`app.class_.lecture_delete.delete_lecture_after_confirmation`
    enforces the same rule, but short-circuiting here as well means a
    misuse of this seam (or an injected fake delete) cannot accidentally
    leak a destructive call past the confirmation gate.
    """
    if not bool(confirmed):
        return {
            "status": "cancelled",
            "class_id": int(class_id),
            "lecture_id": int(lecture_id),
        }
    return delete_fn(
        user_id=int(user_id),
        class_id=int(class_id),
        lecture_id=int(lecture_id),
        confirmed=True,
    )


# --------------------------------------------------------------------------- #
# Default queries (injectable so the preview sandbox + tests can fake them)
# --------------------------------------------------------------------------- #


def _default_lecture_query(class_id: int) -> list[dict[str, Any]]:
    return list_lectures_for_class(int(class_id))


def _default_ready_counts_query(
    lectures: Iterable[Mapping[str, Any]],
) -> dict[int, int]:
    """Per-lecture ready question count map."""
    counts: dict[int, int] = {}
    for lecture in lectures:
        lid = int(lecture["id"])
        counts[lid] = int(ready_question_count_for_lecture(lid) or 0)
    return counts


def _default_attempted_lectures_query(class_id: int) -> set[int]:
    """Set of lecture ids whose questions appear in any completed attempt."""
    attempts = list_completed_attempts_for_class(int(class_id))
    seen: set[int] = set()
    for row in attempts:
        for lid in row.get("lecture_ids") or []:
            try:
                seen.add(int(lid))
            except (TypeError, ValueError):
                continue
    return seen


def _default_weak_los_query(class_id: int) -> list[dict[str, Any]]:
    return list(get_weakest_learning_objectives(int(class_id), limit=3))


def _default_attempts_query(class_id: int) -> list[dict[str, Any]]:
    return list_completed_attempts_for_class(int(class_id))


def _default_ready_counts_per_lo(
    weak_los: Iterable[Mapping[str, Any]],
) -> dict[int, int]:
    counts: dict[int, int] = {}
    for row in weak_los:
        lid = int(row.get("lecture_id") or 0)
        if lid:
            ready = list_ready_questions_for_lecture(lid)
            counts[int(row["lo_id"])] = sum(
                1
                for q in ready
                if int(q.get("learning_objective_id") or 0)
                == int(row["lo_id"])
            )
    return counts


# --------------------------------------------------------------------------- #
# Streamlit rendering
# --------------------------------------------------------------------------- #

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FONTS_DIR = _REPO_ROOT / "assets" / "fonts"


def _font_data_uri(filename: str) -> str:
    encoded = base64.b64encode((_FONTS_DIR / filename).read_bytes()).decode(
        "ascii"
    )
    return f"data:font/woff2;base64,{encoded}"


@lru_cache(maxsize=1)
def _font_face_block() -> str:
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

    /* P3 button font only — scoped to the Class Hub page rail plus
       the P3 delete-dialog buttons, which Streamlit renders in a
       portal outside `.st-key-p3_class_hub_page`. Lecture titles,
       helper copy, generated text, and hidden tile labels are not
       separate typography targets. */
    .st-key-p3_class_hub_page [data-testid="stButton"] button,
    .st-key-p3_class_hub_page [data-testid="stFormSubmitButton"] button,
    .st-key-p3_class_hub_page button[data-baseweb="button"],
    .st-key-p3_class_hub_page [data-testid="stButton"] button *,
    .st-key-p3_class_hub_page [data-testid="stFormSubmitButton"] button *,
    .st-key-p3_class_hub_page button[data-baseweb="button"] *,
    .stDialog .st-key-p3_dialog_keep button,
    .stDialog .st-key-p3_dialog_delete button,
    .stDialog .st-key-p3_dialog_keep button *,
    .stDialog .st-key-p3_dialog_delete button * {
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      letter-spacing: 0.14em !important;
      text-transform: uppercase !important;
    }

    .st-key-p3_class_hub_page {
      box-sizing: border-box;
      padding: 0 32px 32px !important;
    }

    /* Wide DASHBOARD > stamped button (Paper5 fill, Paper light label). */
    .st-key-p3_dashboard_button button {
      background: var(--surf-paper5) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
      font-size: 13px !important;
      font-weight: 700 !important;
      height: 64px !important;
      margin: 0 0 24px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out !important;
      width: 100% !important;
    }
    .st-key-p3_dashboard_button button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .st-key-p3_dashboard_button button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }

    /* Wide CUSTOM MOCK > stamped button — same dimensions/layout as
       DASHBOARD >, red fill so the harder mode reads as separate.
       Phase 7 only; positioned directly under the Dashboard button. */
    .st-key-p3_custom_mock_button button {
      background: var(--surf-accent) !important;
      border: 1.5px solid var(--surf-accent-deep) !important;
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
      font-size: 13px !important;
      font-weight: 700 !important;
      height: 64px !important;
      margin: 0 0 10px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out !important;
      width: 100% !important;
    }
    .st-key-p3_custom_mock_button button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .st-key-p3_custom_mock_button button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }
    .st-key-p3_custom_mock_learn_more {
      margin: 0 0 20px !important;
    }
    .st-key-p3_custom_mock_learn_more button,
    .st-key-p3_custom_mock_learn_more [data-testid="stButton"] button,
    .st-key-p3_custom_mock_learn_more button * {
      align-items: center !important;
      background: transparent !important;
      border: 0 !important;
      box-shadow: none !important;
      color: var(--surf-paper4) !important;
      display: inline-flex !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 15px !important;
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
    .st-key-p3_custom_mock_learn_more button:hover,
    .st-key-p3_custom_mock_learn_more button:hover * {
      background: transparent !important;
      box-shadow: none !important;
      color: var(--surf-accent) !important;
      transform: none !important;
      text-decoration: underline !important;
      text-underline-offset: 3px !important;
    }
    .st-key-p3_custom_mock_help_card {
      background: var(--surf-paper0);
      border: 1.5px dashed var(--surf-paper3);
      border-radius: 4px;
      box-sizing: border-box;
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 15px;
      font-style: italic;
      line-height: 1.5;
      margin: -10px 0 24px;
      padding: 16px 18px;
    }
    .surf-p3-custom-help-body {
      margin: 0;
      white-space: pre-line;
    }

    /* Build mock exam card — Paper0 hard-stamp 3px. */
    .st-key-p3_build_mock_card {
      background: var(--surf-paper0) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 4px !important;
      box-shadow: 3px 3px 0 var(--surf-shadow) !important;
      margin: 0 0 24px !important;
      padding: 24px 28px !important;
    }
    .surf-p3-section-label {
      color: var(--surf-accent);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      font-weight: 500;
      letter-spacing: 0.06em;
      margin: 0 0 8px;
    }
    .surf-p3-section-heading {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 26px;
      font-style: italic;
      font-weight: 600;
      letter-spacing: -0.01em;
      line-height: 1.1;
      margin: 0 0 24px;
    }
    /* Class name displayed as the page title above the DASHBOARD
       button. Same family + italic as the section heading but a step
       up in display size so it reads first. */
    .surf-p3-page-title {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 40px;
      font-style: italic;
      font-weight: 700;
      letter-spacing: -0.015em;
      line-height: 1.05;
      margin: 0 0 20px !important;
    }

    /* Lecture pick cells — click-on-card. The whole cell IS the click
       target when selectable. Selected state reuses the stamped
       card primitive (Paper fill + 1.5px Paper5 border + 4px stamp
       shadow); unselected is the quiet flat Paper0 variant; pending /
       failed / empty are non-clickable read-only variants.

       DOM shape (all states):
         .st-key-p3_lecture_pick_<state>_<id>  (relative wrapper; state ∈
                                                {selected, unselected,
                                                 pending, failed,
                                                 deletable, muted})
           [data-testid="stButton"] button     (hidden-label click target;
                                                selectable / deletable
                                                cells only)
           .surf-p3-lecture-overlay            (absolute visual content;
                                                pointer-events: none) */
    [class*="st-key-p3_lecture_pick_"] {
      box-sizing: border-box;
      margin: 0 0 8px;
      min-height: 56px;
      position: relative;
    }
    [class*="st-key-p3_lecture_pick_"] [data-testid="stButton"] button {
      border-radius: 4px !important;
      box-sizing: border-box !important;
      color: transparent !important;
      cursor: pointer !important;
      font-size: 0 !important;
      height: 56px !important;
      line-height: 0 !important;
      margin: 0 !important;
      min-height: 56px !important;
      padding: 0 !important;
      text-indent: -9999px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
      width: 100% !important;
    }

    /* Selected: stamped-card primitive (Paper + 4px hard shadow). */
    [class*="st-key-p3_lecture_pick_selected_"] [data-testid="stButton"] button {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
    }
    [class*="st-key-p3_lecture_pick_selected_"] [data-testid="stButton"] button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    [class*="st-key-p3_lecture_pick_selected_"] [data-testid="stButton"] button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }

    /* Unselected: flat Paper0 + thin Paper3 border, no shadow. */
    [class*="st-key-p3_lecture_pick_unselected_"] [data-testid="stButton"] button {
      background: var(--surf-paper0) !important;
      border: 1.5px solid var(--surf-paper3) !important;
      box-shadow: none !important;
    }
    [class*="st-key-p3_lecture_pick_unselected_"] [data-testid="stButton"] button:hover {
      background: var(--surf-paper) !important;
      border-color: var(--surf-paper5) !important;
    }

    /* Non-selectable states (pending / failed / empty): no button, just
       a passive cell. Provide the matching chrome on the wrapper itself. */
    [class*="st-key-p3_lecture_pick_pending_"],
    [class*="st-key-p3_lecture_pick_failed_"] {
      background: var(--surf-paper0);
      border: 1.5px solid var(--surf-paper3);
      border-radius: 4px;
      height: 56px;
    }

    /* Empty cell — non-interactive placeholder, NOT wrapped in a
       keyed container (multiple empty cells share the markup; using a
       keyed container would collide on the same key). */
    .surf-p3-lecture-empty-cell {
      align-items: center;
      background: var(--surf-paper);
      border: 1.5px dashed var(--surf-paper3);
      border-radius: 4px;
      box-sizing: border-box;
      display: flex;
      gap: 14px;
      height: 56px;
      margin: 0 0 8px;
      padding: 0 16px;
    }
    .surf-p3-lecture-empty-cell .surf-p3-lecture-title {
      color: var(--surf-paper3);
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      /* Empty-cell placeholder may wrap onto two lines — opt out of
         the single-line ellipsis truncation applied to real lecture
         titles. */
      overflow: visible;
      text-overflow: clip;
      white-space: normal;
    }

    /* Streamlit wraps every st.html / st.button / st.container inside
       its own stElementContainer with position: relative. That wrapper
       becomes the closer positioning ancestor and steals the absolute
       overlay anchor away from the keyed cell. Pin stElementContainer
       static inside lecture cells so the overlay (and the X delete
       affordance) anchor to the cell as intended. */
    [class*="st-key-p3_lecture_pick_"] [data-testid="stElementContainer"],
    [class*="st-key-p3_lecture_pick_"] .stElementContainer {
      position: static !important;
    }
    /* Visual overlay sits above the button; pointer-events: none lets
       clicks pass through to the button below. */
    [class*="st-key-p3_lecture_pick_"] .surf-p3-lecture-overlay {
      align-items: center;
      box-sizing: border-box;
      display: flex;
      gap: 14px;
      height: 56px;
      left: 0;
      padding: 0 16px;
      pointer-events: none;
      position: absolute;
      right: 0;
      top: 0;
      z-index: 2;
    }

    /* Custom checkbox visual rendered inside the overlay. The user
       toggles it by clicking the card; the checkbox is paint-only. */
    .surf-p3-lecture-checkbox {
      background: var(--surf-paper);
      border: 1.5px solid var(--surf-paper5);
      border-radius: 3px;
      display: inline-block;
      flex: 0 0 auto;
      height: 22px;
      position: relative;
      width: 22px;
    }
    .surf-p3-lecture-checkbox.is-selected {
      background: var(--surf-paper5);
    }
    .surf-p3-lecture-checkbox.is-selected::before {
      background-image: url(\""""
        + _CHECKMARK_DATA_URI
        + """\");
      background-position: center;
      background-repeat: no-repeat;
      background-size: 16px 16px;
      content: "";
      inset: 0;
      position: absolute;
    }
    .surf-p3-lecture-checkbox.is-disabled {
      background: var(--surf-paper);
      border-color: var(--surf-paper3);
    }

    .surf-p3-lecture-label {
      color: var(--surf-accent);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 0.04em;
    }
    .surf-p3-lecture-title {
      color: var(--surf-paper5);
      flex: 1 1 auto;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 13px;
      font-weight: 400;
      letter-spacing: 0.02em;
      /* Truncate long lecture names to a single line with an
         ellipsis. min-width: 0 is required so the flex child can
         shrink below its intrinsic content width. */
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .surf-p3-lecture-status {
      color: var(--surf-paper3);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    /* X delete affordance — small stamped icon button, absolutely
       centered against the cell's right edge. The wrapper is pinned
       to the button size (line-height: 0, no padding/margin/gap) so
       translateY(-50%) lands the visible square exactly on the cell
       midline. */
    /* Delete-mode states.

       deletable: rendered like the unselected stamped card; click
       routes to the destructive-confirmation dialog. Hover shows an
       accent-red border to hint that clicking is destructive.

       muted: non-deletable lectures during delete mode. opacity 0.45,
       no shadow, no hover, cursor: not-allowed — clearly outside the
       current intent. */
    [class*="st-key-p3_lecture_pick_deletable_"] [data-testid="stButton"] button {
      background: var(--surf-paper0) !important;
      border: 1.5px solid var(--surf-paper3) !important;
      box-shadow: none !important;
    }
    [class*="st-key-p3_lecture_pick_deletable_"] [data-testid="stButton"] button:hover {
      background: var(--surf-paper) !important;
      border-color: var(--surf-accent) !important;
      box-shadow: 4px 4px 0 var(--surf-accent-deep) !important;
      transform: translate(-1px, -1px) !important;
    }
    [class*="st-key-p3_lecture_pick_deletable_"] [data-testid="stButton"] button:active {
      box-shadow: 0 0 0 var(--surf-accent-deep) !important;
      transform: translate(2px, 2px) !important;
    }
    [class*="st-key-p3_lecture_pick_muted_"] {
      cursor: not-allowed !important;
      opacity: 0.45 !important;
      pointer-events: none !important;
    }
    [class*="st-key-p3_lecture_pick_muted_"] .surf-p3-lecture-overlay,
    [class*="st-key-p3_lecture_pick_muted_"] [data-testid="stButton"] button {
      box-shadow: none !important;
    }

    /* Mock action row: ADD LECTURE | DELETE LECTURE | TAKE MOCK >.
       All three share the 4px corner radius of the DASHBOARD button
       and the stamped-button primitive (4px shadow, press-into-shadow
       active animation). letter-spacing tuned so DELETE LECTURE fits
       in the third-width column without wrapping. */
    .st-key-p3_add_lecture_button button,
    .st-key-p3_delete_lecture_button button,
    .st-key-p3_take_mock_button button {
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      box-sizing: border-box !important;
      align-items: center !important;
      display: flex !important;
      font-size: 12px !important;
      height: 48px !important;
      justify-content: center !important;
      letter-spacing: 0.07em !important;
      line-height: 1 !important;
      min-width: 0 !important;
      overflow: hidden !important;
      padding: 0 12px !important;
      text-align: center !important;
      white-space: nowrap !important;
      width: 100% !important;
      transition: transform 0.08s ease-out,
        box-shadow 0.08s ease-out,
        background 0.08s ease-out !important;
    }
    .st-key-p3_add_lecture_button button *,
    .st-key-p3_delete_lecture_button button *,
    .st-key-p3_take_mock_button button * {
      font-size: 12px !important;
      letter-spacing: 0.07em !important;
      line-height: 1 !important;
      margin: 0 !important;
      overflow: hidden !important;
      text-align: center !important;
      text-overflow: clip !important;
      white-space: nowrap !important;
    }
    .st-key-p3_add_lecture_button button,
    .st-key-p3_delete_lecture_button button {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      color: var(--surf-paper5) !important;
    }
    .st-key-p3_take_mock_button button {
      background: var(--surf-accent) !important;
      border: 1.5px solid var(--surf-accent-deep) !important;
      color: var(--surf-paper) !important;
    }
    .st-key-p3_add_lecture_button button:hover,
    .st-key-p3_delete_lecture_button button:hover,
    .st-key-p3_take_mock_button button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .st-key-p3_add_lecture_button button:active,
    .st-key-p3_delete_lecture_button button:active,
    .st-key-p3_take_mock_button button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }
    .st-key-p3_take_mock_button button:disabled,
    .st-key-p3_delete_lecture_button button:disabled,
    .st-key-p3_add_lecture_button button:disabled {
      background: var(--surf-paper1) !important;
      border-color: var(--surf-paper3) !important;
      box-shadow: 4px 4px 0 var(--surf-paper3) !important;
      color: var(--surf-paper3) !important;
      cursor: not-allowed !important;
    }

    /* Lecture delete confirmation dialog (Streamlit @st.dialog).
       Surf-styled panel: Paper fill, thick Paper5 border, stamped
       shadow, italic Fraunces title, dark backdrop, centered on
       screen. Buttons keyed via st.container so KEEP renders neutral
       and DELETE renders accent-red. */
    .stDialog {
      align-items: center !important;
      backdrop-filter: blur(2px) !important;
      background: rgba(40, 37, 31, 0.32) !important;
      display: flex !important;
      justify-content: center !important;
    }
    /* Streamlit nests an intermediate wrapper with align-items: start
       between .stDialog and the inner [role="dialog"]; override it so
       the panel centers vertically. */
    .stDialog > div {
      align-items: center !important;
      justify-content: center !important;
    }
    .stDialog [role="dialog"] {
      background: var(--surf-paper) !important;
      border: 2px solid var(--surf-paper5) !important;
      border-radius: 6px !important;
      box-shadow: 6px 6px 0 var(--surf-shadow) !important;
      max-width: 480px !important;
      padding: 28px 32px !important;
    }
    .stDialog [data-testid="stDialogTitle"],
    .stDialog h2 {
      color: var(--surf-paper5) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 22px !important;
      font-style: italic !important;
      font-weight: 700 !important;
      letter-spacing: -0.01em !important;
      margin: 0 0 16px !important;
    }
    .stDialog .surf-p3-field-helper {
      color: var(--surf-paper4) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 15px !important;
      font-style: italic !important;
      line-height: 1.45 !important;
      margin: 0 0 24px !important;
    }
    .stDialog [data-testid="stButton"] button {
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      box-sizing: border-box !important;
      font-size: 13px !important;
      height: 44px !important;
      letter-spacing: 0.10em !important;
      white-space: nowrap !important;
      transition: transform 0.08s ease-out, box-shadow 0.08s ease-out !important;
      width: 100% !important;
    }
    .stDialog .st-key-p3_dialog_keep button {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      color: var(--surf-paper5) !important;
    }
    .stDialog .st-key-p3_dialog_delete button {
      background: var(--surf-accent) !important;
      border: 1.5px solid var(--surf-accent-deep) !important;
      color: var(--surf-paper) !important;
    }
    .stDialog [data-testid="stButton"] button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .stDialog [data-testid="stButton"] button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }

    /* Add Lecture inline form — one dashed outer draft surface. */
    .st-key-p3_add_lecture_form_card {
      background: var(--surf-paper) !important;
      border: 2px dashed var(--surf-paper5) !important;
      border-radius: 6px !important;
      box-shadow: none !important;
      box-sizing: border-box !important;
      margin: 24px 0 !important;
      padding: 32px 40px !important;
      width: 100% !important;
    }
    .st-key-p3_add_lecture_form_card [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-p3_add_lecture_form_card > [data-testid="stLayoutWrapper"]
      > [data-testid="stVerticalBlock"] {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      padding: 0 !important;
    }
    .surf-p3-form-title {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 28px;
      font-style: italic;
      font-weight: 700;
      letter-spacing: -0.01em;
      margin: 0 0 28px;
      text-align: center;
    }
    .surf-p3-field-label {
      color: var(--surf-paper4) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 12px !important;
      font-weight: 500 !important;
      letter-spacing: 0.08em !important;
      margin: 16px 0 8px !important;
      text-transform: uppercase !important;
    }
    .surf-p3-field-helper {
      color: var(--surf-paper4) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 14px !important;
      font-style: italic !important;
      line-height: 1.4 !important;
      margin: 8px 0 16px !important;
    }
    /* Text input — wide, rounded, thick black border (mirrors the P2
       Add Class form text-input rules). */
    .st-key-p3_add_lecture_form_card [data-testid="stTextInput"] label {
      display: none !important;
    }
    .st-key-p3_add_lecture_form_card [data-testid="stTextInput"],
    .st-key-p3_add_lecture_form_card [data-testid="stTextInput"] > div {
      width: 100% !important;
    }
    .st-key-p3_add_lecture_form_card [data-testid="stTextInputRootElement"] {
      background: var(--surf-paper) !important;
      border: none !important;
      box-shadow: none !important;
      padding: 0 !important;
      width: 100% !important;
    }
    .st-key-p3_add_lecture_form_card [data-testid="stTextInput"] > div > div {
      background: var(--surf-paper) !important;
      border: 2px solid var(--surf-paper5) !important;
      border-radius: 6px !important;
      box-shadow: none !important;
      width: 100% !important;
    }
    .st-key-p3_add_lecture_form_card [data-testid="stTextInput"] input {
      background: transparent !important;
      color: var(--surf-paper5) !important;
      font-family: "Fraunces", Georgia, serif !important;
      font-size: 17px !important;
      font-style: italic !important;
      min-height: 48px !important;
      padding: 12px 18px !important;
      width: 100% !important;
    }
    .st-key-p3_add_lecture_form_card [data-testid="stTextInput"] input::placeholder {
      color: rgba(40, 37, 31, 0.36) !important;
      font-style: italic !important;
    }
    .st-key-p3_add_lecture_form_card [data-testid="stTextInput"] input:focus {
      outline: none !important;
    }

    /* File uploader — the native Streamlit dropzone is the full visual
       Dropbox target. The real button is stretched invisibly over the
       dashed area, so clicks still open the file picker without the
       small stamped button/extra solid line showing inside the zone. */
    .st-key-p3_lecture_dropbox {
      box-sizing: border-box !important;
      margin: 0 0 8px !important;
      min-height: 260px !important;
      position: relative !important;
      text-align: center !important;
      width: 100% !important;
    }
    .st-key-p3_lecture_dropbox [data-testid="stElementContainer"],
    .st-key-p3_lecture_dropbox .stElementContainer {
      position: static !important;
    }
    .surf-p3-dropbox-visual {
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
    .surf-p3-dropbox-icon {
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
    .surf-p3-dropbox-title {
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
    .surf-p3-dropbox-helper,
    .surf-p3-dropbox-ready {
      color: rgba(108, 100, 85, 0.42);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 24px;
      font-weight: 400;
      letter-spacing: 0.16em;
      line-height: 1.2;
      margin: 0;
      text-transform: uppercase;
    }
    .surf-p3-dropbox-ready {
      bottom: 18px;
      color: var(--surf-status-ok);
      font-size: 12px;
      left: 24px;
      position: absolute;
      right: 24px;
      z-index: 4;
    }
    .st-key-p3_lecture_dropbox [data-testid="stFileUploader"],
    .st-key-p3_lecture_dropbox [data-testid="stFileUploader"] > section {
      width: 100% !important;
    }
    .st-key-p3_lecture_dropbox [data-testid="stFileUploader"] label {
      display: none !important;
    }
    .st-key-p3_lecture_dropbox [data-testid="stFileUploaderDropzone"] {
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
    .st-key-p3_lecture_dropbox [data-testid="stFileUploaderDropzone"]
      [data-testid="stFileUploaderDropzoneInstructions"] {
      display: none !important;
    }
    .st-key-p3_lecture_dropbox [data-testid="stFileUploaderDropzone"]
      [data-testid="stBaseButton-secondary"],
    .st-key-p3_lecture_dropbox [data-testid="stFileUploaderDropzone"] button {
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
    .st-key-p3_lecture_dropbox [data-testid="stFileUploaderDropzone"] button *,
    .st-key-p3_lecture_dropbox [data-testid="stFileUploaderDropzone"]
      [data-testid="stBaseButton-secondary"] * {
      color: transparent !important;
      opacity: 0 !important;
    }
    .st-key-p3_lecture_dropbox [data-testid="stFileUploaderFile"] {
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

    /* Form submit buttons — DISCARD CARD & CLOSE FORM (neutral, left)
       + ADD LECTURE (primary, right). Mirrors the P2 Add Class
       form-submit pattern; reuses the same stamped button primitive. */
    .st-key-p3_add_lecture_form_card [data-testid="stFormSubmitButton"] button {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 3px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
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
    .st-key-p3_add_lecture_form_card
      [data-testid="stFormSubmitButton"] button[kind="primary"],
    .st-key-p3_add_lecture_form_card
      [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] {
      background: var(--surf-paper5) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      color: var(--surf-paper) !important;
    }
    .st-key-p3_add_lecture_form_card
      [data-testid="stFormSubmitButton"] button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .st-key-p3_add_lecture_form_card
      [data-testid="stFormSubmitButton"] button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }

    /* Study Next dashed-border card. */
    .st-key-p3_study_next_card {
      background: var(--surf-paper);
      border: 2px dashed var(--surf-paper5);
      border-radius: 6px;
      box-shadow: none;
      margin: 0 0 24px;
      padding: 24px 28px;
    }
    /* Study Next row wrapper — keyed container is position: relative
       so the small > arrow button anchors against it (mirrors the
       attempt-history review-arrow placement). The overlay's right
       padding leaves room for the absolute 40x40 button. */
    [class*="st-key-p3_study_next_row_"] {
      margin: 0 0 12px;
      position: relative;
    }
    .surf-p3-lo-row {
      align-items: center;
      background: var(--surf-paper0);
      border-radius: 4px;
      box-shadow: none;
      display: flex;
      gap: 24px;
      margin: 0;
      padding: 16px 76px 16px 20px;
    }
    .surf-p3-lo-rank {
      color: var(--surf-accent);
      font-family: "Fraunces", Georgia, serif;
      font-size: 40px;
      font-style: italic;
      font-weight: 700;
      letter-spacing: -0.01em;
      line-height: 1;
      min-width: 64px;
    }
    .surf-p3-lo-content {
      flex: 1 1 auto;
    }
    .surf-p3-lo-title {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 18px;
      font-style: italic;
      font-weight: 600;
      line-height: 1.3;
    }
    .surf-p3-lo-meta {
      color: var(--surf-accent);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      letter-spacing: 0.04em;
      line-height: 1.5;
    }

    /* Study Next per-LO `>` button — small stamped icon button,
       absolutely centered on the right edge of the LO row. Same
       placement logic as the attempt-history review arrow; light
       Paper variant of that style. The keyed wrapper is pinned to
       button-only height so translateY(-50%) lands the visible
       square exactly on the row midline. */
    [class*="st-key-p3_practice_btn_"] {
      gap: 0 !important;
      line-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      position: absolute;
      right: 16px;
      top: 50%;
      transform: translateY(-50%);
      width: auto;
      z-index: 2;
    }
    [class*="st-key-p3_practice_btn_"] [data-testid="stElementContainer"] {
      margin: 0 !important;
      padding: 0 !important;
      position: static !important;
    }
    [class*="st-key-p3_practice_btn_"] [data-testid="stButton"] {
      width: auto !important;
    }
    [class*="st-key-p3_practice_btn_"] [data-testid="stButton"] button {
      background: var(--surf-paper) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 3px !important;
      box-shadow: 2px 2px 0 var(--surf-shadow) !important;
      color: var(--surf-paper5) !important;
      cursor: pointer !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 16px !important;
      font-weight: 700 !important;
      height: 40px !important;
      line-height: 1 !important;
      margin: 0 !important;
      min-height: 40px !important;
      min-width: 40px !important;
      padding: 0 !important;
      width: 40px !important;
    }
    [class*="st-key-p3_practice_btn_"] [data-testid="stButton"] button:hover {
      box-shadow: 3px 3px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    [class*="st-key-p3_practice_btn_"] [data-testid="stButton"] button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(2px, 2px) !important;
    }

    /* Attempt history toggle bar — wide stamped Paper5 button matching
       the DASHBOARD button primitive. */
    .st-key-p3_attempt_history_toggle button {
      background: var(--surf-paper5) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 4px !important;
      box-shadow: 4px 4px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
      font-size: 13px !important;
      font-weight: 700 !important;
      height: 56px !important;
      letter-spacing: 0.14em !important;
      margin: 16px 0 24px !important;
      transition:
        transform 0.08s ease-out,
        box-shadow 0.08s ease-out !important;
      width: 100% !important;
    }
    .st-key-p3_attempt_history_toggle button:hover {
      box-shadow: 5px 5px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    .st-key-p3_attempt_history_toggle button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(4px, 4px) !important;
    }

    /* Attempt history rows — reuse the P2 stamped-card primitive
       (Paper0 fill + 1.5px Paper5 border + 3px stamp shadow), with the
       same color-tier grade typography as the P2 last-4-mock-avg. The
       row itself is a flat band with a small arrow button on the
       right that routes to the P5 review surface. */
    [class*="st-key-p3_attempt_card_"] {
      background: var(--surf-paper);
      border: 1.5px solid var(--surf-paper5);
      border-radius: 4px;
      box-shadow: 3px 3px 0 var(--surf-shadow);
      box-sizing: border-box;
      margin: 0 0 16px;
      padding: 20px 24px;
      position: relative;
    }
    .surf-p3-attempt-row {
      align-items: center;
      display: flex;
      gap: 32px;
      padding-right: 64px; /* leave room for the absolute review arrow */
    }
    .surf-p3-attempt-kind {
      color: var(--surf-paper5);
      flex: 0 0 auto;
      font-family: "Fraunces", Georgia, serif;
      font-size: 22px;
      font-style: italic;
      font-weight: 700;
      min-width: 180px;
    }
    .surf-p3-attempt-kind .surf-p3-attempt-date {
      color: var(--surf-paper4);
      display: block;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      font-style: normal;
      font-weight: 500;
      letter-spacing: 0.08em;
      margin-top: 4px;
      text-transform: uppercase;
    }
    /* Practice-only LO line below the date. Same Mono / uppercase
       chrome as the date so the practice card stack matches the
       mock-card height. */
    .surf-p3-attempt-kind .surf-p3-attempt-lo {
      color: var(--surf-accent);
      display: block;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      font-style: normal;
      font-weight: 500;
      letter-spacing: 0.08em;
      line-height: 1.4;
      margin-top: 8px;
      text-transform: uppercase;
    }
    .surf-p3-attempt-meta {
      color: var(--surf-paper4);
      flex: 1 1 auto;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      letter-spacing: 0.04em;
      line-height: 1.6;
      text-transform: uppercase;
    }
    .surf-p3-attempt-grade {
      align-items: flex-end;
      display: flex;
      flex: 0 0 auto;
      flex-direction: column;
      gap: 2px;
      min-width: 100px;
    }
    .surf-p3-attempt-grade-label {
      color: var(--surf-paper4);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .surf-p3-attempt-grade-value {
      color: var(--surf-paper5);
      font-family: "Fraunces", Georgia, serif;
      font-size: 40px;
      font-style: italic;
      font-weight: 700;
      letter-spacing: -0.02em;
      line-height: 1;
    }
    .surf-p3-attempt-grade-value.tier-fail { color: var(--surf-accent-deep); }
    .surf-p3-attempt-grade-value.tier-borderline { color: var(--surf-status-warn); }
    .surf-p3-attempt-grade-value.tier-pass { color: var(--surf-status-ok); }
    .surf-p3-attempt-grade-value.tier-empty { color: var(--surf-paper3); }

    /* Review-arrow button — small stamped Paper5 button, absolute on
       the right edge of the attempt card. */
    [class*="st-key-p3_attempt_review_btn_"] {
      position: absolute;
      right: 16px;
      top: 50%;
      transform: translateY(-50%);
      width: auto;
      z-index: 2;
    }
    [class*="st-key-p3_attempt_review_btn_"] [data-testid="stButton"] {
      width: auto !important;
    }
    [class*="st-key-p3_attempt_review_btn_"] [data-testid="stButton"] button {
      background: var(--surf-paper5) !important;
      border: 1.5px solid var(--surf-paper5) !important;
      border-radius: 3px !important;
      box-shadow: 2px 2px 0 var(--surf-shadow) !important;
      color: var(--surf-paper) !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 14px !important;
      font-weight: 700 !important;
      height: 40px !important;
      line-height: 1 !important;
      margin: 0 !important;
      min-height: 40px !important;
      min-width: 40px !important;
      padding: 0 !important;
      width: 40px !important;
    }
    [class*="st-key-p3_attempt_review_btn_"] [data-testid="stButton"] button:hover {
      box-shadow: 3px 3px 0 var(--surf-shadow) !important;
      transform: translate(-1px, -1px) !important;
    }
    [class*="st-key-p3_attempt_review_btn_"] [data-testid="stButton"] button:active {
      box-shadow: 0 0 0 var(--surf-shadow) !important;
      transform: translate(2px, 2px) !important;
    }

    /* Recovery state. */
    .surf-p3-recovery-card {
      background: var(--surf-paper0);
      border: 1.5px solid var(--surf-paper5);
      border-radius: 4px;
      box-shadow: 3px 3px 0 var(--surf-shadow);
      padding: 32px 28px;
      text-align: center;
    }

    @media (prefers-reduced-motion: reduce) {
      .st-key-p3_class_hub_page [data-testid="stButton"] button,
      .st-key-p3_class_hub_page [data-testid="stButton"] button:hover,
      .st-key-p3_class_hub_page [data-testid="stButton"] button:active {
        transform: none !important;
        transition: background 0.08s ease-out !important;
      }
    }
    </style>
    """
    )


def _render_recovery(switch_page_fn: Callable[[str], None]) -> None:
    st.html(
        '<div class="surf-p3-recovery-card">'
        f'<h2 class="surf-p3-section-heading">{escape(RECOVERY_NO_CLASS_TITLE)}</h2>'
        f'<p class="surf-p3-field-helper">{escape(RECOVERY_NO_CLASS_BODY)}</p>'
        "</div>"
    )
    if st.button(
        RECOVERY_BACK_TO_HOME_LABEL,
        key="p3_recovery_back",
        type="primary",
    ):
        switch_page_fn(MY_CLASSES_VIEW_PATH)


def _lecture_cell_overlay_html(
    cell: dict[str, Any],
    *,
    is_selected: bool,
) -> str:
    """Build the absolute-positioned visual overlay for a lecture cell.

    The overlay carries the L-prefix label (red), the lecture title
    (dark), the optional status badge (PENDING / FAILED), and a custom
    checkbox visual. ``pointer-events: none`` is applied via CSS so the
    overlay never swallows clicks intended for the underlying button.
    """
    if cell["kind"] == "empty":
        title_html = (
            f'<span class="surf-p3-lecture-title">{escape(cell["title"])}</span>'
        )
        return f'<div class="surf-p3-lecture-overlay">{title_html}</div>'

    parts: list[str] = []
    if cell["selectable"]:
        checkbox_class = (
            "surf-p3-lecture-checkbox is-selected"
            if is_selected
            else "surf-p3-lecture-checkbox"
        )
        parts.append(f'<span class="{checkbox_class}"></span>')
    else:
        parts.append(
            '<span class="surf-p3-lecture-checkbox is-disabled"></span>'
        )
    if cell["label"]:
        parts.append(
            f'<span class="surf-p3-lecture-label">{escape(cell["label"])}</span>'
        )
    parts.append(
        f'<span class="surf-p3-lecture-title">{escape(cell["title"])}</span>'
    )
    if cell["status"] in ("pending", "failed"):
        parts.append(
            f'<span class="surf-p3-lecture-status">{escape(cell["status"].upper())}</span>'
        )
    return f'<div class="surf-p3-lecture-overlay">{"".join(parts)}</div>'


def _render_lecture_pick_cell(
    cell: dict[str, Any],
    *,
    new_selected: set[int],
    delete_mode_active: bool = False,
) -> None:
    """Render one lecture cell — entire card is the click target.

    Idle (``delete_mode_active=False``): selectable cells toggle
    selection for mock building; pending/failed cells are read-only
    with their status badge.

    Delete mode (``delete_mode_active=True``): only ``cell['deletable']``
    cells are clickable, and clicking spawns the destructive-confirmation
    dialog by setting :data:`DELETE_PENDING_LECTURE_KEY`. All other
    lectures (attempted-but-not-deletable + pending/failed) render in
    a visually muted, non-interactive ``muted`` state.

    Mutates ``new_selected`` in place when a normal-mode toggle fires.
    Empty cells are rendered without a keyed container so multiple
    empty cells never collide on a shared Streamlit key.
    """
    if cell["kind"] == "empty":
        st.html(
            '<div class="surf-p3-lecture-empty-cell">'
            f'<span class="surf-p3-lecture-title">{escape(cell["title"])}</span>'
            "</div>"
        )
        return

    lecture_id = int(cell["lecture_id"])
    is_selected = lecture_id in new_selected

    if delete_mode_active:
        state_class = "deletable" if cell["deletable"] else "muted"
    elif cell["selectable"]:
        state_class = "selected" if is_selected else "unselected"
    else:
        state_class = cell["status"]  # "pending" | "failed"

    wrapper_key = f"p3_lecture_pick_{state_class}_{lecture_id}"
    with st.container(key=wrapper_key):
        if delete_mode_active:
            if cell["deletable"]:
                if st.button(
                    " ",
                    key=f"p3_delete_target_btn_{lecture_id}",
                    help=f"Delete {cell['title']}",
                    use_container_width=True,
                ):
                    st.session_state[DELETE_PENDING_LECTURE_KEY] = lecture_id
                    st.rerun()
        elif cell["selectable"]:
            if st.button(
                " ",
                key=f"p3_lecture_btn_{lecture_id}",
                help=f"Toggle {cell['title']}",
                use_container_width=True,
            ):
                if is_selected:
                    new_selected.discard(lecture_id)
                else:
                    new_selected.add(lecture_id)
                st.session_state[SELECTED_LECTURES_KEY] = sorted(new_selected)
                st.rerun()
        st.html(
            _lecture_cell_overlay_html(
                cell,
                is_selected=is_selected and not delete_mode_active,
            )
        )


def _render_lecture_grid(
    cells: list[dict[str, Any]],
    *,
    selected_lecture_ids: set[int],
    delete_mode_active: bool = False,
) -> set[int]:
    """Render the 3-col lecture grid; return the new selected set."""
    new_selected: set[int] = set(selected_lecture_ids)
    rows = [
        cells[i : i + LECTURE_GRID_COLUMNS]
        for i in range(0, len(cells), LECTURE_GRID_COLUMNS)
    ]
    for row in rows:
        cols = st.columns(LECTURE_GRID_COLUMNS, gap="small")
        for col, cell in zip(cols, row):
            with col:
                _render_lecture_pick_cell(
                    cell,
                    new_selected=new_selected,
                    delete_mode_active=delete_mode_active,
                )
    return new_selected


def _render_class_page_title(class_name: str) -> None:
    """Render the class name as a Fraunces italic page title above
    the DASHBOARD button. Same family + italic as the section heading
    (``Pick the lectures you want to be tested on.``) but a step up
    in display size so the page identity reads first.
    """
    clean = (class_name or "").strip()
    if not clean:
        return
    render_page_header(
        kicker=PAGE_TITLE.upper(),
        title=clean,
        helper=BUILD_MOCK_HEADING,
        key="p3_page_header",
    )


def _render_dashboard_button(
    *,
    switch_page_fn: Callable[[str], None] | None = None,
) -> None:
    switch_page = switch_page_fn or st.switch_page
    with st.container(key="p3_dashboard_button"):
        if st.button(
            DASHBOARD_LABEL,
            key="p3_dashboard_action",
            use_container_width=True,
        ):
            switch_page(DASHBOARD_VIEW_PATH)


def _render_custom_mock_button(
    *,
    class_id: int,
    class_name: str | None,
    custom_launch_fn: Callable[..., dict[str, Any]],
    switch_page_fn: Callable[[str], None] | None = None,
) -> None:
    """Render the red `CUSTOM MOCK >` button directly under Dashboard.

    Phase 7. Launches up to 10 highest personal-difficulty questions
    using the existing P4 session contract. Does not change normal
    `TAKE MOCK >`, Study Next, or Dashboard behavior.
    """
    switch_page = switch_page_fn or st.switch_page
    with st.container(key="p3_custom_mock_button"):
        if st.button(
            CUSTOM_MOCK_LABEL,
            key="p3_custom_mock_action",
            use_container_width=True,
        ):
            state = custom_launch_fn(
                class_id=int(class_id),
                class_name=class_name,
            )
            if state.get("ok"):
                switch_page(TAKE_MOCK_VIEW_PATH)
            else:
                st.toast(CUSTOM_MOCK_EMPTY_TOAST)


def _render_custom_mock_explainer() -> None:
    """Render the text-only learn-more toggle under Custom Mock."""
    is_open = bool(st.session_state.get(CUSTOM_MOCK_HELP_OPEN_KEY, False))
    label = CUSTOM_MOCK_HELP_HIDE_LABEL if is_open else CUSTOM_MOCK_HELP_LABEL
    with st.container(key="p3_custom_mock_learn_more"):
        if st.button(label, key="p3_custom_mock_learn_more_action"):
            st.session_state[CUSTOM_MOCK_HELP_OPEN_KEY] = not is_open
    if st.session_state.get(CUSTOM_MOCK_HELP_OPEN_KEY, False):
        with st.container(key="p3_custom_mock_help_card"):
            st.html(
                '<p class="surf-p3-custom-help-body">'
                f"{escape(CUSTOM_MOCK_HELP_BODY)}"
                "</p>"
            )


def _render_take_mock_button(
    state: dict[str, Any],
    *,
    disabled: bool = False,
) -> bool:
    is_disabled = disabled or not state["enabled"]
    with st.container(key="p3_take_mock_button"):
        clicked = st.button(
            TAKE_MOCK_LABEL,
            key="p3_take_mock_action",
            type="primary",
            disabled=is_disabled,
            help=(
                state["honest_short_copy"]
                if state["enabled"] and not disabled
                else TAKE_MOCK_DISABLED_HELP
            ),
            use_container_width=True,
        )
    return clicked


def _study_next_shared_styles(*, key_prefix: str) -> str:
    """Return the reusable Study Next card styles for P3 and P6."""
    escaped_prefix = escape(key_prefix)
    return f"""
    <style>
    .st-key-{escaped_prefix}_study_next_card {{
      background: #F5EFE4;
      border: 2px dashed #28251F;
      border-radius: 6px;
      box-shadow: none;
      margin: 0 0 24px;
      padding: 24px 28px;
    }}
    [class*="st-key-{escaped_prefix}_study_next_row_"] {{
      margin: 0 0 12px;
      position: relative;
    }}
    .surf-p3-lo-row {{
      align-items: center;
      background: #FDF9F2;
      border-radius: 4px;
      box-shadow: none;
      display: flex;
      gap: 24px;
      margin: 0;
      padding: 16px 76px 16px 20px;
    }}
    .surf-p3-lo-rank {{
      color: #B65A3A;
      font-family: "Fraunces", Georgia, serif;
      font-size: 40px;
      font-style: italic;
      font-weight: 700;
      letter-spacing: -0.01em;
      line-height: 1;
      min-width: 64px;
    }}
    .surf-p3-lo-content {{ flex: 1 1 auto; }}
    .surf-p3-lo-title {{
      color: #28251F;
      font-family: "Fraunces", Georgia, serif;
      font-size: 18px;
      font-style: italic;
      font-weight: 600;
      line-height: 1.3;
    }}
    .surf-p3-lo-meta {{
      color: #B65A3A;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      letter-spacing: 0.04em;
      line-height: 1.5;
    }}
    [class*="st-key-{escaped_prefix}_practice_btn_"] {{
      gap: 0 !important;
      line-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      position: absolute;
      right: 16px;
      top: 50%;
      transform: translateY(-50%);
      width: auto;
      z-index: 2;
    }}
    [class*="st-key-{escaped_prefix}_practice_btn_"] [data-testid="stElementContainer"] {{
      margin: 0 !important;
      padding: 0 !important;
      position: static !important;
    }}
    [class*="st-key-{escaped_prefix}_practice_btn_"] [data-testid="stButton"] {{
      width: auto !important;
    }}
    [class*="st-key-{escaped_prefix}_practice_btn_"] [data-testid="stButton"] button {{
      background: #F5EFE4 !important;
      border: 1.5px solid #28251F !important;
      border-radius: 3px !important;
      box-shadow: 2px 2px 0 #171512 !important;
      color: #28251F !important;
      cursor: pointer !important;
      font-family: "JetBrains Mono", ui-monospace, monospace !important;
      font-size: 16px !important;
      font-weight: 700 !important;
      height: 40px !important;
      line-height: 1 !important;
      padding: 0 !important;
      width: 40px !important;
    }}
    </style>
    """


def render_study_next_section(
    view_models: list[dict[str, Any]],
    *,
    st_module: Any = st,
    key_prefix: str = "p3",
) -> int | None:
    """Render the shared P3/P6 Study Next card and return a clicked LO id."""
    practiced_lo_id: int | None = None
    st_module.html(_study_next_shared_styles(key_prefix=key_prefix))
    with st_module.container(key=f"{key_prefix}_study_next_card"):
        st_module.html(
            '<div class="surf-p3-section-label" data-section-label="STUDY NEXT">'
            f"{escape(STUDY_NEXT_SECTION_LABEL)}</div>"
        )
        st_module.html(
            f'<h2 class="surf-p3-section-heading">{escape(STUDY_NEXT_HEADING)}</h2>'
        )
        if not view_models:
            st_module.html(
                f'<p class="surf-p3-field-helper">{escape(STUDY_NEXT_EMPTY_COPY)}</p>'
            )
            return None
        for vm in view_models:
            rank_html = (
                f'<span class="surf-p3-lo-rank">{vm["rank"]:02d}</span>'
            )
            title_html = (
                f'<span class="surf-p3-lo-title">{escape(vm["lo_title"])}</span>'
            )
            meta_html = (
                f'<span class="surf-p3-lo-meta">'
                f'Lecture {vm.get("lecture_label") or vm.get("lecture_id") or "—"}<br>'
                f"Questions Ready {vm['questions_ready']}"
                "</span>"
            )
            with st_module.container(key=f"{key_prefix}_study_next_row_{vm['lo_id']}"):
                st_module.html(
                    '<div class="surf-p3-lo-row">'
                    f"{rank_html}"
                    '<div class="surf-p3-lo-content">'
                    f"{title_html}<br>{meta_html}"
                    "</div>"
                    "</div>"
                )
                with st_module.container(key=f"{key_prefix}_practice_btn_{vm['lo_id']}"):
                    if st_module.button(
                        ">",
                        key=f"{key_prefix}_practice_{vm['lo_id']}",
                        help=f"Practice {vm['lo_title']}",
                    ):
                        practiced_lo_id = int(vm["lo_id"])
    return practiced_lo_id


def _render_delete_lecture_button(
    *,
    delete_mode_active: bool,
    has_deletable: bool,
) -> bool:
    """Render the DELETE LECTURE / UNDO action-row toggle.

    Idle: ``DELETE LECTURE``, disabled when no lecture is currently
    deletable. Active: ``UNDO``, always enabled. Returns whether the
    button was clicked; the caller owns the
    :data:`DELETE_MODE_KEY` session-state slot.
    """
    label = (
        DELETE_LECTURE_UNDO_LABEL
        if delete_mode_active
        else DELETE_LECTURE_BUTTON_LABEL
    )
    is_disabled = (not delete_mode_active) and (not has_deletable)
    if delete_mode_active:
        help_text = DELETE_LECTURE_PROMPT_HELP
    elif is_disabled:
        help_text = DELETE_LECTURE_DISABLED_HELP
    else:
        help_text = "Enter delete mode to remove a lecture."
    with st.container(key="p3_delete_lecture_button"):
        return st.button(
            label,
            key="p3_delete_lecture_action",
            disabled=is_disabled,
            help=help_text,
            use_container_width=True,
        )


def _render_study_next(view_models: list[dict[str, Any]]) -> int | None:
    return render_study_next_section(view_models, st_module=st, key_prefix="p3")


def _render_attempt_history(
    view_models: list[dict[str, Any]],
    *,
    switch_page_fn: Callable[[str], None],
) -> None:
    """Render the Attempt History toggle + (when open) the attempt cards.

    Default-open: when the user has any completed attempt the section
    starts expanded so the most recent grade is visible without an
    extra click. The toggle still lets the user collapse it.

    Each card reuses the P2 stamped-card primitive (Paper0 + Paper5
    border + 3px stamp shadow) and the P2 color-tier grade
    typography. The right edge carries a small stamped arrow button
    that routes to the P5 review surface.
    """
    is_open = bool(st.session_state.get(ATTEMPT_HISTORY_OPEN_KEY, True))
    label = (
        ATTEMPT_HISTORY_CLOSE_LABEL if is_open else ATTEMPT_HISTORY_OPEN_LABEL
    )
    with st.container(key="p3_attempt_history_toggle"):
        if st.button(
            label,
            key="p3_attempt_history_action",
            use_container_width=True,
        ):
            st.session_state[ATTEMPT_HISTORY_OPEN_KEY] = not is_open
            st.rerun()
    if not is_open:
        return
    for vm in view_models:
        finished = vm.get("finished_at")
        date_str = format_finished_at(finished) if finished else "—"
        # Practice attempts move their LO title into the
        # left column under the date so the practice card matches
        # the mock-card height. The meta column keeps Questions /
        # Correct / Lectures Tested.
        meta_lines: list[str] = []
        meta_lines.append(f"{vm['question_count']} Questions")
        meta_lines.append(f"{vm['correct_count']} Correct")
        if vm.get("lecture_labels"):
            meta_lines.append("")
            meta_lines.append("Lectures Tested")
            meta_lines.append(
                " - ".join(escape(str(x)) for x in vm["lecture_labels"])
            )
        meta_html = "<br>".join(meta_lines)
        lo_html = ""
        if vm["kind"] == "practice" and vm.get("lo_title"):
            lo_html = (
                '<span class="surf-p3-attempt-lo">'
                f"{escape(str(vm['lo_title']))}"
                "</span>"
            )
        grade = vm.get("swiss_grade")
        grade_str = (
            f"{float(grade):.2f}" if grade is not None else "—"
        )
        tier_class = f"tier-{vm['swiss_grade_tier']}"

        with st.container(key=f"p3_attempt_card_{vm['attempt_id']}"):
            st.html(
                '<div class="surf-p3-attempt-row">'
                f'<div class="surf-p3-attempt-kind">'
                f"{escape(vm['kind_label'])}"
                f'<span class="surf-p3-attempt-date">{escape(date_str)}</span>'
                f"{lo_html}"
                "</div>"
                f'<div class="surf-p3-attempt-meta">{meta_html}</div>'
                '<div class="surf-p3-attempt-grade">'
                '<span class="surf-p3-attempt-grade-label">Grade</span>'
                f'<span class="surf-p3-attempt-grade-value {tier_class}">'
                f"{escape(grade_str)}</span>"
                "</div>"
                "</div>"
            )
            with st.container(key=f"p3_attempt_review_btn_{vm['attempt_id']}"):
                if st.button(
                    "→",
                    key=f"p3_attempt_review_{vm['attempt_id']}",
                    help=f"Review {vm['kind_label']}",
                ):
                    st.session_state["current_attempt_id"] = vm["attempt_id"]
                    switch_page_fn(REVIEW_MOCK_VIEW_PATH)


def _render_lecture_delete_dialog(
    *,
    user_id: int,
    class_id: int,
    class_name: str,
    lecture: Mapping[str, Any],
    delete_handler: Callable[..., dict[str, Any]],
) -> None:
    @st.dialog(LECTURE_DELETE_DIALOG_TITLE)
    def _dialog() -> None:
        body = LECTURE_DELETE_DIALOG_BODY_TEMPLATE.format(
            title=escape(str(lecture.get("title", "Untitled"))),
            class_name=escape(class_name or "this class"),
        )
        st.html(f'<p class="surf-p3-field-helper">{body}</p>')
        col_keep, col_delete = st.columns(2, gap="small")
        with col_keep:
            with st.container(key="p3_dialog_keep"):
                keep_clicked = st.button(
                    LECTURE_DELETE_KEEP_LABEL,
                    key="p3_delete_lecture_keep",
                    use_container_width=True,
                )
        with col_delete:
            with st.container(key="p3_dialog_delete"):
                delete_clicked = st.button(
                    LECTURE_DELETE_CONFIRM_LABEL,
                    key="p3_delete_lecture_confirm",
                    use_container_width=True,
                )
        if keep_clicked:
            # Cancel: clear the pending pick but stay in delete mode so
            # the user can pick another card.
            st.session_state.pop(DELETE_PENDING_LECTURE_KEY, None)
            st.rerun()
        if delete_clicked:
            result = delete_handler(
                user_id=user_id,
                class_id=class_id,
                lecture_id=int(lecture["id"]),
                confirmed=True,
            )
            st.session_state.pop(DELETE_PENDING_LECTURE_KEY, None)
            # Confirming a deletion exits delete mode.
            st.session_state[DELETE_MODE_KEY] = False
            status = result.get("status")
            if status == "deleted":
                st.toast(LECTURE_DELETE_SUCCESS_TOAST)
            elif status == "blocked":
                st.toast(LECTURE_DELETE_BLOCKED_TOAST)
            elif status == "not_owned":
                st.toast(LECTURE_DELETE_NOT_OWNED_TOAST)
            else:
                st.toast(LECTURE_DELETE_BLOCKED_TOAST)
            st.rerun()

    _dialog()


def _render_add_lecture_form(
    *,
    user_id: int,
    class_id: int,
    submit_fn: Callable[..., dict[str, Any]],
) -> None:
    with (
        st.container(key="p3_add_lecture_form_card"),
        st.form("p3_add_lecture_form", clear_on_submit=False),
    ):
        st.html(f'<div class="surf-p3-form-title">{escape(ADD_LECTURE_FORM_TITLE)}</div>')
        st.html(
            f'<div class="surf-p3-field-label">{escape(LECTURE_NAME_LABEL)}</div>'
        )
        lecture_name = st.text_input(
            LECTURE_NAME_LABEL,
            key="p3_add_lecture_name",
            label_visibility="collapsed",
            placeholder=LECTURE_NAME_PLACEHOLDER,
        )
        st.html(
            f'<div class="surf-p3-field-label">{escape(UPLOAD_SLIDES_LABEL)}</div>'
        )
        with st.container(key="p3_lecture_dropbox"):
            st.html(
                '<div class="surf-p3-dropbox-visual">'
                '<span class="surf-p3-dropbox-icon" aria-hidden="true"></span>'
                f'<div class="surf-p3-dropbox-title">{escape(LECTURE_DROPBOX_TITLE)}</div>'
                f'<p class="surf-p3-dropbox-helper">{escape(LECTURE_DROPBOX_HELPER)}</p>'
                '</div>'
            )
            slide_pdf_file = st.file_uploader(
                UPLOAD_SLIDES_LABEL,
                type=["pdf"],
                key="p3_add_lecture_pdf",
                label_visibility="collapsed",
            )
            if slide_pdf_file is not None:
                st.html(
                    '<p class="surf-p3-dropbox-ready">READY: '
                    f'{escape(getattr(slide_pdf_file, "name", "lecture.pdf"))}'
                    '</p>'
                )
        st.html(
            f'<p class="surf-p3-field-helper">{escape(UPLOAD_SLIDES_HELPER)}</p>'
        )

        col_discard, col_submit = st.columns([1, 1], gap="small")
        with col_discard:
            discard_clicked = st.form_submit_button(
                DISCARD_LECTURE_DRAFT_LABEL,
                use_container_width=True,
            )
        with col_submit:
            submit_clicked = st.form_submit_button(
                ADD_LECTURE_LABEL,
                type="primary",
                use_container_width=True,
            )

    if discard_clicked:
        st.session_state[ADD_LECTURE_OPEN_KEY] = False
        for stale in ("p3_add_lecture_name", "p3_add_lecture_pdf"):
            st.session_state.pop(stale, None)
        st.rerun()
    elif submit_clicked:
        cleaned_lecture_name = (lecture_name or "").strip()
        if not cleaned_lecture_name:
            st.error(ADD_LECTURE_MISSING_TITLE)
            return
        if slide_pdf_file is None:
            st.error(ADD_LECTURE_MISSING_PDF)
            return
        popup = st.empty()
        show_processing_popup(popup, state="processing")
        with st.spinner(ADD_LECTURE_PROCESSING_TOAST):
            result = submit_fn(
                user_id=user_id,
                class_id=class_id,
                lecture_title=cleaned_lecture_name,
                slide_pdf_file=slide_pdf_file,
            )
        if result.get("ok"):
            show_processing_popup(popup, state="done")
            sleep(0.75)
            st.toast(ADD_LECTURE_SAVED_READY_TOAST)
            st.session_state[ADD_LECTURE_OPEN_KEY] = False
            for stale in ("p3_add_lecture_name", "p3_add_lecture_pdf"):
                st.session_state.pop(stale, None)
            st.rerun()
        else:
            popup.empty()
            error = result.get("error")
            if error == "missing_title":
                st.error(ADD_LECTURE_MISSING_TITLE)
            elif error == "missing_pdf":
                st.error(ADD_LECTURE_MISSING_PDF)
            elif error == "missing_api_key":
                st.error(ADD_LECTURE_MISSING_API_KEY)
            else:
                detail = result.get("detail") or ""
                if detail:
                    st.toast(f"{ADD_LECTURE_INGEST_FAIL_TITLE} — {detail}")
                else:
                    st.toast(ADD_LECTURE_INGEST_FAIL_TITLE)


def _default_layout_renderer(payload: dict[str, Any]) -> None:
    user = payload["user"]
    class_id = payload["class_id"]
    class_name = payload["class_name"]
    submit_fn = payload["submit_fn"]
    delete_handler = payload["delete_handler"]
    mock_launch_fn = payload["mock_launch_fn"]
    study_next_launch_fn = payload["study_next_launch_fn"]
    custom_launch_fn = payload["custom_launch_fn"]
    switch_page_fn = payload["switch_page_fn"]
    lecture_cells = payload["lecture_cells"]
    take_mock_state = payload["take_mock_state"]
    study_next = payload["study_next"]
    attempt_history_visible = payload["attempt_history_visible"]
    attempt_history = payload["attempt_history"]

    # Inject page styles via st.markdown(unsafe_allow_html=True) instead
    # of st.html(). The 258KB inline @font-face base64 trips Streamlit's
    # style-only branch which silently no-ops on large payloads; markdown
    # sends through the main delta generator path and paints reliably.
    st.markdown(_styles(), unsafe_allow_html=True)
    with page_rail("p3_class_hub_page"):
        _render_class_page_title(class_name)
        _render_dashboard_button(switch_page_fn=switch_page_fn)
        _render_custom_mock_button(
            class_id=int(class_id),
            class_name=class_name,
            custom_launch_fn=custom_launch_fn,
            switch_page_fn=switch_page_fn,
        )
        _render_custom_mock_explainer()

        with st.container(key="p3_build_mock_card"):
            st.html(
                f'<div class="surf-p3-section-label">{escape(BUILD_MOCK_SECTION_LABEL)}</div>'
            )
            st.html(
                f'<h2 class="surf-p3-section-heading">{escape(BUILD_MOCK_HEADING)}</h2>'
            )
            current_selection = set(
                int(x) for x in st.session_state.get(SELECTED_LECTURES_KEY, [])
            )
            delete_mode_active = bool(
                st.session_state.get(DELETE_MODE_KEY, False)
            )
            grid_selected = (
                set() if delete_mode_active else current_selection
            )
            new_selection = _render_lecture_grid(
                lecture_cells,
                selected_lecture_ids=grid_selected,
                delete_mode_active=delete_mode_active,
            )
            if not delete_mode_active and new_selection != current_selection:
                st.session_state[SELECTED_LECTURES_KEY] = sorted(new_selection)

            has_deletable = any(
                c["kind"] != "empty" and c.get("deletable")
                for c in lecture_cells
            )
            col_add, col_delete, col_take = st.columns(3, gap="medium")
            with col_add:
                with st.container(key="p3_add_lecture_button"):
                    if st.button(
                        ADD_LECTURE_LABEL,
                        key="p3_add_lecture_action",
                        disabled=delete_mode_active,
                        use_container_width=True,
                    ):
                        current = bool(
                            st.session_state.get(ADD_LECTURE_OPEN_KEY, False)
                        )
                        st.session_state[ADD_LECTURE_OPEN_KEY] = not current
                        st.rerun()
            with col_delete:
                _delete_clicked = _render_delete_lecture_button(
                    delete_mode_active=delete_mode_active,
                    has_deletable=has_deletable,
                )
                if _delete_clicked:
                    if delete_mode_active:
                        # UNDO → exit delete mode.
                        st.session_state[DELETE_MODE_KEY] = False
                    else:
                        # Enter delete mode with no previous lecture selection carried over.
                        st.session_state[DELETE_MODE_KEY] = True
                        st.session_state[SELECTED_LECTURES_KEY] = []
                    st.session_state.pop(DELETE_PENDING_LECTURE_KEY, None)
                    st.rerun()
            with col_take:
                _take_mock_clicked = _render_take_mock_button(
                    take_mock_state, disabled=delete_mode_active
                )
                if _take_mock_clicked:
                    mock_launch_fn(
                        class_id=int(class_id),
                        class_name=class_name,
                        selected_lecture_ids=sorted(
                            int(x) for x in st.session_state.get(
                                SELECTED_LECTURES_KEY,
                                [],
                            )
                        ),
                    )
                    switch_page_fn(TAKE_MOCK_VIEW_PATH)

        if st.session_state.get(ADD_LECTURE_OPEN_KEY, False):
            _render_add_lecture_form(
                user_id=int(user["id"]),
                class_id=int(class_id),
                submit_fn=submit_fn,
            )

        practiced_lo_id = _render_study_next(study_next)
        if practiced_lo_id is not None:
            study_next_launch_fn(
                class_id=int(class_id),
                class_name=class_name,
                learning_objective_id=practiced_lo_id,
            )
            switch_page_fn(TAKE_MOCK_VIEW_PATH)

        if attempt_history_visible:
            _render_attempt_history(
                attempt_history,
                switch_page_fn=switch_page_fn,
            )

        pending_lecture_id = st.session_state.pop(
            DELETE_PENDING_LECTURE_KEY, None
        )
        if pending_lecture_id is not None:
            lectures_by_id = payload["lectures_by_id"]
            lecture = lectures_by_id.get(int(pending_lecture_id))
            if lecture is not None:
                _render_lecture_delete_dialog(
                    user_id=int(user["id"]),
                    class_id=int(class_id),
                    class_name=class_name,
                    lecture=lecture,
                    delete_handler=delete_handler,
                )


def render_class_hub_page(
    *,
    user: Mapping[str, Any],
    class_id: int | None,
    get_class_fn: Callable[
        [int], Mapping[str, Any] | None
    ] = get_class_by_id,
    list_lectures_fn: Callable[
        [int], list[dict[str, Any]]
    ] = _default_lecture_query,
    ready_counts_fn: Callable[
        [Iterable[Mapping[str, Any]]], dict[int, int]
    ] = _default_ready_counts_query,
    attempted_lectures_fn: Callable[
        [int], set[int]
    ] = _default_attempted_lectures_query,
    weak_los_fn: Callable[
        [int], list[dict[str, Any]]
    ] = _default_weak_los_query,
    ready_counts_per_lo_fn: Callable[
        [Iterable[Mapping[str, Any]]], dict[int, int]
    ] = _default_ready_counts_per_lo,
    attempts_fn: Callable[
        [int], list[dict[str, Any]]
    ] = _default_attempts_query,
    submit_fn: Callable[..., dict[str, Any]] = submit_add_lecture_form,
    delete_handler: Callable[..., dict[str, Any]] = handle_lecture_delete,
    mock_launch_fn: Callable[..., dict[str, Any]] = launch_mock_standard,
    study_next_launch_fn: Callable[
        ..., dict[str, Any]
    ] = launch_study_next_practice,
    custom_launch_fn: Callable[..., dict[str, Any]] = launch_mock_custom,
    topbar_fn: Callable[..., None] = render_topbar,
    switch_page_fn: Callable[[str], None] | None = None,
    render_layout_fn: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Render the P3 Class Hub.

    Parameters mirror P2's renderer pattern: every side-effect entry is
    injectable so the preview sandbox and tests can stand in fakes
    without touching the real DB or Anthropic.

    When ``class_id`` is missing or ``get_class_fn`` returns None, the
    renderer falls into the recovery state with a BACK TO MY CLASSES
    primary button.
    """
    switch_page = switch_page_fn or st.switch_page
    klass = get_class_fn(int(class_id)) if class_id else None
    class_name = (
        str(klass.get("name", "")).strip() if klass else ""
    )
    topbar_fn("class_view", class_name=class_name or None)
    # See render_class_hub_with_payload — markdown path is the reliable
    # injector for the large @font-face style block.
    st.markdown(_styles(), unsafe_allow_html=True)

    if klass is None:
        with page_rail("p3_class_hub_page"):
            _render_recovery(switch_page_fn=switch_page)
        return

    lectures = list(list_lectures_fn(int(class_id)) or [])
    ready_counts = ready_counts_fn(lectures) or {}
    attempted_ids = set(attempted_lectures_fn(int(class_id)) or set())
    lecture_cells = build_lecture_grid_view_models(
        lectures,
        ready_counts_by_lecture_id=ready_counts,
        attempted_lecture_ids=attempted_ids,
    )
    selected = sorted(
        int(x) for x in st.session_state.get(SELECTED_LECTURES_KEY, [])
    )
    take_mock_state = compute_take_mock_state(
        selected,
        ready_counts_by_lecture_id=ready_counts,
    )

    weak_los = list(weak_los_fn(int(class_id)) or [])
    weak_los_lecture_label_map = {
        int(lecture["id"]): f"L{i + 1:02d}"
        for i, lecture in enumerate(lectures)
    }
    for row in weak_los:
        row.setdefault(
            "lecture_label",
            weak_los_lecture_label_map.get(int(row.get("lecture_id") or 0)),
        )
    ready_per_lo = ready_counts_per_lo_fn(weak_los) or {}
    study_next = build_study_next_view_models(
        weak_los,
        ready_counts_by_lo_id=ready_per_lo,
    )

    attempts = list(attempts_fn(int(class_id)) or [])
    attempt_history = build_attempt_history_view_models(attempts)
    history_visible = attempt_history_is_visible(attempts)

    payload: dict[str, Any] = {
        "user": dict(user),
        "class_id": int(class_id),
        "class_name": class_name,
        "submit_fn": submit_fn,
        "delete_handler": delete_handler,
        "mock_launch_fn": mock_launch_fn,
        "study_next_launch_fn": study_next_launch_fn,
        "custom_launch_fn": custom_launch_fn,
        "switch_page_fn": switch_page,
        "lecture_cells": lecture_cells,
        "lectures_by_id": {
            int(lecture["id"]): lecture for lecture in lectures
        },
        "take_mock_state": take_mock_state,
        "study_next": study_next,
        "attempt_history_visible": history_visible,
        "attempt_history": attempt_history,
    }

    layout = render_layout_fn or _default_layout_renderer
    layout(payload)

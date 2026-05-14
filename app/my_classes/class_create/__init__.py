"""P2 class creation from a required factsheet PDF."""
# --------------------------------------------------------------------------- #
# MODULE OVERVIEW — P2 CLASS CREATION SERVICE
# --------------------------------------------------------------------------- #
# Simple explanation:
# This module owns the back-end side of P2's "ADD CLASS" form. The page
# validates user input here, extracts the uploaded factsheet PDF into
# markdown, asks Claude to clean it into structured JSON, and inserts the
# new class row in SQLite. Class name and the grade-4 threshold are
# setup-only in V1 (editing them later is deferred), and the factsheet
# upload is required.
#
# Important code pieces:
# - `create_class_from_factsheet`: the one public function the renderer
#   calls. Returns a small status dict the UI can render.
# - `_normalize_threshold`: enforces 1..100 integer percent.
# - `_read_upload_bytes`: accepts Streamlit `UploadedFile`, raw bytes, or
#   anything with a `read`/`getvalue` method (helps tests + previews).
# - `_markdown_from_extraction`: extractor may return text or a tuple.
#
# App connection:
# This is the only place P2's "CREATE CLASS" path touches the live DB and
# Claude. The page never calls extractor / cleaner / DB helpers directly.
from __future__ import annotations

# Standard helpers keep uploaded factsheets in a temporary local file only.
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

# Class creation depends on extraction, saved-key lookup, cleaning, and DB insert.
from app.brain.ingestion.pdf_to_md_v3 import extract_with_tables
from app.db.queries_classes import insert_class
from app.db.queries_users import get_saved_anthropic_api_key
from app.my_classes.factsheet_clean import clean_factsheet

# Public service exported for the My Classes renderer.
__all__ = ["create_class_from_factsheet"]


# --------------------------------------------------------------------------- #
# INPUT VALIDATION HELPERS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Small pure functions that check or coerce user inputs before any DB or
# Claude work runs. Failing fast here keeps the live SQLite file clean.
#
# Key detail:
# - `_invalid_input`: returns a renderer-friendly error dict naming the
#   bad field, so the UI can highlight exactly what to fix.


# Renderer-friendly error helper for invalid class setup inputs.
def _invalid_input(field: str) -> dict[str, Any]:
    return {"ok": False, "error": "invalid_input", "field": field}


# The threshold is setup-only and must be a whole percent in the allowed range.
def _normalize_threshold(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, float) and not value.is_integer():
        return None
    try:
        threshold = int(value)
    except (TypeError, ValueError):
        return None
    if threshold < 1 or threshold > 100:
        return None
    return threshold


# Streamlit uploads and tests can supply bytes or file-like objects.
def _read_upload_bytes(factsheet_file_or_bytes: Any) -> bytes | None:
    if factsheet_file_or_bytes is None:
        return None
    if isinstance(factsheet_file_or_bytes, (bytes, bytearray, memoryview)):
        data = bytes(factsheet_file_or_bytes)
    elif hasattr(factsheet_file_or_bytes, "getvalue"):
        try:
            data = factsheet_file_or_bytes.getvalue()
        except Exception:
            return None
    elif hasattr(factsheet_file_or_bytes, "read"):
        try:
            data = factsheet_file_or_bytes.read()
        except Exception:
            return None
    else:
        return None

    if isinstance(data, str):
        data = data.encode("utf-8")
    if not isinstance(data, (bytes, bytearray, memoryview)):
        return None
    out = bytes(data)
    return out if out else None


# `extract_with_tables` returns Markdown first, with optional metadata after it.
def _markdown_from_extraction(extracted: Any) -> str:
    if isinstance(extracted, tuple):
        return extracted[0] if extracted else ""
    return extracted if isinstance(extracted, str) else ""


# --------------------------------------------------------------------------- #
# PUBLIC ENTRY POINT — `create_class_from_factsheet`
# --------------------------------------------------------------------------- #
# Simple explanation:
# The renderer hands us a class name, a grade-4 threshold percent, and the
# uploaded factsheet bytes. We validate every input, look up the saved
# Anthropic key for this local user, extract the PDF to markdown, ask
# Claude to clean it into JSON, then insert one new class row. If any
# step fails the function returns a small error dict and never persists a
# half-built class.
#
# Important code pieces:
# - `TemporaryDirectory`: the uploaded PDF is written to a temp folder and
#   wiped automatically. The factsheet never leaves the user's computer.
# - `get_saved_anthropic_api_key`: reads the locally stored key from
#   SQLite; if missing we return `missing_api_key` instead of calling out.
# - `extract_with_tables`: shared PDF -> markdown helper (no Claude call).
# - `clean_factsheet`: the ~10-line Claude wrapper described in the
#   factsheet_clean package; returns structured JSON.
# - `insert_class`: writes the SQLite row in a single transaction.
#
# App connection:
# This service is invoked from the "CREATE CLASS" form submit handler in
# the P2 renderer. Success closes the form and adds a new class card.
# Public class setup path: validate first, clean factsheet second, insert last.
def create_class_from_factsheet(
    user_id: int,
    class_name: str,
    grade4_threshold_percent: Any,
    factsheet_file_or_bytes: Any,
) -> dict[str, Any]:
    """Validate, clean the factsheet, then insert the class row.

    Returns a small renderer-friendly status dict. The class row is inserted
    only after factsheet extraction and Claude cleaning both succeed.
    """
    cleaned_name = class_name.strip() if isinstance(class_name, str) else ""
    if not cleaned_name:
        return _invalid_input("class_name")

    threshold = _normalize_threshold(grade4_threshold_percent)
    if threshold is None:
        return _invalid_input("grade4_threshold_percent")

    upload_bytes = _read_upload_bytes(factsheet_file_or_bytes)
    if upload_bytes is None:
        return _invalid_input("factsheet")

    saved_key = get_saved_anthropic_api_key(user_id)
    if saved_key is None or not saved_key.strip():
        return {"ok": False, "error": "missing_api_key"}

    try:
        with TemporaryDirectory(prefix="surf_factsheet_") as temp_dir:
            temp_pdf = Path(temp_dir) / "factsheet.pdf"
            temp_pdf.write_bytes(upload_bytes)

            raw_markdown = _markdown_from_extraction(extract_with_tables(temp_pdf))
            if not raw_markdown.strip():
                return {"ok": False, "error": "factsheet_processing_failed"}

            factsheet_json = clean_factsheet(raw_markdown, api_key=saved_key)
    except Exception:
        return {"ok": False, "error": "factsheet_processing_failed"}

    try:
        class_id = insert_class(
            user_id,
            cleaned_name,
            factsheet_json,
            threshold,
        )
    except Exception:
        return {"ok": False, "error": "class_save_failed"}

    return {
        "ok": True,
        "class_id": class_id,
        "class_name": cleaned_name,
    }

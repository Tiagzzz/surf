"""Smoke test — confirms the four real modules import and expose their public API.

Skipped per-module when optional dependencies (anthropic SDK, pdfplumber)
are not installed in the local venv. This keeps the test suite green on
machines that haven't run `pip install -r requirements.txt` yet.

Run with:  pytest -q
"""
from __future__ import annotations

import importlib
from typing import Any

import pytest


def _try_import(module: str) -> Any:
    """Import a module or skip the test cleanly when its deps are missing."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        pytest.skip(f"{module} unavailable: {exc}")


def test_claude_client_exposes_call_claude() -> None:
    mod = _try_import("app.brain.claude_client")
    assert callable(getattr(mod, "call_claude", None)), (
        "app.brain.claude_client must re-export call_claude (see __init__.py)"
    )


def test_factsheet_cleaner_exposes_clean_factsheet() -> None:
    _try_import("app.brain.claude_client")  # transitive: cleaner imports it
    mod = _try_import("app.my_classes.factsheet_clean.factsheet_cleaner")
    assert callable(getattr(mod, "clean_factsheet", None)), (
        "factsheet_cleaner must expose clean_factsheet(raw_md: str) -> dict"
    )


def test_factsheet_renderer_exposes_render() -> None:
    mod = _try_import("app.my_classes.factsheet_clean.factsheet_renderer")
    assert callable(getattr(mod, "render_cleaned_factsheet_markdown", None)), (
        "factsheet_renderer must expose render_cleaned_factsheet_markdown(data: dict) -> str"
    )


def test_pdf_to_md_v3_exposes_extract_with_tables() -> None:
    _try_import("pdfplumber")  # required by the module
    mod = _try_import("app.brain.ingestion.pdf_to_md_v3")
    assert callable(getattr(mod, "extract_with_tables", None)), (
        "pdf_to_md_v3 must expose extract_with_tables(pdf_path: Path)"
    )

"""Smoke test — confirms the four real modules import and expose their public API.

Skipped per-module when optional dependencies (anthropic SDK, pdfplumber)
are not installed in the local venv. This keeps the test suite green on
machines that haven't run `pip install -r requirements.txt` yet.

Run with:  pytest -q
"""
from __future__ import annotations

import importlib
import pathlib
from typing import Any

import pytest


def _try_import(module: str) -> Any:
    """Import a module or skip the test cleanly when its deps are missing."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        pytest.skip(f"{module} unavailable: {exc}")


def fake_extract_los(lecture_md: str, factsheet_subset: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic learning-objective extraction for the smoke fixture."""
    return {
        "learning_objectives": [
            {"title": "Supply & Demand", "page_range": [2, 2]},
        ],
        "ignored_pages": [
            {"page_number": 1, "reason": "title page"},
            {"page_number": 3, "reason": "sources/references-only"},
        ],
        "language": "en",
    }


def fake_generate_mcqs(slides_batch: list[dict[str, Any]]) -> dict[str, Any]:
    """Return one deterministic multi-correct MCQ for each slide in the smoke fixture."""
    by_slide = []
    for slide in slides_batch:
        page = slide["page_number"]
        by_slide.append(
            {
                "page_number": page,
                "mcqs": [
                    {
                        "question": f"Test question for page {page}?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_indices": [0, 2],
                        "rationales_per_option": [
                            "A is correct because ...",
                            "B is wrong because ...",
                            "C is correct because ...",
                            "D is wrong because ...",
                        ],
                        "source_page": page,
                        "language": "en",
                    }
                ],
            }
        )
    return {"by_slide": by_slide}


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


def test_ingestion_end_to_end_against_fresh_sqlite(tmp_path, monkeypatch) -> None:
    """Phase 1 smoke: PDF -> DB end-to-end with fake Claude callers."""
    _try_import("pdfplumber")  # pdf_to_md_v3 dep
    _try_import("app.brain.ingestion.pdf_to_md_v3")

    # Point the DB at tmp BEFORE importing query modules / the orchestrator,
    # so every queries_*/__init__ binds to the fresh tmp connection.
    db_file = tmp_path / "user.sqlite"
    import app.db.connection as conn
    conn.DB.close()
    conn.DB_FILE = db_file
    conn.DB = conn.connect(db_file)
    for m in [
        "app.db.queries_users",
        "app.db.queries_classes",
        "app.db.queries_lectures",
        "app.db.queries_pages",
        "app.db.queries_questions",
        "app.db.queries_learning_objectives",
        "app.class_.lecture_ingest.lecture_ingest",
        "app.class_.lecture_ingest",
    ]:
        importlib.reload(importlib.import_module(m))

    from app.class_.lecture_ingest import ingest_lecture, lecture_ingest
    from app.db.queries_classes import insert_class
    from app.db.queries_learning_objectives import list_learning_objectives_for_lecture
    from app.db.queries_lectures import get_lecture_by_id
    from app.db.queries_questions import list_questions_for_lecture
    from app.db.queries_users import insert_user

    def fake_generate_mcqs_with_question_type(slides_batch):
        response = fake_generate_mcqs(slides_batch)
        for entry in response["by_slide"]:
            for mcq in entry["mcqs"]:
                mcq["question_type"] = "application"
        return response

    uid = insert_user("alice", "sk-test")
    cid = insert_class(uid, "BWL", {
        "surf_extraction_notes": "Intro economics class.",
        "FSLO": ["Understand supply and demand."],
        "core_course_content": {
            "narrative_summary": "An intro to micro.",
            "main_topics": ["supply", "demand"],
            "important_concepts_models_methods": [],
            "skills_students_are_expected_to_develop": [],
        },
        "assessment_and_grading": {"exam_relevant_content": []},
    })
    sample_pdf = pathlib.Path("assets/sample_lectures/sample_lecture.pdf")
    assert sample_pdf.exists(), f"missing {sample_pdf} (Phase 1 smoke fixture)"
    monkeypatch.setattr(
        lecture_ingest,
        "extract_with_tables",
        lambda _path: (
            "--- PAGE 1 ---\nCourse intro agenda and overview.\n\n"
            "--- PAGE 2 ---\n"
            + "Supply and demand curves shift equilibrium prices and quantities. " * 12
            + "\n\n--- PAGE 3 ---\nSource list and references.",
            0,
            800,
        ),
    )

    lecture_id = ingest_lecture(
        class_id=cid,
        pdf_path=sample_pdf,
        title="Sample lecture",
        claude_call_lo=fake_extract_los,
        claude_call_mcq=fake_generate_mcqs_with_question_type,
    )

    lecture = get_lecture_by_id(lecture_id)
    assert lecture is not None
    assert lecture["status"] == "ready", lecture
    los = list_learning_objectives_for_lecture(lecture_id)
    assert len(los) == 1, los
    qs = list_questions_for_lecture(lecture_id)
    assert len(qs) >= 1, qs
    # multi-correct support survives the round-trip (D-2.5)
    # Plan 02-03 (FND-05): query helpers return list[dict]; index with [0]["..."].
    import json as _json
    assert _json.loads(qs[0]["correct_indices"]) == [0, 2]

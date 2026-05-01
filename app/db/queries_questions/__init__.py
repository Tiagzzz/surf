"""Surf — questions query wrappers."""
from __future__ import annotations

import json

import pandas as pd

from app.db.connection import DB


def insert_question(
    slide_page_id: int,
    question_text: str,
    options: list[str],
    correct_indices: list[int],
    rationales_per_option: list[str],
    source_page: int,
    language: str,
    difficulty_word_count: int | None = None,
    difficulty_readability: float | None = None,
    difficulty_distractor_similarity: float | None = None,
) -> int:
    """Insert one MCQ. Phase 4 ML difficulty fields stay NULL — do not pass them yet."""
    with DB:
        cur = DB.execute(
            "INSERT INTO questions ("
            "slide_page_id, question_text, options_json, correct_indices, "
            "rationales_per_option_json, source_page, language, "
            "difficulty_word_count, difficulty_readability, difficulty_distractor_similarity"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                slide_page_id,
                question_text,
                json.dumps(options),
                json.dumps(correct_indices),
                json.dumps(rationales_per_option),
                source_page,
                language,
                difficulty_word_count,
                difficulty_readability,
                difficulty_distractor_similarity,
            ),
        )
        return cur.lastrowid


def list_questions_for_slide_page(slide_page_id: int) -> "pd.DataFrame":
    return pd.read_sql(
        "SELECT * FROM questions WHERE slide_page_id = ? ORDER BY id",
        DB,
        params=(slide_page_id,),
    )


def list_questions_for_lecture(lecture_id: int) -> "pd.DataFrame":
    return pd.read_sql(
        "SELECT q.* FROM questions q "
        "JOIN slide_pages sp ON q.slide_page_id = sp.id "
        "WHERE sp.lecture_id = ? ORDER BY q.id",
        DB,
        params=(lecture_id,),
    )

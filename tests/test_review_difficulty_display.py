"""Tests for the Phase 7 P5 review-card personal-difficulty display."""
from __future__ import annotations

import inspect
import json
from unittest.mock import patch

import app.mock_review.results_render as results_render
from app.mock_review.results_render import (
    _difficulty_flag_tier,
    _difficulty_score_map_for_review,
    _example_view_from_review_row,
    _review_card_header_html,
    _scoring_view_from_review_row,
)


def _make_review_row(qid: int, *, question_type: str = "analysis") -> dict:
    return {
        "question_id": qid,
        "question_text": f"Stem {qid}",
        "options_json": json.dumps(["a", "b", "c", "d"]),
        "rationales_per_option_json": json.dumps(["r0", "r1", "r2", "r3"]),
        "correct_indices": json.dumps([1, 3]),
        "selected_indices": json.dumps([1, 3]),
        "was_skipped": 0,
        "is_correct": 1,
        "question_type": question_type,
        "learning_objective_title": "LO",
        "source_page": 1,
        "language": "en",
        "difficulty_word_count": 42,
        "difficulty_readability": 0.62,
        "difficulty_distractor_similarity": 5.0,
        "difficulty_conceptual_density": 4,
        "difficulty_distractor_derivation": 3,
        "difficulty_reasoning_steps": 2,
        "difficulty_wording_complexity": 4,
        "difficulty_wording_clarity_issue": 1,
    }


# -- 07-04-01: scoring map ---------------------------------------------------


def test_review_page_recalculates_difficulty_score_on_render():
    rows = [_make_review_row(qid=10), _make_review_row(qid=20)]
    calls: list = []

    def fake_examples(class_id):
        calls.append(("examples", class_id))
        return []

    class _Result:
        def __init__(self, score):
            self.score = score
            self.source = "rule"
            self.note = ""

    def fake_score(questions, examples=None):
        calls.append(("score", len(questions), len(examples or [])))
        return [_Result(s) for s in (72, 88)]

    score_map = _difficulty_score_map_for_review(
        class_id=5,
        review_rows=rows,
        examples_fn=fake_examples,
        score_questions_fn=fake_score,
    )
    assert score_map == {10: 72, 20: 88}
    # Both functions were called exactly once during this render path.
    assert ("examples", 5) in calls
    assert any(c[0] == "score" for c in calls)


def test_review_scoring_view_decodes_metadata_contract():
    row = _make_review_row(qid=10, question_type="evaluation")

    view = _scoring_view_from_review_row(row)

    assert view["id"] == 10
    assert view["question_id"] == 10
    assert view["stem"] == "Stem 10"
    assert view["question_text"] == "Stem 10"
    assert view["options"] == ["a", "b", "c", "d"]
    assert view["correct_indices"] == [1, 3]
    assert view["question_type"] == "evaluation"
    assert view["lo_title"] == "LO"
    assert view["difficulty_word_count"] == 42
    assert view["difficulty_readability"] == 0.62
    assert view["difficulty_distractor_similarity"] == 5.0
    assert view["difficulty_conceptual_density"] == 4
    assert view["difficulty_distractor_derivation"] == 3
    assert view["difficulty_reasoning_steps"] == 2
    assert view["difficulty_wording_complexity"] == 4
    assert view["difficulty_wording_clarity_issue"] == 1


def test_review_score_map_passes_metadata_rich_inputs_to_scorer():
    rows = [_make_review_row(qid=10)]
    examples = [_make_review_row(qid=10)]
    examples[0]["is_correct"] = 0
    examples[0]["was_skipped"] = 1
    captured: dict = {}

    class _Result:
        def __init__(self, score):
            self.score = score

    def fake_score(questions, examples=None):
        captured["questions"] = questions
        captured["examples"] = examples
        return [_Result(64)]

    score_map = _difficulty_score_map_for_review(
        class_id=5,
        review_rows=rows,
        examples_fn=lambda class_id: examples,
        score_questions_fn=fake_score,
    )

    assert score_map == {10: 64}
    assert captured["questions"] == [_scoring_view_from_review_row(rows[0])]
    assert captured["examples"] == [_example_view_from_review_row(examples[0])]
    assert captured["examples"][0]["is_skipped"] is True
    assert captured["examples"][0]["is_correct"] is False


def test_review_page_does_not_store_difficulty_snapshot():
    src = inspect.getsource(results_render)
    # No write SQL anywhere in the renderer.
    upper = src.upper()
    for keyword in (
        "UPDATE ATTEMPTS",
        "UPDATE ATTEMPT_ANSWERS",
        "INSERT INTO ATTEMPTS",
        "INSERT INTO ATTEMPT_ANSWERS",
        "ALTER TABLE",
        "CREATE TABLE",
    ):
        assert keyword not in upper, f"P5 renderer must not run {keyword!r}"


def test_review_page_falls_back_to_empty_map_when_class_id_is_missing():
    rows = [_make_review_row(qid=10)]
    score_map = _difficulty_score_map_for_review(
        class_id=None,
        review_rows=rows,
        examples_fn=lambda class_id: [],
        score_questions_fn=lambda q, examples=None: [],
    )
    assert score_map == {}


def test_review_page_handles_scorer_failure_safely():
    def boom_scorer(questions, examples=None):
        raise RuntimeError("scoring is broken")

    rows = [_make_review_row(qid=10)]
    score_map = _difficulty_score_map_for_review(
        class_id=5,
        review_rows=rows,
        examples_fn=lambda class_id: [],
        score_questions_fn=boom_scorer,
    )
    assert score_map == {}


# -- 07-04-02: badge rendering -----------------------------------------------


def test_review_card_header_renders_difficulty_flag():
    html = _review_card_header_html(
        stamp="CORRECT",
        objective="LO title",
        type_label="Analysis",
        question="What is this?",
        difficulty_score=78,
    )
    # Flag container + tier modifier + stacked label + score number.
    assert "surf-personal-difficulty-flag" in html
    assert "surf-personal-difficulty-flag--risk" in html
    assert "DIFFICULTY" in html and "FOR YOU" in html
    assert "surf-personal-difficulty-flag-score" in html
    assert ">78<" in html
    # Aria label preserves the screen-reader copy.
    assert 'aria-label="Difficulty for you: 78/100"' in html
    # Existing question-type chip still rendered.
    assert "surf-question-type-chip" in html
    assert "Analysis" in html


def test_review_card_header_omits_flag_when_score_missing():
    html = _review_card_header_html(
        stamp="CORRECT",
        objective="LO",
        type_label="Analysis",
        question="Q",
        difficulty_score=None,
    )
    assert "surf-personal-difficulty-flag" not in html
    assert "DIFFICULTY" not in html


def test_review_card_header_clamps_out_of_range_scores():
    too_high = _review_card_header_html(
        stamp="CORRECT",
        objective="LO",
        type_label="Analysis",
        question="Q",
        difficulty_score=999,
    )
    too_low = _review_card_header_html(
        stamp="CORRECT",
        objective="LO",
        type_label="Analysis",
        question="Q",
        difficulty_score=-5,
    )
    # Out-of-range values are silently dropped rather than rendered as
    # nonsense — the renderer never lies.
    assert "surf-personal-difficulty-flag" not in too_high
    assert "surf-personal-difficulty-flag" not in too_low


def test_review_difficulty_flag_escapes_surrounding_dynamic_values():
    # The score is only ever an int after clamp; the surrounding dynamic
    # values must still be html-escaped to satisfy the no-injection
    # contract.
    html = _review_card_header_html(
        stamp="CORRECT",
        objective="<script>alert(1)</script>",
        type_label="<b>x</b>",
        question="<x>",
        difficulty_score=42,
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<b>" not in html.split("surf-question-type-chip")[1].split("</div>")[0]


def test_review_card_header_has_score_in_range():
    for score in (0, 1, 50, 99, 100):
        html = _review_card_header_html(
            stamp="CORRECT",
            objective="LO",
            type_label="Analysis",
            question="Q",
            difficulty_score=score,
        )
        assert "surf-personal-difficulty-flag" in html
        assert f">{score}<" in html


def test_difficulty_flag_tier_thresholds():
    # Boundaries: <33 → ok, 33..66 → warn, >66 → risk.
    assert _difficulty_flag_tier(0) == "ok"
    assert _difficulty_flag_tier(32) == "ok"
    assert _difficulty_flag_tier(33) == "warn"
    assert _difficulty_flag_tier(50) == "warn"
    assert _difficulty_flag_tier(66) == "warn"
    assert _difficulty_flag_tier(67) == "risk"
    assert _difficulty_flag_tier(100) == "risk"


def test_review_card_header_picks_tier_class_per_score():
    samples = [
        (12, "ok"),
        (32, "ok"),
        (33, "warn"),
        (50, "warn"),
        (66, "warn"),
        (67, "risk"),
        (95, "risk"),
    ]
    for score, expected_tier in samples:
        html = _review_card_header_html(
            stamp="CORRECT",
            objective="LO",
            type_label="Analysis",
            question="Q",
            difficulty_score=score,
        )
        assert f"surf-personal-difficulty-flag--{expected_tier}" in html, (
            f"score {score} expected tier {expected_tier}"
        )
        # Only the chosen tier modifier should be present.
        other_tiers = {"ok", "warn", "risk"} - {expected_tier}
        for tier in other_tiers:
            assert f"surf-personal-difficulty-flag--{tier}" not in html


# -- 07-04-03: structural contract -------------------------------------------


def test_review_renderer_imports_personal_difficulty_score_function():
    src = inspect.getsource(results_render)
    assert "from app.ml.personal_difficulty import score_questions" in src
    assert "list_personal_difficulty_examples_for_class" in src


def test_review_renderer_uses_score_map_for_render_row():
    src = inspect.getsource(results_render.render_review_mock_page)
    assert "_difficulty_score_map_for_review" in src
    assert "difficulty_score" in src


def test_review_page_has_difficulty_score_explainer_before_cards():
    src = inspect.getsource(results_render)
    render_src = inspect.getsource(results_render.render_review_mock_page)

    assert "Understand your difficulty score" in src
    assert "Your difficulty score tells you how hard a question really is" in src
    assert "Nailing a 75" in src
    assert ".st-key-p5_difficulty_score_explainer button" in src
    assert "_render_difficulty_score_explainer" in src

    explainer_idx = render_src.index("_render_difficulty_score_explainer()")
    first_row_idx = render_src.index("for row in review_rows:")
    assert explainer_idx < first_row_idx


def test_review_difficulty_explainer_does_not_call_scoring_or_db():
    helper = inspect.getsource(results_render._render_difficulty_score_explainer)

    assert "_DIFFICULTY_EXPLAINER_OPEN_KEY" in helper
    assert "_DIFFICULTY_EXPLAINER_BODY" in helper
    assert "p5_difficulty_score_explainer_action" in helper
    assert "score_questions" not in helper
    assert "list_personal_difficulty_examples_for_class" not in helper
    assert "get_attempt_review_rows" not in helper


def test_review_renderer_does_not_freeze_score_to_attempt_answers():
    src = inspect.getsource(results_render)
    # No score-snapshot field name appears.
    assert "frozen_difficulty" not in src
    assert "difficulty_snapshot" not in src
    # And no UPDATE/INSERT on attempt_answers from this module.
    assert "INSERT INTO attempt_answers" not in src
    assert "UPDATE attempt_answers" not in src


def test_difficulty_flag_css_classes_present():
    src = inspect.getsource(results_render)
    # Base class.
    assert ".surf-personal-difficulty-flag" in src
    # All three tier modifiers exist.
    for tier in ("ok", "warn", "risk"):
        assert f".surf-personal-difficulty-flag--{tier}" in src
    # Color tokens match the design system, including the warm-yellow
    # paper5 text rule for the medium tier.
    assert "--surf-status-ok" in src
    assert "--surf-status-warn" in src
    assert "--surf-accent-deep" in src
    # V-notch via clip-path.
    assert "clip-path" in src
    # The review row anchors the flag with position: relative.
    assert "position: relative" in src


def test_render_review_row_renders_flag(monkeypatch):
    captured: dict = {}

    def fake_html(content):
        captured.setdefault("html", []).append(content)

    class _Container:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    def fake_container(*args, **kwargs):
        return _Container()

    with patch.object(results_render.st, "html", fake_html), \
         patch.object(results_render.st, "container", fake_container):
        results_render._render_review_row(
            _make_review_row(qid=10),
            difficulty_score=84,
        )
    rendered = "".join(captured.get("html", []))
    assert "surf-personal-difficulty-flag" in rendered
    assert "surf-personal-difficulty-flag--risk" in rendered
    assert ">84<" in rendered
    assert 'aria-label="Difficulty for you: 84/100"' in rendered

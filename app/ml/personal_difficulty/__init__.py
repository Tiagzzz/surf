"""Personal difficulty / wrong-answer-risk scoring for Surf Phase 7.

This package is intentionally pure-Python and side-effect free. It must not
import Streamlit, the Claude client, NotebookLM helpers, the live SQLite
connection, or any network client. Callers from `app/db/queries_*` and
`app/class_/custom_mock_selection/` pass plain question rows and completed
answer-example dicts in; this module returns a score per question along with
a transparent `source` field (`"rule"` or `"ml"`).

Rule scoring is the honest default. Local scikit-learn scoring only influences
the result once the student has enough completed answers with both correct and
wrong labels (see ``can_train_personal_model``) and the validation quality is
credible. When fitting, evaluation, or prediction fails for any reason, callers
receive rule scores instead.
"""
# Pure scoring core for Phase 7 personal difficulty.
from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This module deliberately keeps its imports tiny. It must stay pure Python
# with no Streamlit, no DB connection, no Anthropic client, and no network
# call. scikit-learn is imported lazily inside the model helpers so this file
# can still be imported in environments that do not have it installed.
#
# Important code pieces:
# - `collections.abc` (`Iterable`, `Mapping`, `Sequence`): generic container
#   types used for read-only function arguments — they say "I will iterate /
#   look up keys / read by index" without forcing a concrete `list`/`dict`.
# - `dataclasses.dataclass`: decorator used below to build the small frozen
#   `ScoreResult` record.
# - `typing.Any`: a type hint meaning "any value is allowed".
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# --------------------------------------------------------------------------- #
# READINESS THRESHOLDS AND ML CAPS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Phase 7's "honest ML" promise is enforced here. The rule branch always runs
# first; the optional ML blend is only allowed to influence the score once
# the student has enough completed answers spread across both correct AND
# wrong/skipped outcomes, and only when the trained tree clears a quality
# bar. These four numbers encode that contract so a single read of this
# block makes the gate obvious.
#
# Important code pieces:
# - `MIN_EXAMPLES_FOR_ML`: total completed answers required before any ML
#   path is even considered.
# - `MIN_EXAMPLES_PER_CLASS`: minimum count in each of the two outcome
#   classes (correct vs wrong/skipped) so the model is not all-one-class.
# - `MODEL_RANDOM_STATE`: fixed seed so the small tree is reproducible
#   between sessions.
# - `MAX_ML_RELIABILITY`: hard ceiling on how much the ML branch is allowed
#   to influence the final blended score.
#
# App connection:
# These thresholds are why a brand-new student or a class with no wrong
# answers still gets a transparent rule-based score on P5 difficulty flags
# rather than a fake ML number.

# Minimum total completed answer examples before the ML branch can run.
MIN_EXAMPLES_FOR_ML: int = 30
# Minimum examples in each target class (correct vs wrong/skipped).
MIN_EXAMPLES_PER_CLASS: int = 5
MODEL_RANDOM_STATE: int = 7
MAX_ML_RELIABILITY: float = 0.85

# --------------------------------------------------------------------------- #
# RULE-BASED RISK CONSTANTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# These tables convert a question's metadata into a 0..1 "risk" number that
# the rule formula then combines and scales to the locked 0..100 range. Each
# constant maps one input dimension (cognitive type, weighted feature,
# difficulty metadata field) to a numeric contribution.
#
# Important code pieces:
# - `QUESTION_TYPE_RISK`: per question_type slug risk weight. Knowledge
#   sits at the gentle end (0.00) and Evaluation at the hard end (1.00).
# - `RULE_WEIGHTS`: how much each metadata signal contributes to the final
#   weighted sum. Weights add to 1.0 so the scaled score lands in 0..100.
# - `DIFFICULTY_METADATA_KEYS`: pairs the rule-formula risk name with the
#   exact stored difficulty_* field name on a question row.
# - `STRUCTURED_FEATURE_NAMES`: ordered list of feature columns the
#   scikit-learn tree expects when fitting or predicting.
# - `FALLBACK_LONG_TEXT_BASELINE` and `FALLBACK_LONG_TEXT_SPAN`: numbers
#   used when difficulty metadata is missing so the fallback rule path can
#   still produce an honest score from the question's stem length.
#
# Research-calibrated Phase 7.1 rule formula. Values are normalized to 0..1
# before the weighted sum is scaled to Surf's 0..100 wrong-risk range.
QUESTION_TYPE_RISK: dict[str, float] = {
    "knowledge": 0.00,
    "comprehension": 0.20,
    "application": 0.45,
    "analysis": 0.70,
    "synthesis": 0.90,
    "evaluation": 1.00,
}
RULE_WEIGHTS: dict[str, float] = {
    "distractor_similarity": 0.24,
    "distractor_derivation": 0.20,
    "reasoning_steps": 0.18,
    "conceptual_density": 0.14,
    "wording_complexity": 0.08,
    "question_type": 0.08,
    "multi_correct": 0.08,
}
DIFFICULTY_METADATA_KEYS: tuple[tuple[str, str], ...] = (
    ("distractor_similarity", "difficulty_distractor_similarity"),
    ("distractor_derivation", "difficulty_distractor_derivation"),
    ("reasoning_steps", "difficulty_reasoning_steps"),
    ("conceptual_density", "difficulty_conceptual_density"),
    ("wording_complexity", "difficulty_wording_complexity"),
)
STRUCTURED_FEATURE_NAMES: tuple[str, ...] = (
    "distractor_similarity",
    "conceptual_density",
    "distractor_derivation",
    "reasoning_steps",
    "wording_complexity",
    "wording_clarity_issue",
    "question_type_risk",
    "correct_index_count",
    "multi_correct_risk",
    "word_count_risk",
    "readability",
)
FALLBACK_LONG_TEXT_BASELINE: int = 80
FALLBACK_LONG_TEXT_SPAN: int = 320


# --------------------------------------------------------------------------- #
# SCORE RESULT RECORD
# --------------------------------------------------------------------------- #
# Simple explanation:
# Each scored question returns one small immutable record. The `source` field
# is what callers display when explaining the score: `"rule"` for the honest
# default and `"ml"` only when the ML reliability path actually engaged.
#
# Key detail:
# - `@dataclass(frozen=True)`: decorator that turns a class into a small
#   value object whose fields cannot be reassigned after creation.
@dataclass(frozen=True)
class ScoreResult:
    """Result of scoring a single question."""

    score: int
    source: str  # "rule" or "ml"
    note: str = ""


def clamp_score(value: float | int) -> int:
    """Clamp a numeric score to the integer range 0..100."""
    if value is None:
        return 0
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return 0
    if as_float < 0:
        return 0
    if as_float > 100:
        return 100
    return int(round(as_float))


def normalize_1_to_5(value: object) -> float | None:
    """Normalize an integer-like 1..5 metadata value to 0.00..1.00."""
    if isinstance(value, bool):
        return None
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None
    if numeric < 1 or numeric > 5:
        return None
    return (numeric - 1) / 4


def difficulty_band(score: float | int) -> str:
    """Return the locked Phase 7.1 band label for a 0..100 score."""
    bounded = clamp_score(score)
    if bounded <= 32:
        return "easy"
    if bounded <= 66:
        return "medium"
    return "difficult"


def _read_str(mapping: Mapping[str, Any] | None, key: str) -> str:
    if not mapping:
        return ""
    value = mapping.get(key)
    return "" if value is None else str(value)


def _question_text_length(question: Mapping[str, Any] | None) -> int:
    text = _read_str(question, "stem") or _read_str(question, "question_text")
    return len(text)


def _correct_index_count(question: Mapping[str, Any] | None) -> int:
    if not question:
        return 0
    correct = question.get("correct_indices")
    if isinstance(correct, (list, tuple, set)):
        return len(set(correct))
    return 0


def _as_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _question_type_risk(question: Mapping[str, Any] | None) -> float:
    qt = _read_str(question, "question_type").strip().lower()
    return QUESTION_TYPE_RISK.get(qt, 0.45)


def multi_correct_risk(correct_indices: object) -> float:
    """Return risk contribution from the number of unique correct options."""
    if not isinstance(correct_indices, (list, tuple, set)):
        return 0.0
    count = len(set(correct_indices))
    if count <= 1:
        return 0.0
    if count == 2:
        return 0.55
    if count == 3:
        return 0.80
    return 1.00


def _long_text_risk(question: Mapping[str, Any] | None) -> float:
    length = _question_text_length(question)
    normalized = (length - FALLBACK_LONG_TEXT_BASELINE) / FALLBACK_LONG_TEXT_SPAN
    return min(max(normalized, 0.0), 1.0)


def _word_count(question: Mapping[str, Any] | None) -> int:
    explicit = None if not question else _as_float(question.get("difficulty_word_count"))
    if explicit is not None and explicit >= 0:
        return int(round(explicit))
    text = _read_str(question, "stem") or _read_str(question, "question_text")
    words = [part for part in text.split() if part.strip()]
    if words:
        return len(words)
    return max(_question_text_length(question) // 6, 0)


def _word_count_risk(question: Mapping[str, Any] | None) -> float:
    return _clamp01(_word_count(question) / 200)


def _readability_feature(question: Mapping[str, Any] | None) -> float:
    value = None if not question else _as_float(question.get("difficulty_readability"))
    if value is None:
        return 0.5
    if value > 1:
        return _clamp01(value / 100)
    return _clamp01(value)


def _bool_feature(value: object) -> float:
    if isinstance(value, str):
        return 1.0 if value.strip().lower() in {"1", "true", "yes", "y"} else 0.0
    return 1.0 if bool(value) else 0.0


def _metadata_risks(question: Mapping[str, Any]) -> dict[str, float] | None:
    risks: dict[str, float] = {}
    for risk_key, question_key in DIFFICULTY_METADATA_KEYS:
        normalized = normalize_1_to_5(question.get(question_key))
        if normalized is None:
            return None
        risks[risk_key] = normalized
    return risks


def _metadata_feature(question: Mapping[str, Any] | None, key: str) -> float:
    if not isinstance(question, Mapping):
        return 0.5
    normalized = normalize_1_to_5(question.get(key))
    return 0.5 if normalized is None else normalized


def structured_feature_row(row: Mapping[str, Any] | None) -> dict[str, float]:
    """Build the structured metadata feature row used by the tree model."""
    correct_count = _correct_index_count(row)
    return {
        "distractor_similarity": _metadata_feature(
            row,
            "difficulty_distractor_similarity",
        ),
        "conceptual_density": _metadata_feature(row, "difficulty_conceptual_density"),
        "distractor_derivation": _metadata_feature(
            row,
            "difficulty_distractor_derivation",
        ),
        "reasoning_steps": _metadata_feature(row, "difficulty_reasoning_steps"),
        "wording_complexity": _metadata_feature(row, "difficulty_wording_complexity"),
        "wording_clarity_issue": _bool_feature(
            None if not row else row.get("difficulty_wording_clarity_issue")
        ),
        "question_type_risk": _question_type_risk(row),
        "correct_index_count": float(correct_count),
        "multi_correct_risk": multi_correct_risk(
            None if not row else row.get("correct_indices")
        ),
        "word_count_risk": _word_count_risk(row),
        "readability": _readability_feature(row),
    }


def _structured_feature_values(row: Mapping[str, Any] | None) -> list[float]:
    features = structured_feature_row(row)
    return [features[name] for name in STRUCTURED_FEATURE_NAMES]


def _rule_score_without_history(question: Mapping[str, Any]) -> tuple[int, str]:
    metadata = _metadata_risks(question)
    question_type_z = _question_type_risk(question)
    multi_correct_z = multi_correct_risk(question.get("correct_indices"))
    if metadata is None:
        fallback_score = 100 * (
            0.45 * question_type_z
            + 0.30 * multi_correct_z
            + 0.25 * _long_text_risk(question)
        )
        return clamp_score(fallback_score), "missing_difficulty_metadata"

    rule_score = 100 * (
        RULE_WEIGHTS["distractor_similarity"] * metadata["distractor_similarity"]
        + RULE_WEIGHTS["distractor_derivation"] * metadata["distractor_derivation"]
        + RULE_WEIGHTS["reasoning_steps"] * metadata["reasoning_steps"]
        + RULE_WEIGHTS["conceptual_density"] * metadata["conceptual_density"]
        + RULE_WEIGHTS["wording_complexity"] * metadata["wording_complexity"]
        + RULE_WEIGHTS["question_type"] * question_type_z
        + RULE_WEIGHTS["multi_correct"] * multi_correct_z
    )
    return clamp_score(rule_score), ""


def history_adjusted_score(
    rule_score: float | int,
    correct_count: int,
    wrong_or_skipped_count: int,
    prior_strength: int = 4,
) -> int:
    """Bayesian exact-question history update for a rule score."""
    correct = max(int(correct_count or 0), 0)
    wrong_or_skipped = max(int(wrong_or_skipped_count or 0), 0)
    prior = max(int(prior_strength or 0), 0)
    total_attempts = correct + wrong_or_skipped
    if prior + total_attempts == 0:
        return clamp_score(rule_score)
    adjusted = (
        prior * clamp_score(rule_score)
        + 100 * wrong_or_skipped
    ) / (prior + total_attempts)
    return clamp_score(adjusted)


def _history_counts(history: Sequence[Mapping[str, Any]] | None) -> tuple[int, int]:
    correct = 0
    wrong_or_skipped = 0
    if not history:
        return correct, wrong_or_skipped
    for entry in history:
        target = _target_from_example(entry)
        if target == 1:
            wrong_or_skipped += 1
        elif target == 0:
            correct += 1
    return correct, wrong_or_skipped


def _append_note(existing: str, addition: str) -> str:
    if not existing:
        return addition
    if addition in existing.split(";"):
        return existing
    return f"{existing};{addition}"


# --------------------------------------------------------------------------- #
# RULE-BASED SCORING — `score_rule_based`
# --------------------------------------------------------------------------- #
# Simple explanation:
# The honest default Phase 7 path. Reads the question's locked metadata,
# turns each piece into a 0..1 risk, weights them per `RULE_WEIGHTS`, scales
# to 0..100, and then nudges the result up or down by the user's history on
# that exact question. Missing or malformed inputs return a safe 0 with an
# explanatory note instead of crashing.
#
# App connection:
# This is the function that produces the difficulty number shown on the P5
# review card flag when ML is not engaged.
def score_rule_based(
    question: Mapping[str, Any] | None,
    history: Sequence[Mapping[str, Any]] | None = None,
) -> ScoreResult:
    """Deterministic rule-based personal difficulty for a question.

    `question_type` is read as a feature but never modified. Missing or
    malformed inputs return a safe minimum score rather than raising.
    """
    if not isinstance(question, Mapping):
        return ScoreResult(score=0, source="rule", note="missing_question")

    score, note = _rule_score_without_history(question)
    correct, wrong_or_skipped = _history_counts(history)
    if correct or wrong_or_skipped:
        score = history_adjusted_score(score, correct, wrong_or_skipped)
        note = _append_note(note, "history_adjusted")

    return ScoreResult(score=score, source="rule", note=note)


def _target_from_example(example: Mapping[str, Any] | None) -> int | None:
    """Return 1 for wrong/skipped answers and 0 for correct answers."""
    if not isinstance(example, Mapping):
        return None
    if example.get("is_skipped"):
        return 1
    correctness = example.get("is_correct")
    if correctness is None:
        return None
    return 0 if bool(correctness) else 1


def can_train_personal_model(examples: Iterable[Mapping[str, Any]] | None) -> bool:
    """Return True only when enough two-class completed answers exist."""
    if not examples:
        return False
    correct = 0
    wrong = 0
    total = 0
    for example in examples:
        target = _target_from_example(example)
        if target is None:
            continue
        total += 1
        if target == 0:
            correct += 1
        else:
            wrong += 1
    if total < MIN_EXAMPLES_FOR_ML:
        return False
    return correct >= MIN_EXAMPLES_PER_CLASS and wrong >= MIN_EXAMPLES_PER_CLASS


def _training_matrix(
    examples: Sequence[Mapping[str, Any]] | None,
) -> tuple[list[list[float]], list[int]]:
    features: list[list[float]] = []
    labels: list[int] = []
    for example in examples or []:
        target = _target_from_example(example)
        if target is None:
            continue
        features.append(_structured_feature_values(example))
        labels.append(target)
    return features, labels


def _label_counts(labels: Sequence[int]) -> tuple[int, int]:
    return labels.count(0), labels.count(1)


def _can_train_from_labels(labels: Sequence[int]) -> bool:
    correct, wrong = _label_counts(labels)
    return (
        len(labels) >= MIN_EXAMPLES_FOR_ML
        and correct >= MIN_EXAMPLES_PER_CLASS
        and wrong >= MIN_EXAMPLES_PER_CLASS
    )


def _new_tree_model():
    from sklearn.tree import DecisionTreeClassifier

    return DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=MODEL_RANDOM_STATE,
    )


def fit_personal_model(examples: Sequence[Mapping[str, Any]]):
    """Fit an in-memory shallow tree from completed answer metadata."""
    features, labels = _training_matrix(examples)
    if not _can_train_from_labels(labels):
        return None

    try:
        model = _new_tree_model()
        model.fit(features, labels)
    except Exception:
        return None
    return model


def _empty_metrics(total: int = 0, correct: int = 0, wrong: int = 0) -> dict[str, Any]:
    return {
        "balanced_accuracy": 0.0,
        "accuracy": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "confusion_matrix": [[0, 0], [0, 0]],
        "total_examples": total,
        "correct_examples": correct,
        "wrong_examples": wrong,
        "evaluation_scope": "unavailable",
    }


def evaluate_personal_model(examples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return standard classification metrics for the structured tree path."""
    features, labels = _training_matrix(examples)
    correct, wrong = _label_counts(labels)
    if not _can_train_from_labels(labels):
        return _empty_metrics(len(labels), correct, wrong)

    try:
        from sklearn.metrics import (
            accuracy_score,
            balanced_accuracy_score,
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
        )
        from sklearn.model_selection import train_test_split

        if len(labels) >= 60:
            x_train, x_eval, y_train, y_eval = train_test_split(
                features,
                labels,
                test_size=0.25,
                random_state=MODEL_RANDOM_STATE,
                stratify=labels,
            )
            scope = "validation"
        else:
            x_train = x_eval = features
            y_train = y_eval = labels
            scope = "training"

        model = _new_tree_model()
        model.fit(x_train, y_train)
        predictions = model.predict(x_eval)
        return {
            "balanced_accuracy": float(balanced_accuracy_score(y_eval, predictions)),
            "accuracy": float(accuracy_score(y_eval, predictions)),
            "precision": float(precision_score(y_eval, predictions, zero_division=0)),
            "recall": float(recall_score(y_eval, predictions, zero_division=0)),
            "f1": float(f1_score(y_eval, predictions, zero_division=0)),
            "confusion_matrix": confusion_matrix(
                y_eval,
                predictions,
                labels=[0, 1],
            ).tolist(),
            "total_examples": len(labels),
            "correct_examples": correct,
            "wrong_examples": wrong,
            "evaluation_scope": scope,
        }
    except Exception:
        return _empty_metrics(len(labels), correct, wrong)


def ml_reliability(
    total: int,
    correct: int,
    wrong: int,
    balanced_accuracy: float | int | None,
) -> float:
    """Progressively weight ML influence from data volume, balance, and quality."""
    try:
        total_i = int(total)
        correct_i = int(correct)
        wrong_i = int(wrong)
        balanced_accuracy_f = float(balanced_accuracy)
    except (TypeError, ValueError):
        return 0.0

    if (
        total_i < MIN_EXAMPLES_FOR_ML
        or correct_i < MIN_EXAMPLES_PER_CLASS
        or wrong_i < MIN_EXAMPLES_PER_CLASS
    ):
        return 0.0
    if balanced_accuracy_f <= 0.55:
        return 0.0

    quality = _clamp01((balanced_accuracy_f - 0.55) / 0.25)
    balance = min(correct_i, wrong_i) / max(correct_i, wrong_i)
    if total_i < 60:
        volume = 0.10 + ((total_i - MIN_EXAMPLES_FOR_ML) / 30) * 0.15
    else:
        volume = 0.25 + min((total_i - 60) / 90, 1.0) * 0.60
    return min(MAX_ML_RELIABILITY, round(volume * quality * balance, 4))


def _predict_probabilities(model, features: Sequence[Sequence[float]]) -> list[float] | None:
    try:
        probabilities = model.predict_proba(features)
    except Exception:
        return None
    # The model is trained with labels 0 (correct) and 1 (wrong/skipped).
    # We want the wrong-risk probability — column matching class label 1.
    try:
        classes = list(getattr(model, "classes_", []))
        if 1 in classes:
            wrong_index = classes.index(1)
        else:
            wrong_index = -1
    except Exception:
        wrong_index = -1
    try:
        return [float(row[wrong_index]) for row in probabilities]
    except Exception:
        return None


def _question_identity(row: Mapping[str, Any] | None) -> Any:
    if not isinstance(row, Mapping):
        return None
    question_id = row.get("question_id")
    if question_id is not None:
        return question_id
    return row.get("id")


def _history_by_question_id(
    examples: Sequence[Mapping[str, Any]] | None,
) -> dict[Any, list[Mapping[str, Any]]]:
    grouped: dict[Any, list[Mapping[str, Any]]] = {}
    if not examples:
        return grouped
    for example in examples:
        key = _question_identity(example)
        if key is None:
            continue
        grouped.setdefault(key, []).append(example)
    return grouped


# --------------------------------------------------------------------------- #
# PUBLIC ENTRY POINT — `score_questions`
# --------------------------------------------------------------------------- #
# Simple explanation:
# The function callers actually use. It always returns one rule-based score
# per question. If — and only if — there is enough labelled history to train
# the tree AND the trained tree is reliable enough, it blends a capped ML
# contribution on top. Every failure path falls back to rule scoring with a
# transparent `note` explaining why (e.g. `ml_fit_failed`, `ml_unreliable`,
# `ml_predict_failed`).
#
# App connection:
# Used by `app/mock_review/results_render/` to compute the P5 difficulty
# flag scores fresh on every render — nothing is persisted to SQLite.
def score_questions(
    questions: Sequence[Mapping[str, Any]],
    examples: Sequence[Mapping[str, Any]] | None = None,
) -> list[ScoreResult]:
    """Score each question with rule/history first and capped ML influence."""
    if not questions:
        return []

    examples_list = list(examples or [])
    histories = _history_by_question_id(examples_list)
    rule_results = [
        score_rule_based(q, history=histories.get(_question_identity(q)))
        for q in questions
    ]

    ml_ready = can_train_personal_model(examples_list)
    if not ml_ready:
        return rule_results

    model = fit_personal_model(examples_list)
    if model is None:
        return [
            ScoreResult(
                score=result.score,
                source="rule",
                note=_append_note(result.note, "ml_fit_failed"),
            )
            for result in rule_results
        ]

    metrics = evaluate_personal_model(examples_list)
    reliability = ml_reliability(
        total=metrics.get("total_examples", 0),
        correct=metrics.get("correct_examples", 0),
        wrong=metrics.get("wrong_examples", 0),
        balanced_accuracy=metrics.get("balanced_accuracy", 0.0),
    )
    if reliability <= 0:
        return [
            ScoreResult(
                score=result.score,
                source="rule",
                note=_append_note(result.note, "ml_unreliable"),
            )
            for result in rule_results
        ]

    feature_rows = [_structured_feature_values(q) for q in questions]
    probabilities = _predict_probabilities(model, feature_rows)
    if probabilities is None or len(probabilities) != len(questions):
        return [
            ScoreResult(
                score=result.score,
                source="rule",
                note=_append_note(result.note, "ml_predict_failed"),
            )
            for result in rule_results
        ]

    results: list[ScoreResult] = []
    for rule_result, probability in zip(rule_results, probabilities):
        ml_score = clamp_score(probability * 100)
        blended = clamp_score(
            (1 - reliability) * rule_result.score + reliability * ml_score
        )
        note = _append_note(rule_result.note, f"ml_reliability={reliability:.2f}")
        results.append(ScoreResult(score=blended, source="ml", note=note))
    return results


__all__ = [
    "MIN_EXAMPLES_FOR_ML",
    "MIN_EXAMPLES_PER_CLASS",
    "ScoreResult",
    "can_train_personal_model",
    "clamp_score",
    "difficulty_band",
    "evaluate_personal_model",
    "fit_personal_model",
    "history_adjusted_score",
    "ml_reliability",
    "multi_correct_risk",
    "normalize_1_to_5",
    "score_questions",
    "score_rule_based",
    "structured_feature_row",
]

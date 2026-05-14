# `app/ml/personal_difficulty/` — personal wrong-answer-risk scoring

This package estimates **how likely the current student is to get a question wrong**, not the absolute difficulty of the question itself. It is the only `app/ml/` module that is wired into the live app in Phase 7. The visible product surfaces that consume it are the **Custom Mock** entry point on the Class page and the **`Difficulty for you: X/100`** badge on P5 review cards.

The score has two sources:

- `"rule"` — a deterministic, transparent rule/history estimate computed from Claude's stored difficulty metadata, safe fallback features, and the student's prior answers on that exact question.
- `"ml"` — a local scikit-learn `DecisionTreeClassifier` over structured metadata features. Its probability is blended into the rule/history score only when there is enough real completed-answer data and the validation quality is credible.

Plan 07.1-05 replaced the stale Phase 7 text-only branch with the course-aligned structured tree path. `LogisticRegression`, `TfidfVectorizer`, and TF-IDF pipelines are rejected/deferred for Phase 7.1 per Tiago's NotebookLM correction. KNN is not production-wired; it may only be mentioned in reports as course comparison evidence.

The score is **always recalculated on demand**. Nothing in this package writes to the SQLite database, persists a model artifact, calls Claude or NotebookLM, imports Streamlit, or touches the network.

Purity note: this runtime package receives plain dictionaries from callers and is intentionally pure. The separate offline dataset-prep tools under `app/ml/dataset_labels/` may perform read-only SQLite exports or write local JSON/JSONL evidence only when a teammate explicitly runs those scripts; that offline behavior is not part of the live `app/ml/personal_difficulty` scoring path.

## Files

| File | Purpose |
| --- | --- |
| `app/ml/personal_difficulty/__init__.py` | Pure scoring core (rule, readiness, in-memory model fit, score map). |
| `app/ml/personal_difficulty/personal_difficulty.md` | This sidecar. |

## Connected callers

| Caller | Why it calls this module |
| --- | --- |
| `app/class_/custom_mock_selection/__init__.py` (Plan 07-02) | Ranks ready class questions by current personal difficulty score. |
| `app/mock_review/results_render/__init__.py` (Plan 07-04) | Renders `Difficulty for you: X/100` on each review card. |

The query helpers in `app/db/queries_questions/` and `app/db/queries_attempts/` (Plan 07-02) hand plain dictionaries / lists into this module. This module never reaches back into the DB.

## Inputs, outputs, and data flow

Inputs are plain Python dictionaries: ready-question rows with stored metadata fields and optional completed-answer example rows with `selected_indices`, `is_correct`, and `is_skipped`/`was_skipped`. Outputs are `ScoreResult` objects or score maps carrying an integer `score`, a `source` (`"rule"` or `"ml"`), and an explanatory `note` when a fallback, history adjustment, or ML blend happened. The data flow is intentionally one-way: DB/query helpers read SQLite, callers project rows into dictionaries, this module scores in memory, and callers decide how to display or rank the resulting scores. No score is written back to SQLite by this module.

## Code walkthrough

### Constants and locked bands

- `MIN_EXAMPLES_FOR_ML = 30` — minimum total completed answer examples before the ML branch can influence scores.
- `MIN_EXAMPLES_PER_CLASS = 5` — minimum examples on each side (correct vs wrong/skipped).
- `MODEL_RANDOM_STATE = 7` — fixed seed for the active tree and validation split.
- `MAX_ML_RELIABILITY = 0.85` — hard cap so ML can never fully replace rule/history scoring.
- `QUESTION_TYPE_RISK` — read-only ordinal risk for Surf's canonical `question_type` slugs: `knowledge=0.00`, `comprehension=0.20`, `application=0.45`, `analysis=0.70`, `synthesis=0.90`, `evaluation=1.00`.
- `RULE_WEIGHTS` — metadata-first formula weights: distractor similarity `0.24`, distractor derivation `0.20`, reasoning steps `0.18`, conceptual density `0.14`, wording complexity `0.08`, question type `0.08`, and multi-correct shape `0.08`.
- `DIFFICULTY_METADATA_KEYS` — the five stored Claude metadata fields the formula requires.
- `STRUCTURED_FEATURE_NAMES` — feature order for the tree model: the five difficulty metadata values, wording clarity issue, question-type risk, unique correct-index count, multi-correct risk, word-count risk, and readability.
- `FALLBACK_LONG_TEXT_BASELINE = 80` and `FALLBACK_LONG_TEXT_SPAN = 320` — bounds for the fallback long-text feature.

The locked score bands are:

| Score | Band |
| ---: | --- |
| `0..32` | `easy` |
| `33..66` | `medium` |
| `67..100` | `difficult` |

Four-option count is deliberately absent. Every Surf MCQ normally has four options, so option count carries no difficulty signal.

### `ScoreResult`

Frozen dataclass returned by every scoring entry point. It carries the integer `score` (`0..100`), a `source` field (`"rule"` or `"ml"`), and an optional `note` string. The note can include values such as `"missing_question"`, `"missing_difficulty_metadata"`, `"history_adjusted"`, `"ml_fit_failed"`, `"ml_unreliable"`, `"ml_predict_failed"`, or `ml_reliability=...` when the safe fallback or blend path is taken.

### `clamp_score(value)`

Defensive clamp. Returns an integer in `0..100`. Non-numeric or `None` inputs collapse to `0` instead of raising — Surf must never crash a P5 page render because of a bad row.

### `normalize_1_to_5(value)` and `difficulty_band(score)`

`normalize_1_to_5(...)` converts each Claude rubric value to the formula scale:

- `1 -> 0.00`
- `2 -> 0.25`
- `3 -> 0.50`
- `4 -> 0.75`
- `5 -> 1.00`

Values outside `1..5`, booleans, or non-integer-like values return `None`. `difficulty_band(...)` applies the locked bands after clamping the score to `0..100`.

### `_read_str`, `_question_text_length`, `_correct_index_count`, `_as_float`, and `_clamp01`

Tiny helpers that read fields from a question or example dict without raising on missing keys. `_as_float(...)` and `_clamp01(...)` normalize optional numeric metadata for the structured tree features.

### `_question_type_risk(question)`, `multi_correct_risk(correct_indices)`, and `_long_text_risk(question)`

`_question_type_risk(...)` reads the stored `question_type` as a small prior and never rewrites the taxonomy. Unknown or missing slugs fall back to `0.45` so old rows remain scoreable.

`multi_correct_risk(...)` uses the unique count of decoded `correct_indices`:

- one correct answer -> `0.00`
- two correct answers -> `0.55`
- three correct answers -> `0.80`
- four or more correct answers -> `1.00`

Duplicate indices do not inflate risk because the function uses `set(correct_indices)`.

`_long_text_risk(...)` is only for missing-metadata fallback rows. It normalizes question text length with:

```text
min(max((len(question_text) - 80) / 320, 0.0), 1.0)
```

### `_metadata_risks(question)` and `_rule_score_without_history(question)`

`_metadata_risks(...)` normalizes the five stored Claude fields:

- `difficulty_distractor_similarity`
- `difficulty_distractor_derivation`
- `difficulty_reasoning_steps`
- `difficulty_conceptual_density`
- `difficulty_wording_complexity`

If any required metadata value is missing or malformed, `_rule_score_without_history(...)` switches to the safe fallback formula and returns the note `missing_difficulty_metadata`.

Metadata-first formula:

```text
score = round(100 * (
  0.24 * distractor_similarity_z
  + 0.20 * distractor_derivation_z
  + 0.18 * reasoning_steps_z
  + 0.14 * conceptual_density_z
  + 0.08 * wording_complexity_z
  + 0.08 * question_type_z
  + 0.08 * multi_correct_z
))
```

Fallback formula for old rows or failed metadata enrichment:

```text
score = round(100 * (
  0.45 * question_type_z
  + 0.30 * multi_correct_z
  + 0.25 * long_text_z
))
```

`difficulty_wording_clarity_issue` is not rewarded as “good hard.” It stays available for quality review but does not raise the difficulty score.

### Structured ML feature helpers

`_word_count(...)`, `_word_count_risk(...)`, `_readability_feature(...)`, `_bool_feature(...)`, `_metadata_feature(...)`, `structured_feature_row(...)`, and `_structured_feature_values(...)` build the active tree input. The model sees only structured metadata and safe row shape features:

- the five Claude difficulty metadata values normalized from `1..5` to `0..1`;
- `difficulty_wording_clarity_issue` as `0.0` / `1.0`;
- canonical `question_type` as the read-only ordinal risk;
- unique `correct_indices` count and multi-correct risk;
- `difficulty_word_count` when present, otherwise question text length/word count fallback;
- `difficulty_readability` when present, otherwise neutral `0.5`.

Missing metadata is neutralized for the model row instead of crashing. The rule score still records `missing_difficulty_metadata` when its required formula inputs are absent.

### `history_adjusted_score(...)`, `_history_counts(...)`, and `_append_note(...)`

`history_adjusted_score(...)` applies the exact-question Bayesian update:

```text
adjusted = (
  prior_strength * rule_score
  + 100 * wrong_or_skipped_count
  + 0 * correct_count
) / (prior_strength + correct_count + wrong_or_skipped_count)
```

The default `prior_strength=4` means the metadata rule score acts like four prior observations. One wrong/skipped answer nudges the score up; one correct answer nudges it down. `_history_counts(...)` maps prior examples to correct vs wrong/skipped counts using `_target_from_example(...)`. `_append_note(...)` preserves result notes such as `missing_difficulty_metadata`, `history_adjusted`, `ml_fit_failed`, and `ml_predict_failed`.

### `score_rule_based(question, history=None)`

Builds the deterministic rule/history score:

1. If the question is not a dict, return score `0` with note `missing_question`.
2. If all five Claude metadata fields are present and valid, compute the weighted metadata formula.
3. If metadata is missing, compute the fallback formula and add note `missing_difficulty_metadata`.
4. Read `question_type` and `correct_indices`; do not mutate the question row.
5. If exact-question history is provided, apply `history_adjusted_score(...)` and add note `history_adjusted`.
6. Clamp the result and return a `ScoreResult` with `source="rule"`.

`history` is optional and must already be scoped to the exact question. The public `score_questions(...)` helper performs that grouping for normal callers.

### `_target_from_example(example)`

Maps an answer-example dict to a training target:

- `is_skipped=True` → `1` (wrong-risk positive class).
- `is_correct=True` → `0`.
- `is_correct=False` → `1`.
- Anything missing → `None` (the example is ignored).

### `can_train_personal_model(examples)`

Returns `True` only when:

- The total number of valid examples is at least `MIN_EXAMPLES_FOR_ML`, **and**
- Each target class (correct and wrong/skipped) has at least `MIN_EXAMPLES_PER_CLASS`.

This is the **readiness gate** that prevents tiny or one-sided history from producing misleading "ML" scores.

### `_training_matrix(...)`, `_label_counts(...)`, and `_can_train_from_labels(...)`

These helpers convert completed-answer examples into structured feature rows and binary labels. The label is still `1` for wrong/skipped and `0` for correct. They intentionally do not read the database or mutate the input rows.

### `fit_personal_model(examples)`

Builds an in-memory `DecisionTreeClassifier(max_depth=3, min_samples_leaf=3, class_weight="balanced", random_state=7)`. It re-checks readiness through the structured labels and returns `None` on any failure. **No model artifact is persisted.**

### `evaluate_personal_model(examples)`

Returns standard scikit-learn classification metrics for the structured tree path:

- balanced accuracy
- accuracy
- precision
- recall
- F1
- confusion matrix

At `60+` examples it uses a stratified validation split with `random_state=7`; below that it can only report a training-scope metric, which keeps reliability small. `balanced_accuracy` is the reliability anchor because the student's history can be skewed toward correct or wrong/skipped examples. If fitting or evaluation fails, all metrics fall back to zero with `evaluation_scope="unavailable"`.

### `ml_reliability(total, correct, wrong, balanced_accuracy)`

Converts data volume, class balance, and validation quality into the ML blend weight. It returns `0` below the training thresholds, starts small around `30` balanced examples, uses balanced accuracy once `60+` examples are available, penalizes one-sided class balance, and caps at `0.85`. This is the guard that prevents a hard switch from rule scoring to ML scoring.

### `_predict_probabilities(model, features)`

Calls `model.predict_proba(...)` and extracts the probability of the wrong-risk class (`1`). Returns `None` on failure so the caller can fall back to rule scores.

### `_question_identity(row)` and `_history_by_question_id(examples)`

These helpers keep personalization honest. They group completed-answer examples only by exact `question_id` / `id` match. They do not infer similarity from nearby questions, lecture titles, or question types.

### `score_questions(questions, examples=None)`

The public entry point:

1. Empty `questions` → empty list.
2. Group examples by exact question ID.
3. Compute each question's rule/history score before any ML branch.
4. Not enough two-class data → return those rule/history scores.
5. Fit fails → return rule/history scores with `note="ml_fit_failed"` appended.
6. Evaluate the model and compute `ml_reliability(...)`.
7. Reliability is `0` → return rule/history scores with `note="ml_unreliable"` appended.
8. Predict fails or row count mismatch → return rule/history scores with `note="ml_predict_failed"` appended.
9. Otherwise → blend each score as `(1 - reliability) * rule_history_score + reliability * ml_score`, with `source="ml"` and a reliability note.

The deterministic rule/history score remains the anchor even when ML is active; the tree never fully takes over because reliability is capped at `0.85`.

The function returns only in-memory `ScoreResult` objects. It does not cache fitted trees, serialize artifacts, update questions, or freeze P5 attempt snapshots.

## Safety boundaries

- No `import streamlit`, `from app.db ...`, `from app.brain.claude_client ...`, `import requests`, `import httpx`, or NotebookLM/`nlm` imports anywhere in this package.
- No file I/O: nothing in this package opens, reads, or writes a file. Model artifacts are deliberately not saved.
- No global mutable state: every call is pure and re-fits the model on demand.
- Question rows are **never mutated**. `question_type` in particular is only **read** as a feature.

These boundaries are enforced by the regression tests in `tests/test_phase7_no_side_effects.py`.

## What could break if this is changed carelessly

- Lowering the readiness thresholds risks fake-ML behavior on tiny answer history. Tiago's lock forbids fake analytics in production.
- Adding an import from `streamlit`, `app.db`, `app.brain.claude_client`, or any network client would break the side-effect guard tests and the `app/ml/` safety contract.
- Changing the `ScoreResult.source` strings (`"rule"` / `"ml"`) would invalidate the test that proves rule fallback is used before the readiness gate trips.
- Persisting a model artifact would violate D-22 unless separately re-approved.

# `app/ml/` — ML bucket and personal difficulty scoring

This bucket holds Surf's ML code. As of the Phase 7.1 closeout it has exactly one live runtime module — `personal_difficulty/` — plus offline dataset-prep/reference helpers under `dataset_labels/`. Empty future scaffolds were removed on 2026-05-14 to avoid stale ownership hints. The dashboard must never invent analytics that were not produced from stored attempt data, and runtime `app/ml/` code must never import Streamlit, secrets, the live SQLite connection, the Claude client, NotebookLM helpers, or any network client.

## Bucket purpose

`app/ml/personal_difficulty/` provides Phase 7.1's personal wrong-answer-risk score (`source="rule"` until enough real answer history exists, then `source="ml"` only for a reliability-weighted structured tree blend). `app/ml/dataset_labels/` remains offline evidence/reference material for future approved ML work. Future runtime or training packages should be recreated only when Tiago approves a concrete scope; empty placeholder packages are intentionally not kept in the repo.

## What lives here now

| Path | Reserved future ownership | Current status |
|---|---|---|
| `app/ml/__init__.py` | Marks the bucket as importable Python. | Package marker; no runtime behavior. |
| `app/ml/personal_difficulty/__init__.py` | **Live in Phase 7.1.** Pure-Python personal wrong-answer-risk scoring (rule/history + shallow structured `DecisionTreeClassifier` blend). | Active. See `personal_difficulty/personal_difficulty.md`. |
| `app/ml/personal_difficulty/personal_difficulty.md` | Sidecar with `## Code walkthrough` for the scoring module. | Active. |
| `app/ml/dataset_labels/__init__.py` | Marks the dataset-label folder as importable Python. | Empty package marker. |
| `app/ml/dataset_labels/normalize_bloom_dataset.py` | Offline converter from Bloom-labeled MCQ JSONL rows into Surf `question_type` notation. | Added for Phase 7 dataset prep; no DB, Streamlit, secret, network, training, or inference side effects. |
| `app/ml/dataset_labels/train_mcq_confidence_08_surf.jsonl` | Converted local dataset copy using Surf slugs. | Generated from Tiago's downloaded `train_mcq_confidence_08.jsonl`; source `question_type=mcq` is preserved as `question_format`, and Bloom labels become Surf `question_type`. |
| `app/ml/dataset_labels/train_mcq_confidence_08_surf_summary.json` | Conversion evidence. | Records 3,878 rows, per-slug counts, subject counts, taxonomy version, and 403 repaired text rows. |
| `app/ml/dataset_labels/export_generated_questions.py` | Offline read-only SQLite exporter for generated Surf questions. | Added for Phase 7 Step 2; opens SQLite with `mode=ro` and writes JSONL only. |
| `app/ml/dataset_labels/mii_generated_questions_surf_labeled.jsonl` | MII generated questions with non-null canonical `question_type` labels. | 91 Claude-labeled rows from `MII_SM2` through `MII_SM6`; safer future train/eval input. |
| `app/ml/dataset_labels/mii_generated_questions_surf_all.jsonl` | All MII generated questions. | 110 rows including 19 legacy `MII_SM1` rows with `question_type: null`; inventory/relabeling reference. |
| `app/ml/dataset_labels/teammate_bloom_reference/` | Reference-only import from teammate Bloom classifier repo. | Contains teammate datasets, metadata, and original scripts saved as `.py.txt` for Phase 7 comparison; not imported by Surf and not executed during app startup. |

## How it fits into Surf

Current Surf question-type behavior is **not** ML-driven. Question rows store a canonical `questions.question_type` slug such as `analysis`, `application`, or `knowledge`. The take, review, and dashboard pages display or aggregate that stored value from real completed attempts. Claude remains the source of truth for `question_type`; Phase 7 does not replace it.

The one place ML touches the app today is Phase 7.1's **personal difficulty score**:

- `app/ml/personal_difficulty/score_questions(...)` returns a per-question wrong-risk score.
- `app/class_/custom_mock_selection/` ranks ready questions by that score for the red `CUSTOM MOCK >` button on the Class page (Plan 07-02 / 07-03).
- `app/mock_review/results_render/` displays `Difficulty for you: X/100` on each P5 review card (Plan 07-04).

The active scoring path is:

1. metadata-first rule scoring from Claude difficulty fields, question type, and multi-correct shape;
2. a safe fallback formula for old rows or failed metadata enrichment;
3. exact-question Bayesian history adjustment from the student's own completed answers;
4. optional shallow `DecisionTreeClassifier(max_depth=3, min_samples_leaf=3, class_weight="balanced", random_state=7)` probability over structured metadata features; and
5. progressive reliability blending based on completed-answer volume, class balance, and standard metrics, with `balanced_accuracy` as the quality anchor and a hard `0.85` ML-weight cap.

The locked score bands are `0..32 = easy`, `33..66 = medium`, and `67..100 = difficult`. `LogisticRegression`, `TfidfVectorizer`, and TF-IDF pipelines are rejected/deferred for Phase 7.1; KNN is not production-wired and may only be discussed as report-only course comparison evidence.

## Simple explanation: how the ML tool learns and scores difficulty

Think of the score as a **personal wrong-answer risk**, not a universal difficulty label. A score of `0` means "this looks easy for this student" and `100` means "this looks risky for this student." The app shows that as `Difficulty for you: X/100`.

Surf derives that score in layers:

1. **Start with the question itself.** Claude adds difficulty metadata for each generated MCQ: how similar the distractors are, whether distractors require derivation, how many reasoning steps are needed, conceptual density, wording complexity, and whether the wording has a clarity issue.
2. **Turn those fields into a first score.** Each 1-to-5 metadata field is normalized to a 0-to-1 risk value. Surf then combines the values with fixed weights. Distractor similarity matters most, followed by distractor derivation, reasoning steps, conceptual density, wording complexity, question type, and multi-correct shape.
3. **Use a safe fallback when metadata is missing.** If an old or failed question has no valid metadata, Surf estimates risk from the stored `question_type`, whether the question has multiple correct answers, and question length. It does not invent hidden ML values.
4. **Adjust for this student's exact history.** If the student has already answered this exact question, Surf blends the first score with their history: wrong or skipped answers pull the score upward, correct answers pull it downward. A small prior keeps one answer from overreacting too much.
5. **Only learn from data when there is enough data.** The real ML branch stays off until there are at least 30 completed answers, including at least 5 correct and 5 wrong/skipped examples. Until then, Surf uses the rule/history score only.
6. **Train a small local model in memory.** When enough data exists, Surf trains a shallow `DecisionTreeClassifier` on structured features only: the Claude metadata, question-type risk, correct-answer count, multi-correct risk, word-count risk, and readability. The target is simple: `0 = correct`, `1 = wrong or skipped`.
7. **Trust the model only as much as it deserves.** Surf checks standard metrics, especially balanced accuracy. If the model is weak, imbalanced, or has too little data, its influence is `0`. If it is credible, Surf blends the model's wrong-answer probability into the rule/history score. The model can never control more than 85% of the final score.

In formula form, the normal path is:

```text
base score = weighted metadata/question-shape risk
history score = blend(base score, exact-question correct/wrong/skipped history)
final score = blend(history score, model wrong-answer probability, reliability weight)
```

The result is intentionally conservative: the app always has an explainable rule score, and ML only becomes a helper after enough real student answers prove that it is useful. No model file is saved; the small tree is fitted fresh in memory from the completed-answer examples passed into the scorer.

Other rules stay the same:

- P4/P5 display stored `question_type` values; no relabeling.
- P6 question-type performance uses completed mock/practice answers joined to stored question rows.
- Empty or missing data must show honest empty states, not fake analytics.

## Future readiness gate

Before code in this bucket is wired into the app, the team must approve:

1. The exact goal: classifier, taxonomy migration, dashboard feature, or no-op deferral.
2. The input contract from Surf tables and page state.
3. The output contract, including confidence values and failure modes.
4. The model artifact path, dependency list, license limits, runtime cost, and privacy risk.
5. Tests that prove imports do not touch SQLite, Streamlit, secrets, or the network.

## Data and safety boundaries

These boundaries are active now and stay true for `personal_difficulty/` and every other package in this bucket. They are enforced by tests in `tests/test_phase7_no_side_effects.py`:

- No direct SQLite reads or writes from `app/ml/` — query helpers under `app/db/queries_*` pass plain dicts in.
- No `import streamlit` from `app/ml/`.
- No secret reads from `app/ml/` (no `.env`, no `ANTHROPIC_API_KEY`, no `os.environ` reads for keys).
- No automatic network calls from `app/ml/` (no `requests`, `httpx`, `urllib.request`, or NotebookLM calls).
- No imports from `app.brain.claude_client` or any NotebookLM helper.
- No schema changes from `app/ml/`.
- No production dependency additions from `app/ml/` without approval.
- No model artifact or training output committed unless the team approves its source, size, privacy, and license. The Phase 7.1 personal-difficulty tree is fitted in memory and never persisted.

Runtime purity means `app/ml/personal_difficulty/` cannot inspect or mutate SQLite, secrets, Streamlit state, Claude, NotebookLM, or the filesystem. The older `dataset_labels/` scripts are a separate offline-prep exception: they may open SQLite read-only (`mode=ro`) or write local JSON/JSONL exports only when explicitly invoked from the command line for dataset research. They are not imported by the Streamlit app and are not part of production scoring.

## Code walkthrough

This bucket now has one live runtime module (`personal_difficulty/`) plus offline/reference `dataset_labels/` material. The runtime module is pure and side-effect-free; offline dataset-prep tools stay manually invoked and outside Streamlit startup. Empty placeholder packages for future inference, model artifacts, radar features, and training were removed during Phase 7.1 closeout so teammates do not mistake them for active or promised V1 code.

### `app/ml/__init__.py`

Marks the top-level ML bucket. It has no imports, functions, DB calls, Streamlit calls, or side effects.

### `personal_difficulty/`

**Live in Phase 7.1.** Pure-Python scoring core for personal wrong-answer-risk. Exposes `score_questions(questions, examples)` and helpers (`score_rule_based`, `can_train_personal_model`, `fit_personal_model`, `evaluate_personal_model`, `ml_reliability`, `structured_feature_row`, `ScoreResult`, `clamp_score`). Rule/history scoring is the deterministic default: metadata-first score, fallback score when metadata is missing, and exact-question Bayesian history. The scikit-learn branch uses `DecisionTreeClassifier` on structured metadata features only, activates only after at least `MIN_EXAMPLES_FOR_ML=30` completed answers with at least `MIN_EXAMPLES_PER_CLASS=5` correct and 5 wrong/skipped labels, and then blends progressively with the rule/history score using a reliability weight capped at `0.85`. Standard metrics include balanced accuracy, accuracy, precision, recall, F1, and a confusion matrix. The model is fit in memory on every call; no artifact is persisted. See `personal_difficulty/personal_difficulty.md` for the section-by-section walkthrough.

### `dataset_labels/`

Contains the offline Bloom-to-Surf dataset converter, the converted external JSONL copy, and the read-only generated-question exporter. The converter maps `Remember/Understand/Apply/Analyze/Evaluate/Create` to Surf's `knowledge/comprehension/application/analysis/evaluation/synthesis` slugs, repairs common downloaded text mojibake, and writes a summary JSON. The generated-question exporter opens SQLite in `mode=ro`, exports MII generated MCQs, and records lecture-level `split_group` values for future train/test splitting. These tools do not read saved keys, mutate the live local database, import Streamlit, run training/inference, or call the network. The `teammate_bloom_reference/` subfolder is a readable reference import from `/Users/tiagoreimann/Downloads/Bloom-main.zip`: it gives Phase 7 planning access to the teammate datasets and training-script patterns while keeping upstream scripts as text so Surf cannot accidentally import or run them.

## Teammate talking points

- Surf V1 works without additional ML scaffolds; the only live runtime ML package is `personal_difficulty/`, and future packages should be recreated only after approval.
- Current analytics come from `questions.question_type` and completed attempts, not generated placeholder values.
- The Phase 7 dataset-prep file uses Surf `question_type` notation, but it is still offline evidence only.
- The active personal-difficulty ML path is the Phase 7.1 structured `DecisionTreeClassifier`, not text-only logistic regression or KNN.
- The teammate Bloom reference folder can inform Phase 7 dataset comparison, but any future-approved train/save artifact work must create a Surf-compatible model artifact and use the approved BT-to-Surf label mapping.
- Future ML must be privacy-reviewed before it can read class material, produce model artifacts, or affect the app UI.

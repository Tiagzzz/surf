# `app/class_/mcq_difficulty_metadata/` — Claude difficulty metadata critic

This package runs the Phase 7.1 second Claude call. The first Claude call creates valid MCQs; this critic call reads those finished MCQs plus the source slide text and returns intrinsic difficulty metadata for scoring.

The package is intentionally under `app/class_/`, not `app/ml/`, because it calls Claude through the shared wrapper. `app/ml/**` must stay pure and side-effect-free.

## Files

| File | Purpose |
| --- | --- |
| `app/class_/mcq_difficulty_metadata/__init__.py` | Builds the critic request, calls Claude through `app.brain.claude_client.call_claude`, and normalizes untrusted metadata. |
| `app/class_/mcq_difficulty_metadata/mcq_difficulty_metadata_system_prompt.md` | The assessment rubric Claude uses for five 1..5 feature scores plus the clarity flag. |
| `app/class_/mcq_difficulty_metadata/mcq_difficulty_metadata.md` | This sidecar. |

## Connected files

- Calls only `app.brain.claude_client.call_claude` for the external model request.
- `app/class_/lecture_ingest/lecture_ingest.py` wires this package in as the second ingestion-time Claude call, after generated MCQs pass validation.
- `app/db/queries_questions.insert_question(...)` stores the normalized fields when present and keeps nullable fields empty when metadata is absent.
- Later scoring reads these fields from DB query helpers and passes plain dicts into `app/ml/personal_difficulty/`.

## Inputs and outputs

Input to `score_mcq_difficulty_metadata(...)`:

- `slides_batch`: the slide batch sent to the MCQ generator, shaped like `{"page_number": int, "raw_md": str}`.
- `by_slide`: generated MCQs grouped by page. Each MCQ should include an ingestion-only `local_id` so the critic response can be matched without relying on question text equality.
- `api_key`: optional saved Anthropic key routed into the shared wrapper.

Output is one normalized row per expected `local_id`:

- `difficulty_distractor_similarity`
- `difficulty_conceptual_density`
- `difficulty_distractor_derivation`
- `difficulty_reasoning_steps`
- `difficulty_wording_complexity`
- `difficulty_wording_clarity_issue`

The first five fields are either integers from `1` to `5` or `None`. The clarity flag is always `0` or `1`.

## Critic prompt contract

The system prompt asks Claude to act as an assessment-quality critic, not as a question rewriter. The request includes source slide text, generated question text, four options, the stored `correct_indices`, rationale text, canonical `question_type`, source page, language, and the ingestion-only `local_id`. The response must preserve each `local_id` so Surf can match metadata back to the already-validated MCQs without comparing natural-language question text.

The accepted rubric fields are:

| Claude feature | Stored field | Accepted values |
|---|---|---|
| `distractor_similarity` | `difficulty_distractor_similarity` | integer `1..5` or `None` fallback |
| `conceptual_density` | `difficulty_conceptual_density` | integer `1..5` or `None` fallback |
| `distractor_derivation` | `difficulty_distractor_derivation` | integer `1..5` or `None` fallback |
| `reasoning_steps` | `difficulty_reasoning_steps` | integer `1..5` or `None` fallback |
| `wording_complexity` | `difficulty_wording_complexity` | integer `1..5` or `None` fallback |
| `wording_clarity_issue` | `difficulty_wording_clarity_issue` | boolean-like value normalized to `0` or `1`; malformed values become `0` |

`wording_clarity_issue` is a quality flag, not a reward for difficulty. It marks ambiguous, misleading, grammatically unclear, or unfair wording. Surf stores it separately from `difficulty_wording_complexity` so dense wording can be scored without treating bad wording as desirable.

## Code walkthrough

### Module constants

`_SYSTEM_PROMPT_PATH` points at the sibling rubric prompt. `_SCORE_FIELDS` maps Claude's raw feature names to Surf's storage field names.

### `empty_metadata_for_local_id(local_id)`

Returns the safe fallback row for one MCQ. Numeric rubric fields are `None`; `difficulty_wording_clarity_issue` is `0` because the DB column added in Plan 07.1-02 is non-nullable.

### `build_metadata_request(slides_batch, by_slide)`

Creates the JSON-serializable payload for Claude. Keeping this helper separate makes tests and future debugging easier without duplicating the shape.

### `score_mcq_difficulty_metadata(slides_batch, by_slide, api_key=None)`

Extracts expected local IDs from `by_slide`, reads the system prompt, and calls the shared Claude wrapper with `expect_json=True`. It catches metadata-call failures and returns fallback rows so valid MCQs are not blocked by the second call.

This function must not log API keys or call Anthropic directly. Tests monkeypatch the imported `call_claude` seam so no live Anthropic request runs.

### `validate_difficulty_metadata_response(response, expected_local_ids)`

Treats Claude JSON as untrusted data. It ignores unknown `local_id` values, normalizes only expected IDs, and returns rows in the same order as `expected_local_ids`. Missing expected IDs receive `empty_metadata_for_local_id(...)`.

### `_expected_local_ids(by_slide)`

Walks the generated MCQ batch and collects each MCQ's ingestion-only `local_id` in stable order. If no IDs exist, the critic call is skipped.

### `_iter_raw_metadata_items(response)`

Safely pulls `difficulty_metadata` arrays out of Claude's `by_slide` response shape. Malformed response pieces are ignored.

### `_normalize_item(local_id, raw_item)`

Builds one normalized Surf row. It accepts `difficulty_features` as the normal shape but can also read flat raw fields defensively.

### `_coerce_score(value)`

Accepts only rubric values from `1` to `5`. Missing values, booleans, out-of-range values, and unrelated strings become `None`.

### `_coerce_clarity_issue(value)`

Converts common boolean forms to `0` or `1`. Unknown values default to `0` so unclear metadata does not invent a clarity problem.

## Testing notes

Tests monkeypatch the imported `call_claude` seam or call the pure validator directly. They must never require a real Anthropic key, never hit the network, and never touch SQLite. Local IDs and null-safe fallback rows are the important behaviors to preserve when tests change.

## Failure modes and safety boundaries

- Claude call fails: return fallback rows; do not fail the MCQ batch.
- Claude returns malformed JSON shape: return fallback rows for missing IDs.
- Claude returns unknown IDs: ignore them.
- Claude omits a required expected ID: return a fallback row for that ID.
- Claude returns explanation fields: do not store them in Phase 7.1.
- No direct `anthropic`, `requests`, `httpx`, `sqlite3`, NotebookLM, Streamlit, or `app.ml` imports.

## Impact check handoff

- Requested change: add Phase 7.1 metadata critic wrapper, prompt, validator, and fake-call tests.
- Register rows read: 1.35 and 1.36 from the Code & Tool Impact Register.
- Direct artifacts: this package and `tests/test_mcq_difficulty_metadata.py`.
- Downstream artifacts: Plan 07.1-02 ingestion/schema/query changes; Plan 07.1-03/04/05 scoring consumers.
- Required tests: `python -m pytest -q tests/test_mcq_difficulty_metadata.py` and `python -m ruff check app/class_/mcq_difficulty_metadata tests/test_mcq_difficulty_metadata.py --no-cache`.
- Sidecar/register co-update: Plan 07.1-06 must add/align the Phase 7.1 register row and bucket docs.
- Data/secrets/live-DB risk: no live DB mutation; tests fake Claude and must not require a real Anthropic key.
- What could break: if local IDs are not added during ingestion, metadata cannot be matched; if this module moves under `app/ml/**`, it violates the pure-ML boundary.

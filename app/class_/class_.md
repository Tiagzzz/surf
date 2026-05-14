# `app/class_/` bucket — Class Hub, lecture ingestion, and launch helpers

This bucket owns the class-specific study flow. It turns an uploaded lecture PDF into stored learning objectives and questions, renders the Class Hub, launches mock/practice sessions through Streamlit session state, and exposes the narrow lecture-delete seam for lectures that are safe to remove.

The folder is named `class_` because `class` is a Python keyword.

## What lives in this bucket

| Folder / file | What it does |
|---|---|
| `class_hub/` | Renders the Class Hub page: topbar, class title, lecture grid, `ADD LECTURE`, `DELETE LECTURE`, `TAKE MOCK >`, Study Next, Attempt History, dashboard navigation, and the destructive lecture-delete dialog. |
| `lecture_ingest/` | Orchestrates PDF → Markdown → slide split → LO extraction → MCQ generation → SQLite writes. It requires an explicit lecture title, uses the saved user API key for generation calls, isolates invalid MCQs, and stores validated `question_type` slugs. |
| `lo_extract/` | Loads the LO extractor prompt and asks the Anthropic API for learning objectives plus ignored pages. |
| `mcq_generate/` | Loads the MCQ generator prompt and asks the Anthropic API for multi-select MCQs with one stored `question_type` slug per question. |
| `mcq_difficulty_metadata/` | Phase 7.1 second-Claude-call critic. Reads already-valid generated MCQs plus slide text, matches rows by ingestion-only `local_id`, and returns null-safe intrinsic difficulty metadata for storage. It stays in `app/class_/`, not `app/ml/**`, because it can call Claude. |
| `lecture_delete/` | Confirmation-gated service wrapper around the ownership-checked lecture delete DB helper. |
| `mock_standard_launch/` | Freezes selected ready questions for `TAKE MOCK >` in session state. It creates no `attempts` row. |
| `study_next_launch/` | Freezes ready questions for one weak learning objective in session state for practice mode. It creates no `attempts` row. |
| `custom_mock_selection/` | Phase 7/7.1 ranking seam for the red `CUSTOM MOCK >` button. Joins ready questions and completed answer history with stored metadata fields, calls pure `app.ml.personal_difficulty.score_questions(...)`, and returns the top 10 highest personal-difficulty questions. Does **not** touch `mock_standard_launch/` or `study_next_launch/`. |
| `mock_custom_launch/` | Phase 7 launch helper for the red `CUSTOM MOCK >` button. Reads the top-N from `custom_mock_selection/`, writes the same P4 launch session keys as `mock_standard_launch/` (`mock_kind = "mock"`), and creates no `attempts` row. |

## How the pieces interact

```text
views/class_view.py
        │
        └── app.class_.class_hub.render_class_hub_page(...)
                │
                ├── list class lectures, ready counts, attempts, and weak LOs
                │
                ├── submit Add Lecture
                │       └── lecture_ingest.ingest_lecture(..., api_key=saved_key)
                │              ├── app.brain.ingestion.pdf_to_md_v3.extract_with_tables
                │              ├── app.class_.lo_extract.extract_los / call_claude
                │              ├── app.class_.mcq_generate.generate_mcqs / call_claude
                │              ├── app.class_.mcq_difficulty_metadata.score_mcq_difficulty_metadata / call_claude
                │              ├── app.brain.question_type validation
                │              └── app.db query helpers for lectures, pages, LOs, questions + metadata fields
                │
                ├── launch Custom Mock
                │       └── custom_mock_selection.select_custom_mock_questions(...)
                │              ├── reads metadata-rich ready-question rows
                │              ├── reads completed-answer examples
                │              └── calls pure app.ml.personal_difficulty.score_questions(...)
                │
                ├── launch selected-lecture mock
                │       └── mock_standard_launch.launch_mock_standard(...)
                │              └── writes P4 launch payload to session state only
                │
                ├── launch Study Next practice
                │       └── study_next_launch.launch_study_next_practice(...)
                │              └── writes P4 launch payload to session state only
                │
                └── delete a safe lecture
                        └── lecture_delete.delete_lecture_after_confirmation(...)
                               └── app.db.queries_lectures.delete_lecture_for_user
```

## Constraints

- `question_type` is stored question metadata for display and later real analytics, not an executable classifier or score.
- Every generation call goes through `app.brain.claude_client.call_claude`.
- Lecture title and PDF upload are mandatory; the app does not silently fall back to the PDF filename.
- Tests must not touch the live local SQLite database; they use temp SQLite or in-memory databases.
- Phase 7.1 metadata enrichment is an ingestion-time class-bucket responsibility because it can call Claude. `app/ml/**` only receives plain dictionaries after DB/query helpers read stored rows.
- Valid MCQs must survive metadata failure. Missing, malformed, or failed metadata becomes nullable rubric fields plus `difficulty_wording_clarity_issue=0`, not a failed lecture by itself.
- Mock and Study Next launch helpers write session state only. P4 final submit owns the `attempts` and `attempt_answers` write.
- Lecture deletion is blocked when any attempt answer references a question from that lecture.

## Code walkthrough

### `class_hub/`
`render_class_hub_page(...)` composes the visible Class Hub, while its pure helpers build lecture-grid, Study Next, Take Mock, and Attempt History view-models for tests. The renderer uses query helpers instead of direct SQLite calls, fetches the saved user API key only when Add Lecture is submitted, and routes mock/practice launches through the session-only helpers.

### `lecture_ingest/lecture_ingest.py`
`ingest_lecture(...)` validates the PDF path and title, extracts Markdown, inserts a pending lecture row, builds a factsheet subset, extracts LOs, writes slide pages, generates MCQs in batches, validates each generated MCQ including `question_type`, inserts only valid questions, and marks the lecture `ready`, `pending`, or `failed` honestly.

### `lo_extract/lo_extractor.py`
`extract_los(...)` JSON-encodes lecture Markdown plus the curated factsheet subset and calls the shared Anthropic wrapper with the LO extractor system prompt.

### `mcq_generate/mcq_generator.py`
`generate_mcqs(...)` validates batch size, JSON-encodes slide records, reads the MCQ system prompt, and calls the shared Anthropic wrapper. Storage validation stays in `lecture_ingest` and `queries_questions`.

### `mcq_difficulty_metadata/`
`score_mcq_difficulty_metadata(...)` is the second Claude call for Phase 7.1 difficulty metadata. It receives only already-valid MCQs, uses ingestion-only local IDs for matching, accepts five `1..5` rubric scores plus `wording_clarity_issue`, and converts bad/missing data into null-safe rows. Its tests fake the Claude seam; no live Anthropic call is required. Keeping this module outside `app/ml/**` preserves the pure-ML boundary.

### `lecture_delete/__init__.py`
`delete_lecture_after_confirmation(...)` returns `cancelled` without calling the DB unless the UI has confirmed deletion. Confirmed deletes still go through the ownership/history-safe query helper.

### Launch helpers
`mock_standard_launch.launch_mock_standard(...)` and `study_next_launch.launch_study_next_practice(...)` freeze question ids and display payloads in session state. They preserve `question_type` and never include correct answers or rationales in the pre-submit payload.

### `custom_mock_selection/`
`select_custom_mock_questions(...)` reads class-scoped ready questions through `list_ready_questions_for_class(...)` and completed-answer examples through `list_personal_difficulty_examples_for_class(...)`. Both rows now carry the Phase 7.1 metadata fields. The selector projects them into the shared plain-dict scoring shape, calls `app.ml.personal_difficulty.score_questions(...)`, then annotates the original ready-question rows with `personal_difficulty_score` and `personal_difficulty_source`. It is ranking only: it does not call Claude, write SQLite, redesign P3/P5, or create attempts.

## Testing notes

```bash
python -m ruff check app/class_ views/class_view.py --no-cache
python -m pytest -q tests/test_class_hub_render_contract.py tests/test_mock_standard_launch.py tests/test_study_next_launch.py tests/test_lecture_delete.py tests/test_question_type_launch_handoff.py
```

## What could break if changed

- Accepting a blank lecture title would make lecture cards ambiguous.
- Dropping saved-key threading would make generation use the wrong Anthropic key path.
- Storing malformed MCQs would break P4/P5 grading and review.
- Moving the metadata critic into `app/ml/**` would mix live Claude side effects into the pure scoring bucket.
- Treating metadata failure as ingestion failure would discard valid questions that should remain usable with fallback scoring.
- Creating attempts during launch would violate the session-only handoff contract.
- Deleting lectures with attempt history would corrupt review and dashboard history.
- Adding executable difficulty or classifier hooks here would get ahead of the separate readiness gate.

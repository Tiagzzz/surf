# Prompt and API Guide

Surf uses Anthropic Claude for four generation/critic flows: factsheet cleaning,
learning-objective extraction, MCQ generation, and MCQ difficulty metadata review.
All Claude calls use the
same wrapper at `app.brain.claude_client`.

## Prompt file locations

| Flow | Prompt file | Caller | What goes in | What comes back |
|---|---|---|---|---|
| Factsheet cleaning | `app/my_classes/factsheet_clean/factsheet_cleaner_system_prompt.md` | `app/my_classes/factsheet_clean/factsheet_cleaner.py` | Extracted factsheet Markdown | Structured factsheet JSON |
| Learning objectives | `app/class_/lo_extract/lo_extractor_system_prompt.md` | `app/class_/lo_extract/lo_extractor.py` | Lecture Markdown plus class context | Learning objectives with page ranges |
| MCQ generation | `app/class_/mcq_generate/mcq_generator_system_prompt.md` | `app/class_/mcq_generate/mcq_generator.py` | Small lecture-page batches and learning-objective context | Four-option MCQs with rationales, difficulty estimate, and `question_type` |
| Difficulty metadata critic | `app/class_/mcq_difficulty_metadata/mcq_difficulty_metadata_system_prompt.md` | `app/class_/mcq_difficulty_metadata/__init__.py` | Generated MCQs and context | Intrinsic metadata fields for distractors, conceptual density, reasoning steps, wording complexity, and wording clarity |

## Shared wrapper

```python
from app.brain.claude_client import call_claude

result = call_claude(
    system_prompt=system_prompt,
    user_message=user_message,
    expect_json=True,
    api_key=saved_key,
)
```

The wrapper handles the Anthropic SDK client, prompt caching for the system
block, response text extraction, optional JSON parsing, and Markdown code-fence
cleanup.

## Saved-key safety

- Signup validates a typed key before saving it locally.
- Generation callers pass the saved key into `call_claude(..., api_key=saved_key)`
  for one request.
- The key value must not be printed, logged, written into docs, or committed.
- Settings validates a replacement key before saving it; blank or failed
  replacement keeps the old saved key.
- This guide does not contain a real key. Tests for this flow use fake
  clients or sample strings, not a teacher's saved key.

## Generation boundaries

- Factsheet cleaning supports class setup and class context.
- Learning-objective extraction uses lecture text and class factsheet context.
- MCQ generation creates multi-select questions with unique correct indices,
  rationales, difficulty estimate, and canonical `question_type` metadata.
- The second Claude metadata critic runs after MCQ generation and records
  intrinsic difficulty metadata. If that critic fails or returns malformed data,
  Surf keeps the valid MCQs and stores safe null/default metadata instead of
  blocking the lecture.
- Personal difficulty is then scored locally from metadata and completed-answer
  history. Phase 7.1 uses metadata-first rules and a reliability-capped
  structured `DecisionTreeClassifier` path, not text-only `LogisticRegression`
  or `TfidfVectorizer` production scoring.
- The app must not fake analytics that look generated or model-derived. Review
  and Dashboard should use stored completed attempts. P5 shows only the
  `Difficulty for you: X/100` badge, not a visible six-feature metadata panel.

## External tools and functions

- `anthropic.Anthropic` SDK through `app.brain.claude_client`.
- `call_claude(...)` for generation calls.
- `validate_anthropic_key(...)` for typed-key validation.
- `json.loads(...)` inside the wrapper when `expect_json=True`.
- Prompt `.md` files beside their caller modules.

## Teammate talking points

1. **Prompts live beside their caller.** That makes each generation flow easy to
   explain from input file to output shape.
2. **The wrapper is the API door.** It keeps prompt caching, JSON cleanup, and
   saved-key handling in one place.
3. **Secrets stay local.** The saved key is passed for one request and should
   never appear in logs, screenshots, docs, or committed files.

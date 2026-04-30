---
title: "factsheet_cleaner.py — Surf factsheet → strict JSON"
tags:
  - surf/script
  - surf/my_classes
  - surf/factsheet
status: docs
bucket: app/my_classes/factsheet_clean
---

# `factsheet_cleaner.py`

> Related: depends on [claude_client](../../brain/claude_client/claude_client.md) and [factsheet_cleaner_system_prompt](factsheet_cleaner_system_prompt.md). Consumes the output of [pdf_to_md_v3](../../brain/ingestion/pdf_to_md_v3.md). Its output is consumed by [factsheet_renderer](factsheet_renderer.md) (and the database via the `app/my_classes/factsheet_clean/` pipeline).

## What it does

Takes the raw Markdown produced by `pdf_to_md_v3.py` and asks Claude (via the shared `claude_client`) to clean it into **strict JSON** matching Surf's factsheet schema. The JSON is what gets stored in the database and rendered for the student.

**Analogy**: think of it as handing a messy hand-written form to a careful assistant who fills out a clean structured template based on it.

The full schema and field rules live in [factsheet_cleaner_system_prompt](factsheet_cleaner_system_prompt.md) — this script is just the wiring.

## How to call it

```python
from factsheet_cleaner import clean_factsheet

raw_md = open("FS_MB Topics_flagged.md").read()
data = clean_factsheet(raw_md)
# data is now a dict with keys: course_snapshot, FSLO, core_course_content,
# assessment_and_grading, prerequisites_and_assumed_knowledge,
# surf_extraction_notes, source_gaps
```

## Dependencies

- **[claude_client](../../brain/claude_client/claude_client.md)** — same project, `app/brain/claude_client/claude_client.py`
- **[factsheet_cleaner_system_prompt](factsheet_cleaner_system_prompt.md)** — sibling `.md` file, loaded at runtime
- Indirect: `anthropic` SDK (via `claude_client`) and `ANTHROPIC_API_KEY` env var

## Inputs

| Argument | Type | Required | Purpose |
|---|---|---|---|
| `raw_md` | `str` | yes | Markdown produced by `pdf_to_md_v3.py` from a factsheet PDF |

## Outputs

`dict[str, Any]` — a parsed JSON object matching the schema in [factsheet_cleaner_system_prompt](factsheet_cleaner_system_prompt.md). Top-level keys:

- `course_snapshot` — name, code, semester, ECTS, language, lecturers, format
- `FSLO` — Factsheet Learning Objectives (course-level outcomes)
- `core_course_content` — `narrative_summary`, `main_topics`, `important_concepts_models_methods`, `skills_students_are_expected_to_develop`
- `assessment_and_grading` — `assessment_components` (list), `exam_relevant_content` (list)
- `prerequisites_and_assumed_knowledge` — list
- `surf_extraction_notes` — short string (1–3 sentences) for downstream SLO extractor
- `source_gaps` — list of what's missing from the source

## Still to do

- [ ] **Anthropic SDK install**: requires `pip install anthropic` in the Surf venv. Not yet installed system-wide on Tiago's machine — will be addressed when the Streamlit app's `requirements.txt` is created.
- [ ] **Error handling**: currently lets `claude_client`'s exceptions bubble (`json.JSONDecodeError` if Claude returns malformed JSON, `anthropic.*Error` for API issues). The Streamlit caller should catch and surface a friendly retry UX.
- [ ] **Schema validation**: the JSON is trusted as-is. A jsonschema validation pass against the locked schema would catch cleaner regressions before the data hits the DB. Defer until the cleaner prompt is locked across more factsheet shapes.
- [ ] **Cost / latency telemetry**: not currently logged. Pair with the same TODO on [claude_client](../../brain/claude_client/claude_client.md).

---

## Code, section by section

### Imports

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.brain.claude_client import call_claude
```

A plain package import — no `sys.path` manipulation. `app/brain/claude_client/__init__.py` re-exports `call_claude`, so callers anywhere in the repo say `from app.brain.claude_client import call_claude` and Python's normal import machinery does the rest.

This works because Streamlit is launched from the repo root (`streamlit run streamlit_app.py`), which puts the repo root on `sys.path` automatically. Every bucket under `app/` is a regular Python package (it has an `__init__.py`).

### System prompt path

```python
_SYSTEM_PROMPT_PATH = Path(__file__).with_name("factsheet_cleaner_system_prompt.md")
```

`Path.with_name` returns the same parent folder with the new filename. So this resolves to the sibling `factsheet_cleaner_system_prompt.md` in the same bucket folder, regardless of where the script is invoked from. **Why a sibling .md instead of inlining the prompt?** Tiago and any teammate can edit the prompt without touching Python.

### The `clean_factsheet` function

```python
def clean_factsheet(raw_md: str) -> dict[str, Any]:
    system_prompt = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return call_claude(
        system_prompt=system_prompt,
        user_message=raw_md,
        expect_json=True,
    )
```

Three lines of real work:
1. Load the system prompt fresh on each call (so a saved edit takes effect immediately — no module reload needed).
2. Hand off to [claude_client](../../brain/claude_client/claude_client.md)'s `call_claude` with `expect_json=True` — that flag tells the wrapper to parse the response as JSON and strip any stray code fences.
3. Return the parsed dict directly to the caller.

Notice the script doesn't pick a model, set max_tokens, or worry about prompt caching — those defaults all live in `claude_client`. **This is the payoff of the shared wrapper**: every specialist script stays this small.

---

## Full code

```python
"""Surf — factsheet cleaner.

Sends a raw factsheet markdown (the output of pdf_to_md_v3.py) to Claude
with the cleaner system prompt, and returns strict cleaned JSON ready to
be saved to the database and rendered for the student.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.brain.claude_client import call_claude

_SYSTEM_PROMPT_PATH = Path(__file__).with_name("factsheet_cleaner_system_prompt.md")


def clean_factsheet(raw_md: str) -> dict[str, Any]:
    """Clean a raw factsheet markdown into strict JSON via Claude.

    Args:
        raw_md: the markdown produced by pdf_to_md_v3.py from the user's
            uploaded factsheet PDF.

    Returns:
        Parsed JSON dict matching the schema defined in
        factsheet_cleaner_system_prompt.md.
    """
    system_prompt = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return call_claude(
        system_prompt=system_prompt,
        user_message=raw_md,
        expect_json=True,
    )
```

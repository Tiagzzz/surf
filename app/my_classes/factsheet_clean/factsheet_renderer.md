---
title: "factsheet_renderer.py — cleaned JSON → student-facing Markdown"
tags:
  - surf/script
  - surf/my_classes
  - surf/factsheet
status: docs
bucket: app/my_classes/factsheet_clean
---

# `factsheet_renderer.py`

> Wikilinks: consumes the output of [[factsheet_cleaner]]. The rendered Markdown is what the student reviews and approves on the **MY_CLASSES** page (P2). No outbound dependencies (pure Python).

## What it does

Takes the strict JSON produced by [[factsheet_cleaner]] and renders it into Markdown for the student to read in Streamlit (or Obsidian during testing). **Pure Python — no Claude API call.**

Key behaviors:
- **No section numbers** in headings (`## Course Snapshot`, not `## 1. Course Snapshot`).
- **`surf_extraction_notes` is intentionally NOT rendered** — it's an internal-only context note for the future SLO extractor, never shown to the student.
- **Empty subsections auto-hide** (e.g. if the cleaner returned an empty `important_concepts_models_methods`, that subsection's heading is omitted entirely instead of rendering `- Not specified`).
- **Assessment Components render as bullets, not tables** (per the locked rendering rule — easier to read on narrow Streamlit columns).

**Analogy**: think of it as the printer in a print-shop. The cleaner is the typesetter who lays out the page; the renderer is the machine that puts ink on paper for the customer to read.

## How to call it

```python
import json
from factsheet_renderer import render_cleaned_factsheet_markdown

data = json.load(open("FS_MB_cleaned.json"))
md = render_cleaned_factsheet_markdown(data)
print(md)  # or st.markdown(md) in Streamlit
```

## Dependencies

- **Python ≥ 3.9**
- Standard library only (`typing`)

No Surf-internal dependencies.

## Inputs

| Argument | Type | Required | Purpose |
|---|---|---|---|
| `data` | `dict[str, Any]` | yes | Cleaned JSON matching the schema in [[factsheet_cleaner_system_prompt]] |

## Outputs

`str` — Markdown text. Begins with YAML frontmatter (`title`, `tags`, `status`, `course_code`, `ects`) for Obsidian indexing, followed by the rendered sections.

## Sections rendered (in order)

1. **Course Snapshot** — name, code, semester, ECTS, language, lecturers, format
2. **Course Narrative** — Claude-distilled prose summary
3. **Learning Objectives** — bullets from the FSLO array
4. **Core Course Content** — Main Topics / Important Concepts / Skills (each subsection auto-hidden if empty)
5. **Assessment and Grading** — Assessment Components (bullets) / Exam-Relevant Content
6. **Prerequisites and Assumed Knowledge**
7. **Source Gaps**

## Sections intentionally NOT rendered

- **`surf_extraction_notes`** — internal-only context for the SLO extractor.

## Still to do

- [ ] **Streamlit integration**: this returns a Markdown string. The Streamlit caller will pass it to `st.markdown(md)` for display. Confirm Streamlit honours the YAML frontmatter (it doesn't natively — frontmatter will render as a code block). Strip frontmatter before display when called from Streamlit; keep it when writing to disk for Obsidian.
- [ ] **Re-render-on-edit**: when the student edits the cleaned JSON during the review step, the rendered MD needs to refresh. Cheap enough to call this on every JSON change — no caching needed.

---

## Code, section by section

### Imports + module type

```python
from __future__ import annotations
from typing import Any

FactsheetJSON = dict[str, Any]
```

Standard typing setup. The `FactsheetJSON` alias makes function signatures more readable.

### Helper: safe value with fallback

```python
def _value(value: Any, fallback: str = "Not specified") -> str:
    if value is None or value == "":
        return fallback
    return str(value).strip()
```

Defensive helper. If the cleaner returns `None` or an empty string for any field, we render `"Not specified"` instead of crashing or showing `None` to the student.

### Helper: render a list as bullets

```python
def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {_value(item)}" for item in items)
```

Joins a list of strings into a Markdown bullet list. Each item passes through `_value` so `None`s get the fallback.

### Helper: assessment components as bullets (no tables)

```python
def _assessment_bullets(components: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for component in components:
        name = _value(component.get("component"))
        weight = _value(component.get("weight"), fallback="")
        headline = f"**{name}**" if not weight else f"**{name} ({weight})**"

        details: list[str] = []
        for label, key in [
            ("Format", "format"),
            ("Timing", "timing"),
            ("Individual/Group", "individual_or_group"),
            ("Notes", "notes"),
        ]:
            raw = component.get(key)
            if raw is None or raw == "":
                continue
            details.append(f"- {label}: {_value(raw)}")

        block = headline + ("\n\n" + "\n".join(details) if details else "")
        blocks.append(block)

    return "\n\n".join(blocks)
```

Each assessment component (e.g. "Quiz 30%", "Written midterm 70%") renders as a bold headline + nested detail bullets. **Empty fields are silently dropped** — so a closed-book exam without supplementary aids doesn't show a confusing `Notes: Not specified` line.

For Math B (1 component), this produces a single block. For ACA (Quiz + Written), two blocks separated by a blank line. Cleaner than a wide table that wraps awkwardly in narrow Streamlit columns.

If `components` is empty, this returns an empty string. The caller in `render_cleaned_factsheet_markdown` already guards with `if components:`, so the empty case is unreachable in normal use — no dead "Not specified" fallback inside this helper.

### Helper: auto-hide empty subsection

```python
def _maybe_subsection(heading: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return [heading, "", _bullets(items), ""]
```

Returns the lines for a heading + bullet list — but **only if the list is non-empty**. This is what makes empty subsections disappear gracefully instead of rendering ugly placeholders.

### Main render function

The main function builds a `lines` list and joins it with newlines at the end. It uses three patterns:

1. **Always-rendered sections** (Course Snapshot) — appended directly.
2. **Conditionally-rendered sections** (Course Narrative — only if narrative is non-empty) — appended inside an `if`.
3. **Auto-hide-empty sections** (Learning Objectives, the Core Course Content subsections, Source Gaps) — built via `_maybe_subsection` so they vanish when empty.

The `Core Course Content` H2 itself is only rendered if at least one of its subsections has content. Same for `Assessment and Grading`. **Why?** Avoids dangling H2 headings with nothing under them.

**Defensive top-level access**: every top-level key is read with `data.get(..., {})` instead of `data["..."]`. If the cleaner ever returns malformed JSON missing one of these keys, the renderer degrades gracefully (empty section) instead of crashing the Streamlit page with `KeyError`.

**`main_lecturers` null-safety**: read as `snapshot.get("main_lecturers") or []` rather than `snapshot.get("main_lecturers", [])`. The `or []` form catches the case where the key is present but the value is explicitly `null` (which Claude occasionally emits for empty fields), preventing a `TypeError` from `", ".join(None)`.

---

## Full code

```python
"""Surf — factsheet renderer.

Takes the cleaned factsheet JSON (output of factsheet_cleaner.py) and
renders it as student-facing Markdown for display in Streamlit / Obsidian.

Pure Python — no Claude API call. Empty subsections auto-hide instead of
rendering placeholder text. surf_extraction_notes is intentionally NOT
rendered (internal-only — consumed by the future SLO extractor).
"""
from __future__ import annotations

from typing import Any

FactsheetJSON = dict[str, Any]


def _value(value: Any, fallback: str = "Not specified") -> str:
    """Safe display string. Returns the fallback when value is None or empty."""
    if value is None or value == "":
        return fallback
    return str(value).strip()


def _bullets(items: list[str]) -> str:
    """Render a list of strings as Markdown bullets."""
    return "\n".join(f"- {_value(item)}" for item in items)


def _assessment_bullets(components: list[dict[str, Any]]) -> str:
    """Render assessment components as a flat bullet list (no tables).

    Each component gets a bold headline (component name + weight) followed
    by nested bullets for format, timing, individual/group, and notes.
    Empty fields are silently skipped — only meaningful detail surfaces.

    Returns an empty string when components is empty. Callers in
    render_cleaned_factsheet_markdown only invoke this inside `if components:`,
    so the empty case is unreachable in normal use.
    """
    blocks: list[str] = []
    for component in components:
        name = _value(component.get("component"))
        weight = _value(component.get("weight"), fallback="")
        headline = f"**{name}**" if not weight else f"**{name} ({weight})**"

        details: list[str] = []
        for label, key in [
            ("Format", "format"),
            ("Timing", "timing"),
            ("Individual/Group", "individual_or_group"),
            ("Notes", "notes"),
        ]:
            raw = component.get(key)
            if raw is None or raw == "":
                continue
            details.append(f"- {label}: {_value(raw)}")

        block = headline + ("\n\n" + "\n".join(details) if details else "")
        blocks.append(block)

    return "\n\n".join(blocks)


def _maybe_subsection(heading: str, items: list[str]) -> list[str]:
    """Return [heading, '', bullets, ''] only if items is non-empty.

    This is the auto-hide behaviour: when the cleaner returns an empty
    list (e.g. no Skills section in the source factsheet), the subsection
    disappears rather than rendering 'Not specified'.
    """
    if not items:
        return []
    return [heading, "", _bullets(items), ""]


def render_cleaned_factsheet_markdown(data: FactsheetJSON) -> str:
    """Render student-facing Markdown from cleaned factsheet JSON.

    Sections rendered (in order, all without numbers):
      Course Snapshot · Course Narrative · Learning Objectives ·
      Core Course Content (with subsections) · Assessment and Grading
      (with subsections) · Prerequisites · Source Gaps.

    Sections intentionally NOT rendered:
      - surf_extraction_notes — internal-only, consumed by the SLO extractor.
    """
    snapshot = data.get("course_snapshot", {})
    content = data.get("core_course_content", {})
    assessment = data.get("assessment_and_grading", {})
    title = _value(snapshot.get("course_name"))
    narrative = _value(content.get("narrative_summary"), fallback="")
    lecturers = snapshot.get("main_lecturers") or []

    lines = [
        "---",
        f'title: "{title} - Cleaned Factsheet"',
        "tags:",
        "  - surf/factsheet",
        "  - surf/cleaned",
        "  - course",
        "status: cleaned",
        f'course_code: "{_value(snapshot.get("course_code"))}"',
        f'ects: "{_value(snapshot.get("ects_credits"))}"',
        "---",
        "",
        f"# {title}",
        "",
        "## Course Snapshot",
        "",
        f"- **Course name:** {title}",
        f"- **Course code:** {_value(snapshot.get('course_code'))}",
        f"- **Semester:** {_value(snapshot.get('semester'))}",
        f"- **ECTS credits:** {_value(snapshot.get('ects_credits'))}",
        f"- **Course language:** {_value(snapshot.get('course_language'))}",
        f"- **Main lecturer(s):** {', '.join(lecturers) or 'Not specified'}",
        f"- **Course format:** {_value(snapshot.get('course_format'))}",
        "",
    ]

    if narrative:
        lines += ["## Course Narrative", "", narrative, ""]

    lines += _maybe_subsection("## Learning Objectives", data.get("FSLO", []))

    core_subs: list[str] = []
    core_subs += _maybe_subsection("### Main Topics", content.get("main_topics", []))
    core_subs += _maybe_subsection(
        "### Important Concepts, Models, or Methods",
        content.get("important_concepts_models_methods", []),
    )
    core_subs += _maybe_subsection(
        "### Skills Students Are Expected to Develop",
        content.get("skills_students_are_expected_to_develop", []),
    )
    if core_subs:
        lines += ["## Core Course Content", "", *core_subs]

    assess_subs: list[str] = []
    components = assessment.get("assessment_components", [])
    if components:
        assess_subs += [
            "### Assessment Components",
            "",
            _assessment_bullets(components),
            "",
        ]
    assess_subs += _maybe_subsection(
        "### Exam-Relevant Content", assessment.get("exam_relevant_content", [])
    )
    if assess_subs:
        lines += ["## Assessment and Grading", "", *assess_subs]

    lines += _maybe_subsection(
        "## Prerequisites and Assumed Knowledge",
        data.get("prerequisites_and_assumed_knowledge", []),
    )

    lines += _maybe_subsection("## Source Gaps", data.get("source_gaps", []))

    return "\n".join(lines)
```

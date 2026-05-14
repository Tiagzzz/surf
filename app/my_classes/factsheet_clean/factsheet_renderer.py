"""Surf — factsheet renderer.

Takes the cleaned factsheet JSON (output of factsheet_cleaner.py) and
renders it as student-facing Markdown for display in Streamlit / Obsidian.

Pure Python — no Claude API call. Empty subsections auto-hide instead of
rendering placeholder text. surf_extraction_notes is intentionally NOT
rendered (internal-only — consumed by the future SLO extractor).
"""
from __future__ import annotations

from typing import Any

# The cleaner returns a JSON-like dictionary for all factsheet sections.
FactsheetJSON = dict[str, Any]


# Shared fallback for optional factsheet fields.
def _value(value: Any, fallback: str = "Not specified") -> str:
    """Safe display string. Returns the fallback when value is None or empty."""
    if value is None or value == "":
        return fallback
    return str(value).strip()


# Markdown bullet rendering for list-shaped factsheet sections.
def _bullets(items: list[str]) -> str:
    """Render a list of strings as Markdown bullets."""
    return "\n".join(f"- {_value(item)}" for item in items)


# Assessment components render as readable bullets instead of wide tables.
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


# Empty factsheet arrays should hide their subsection instead of showing filler.
def _maybe_subsection(heading: str, items: list[str]) -> list[str]:
    """Return [heading, '', bullets, ''] only if items is non-empty.

    This is the auto-hide behaviour: when the cleaner returns an empty
    list (e.g. no Skills section in the source factsheet), the subsection
    disappears rather than rendering 'Not specified'.
    """
    if not items:
        return []
    return [heading, "", _bullets(items), ""]


# Public renderer that turns cleaned factsheet JSON into student-facing Markdown.
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

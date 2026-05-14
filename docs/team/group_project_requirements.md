# Group Project Requirements Mapping

This page summarizes how Surf currently covers the project expectations we know about. It is a working team guide, not the final contribution matrix.

## Current coverage rationale

| Requirement area | Surf evidence |
|---|---|
| Interactive app | Streamlit app with seven page flows, forms, buttons, dialogs, uploads, and navigation. |
| Data persistence | SQLite schema with users, classes, lectures, learning objectives, slide pages, questions, attempts, and answers. |
| Course-relevant problem | Converts HSG lecture material and factsheets into study objectives, MCQs, mock exams, and review. |
| External API use | Anthropic Claude API is used through one shared wrapper for factsheet cleaning, learning-objective extraction, and MCQ generation. |
| User-specific workflow | Local profile, class setup, lecture selection, attempt history, and reset/settings behavior. |
| Explainability | Code sidecars plus `docs/team/` explain the architecture, database, prompts, UI, and demo flow. |
| Safety/privacy | Local-first storage, no tracked private DBs, no real API keys in repo files, and approval-gated teacher/demo data. |

## What remains approval-gated

- The final teacher/demo database is documented at recipe level only here. It should be generated later with selected demo data and an explicitly approved capped key path.
- The final teacher package is a later packaging step. `docs/team/` is the team learning folder, not automatically the final package.
- The contribution matrix now exists at `docs/contribution_matrix.md` as a **template only**. The team must still complete and confirm the blank/TBD cells before submission. Do not create a second `docs/team/contribution_matrix.md` unless the final package explicitly needs that copy.
- The final video, Canvas upload, HSG GenAI/reference compliance check, and presentation/Q&A assignments remain pending Tiago/team confirmation.

## Team explanation checklist

Each teammate should be able to explain:

1. why Surf is local-first;
2. how a lecture moves from uploaded PDF to generated questions;
3. how exact-match grading works for multi-select MCQs;
4. why the dashboard only shows real attempt-derived data;
5. where API keys and local data must not appear.

## External tools and functions

- Streamlit: app UI and navigation.
- SQLite: local persistent database.
- Anthropic Claude API: generation provider.
- `pytest` and `ruff`: local verification tools for maintainers.
- `README.md`: public setup and structure guide.

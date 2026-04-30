# Surf — Architecture

This document is the on-repo summary. The canonical, evolving architecture lives in the **Idea & Progress** NotebookLM notebook (latest `Idea vN` source).

## 10 buckets

3 infrastructure buckets + 7 page-aligned buckets:

| Tier | Buckets |
|---|---|
| 1 — Infrastructure | `brain/` · `db/` · `ml/` |
| 2 — User-facing (P1–P7) | `signup/` · `my_classes/` · `class_/` · `mock_take/` · `mock_review/` · `dashboard/` · `settings/` |

Inside each bucket, **one sub-folder per pipeline**. A pipeline is a self-contained flow (e.g. `settings/username_save/`) from trigger to persistence/output.

## Data model (page-first)

Canonical hierarchy: `Class → Lecture → SlidePage → Question → Attempt`.
`Topic` and `LearningObjective` are useful metadata, but **LO extraction is optional/non-blocking**. Coverage = % of saved SlidePages with at least one correct answer on a linked question.

## Stack (locked)

- Python 3.11 + Streamlit (UI)
- SQLite at `~/.surf/user.sqlite` (persistence)
- Anthropic Claude API (LLM-backed pipelines)
- scikit-learn linear regression (6-criteria difficulty model)

## Question type

MCQ only. 4 options + correct index + rationale. True/False and open-ended dropped at the 2026-04-29 pivot.

## Mock-exam mechanics

- **Standard mock:** `5 × N_lectures` questions, lectures picked on P3.
- **Practice mock (Study Next):** for each SlidePage linked to a chosen LO, exactly one question is selected with priority `unseen → previously-wrong → already-correct refresh`.
- Both modes avoid duplicate questions inside a single mock.

## Grading scale (per class)

User picks `P%` needed for grade 4.0 on a slider (default 50%).
- If `s < P`: `grade = 1 + 3 × (s / P)`
- If `s >= P`: `grade = 4 + 2 × ((s - P) / (100 - P))`
- Rounded to the nearest 0.25.
- Raw `correct/total` always stored; grade computed at display time.

## ML — 6-criteria difficulty model

Real ML, scored *post-generation*. Four named criteria: word count, language complexity / readability, distractor similarity, option length variance. Two more TBD during ML implementation. Two consumers: per-question difficulty score (stored with each question) and the P6 strengths/weaknesses radar.

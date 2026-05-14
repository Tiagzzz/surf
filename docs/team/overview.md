# Surf Team Overview

Surf is a local study app that turns class material into mock-exam practice. A student adds a class factsheet, uploads lecture PDFs, generates learning objectives and multiple-choice questions, then takes mock or practice attempts and reviews progress.

## What problem Surf solves

Students often have lecture slides, factsheets, and exam rules in separate places. Surf connects them into one flow:

1. set up a local profile and API key;
2. create a class with its factsheet and grading threshold;
3. upload lectures and generate learning objectives/questions;
4. take standard mocks, red `CUSTOM MOCK >` mocks, or Study Next practice;
5. review answers, see personal difficulty where available, and use dashboard feedback to decide what to study next.

## V1 pages

| Page | What the user does | Main code area |
|---|---|---|
| Signup | saves a local display name and validates an Anthropic API key | `views/signup.py`, `app/signup/` |
| My Classes | creates classes and deletes a class after confirmation | `views/my_classes.py`, `app/my_classes/` |
| Class Hub | uploads lectures, generates study material, starts standard mocks/practice, and offers red `CUSTOM MOCK >` for the currently hardest questions | `views/class_view.py`, `app/class_/` |
| Take Mock / Practice | answers multi-select questions one at a time | `views/take_mock_exam.py`, `app/mock_take/` |
| Review | checks correct, wrong, and skipped answers, with `Difficulty for you: X/100` on review cards when scoring is available | `views/review_mock_exam.py`, `app/mock_review/` |
| Dashboard | shows real attempt-derived progress | `views/dashboard.py`, `app/dashboard/` |
| Settings | replaces the API key or resets local data | `views/settings.py`, `app/settings/` |

## Local-first privacy

Surf stores data on the user's computer in SQLite. The normal repo must not contain real API keys, private databases, uploaded private files, cookies, or generated private data.

The app can call the Anthropic Claude API only when a user provides a valid key. The key is saved locally so generated questions can be created later without asking again.

## How Surf maps to app goals

- **Runnable application:** Streamlit provides the interface and page routing.
- **Persistent data:** SQLite stores classes, lectures, questions, attempts, and answers.
- **Generated content:** prompt-backed pipelines clean factsheets, extract learning objectives, generate MCQs, and ask a second Claude metadata critic for intrinsic difficulty signals.
- **Personal practice:** Custom Mock ranks ready questions by personal wrong-answer risk using stored metadata and completed-answer history, then opens the normal Take Mock flow.
- **Useful analytics:** the dashboard uses completed attempts, not fake demo analytics or placeholder ML widgets.
- **Explainable codebase:** sidecar docs and this folder explain how the main pieces work.

## External tools and Surf functions to know

- `streamlit run streamlit_app.py` starts the app.
- `sqlite3` is the standard-library database engine used through `app/db/connection.py`.
- `app.brain.claude_client.call_claude(...)` is the shared API wrapper for generation.
- `app.ml.personal_difficulty.score_questions(...)` scores personal wrong-answer risk locally from metadata and answer history.
- `app.brain.topbar.render_topbar(...)` and `app.brain.page_header.render_page_header(...)` provide shared page chrome.
- `st.session_state` carries route selections and in-progress attempt state during a browser session.

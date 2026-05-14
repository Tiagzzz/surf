# Demo Script

This is a walkthrough helper for explaining Surf. It does not generate a final video, final package, seeded database, or real demo key.

## Suggested walkthrough

1. **Signup** — explain that the app is local-first and needs an Anthropic API key for generation.
2. **My Classes** — create or open a class, show the factsheet requirement, and explain the grade-4 threshold.
3. **Class Hub** — show lectures, statuses, generated learning objectives/questions, Study Next, the normal mock launch button, and the red `CUSTOM MOCK >` button.
4. **Take Mock / Practice** — answer one multi-select MCQ, skip another if useful, and explain exact-match grading.
5. **Review** — show selected answers, correct answers, rationales, skipped/wrong states, and the `Difficulty for you: X/100` badge if it appears.
6. **Dashboard** — explain that all progress comes from real completed attempts; it does not contain a fake ML/demo widget.
7. **Settings** — show API-key replacement and the reset confirmation concept without using a real shared key.

## What to emphasize

- Surf turns real course material into practice.
- Question generation and factsheet cleaning are centralized through one API wrapper.
- Data is local and private by default.
- Custom Mock chooses up to 10 currently difficult questions for the student, then uses the normal mock-taking screen.
- The P5 personal difficulty badge is recalculated from stored metadata and completed-answer history.
- The dashboard is honest: it does not display fake ML analytics.
- A seeded teacher/demo database can be produced later only through the approval-gated path.

## Safe demo data notes

- Use selected non-private demo lectures and factsheets.
- Do not screen-share real personal keys.
- Do not commit generated private data.
- If a demo key is needed later, use a capped, revocable key only inside the approved final artifact.

## External tools and functions to mention

- Streamlit for the browser app.
- SQLite for local storage.
- Anthropic Claude API for generation.
- `call_claude(...)` as the single generation wrapper.
- `st.navigation` and `st.switch_page` for page flow.

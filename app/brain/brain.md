# `app/brain/` bucket — shared Surf infrastructure

This bucket holds the shared helpers that every page can reuse: saved-user
session checks, the single Anthropic wrapper, grading, question-type taxonomy,
PDF ingestion, shared page layout/header helpers, and the
authenticated topbar. Full pages live in `views/` and app buckets such as
`app/my_classes/`, `app/class_/`, `app/mock_take/`, `app/mock_review/`,
`app/dashboard/`, and `app/settings/`.

## What lives in this bucket

| Folder / file | What it does | Main consumers |
|---|---|---|
| `session/` | Reads the saved local user/key state through query helpers without opening the database at import time. | `streamlit_app.py`, P1/P7/authenticated wrappers |
| `claude_client/` | Single Anthropic Claude API wrapper: `call_claude(...)` for generation and `validate_anthropic_key(...)` for typed-key validation. | Factsheet cleaning, LO extraction, MCQ generation, Signup, Settings |
| `grading_formula/` | Pure exact-match grading and Swiss grade helpers. | Final submit, Review, Dashboard |
| `question_type/` | Canonical provisional question-type slugs, labels, normalization, and validation. | Lecture ingestion, P4/P5 display, P6 type analytics |
| `ingestion/` | Local PDF-to-Markdown extraction and page splitting for lecture/factsheet input. | P2 factsheet setup, P3 lecture upload/generation |
| `theme/` | Shared color/spacing tokens and small CSS helpers. | Shared UI buckets |
| `topbar/` | Fixed authenticated topbar with Surf logo, breadcrumb, Home, and Settings controls. | P2-P7 authenticated pages |
| `page_layout/` | Shared 880px authenticated page rail with 32px horizontal padding. | P2/P3/P6/P7 headers/cards and aligned page surfaces |
| `page_header/` | Shared authenticated header: kicker, title, helper text, escaped HTML. | My Classes, Class Hub, Dashboard, Settings |

Cleanup note: the old empty `routing/` and `state_helpers/` scaffold folders were deleted on 2026-05-13 because the running app uses `streamlit_app.py`, `session/`, and page-owned session keys instead. Recreate a narrow helper folder later only if repeated routing/state code appears.

## How the pieces interact

```text
streamlit_app.py
        │
        ├── session.is_authenticated() / get_saved_user()
        └── Streamlit navigation
                │
                ▼
views/<page>.py
        │
        ├── topbar.render_topbar(...)
        ├── page_layout.page_rail(...)
        ├── page_header.render_page_header(...)
        ├── grading_formula for exact-match and Swiss grade math
        ├── question_type for stored MCQ type slugs
        └── claude_client.call_claude(..., api_key=saved_key)
```

`ingestion/pdf_to_md_v3.py` can also run as a CLI before lecture generation. It
writes Markdown on disk and does not call Anthropic or SQLite.

## Connected pages and buckets

- **Signup** validates a typed Anthropic key before saving local setup data.
- **My Classes** reads the saved user, renders class cards, and passes the saved
  key into factsheet cleaning.
- **Class Hub** uses PDF ingestion, LO extraction, MCQ generation, question-type
  validation, session-only mock/practice launch state, and the shared topbar.
- **Take Mock** uses session-only answer state until final submit, then grading
  helpers score answers and compute the Swiss grade.
- **Review** reads stored attempt rows and uses question-type labels for chips.
- **Dashboard** validates class ownership before aggregate reads, then renders
  real attempt-derived charts and type performance.
- **Settings** validates replacement keys through the wrapper and preserves the
  old key on blank or failed replacement.

## Requirement coverage

| Area | Covered by this bucket |
|---|---|
| Single Anthropic API path | `claude_client.call_claude` and `validate_anthropic_key` |
| Saved-key safety | `session` reads user state; wrapper accepts per-call `api_key`; docs warn never to log keys |
| Exact grading | `grading_formula.is_exact_match`, `compute_swiss_grade`, and `compute_score_summary` |
| Question-type continuity | `question_type` centralizes slugs and display labels without ML wiring |
| Shared authenticated shell | `topbar`, `page_layout`, and `page_header` keep page chrome aligned; page-specific session keys stay in their owning page modules until a shared helper is needed |
| Local ingestion | `ingestion` prepares PDF text/page records before generation |

## Code walkthrough

This bucket-level walkthrough points to the sidecar to read for each code area:

1. Start with `session/session.md` to understand saved-user auth and why imports
   stay database-safe.
2. Read `claude_client/claude_client.md` before changing any prompt-backed
   generation or key-validation flow.
3. Read `ingestion/pdf_to_md_v3.md` and `ingestion/page_splitter/page_splitter.md`
   before changing lecture/factsheet PDF handling.
4. Read `question_type/question_type.md` before changing generation payloads,
   type display, or type analytics.
5. Read `grading_formula/grading_formula.md` before touching final-submit,
   Review, or Dashboard grade math.
6. Read `page_layout/page_layout.md`, `page_header/page_header.md`, and
   `topbar/topbar.md` before changing authenticated page chrome.

## Teammate talking points

- **One API door:** Surf's Claude calls use one wrapper, so saved-key safety,
  prompt caching, and JSON parsing are easier to explain and test.
- **Local-first privacy:** the user key is stored locally, passed into a call
  only when generation needs it, and should never appear in logs or docs.
- **Real data only:** question types, grades, and dashboard analytics come from
  stored questions and completed attempts, not placeholder ML output.

## What could break if changed

- Direct Anthropic SDK calls outside `claude_client` can bypass no-secret and
  prompt-cache safeguards.
- Logging a saved user dict can expose the local plaintext key.
- Changing Swiss grade math can drift Review and Dashboard results.
- Duplicating question-type slugs outside `question_type` can make P4/P5/P6
  disagree after a taxonomy change.
- Adding page-local top padding can fight the fixed topbar and misalign the
  shared page rail.

## Verification commands

```bash
python -m pytest -q tests/test_claude_contract.py tests/test_question_type.py tests/test_page_layout_contract.py tests/test_page_header_contract.py tests/test_topbar_dashboard_breadcrumb.py tests/test_no_secrets_committed.py
ruff check app/brain --no-cache
```

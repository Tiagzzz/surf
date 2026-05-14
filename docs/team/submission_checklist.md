# Submission Checklist

Use this checklist before sharing the repo or building the final teacher handoff package.

## Include in the normal repo

- `streamlit_app.py`, `views/`, and `app/`.
- Sidecar docs beside important app modules.
- `docs/team/` educational docs.
- `README.md`, `requirements.txt`, `pyproject.toml`, `.streamlit/config.toml`, `LICENSE`, safe assets, and `.gitignore`.

## Exclude from the normal repo

No normal tracked development file may contain:

- real Anthropic API keys;
- `.env` files or local auth artifacts;
- private SQLite databases or WAL/SHM files;
- private uploaded lecture/factsheet files;
- generated private user data;
- cookies, browser profiles, or credentials;
- final package artifacts before approval.

Internal planning/history folders, local verification tests, and preview sandboxes stay excluded unless the team makes a later explicit tracking decision.

## Setup and run checks

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Maintainers can also run local verification before final cleanup:

```bash
python -m pytest -q
python -m ruff check .
```

## Data and secret cleanup

Before sharing:

1. check `.gitignore` still excludes databases, secrets, caches, internal planning folders, local tests, previews, and generated package artifacts;
2. run a filename/content sweep for obvious key or database leaks;
3. verify no final teacher/demo database or real key has been created in the normal repo;
4. keep any capped demo key isolated to the later approved final artifact path.

## Approval-gated final package

The final package may later include a seeded teacher/demo database and a capped demo key. That step needs a named file path, selected demo data, key-spend cap, revocation plan, and explicit approval before generation.

## Course submission constraints

| Item | Status | Owner / next action |
|---|---|---|
| Runnable app and resources | pending Tiago/team | Confirm the repo/package includes the app files, requirements, safe assets, setup instructions, and any approved demo resources needed to run Surf. |
| Contribution matrix | template ready; pending Tiago/team | Fill and confirm `docs/contribution_matrix.md` before submission. Do not invent contributions, percentages, GitHub usernames, or member confirmations. |
| Max 4-minute video | pending Tiago/team | Keep the final video at or under 4 minutes; use `docs/team/demo_script.md` as a guide, then trim to the course limit. |
| No AI-generated audio | pending Tiago/team | Use human narration or allowed non-AI audio only; do not submit AI-generated audio. |
| HSG GenAI/reference rules | pending Tiago/team | Verify the final repo/video/package follows the current HSG GenAI and reference/citation rules before upload. |
| Canvas deadline and buffer upload | pending Tiago/team | Upload before the known 2026-05-14 23:59 Canvas deadline with a safety buffer; confirm the final course page has not changed the deadline. |
| Final presentation and Q&A logistics | pending Tiago/team | Confirm who presents which parts, who answers technical questions, and what files/screens are available for the presentation/Q&A. |

## AI-use note handling

`handoff_artifacts/AI_USE_NOTE.md` remains an ignored/local handoff artifact for now. Do not publish or copy it into `docs/team/` automatically. Include or adapt it only if Tiago/team decide the final package needs an AI-use note.

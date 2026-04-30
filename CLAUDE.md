# Surf — Repo Claude Config

> **Auto-loaded by Claude Code at session start in `~/surf/`.** Code-focused — for day-to-day work in this repo.
> For deep project context (full architecture, decision log, deadlines, grading, communication preferences), see the **vault `CLAUDE.md`** at `~/CS/CLAUDE.md` (and its mirror `~/CS/AGENTS.md` for Codex).

---

## 0. SESSION PROTOCOL

1. **Read `docs/idea_v1.md`** for the canonical project state (locked 2026-04-29; future changes land as `docs/idea_v2.md` etc.).
2. **For grading / deadline / communication-style questions** → vault `~/CS/CLAUDE.md` is the deeper authority.
3. **For "what changed lately?"** → check NotebookLM Idea & Progress notebook (https://notebooklm.google.com/notebook/3e02fa3d-8ce2-4a6d-9da7-ac974e32452f) for new Idea versions or Decision Log entries that may have landed since `docs/idea_v1.md` was committed.
4. **Default posture for ambiguous requests:** reformulate and confirm before starting (per `~/CS/CS_Obsidian/CS_EN_VF/setup/tiago_guidelines.md`).

---

## 1. PROJECT IDENTITY (short)

| Field | Value |
|---|---|
| Name | **Surf** — Adaptive HSG Study Companion |
| Course | HSG FS 2026 — FCS-BWL (Computer Science for Business) |
| Stack | Python 3.11 · Streamlit · SQLite (stdlib `sqlite3`, no ORM) · Anthropic Claude API |
| Submission | Canvas, by **2026-05-14 23:59** (buffer 2026-05-13 — Auffahrt collision) |
| Team | Tiago, Nikita, Cons, Juliette, Jojo |

Full constraints + the 8 graded requirements: see `docs/idea_v1.md` §2 + §9.

---

## 2. CODE ORGANIZATION — 10 buckets

Every Surf module lives in one of 10 buckets, organised one **sub-folder per pipeline**. Spec: `~/CS/CS_Obsidian/CS_EN_VF/setup/code_buckets.md`.

| Tier | Bucket | Owns |
|---|---|---|
| Infra | `app/brain/` | `claude_client/`, `ingestion/`, `topbar/`, `session/`, `grading_formula/`, `routing/`, `state_helpers/` |
| Infra | `app/db/` | `schema/`, `migrations/`, `queries_users/`, `queries_classes/`, `queries_lectures/`, `queries_pages/`, `queries_questions/`, `queries_attempts/` |
| Infra | `app/ml/` | `training_pipeline/`, `dataset_labels/`, `model_artifact/`, `inference_per_question/`, `radar_features/` |
| Page | `app/signup/` | P1 |
| Page | `app/my_classes/` | P2 — includes already-shipped `factsheet_clean/` pipeline |
| Page | `app/class_/` | P3 (`class_` with trailing `_` because `class` is a Python keyword) |
| Page | `app/mock_take/` | P4 |
| Page | `app/mock_review/` | P5 |
| Page | `app/dashboard/` | P6 |
| Page | `app/settings/` | P7 |

Streamlit page wrappers live in `views/` (one thin file per page; renamed from `pages/` to avoid Streamlit auto-discovery collision with `st.navigation()`).

---

## 3. ALREADY-BUILT PIPELINES (do NOT re-implement)

The factsheet-clean pipeline shipped end-to-end on 2026-04-30:

- **`app/brain/claude_client/claude_client.py`** — shared Anthropic API wrapper. **Every Claude call goes through this.** Prompt caching enabled by default.
- **`app/brain/ingestion/pdf_to_md_v3.py`** — PDF → MD with `--- PAGE N ---` markers (per Idea v1 A3) [TODO: marker injection still pending — currently emits `# Page N`].
- **`app/my_classes/factsheet_clean/`** — system prompt (`.md`) + cleaner (10-line wrapper around `claude_client`) + renderer (pure Python, JSON → student-facing MD).

Each script has a sibling `.md` doc. **When extending or reusing**, read the `.md` first.

---

## 4. CONVENTIONS

### Branches & commits
- Solo iteration: direct push to `main` is OK for small fixes
- Anything reviewed (self or team): branch `feature/<short-name>`, push, open PR
- Atomic commits per logical unit; commit message = imperative + body
- All commits include `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` when Claude generated them

### Imports across buckets
- Every bucket folder is a Python package (has `__init__.py`)
- Specialist scripts use proper package imports: `from app.brain.claude_client import call_claude`
- The `__init__.py` in `app/brain/claude_client/` re-exports `call_claude` for clean import paths

### Linting & tests
- Ruff config in `pyproject.toml` (E/F/I rules, line-length 100, target py311)
- Run lint: `ruff check .`
- Run tests: `pytest -q` (smoke test in `tests/test_smoke.py`; per-module skip when optional deps missing)
- CI workflow not yet set up — defer until ~2 days before submission

### Claude API pattern
Every Claude-backed script follows the same shape (~10 lines):

```python
from pathlib import Path
from app.brain.claude_client import call_claude

_SYSTEM_PROMPT = Path(__file__).with_name("<this_script>_system_prompt.md")

def <verb>_<noun>(input_text: str) -> dict:
    return call_claude(
        system_prompt=_SYSTEM_PROMPT.read_text(),
        user_message=input_text,
        expect_json=True,
    )
```

The system prompt lives as a `.md` file next to the script — editable without touching Python. Prompt caching is enabled by default in `call_claude` (5-min TTL on the system block).

---

## 5. FILE LOCATIONS — quick lookup

| Looking for… | Path |
|---|---|
| Canonical project state | `docs/idea_v1.md` |
| Code-bucket spec | `~/CS/CS_Obsidian/CS_EN_VF/setup/code_buckets.md` |
| Communication rules | `~/CS/CS_Obsidian/CS_EN_VF/setup/tiago_guidelines.md` |
| Vault CLAUDE.md (deep context) | `~/CS/CLAUDE.md` |
| Vault AGENTS.md (Codex equiv) | `~/CS/AGENTS.md` |
| Session work logs | `~/CS/CS_Obsidian/CS_EN_VF/work_log/` |
| Test factsheets | `~/CS/Factsheets/FS_Flagged/` |
| Cleaned factsheet outputs | `~/CS/Factsheets/FS_Cleaned/` |

---

## 6. RULES CLAUDE MUST FOLLOW (repo-scoped)

1. **Read `docs/idea_v1.md` before claiming anything is "locked"** — only what's in v1 (or in a later Decision Log) is locked. Everything else is open.
2. **Don't re-implement shipped pipelines** — extend `claude_client`, the factsheet cleaner/renderer, and `pdf_to_md_v3.py` rather than building parallel versions.
3. **System prompts are `.md` files next to their script** — never inline a multi-line system prompt in Python.
4. **`from app.brain.claude_client import call_claude`** — never re-instantiate `Anthropic()` directly in specialist scripts.
5. **No SQLAlchemy or other ORMs** — stdlib `sqlite3` only (Idea v1 §2 — SQLAlchemy not taught in the course).
6. **No AI-generated audio** in the submission video (Idea v1 §2).
7. **Cite course slides** when applying course-aligned methods (e.g. `[6. Machine Learning, slide 77]`) — graders will spot non-course methods otherwise.
8. **Honesty charter:** no sycophancy, quantify risks, name rejected alternatives, preserve dissent.

---

**End of repo `CLAUDE.md`.** Deeper context: `~/CS/CLAUDE.md`. Canonical state: `docs/idea_v1.md`.

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

# Surf — Project-specific instructions

## Source of truth

- **Canonical project state:** [docs/idea_v1.md](docs/idea_v1.md) (mirrors NotebookLM Idea v1, source `a815d393-1f9f-4ac1-841c-09f5c23bc285`).
- **Deep context** (grading rubric, deadlines, full architecture, communication style): vault `~/CS/CLAUDE.md` and `~/CS/AGENTS.md` (Codex equivalent).
- **Communication rules:** `~/CS/CS_Obsidian/CS_EN_VF/setup/tiago_guidelines.md` — non-negotiable; describes Tiago's working style. Read first.

## NotebookLM workflow (non-negotiable — team alignment)

Two project notebooks must stay current. The rest of the team reads from them.

- **Lectures** — id `6bc919e0-21c9-452e-b203-507f078efa33` (read-only). Reference for *how the class teaches us to do things*. Query before introducing a new pattern (sqlite usage, Streamlit idioms, prompt structure, etc.) so the implementation stays course-aligned.
- **Idea & Progress** — id `3e02fa3d-8ce2-4a6d-9da7-ac974e32452f` (shared with team; read + write). Source of truth for requirements, decisions, and progress.

**Read pattern:** before planning or implementing, query the relevant notebook with `nlm-query` skill conventions (surgical source filtering, the four prompt templates).

**Write-back pattern (Idea & Progress only).** Trigger when a phase/plan completes, a key decision changes, a TBD resolves, an architecture choice is locked, or a milestone ships:

1. **Add a work-log source** — short markdown summarising what changed, when, and why. Use `mcp__notebooklm-mcp__source_add` (`source_type=text` for inline, `file` if a doc already lives in the repo).
2. **Archive stale sources** — sources superseded by the new work log are removed from Idea & Progress and copied to `docs/archive/notebook_sources/<YYYY-MM-DD>_<source-name>.md` so history survives.
3. **Filename convention** — apply the `nlm-new-notebook` skill's force-sort filenames so sources stay chronological.

**Mandatory:** read the `nlm-new-notebook` and `nlm-query` SKILL.md files before any nlm tool call (per global SKILL-READ-RULE).

## Hard constraints (non-negotiable per Idea v1)

- Python 3.11 + Streamlit only (no Flask, FastAPI, Django).
- Anthropic Claude API only (no OpenAI).
- SQLite via Python stdlib `sqlite3` — **no SQLAlchemy or any ORM** (not taught in the course).
- **No AI-generated audio** in the submission video.
- Submission deadline: **2026-05-14 23:59 Europe/Zurich** (buffer-upload **2026-05-13** — Auffahrt collision).

## Code organization (10 buckets, one sub-folder per pipeline)

`app/<bucket>/<pipeline>/`

- **Infra:** `brain/`, `db/`, `ml/`
- **Pages (P1–P7):** `signup/`, `my_classes/`, `class_/` (trailing `_` — `class` is a Python keyword), `mock_take/`, `mock_review/`, `dashboard/`, `settings/`
- Streamlit page wrappers in `views/` (one thin file per page).
- Naming: `lower_snake_case`, verb-driven (`username_save`, not `username`).
- Full spec: `~/CS/CS_Obsidian/CS_EN_VF/setup/code_buckets.md`.

## Already shipped — do NOT re-implement

- `app/brain/claude_client/claude_client.py` — single shared Anthropic wrapper. **Every Claude call goes through this** (`from app.brain.claude_client import call_claude`). Prompt caching enabled by default.
- `app/brain/ingestion/pdf_to_md_v3.py` — PDF → MD. (TODO: `--- PAGE N ---` marker injection per Idea v1 A3 still pending.)
- `app/my_classes/factsheet_clean/` — system prompt + cleaner (10-line wrapper) + renderer (pure Python, no API).

Each script has a sibling `.md` doc — read it before extending.

## The standard Claude-call pattern (~10 lines)

```python
from pathlib import Path
from app.brain.claude_client import call_claude

_SYSTEM_PROMPT = Path(__file__).with_name("<script>_system_prompt.md")

def <verb>_<noun>(input_text: str) -> dict:
    return call_claude(
        system_prompt=_SYSTEM_PROMPT.read_text(),
        user_message=input_text,
        expect_json=True,
    )
```

System prompts live as sibling `.md` files — editable without touching Python.

## Test + lint

```bash
pytest -q          # smoke test in tests/test_smoke.py (skips on missing optional deps)
ruff check .       # config in pyproject.toml (E/F/I, line 100, py311)
```

## Visual preview gate (non-negotiable for Phase 2+)

Every plan task that creates or modifies a visual element or page must ship a **preview gate** alongside the production code. Code review of Streamlit visuals is unreliable; only a running preview tells the truth.

**Sandbox isolation — non-negotiable:**

Previews live in `previews/` at the repo root, **outside `app/`**. Previews must NOT import from `app/`. When you need production code in a preview, **copy** the file(s) into the sandbox — don't reach into `app/` at runtime. Closed sandboxes mean a preview can never accidentally touch the user's real DB, real API key, or real session.

**Structure:**

- `previews/` — top-level folder, sibling of `app/`.
- `previews/_fixtures.py` — shared **pure data** (Python dicts/lists for fake user, class, mock, MCQs, attempts). No imports from `app/`. Sandboxes import this OR copy from it — either is fine.
- `previews/components/<component>/` — one sandbox per reusable visual component (`card/`, `mcq_card/`, `timer_header/`, `ingestion_log/`, `factsheet_renderer/`, etc.). Each sandbox contains: a copy of the production component code, any helpers it needs (also copies), and a `preview.py` entry point.
- `previews/pages/<page>/` — one sandbox per page (`p1_signup/`, `p2_my_classes/`, `p3_class_hub/`, `p4_take_mock/`, `p5_review_mock/`). Each sandbox copies the page wrapper plus its component dependencies, then composes them in `preview.py`.

**Sandbox rules:**

- No `from app...` imports inside any `previews/` file. (Enforce with a ruff rule or smoke check.)
- No real Anthropic calls — sandboxes use stubbed responses (a fake `call_claude` returning hard-coded JSON).
- No real DB — sandboxes use `:memory:` SQLite or fixture dicts.
- Sandbox copies drift from `app/` deliberately. When a production component changes meaningfully, the next visual task on that component refreshes the sandbox copy and re-runs the preview gate. Drift is a feature: it forces a re-approval cycle.

**Per-task acceptance criteria must include:**

1. The sandbox path being created/updated (e.g., `previews/components/mcq_card/`).
2. The exact `streamlit run previews/.../preview.py` command Tiago runs.
3. The line: "Tiago has visually approved the preview" — task is NOT done without this.

**Atomic commits:** production code + sandbox updates land in the same commit.

**Out of scope for the gate:** infra-only tasks (DB schema, ingestion glue, claude_client wrappers) that ship no visible UI. Those follow normal verification.

## Branch + commit

- Solo work: direct push to `main` is OK for small fixes.
- Anything reviewed: `feature/<short-name>` branch + PR.
- Atomic commits, imperative subject + body.
- Add `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` when Claude generated the change.

# FigJam diagram specs

Source-of-truth JSON specs that describe FigJam diagrams of the Surf codebase. The specs are tool-agnostic — **Claude writes them, Codex renders them.**

## Why a spec layer

- The spec is **deterministic, reviewable, and diff-able** in git. The rendered FigJam canvas isn't.
- The same spec can drive re-renders across iterations without re-explaining intent.
- Verification (every required FK / table / connector present) runs against the spec, not the canvas.
- **Separation of concerns:** Claude knows the code; Codex knows FigJam layout. Neither has to be good at the other.

## Spec format (v1 — canonical)

Specs are pure semantic descriptions: what to show + how things connect + what to call out. **No visuals** (no colors, no x/y, no card-type strings, no fonts, no labeled connectors). Codex picks all of that.

### Top-level fields

| Field | Required | Purpose |
|---|---|---|
| `spec_version` | yes | Currently `1`. Bump if vocab changes. |
| `diagram_id` | yes | Stable id (e.g. `lecture_ingestion_v1`). |
| `title` | yes | Human-readable diagram title. |
| `purpose` | yes | One sentence: what story this diagram tells. Codex uses this to set tone. |
| `audience` | yes | Who reads this. Default: "non-engineer teammates and the grading teacher". |
| `linked_sidecars` | yes | Repo-relative paths to `.md` files Codex pulls richer text from. |
| `groups` | optional | Logical groupings; `id` + `label`. Codex draws section frames. |
| `nodes` | yes | The boxes. See vocab below. |
| `edges` | yes | The arrows. See vocab below. |
| `verification` | yes | Self-check list — Claude validates before handoff; Codex echoes back at render. |

### Node vocab (`kind`)

Closed set. Codex maps each `kind` to a reusable FigJam card.

`file_input`, `file_output`, `script`, `function`, `claude_call`, `claude_prompt`, `db_table`, `db_column`, `db_write`, `db_read`, `ui_page`, `external_api`, `decision_point`

Each node: `id`, `kind`, `label`, optional `group`, optional `description` (sticky-note text).

### Edge vocab (`kind`)

Closed set. Codex picks arrow style; **edges never carry visible labels**.

`consumes`, `produces`, `reads`, `writes`, `calls`, `foreign_key`, `depends_on`, `triggers`

Each edge: `from`, `to`, `kind`, optional `description` (sticky note placed near the arrow).

## When specs are written

End of each wave. Each spec lives at `docs/figjam_specs/phase_<NN>/<NN>_<name>.json`.

## Diagram catalog

### Phase 1 (`phase_01/`) — written 2026-05-01

| # | File | Story |
|---|---|---|
| 1 | `01_db_structure.json` | The 8 SQLite tables + columns + foreign keys |
| 2 | `02_lecture_ingestion.json` | The 5-stage lecture pipeline (orchestration view) |
| 3 | `03_claude_calls_in_ingestion.json` | Zoom into the LO + MCQ Claude calls (inputs, prompts, retry, validation, failure policies) |
| 4 | `04_factsheet_pipeline.json` | The smaller factsheet pipeline — clean (Claude) + render (pure Python) |
| 5 | `05_claude_api_layer.json` | The shared `claude_client` wrapper + 10-line caller pattern (GLOBAL — updated each phase) |
| 6 | `06_query_layer.json` | The 6 `queries_*` modules — every read/write boundary |
| 7 | `07_end_to_end_overview.json` | The elevator-pitch diagram — everything Phase 1 ships, ready for Phase 2 to plug into |

### Pre-spec drafts (kept for history)

- `db_structure_v1_draft.json` — first attempt at the DB diagram on 2026-05-01 (had layout coordinates + style hints; superseded by `phase_01/01_db_structure.json` once we settled on the visuals-free format).

## Claude → Codex handoff

End of each wave:

1. Claude writes the JSONs to `docs/figjam_specs/phase_<NN>/`.
2. Claude runs the `verification[]` checklist against the spec and the live code.
3. Hand the JSON + the linked sidecars to Codex with one instruction: *"render this in FigJam".*
4. Codex picks layout, cards from the reusable library, sticky placement, grouping frames.

## Open work

- First end-to-end render with Codex (validates the format under load).
- If the closed `kind` vocab needs extension for Phase 2+ (e.g. ML pipeline shapes), add additively and bump `spec_version`.

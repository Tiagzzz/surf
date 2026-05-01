# FigJam diagram specs

Source-of-truth JSON specs that describe FigJam diagrams of the Surf codebase. The specs are tool-agnostic — Codex (or any other renderer) consumes them to produce the actual FigJam canvas.

## Why a spec layer

- The spec is **deterministic, reviewable, and diff-able** in git. The rendered FigJam canvas isn't.
- The same spec can drive re-renders across iterations without re-explaining intent.
- Verification (every required FK / table / connector present) runs against the spec, not the canvas.

## Files

- `db_structure_v1_draft.json` — the DB schema visualization spec used in the first pass on 2026-05-01. Contains: 8 tables × columns, 9 FK connectors (incl. `learning_objectives → slide_pages`), layout coordinates, style references to the FigJam reusable cards, verification checklist. **Format is not yet locked — to be refined with Codex at the start of Phase 2.**

## Open work (Phase 2 kickoff)

- Decide on the canonical spec format (fields, optional vs required, layout strategy, naming convention).
- Decide which artefacts get a spec (DB only? per-pipeline? per-phase?).
- Decide when in the workflow specs are written (end-of-phase? end-of-wave?).
- Codex consumes the spec via its FigJam-creation tool; agree on the contract.

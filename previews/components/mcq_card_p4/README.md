# `previews/components/mcq_card_p4/` — full P4 Take Mock card sandbox

**Status:** sandbox-only exploration ahead of plan 02-05's formal start. NOT plan execution. NOT a production code change. Lives entirely under `previews/` and does not modify anything under `app/`.

## How to run

From the repo root:

```bash
streamlit run previews/components/mcq_card_p4/preview.py
```

## What it demonstrates

One MCQ card rendered in production-like P4 composition:

1. **Question header** — Q-chip + class chip + 5-slot difficulty stars (`difficulty_stars()` rendering; demos cycle through 0.62 → 3 stars, 0.18 → 1 star, 0.45 → 2 stars).
2. **Question text** — Serif/H2 (Fraunces SemiBold Italic 28/115%/-1%) per the locked Figma type scale.
3. **Meta line** — `P4 · Q{n} of {total} · {lecture}` in mono caps-tracked grey.
4. **4 options A–D** — single-select (radio behaviour with the locked custom 20×20 checkbox glyph). Clicking a new option live-deselects the previous one. The Off→On animation runs through the existing `:has(input:checked)` rule (D-2.20a).
5. **Rationale block** — hidden until Submit. Revealed inline below the options inside a `card-passive-rationale` wrapper, with an eyebrow line indicating the verdict ("CORRECT ✓" or "NOT QUITE") and italic-grey caption pointing at the production data source (`questions.rationales_per_option_json`).
6. **Action row** — three buttons pre-submit, one full-width post-submit:
   - **Pre-submit:** `[Clear] [Skip] [Submit]` — Clear is disabled until something is picked; Submit is disabled until something is picked; Skip is always enabled.
   - **Post-submit:** `[Next question]` (full-width).
7. **Three demo questions** cycled by Skip / Next so the full state machine is walkable: unanswered → selected → submitted-correct OR submitted-incorrect → next.

### State machine demonstrated by clicking

| State | How to reach it | What renders |
|---|---|---|
| **unanswered** | First load, or after Skip / Clear / Next | All 4 options Off; Submit + Clear disabled; Skip enabled; rationale hidden |
| **selected (pre-submit)** | Click any option | Picked option flips to On (paper-0 bg, 2 px border, 2 px stamp, 14/15 padding via D-2.20a); Submit + Clear become enabled |
| **selected — different option** | Click a second option | First option auto-deselects, second option flips to On (radio behaviour) |
| **submitted-correct** | Pick correct option → Submit | Picked option paints `mcq-opt-…-correct` (mint-wash bg + ok border + stamp); rationale block reveals; action row collapses to single full-width Next |
| **submitted-incorrect** | Pick wrong option → Submit | Picked option paints `mcq-opt-…-incorrect` (accent-soft bg + accent-deep border + stamp); the actually-correct option ALSO highlights as `-correct` so the user sees what was right; rationale reveals; action row collapses to Next |
| **next / skip** | Click Next or Skip | Card resets to a fresh unanswered question (cycles through 3 demos) |

## Design choices made (defensible defaults where the spec was ambiguous)

### 1. Action row — `[Clear] [Skip] [Submit]` pre-submit, `[Next question]` post-submit

The brief asked for `Skip / Submit / Next`. The locked spec sources said:

- **D-2.23 (CONTEXT):** P4 footer is `[Clear] [Clear] [Submit/REST]` — two Ghost Clears + one Default Submit. Post-submit collapses to a single full-width `[REST]`.
- **02-FIGMA-RESEARCH.md line 524:** Phase-3 cleanup ticket — "P4 Quizz card fix: 5 options → 4 options + `CLEAR` button → `SKIP` button (Idea v1 §3 P4)." Idea v1 is canonical.

**Synthesis applied here:** pre-submit row carries one `Clear` (deselect, no advance) + one `Skip` (advance without answering, write `selected_indices=NULL`) + one `Submit` (lock + reveal rationale). Honours both D-2.23's three-button layout AND Idea v1's "Skip not Clear" naming, and gives Skip and Clear semantically-distinct affordances (Idea v1 only listed "Skip" so the Clear button as a sibling is the gentlest interpretation of D-2.23's "two Ghost slots"). Post-submit row collapses to a single full-width button labelled `Next question` — D-2.23 calls this `[REST]`; the brief calls it `[Next]`. Same affordance, different label. **Decision deferred to plan 02-05** — the next plan picks the final label and bakes either choice into production.

### 2. Single-select with checkbox glyph (radio behaviour, locked checkbox visual)

D-2.20 locks the custom 20×20 checkbox glyph for ALL MCQ options, even single-correct questions. P4 take-mock uses single-correct, so I needed radio behaviour (only-one-checked) with the checkbox visual.

**Pattern used:** one session-state key (`selected: 'A' | 'B' | 'C' | 'D' | None`); each option's `st.checkbox(value=)` is computed from `selected == letter` on every rerun; an `on_change` callback writes the new letter to session state. No `key=` carrying state across reruns on the checkboxes themselves — a per-render `key=f"_cb_q{q}_{letter}_{submitted}"` prevents Streamlit's "the key already has a value" complaints when the disabled state changes.

**Why not `st.radio`:** `st.radio` renders BaseWeb radio circles that the locked design system specifically replaces with the checkbox glyph (D-2.20). Restyling a radio's circle into a square-with-checkmark via CSS is fragile across Streamlit versions; the checkbox+session-state pattern is more durable.

### 3. Rationale data source

This sandbox uses ONE rationale per question for simplicity. Production (Plan 02-05 / 02-06) pulls `rationales[selected_index]` from `questions.rationales_per_option_json` so each option carries its own tailored rationale (Phase 1 D-2.6). The sandbox's caption line under the rationale block points at the production source so plan-02-05 has the pointer.

### 4. Difficulty stars hard-coded per demo

Each demo question carries a `difficulty_score` (0.62 / 0.18 / 0.45) so Tiago sees the chip change as he cycles. Production (Phase 4 ML) writes the real score; the function signature is identical.

## Sandbox isolation (CLAUDE.md)

Zero `from app...` / `import app...` lines. The mechanical enforcement test is `tests/test_no_app_imports_in_previews.py`.

### Files

```
previews/components/mcq_card_p4/
├── README.md          ← this file
├── preview.py         ← sandbox entry (single Streamlit page)
├── _theme.py          ← byte-for-byte copy of app/brain/theme/theme.py
├── _fixtures.py       ← byte-for-byte copy of previews/_fixtures.py
├── _difficulty.py     ← copy of app/mock_take/question_render/_difficulty.py
│                        with ONE intentional drift: `_ICONS_DIR` resolves
│                        to this folder instead of <repo>/assets/icons/ so
│                        the sandbox is fully self-contained.
├── star_filled.svg    ← copy from assets/icons/
└── star_empty.svg     ← copy from assets/icons/
```

The `_difficulty.py` drift is the only deviation from byte-equality across the copies. The drift is documented in the file's docstring + here. CLAUDE.md sandbox-rules permit drift; the bench-isolation test only enforces "no `from app...`".

## Out of scope (NOT in this sandbox)

- Real Anthropic calls — no LLM call is made; rationales are hard-coded per question.
- DB writes — no SQLite touched. Production session-state ↔ DB sync (UPSERT on Next/Prev/Skip per D-3.3) is plan 02-05's job.
- Topbar / navigation chrome — only the card itself. Plan 02-05 composes the card inside a topbar + page header + per-mock progress indicator.
- The `-correct`/`-incorrect` review states ON OPTIONS NOT PICKED post-submit (P5 review behaviour, plan 02-06 territory). This sandbox does highlight the correct option even when not picked so the user can see the right answer — a reasonable approximation of P5 behaviour, but plan 02-06 owns the final review-screen design.
- Multi-correct questions (Phase 1 D-2.5 schema supports them; this sandbox is single-correct only).

## Questions surfaced for plan 02-05

1. **Final action-row label:** `Clear / Skip / Submit` then `Next question`, OR the D-2.23 verbatim `Clear / Clear / Submit` then `[REST]`? The synthesis above is the executor's defensible default; plan 02-05 should lock the actual labels.
2. **Skip semantics:** D-3.1 says SKIP is "advance-only, returnable". This sandbox advances on Skip and resets the card; production needs to also write `selected_indices=NULL` to `attempt_answers` AND make Prev/Skip return-able (so the user can revisit a skipped question). Plan 02-05 design.
3. **Correct-option highlight on submitted-incorrect:** this sandbox highlights the correct option (mint-wash + ok border) AT SUBMIT TIME so the user sees what was right, even though they're still on P4. The plan/Figma may want this only on P5 review. Plan 02-05 calls it.
4. **Rationale rendering location:** this sandbox shows the rationale inline under the action row in a `card-passive-rationale` wrapper. Plan 02-06 spec says rationale is rendered inline UNDER EACH OPTION on P5. P4 may want the same per-option treatment, OR a single block, OR no rationale at all on P4 (push to P5 only). Plan 02-05/02-06 boundary decision.
5. **Disabled-button styling vs the locked stamp shadow:** Submit disabled = `--paper-2` bg + `--paper-3` text + no shadow per D-2.13. Verify visually that disabled Clear / Submit don't fight the active Skip in the row. (The bench rendered disabled buttons in isolation; this is the first time three buttons sit side-by-side with mixed enabled/disabled states.)

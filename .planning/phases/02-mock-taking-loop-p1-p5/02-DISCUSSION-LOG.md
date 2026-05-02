# Phase 2: Mock Taking Loop (P1–P5) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `02-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-05-02
**Phase:** 02-mock-taking-loop-p1-p5
**Areas discussed:** UI design system lock, Page-flow UX, P4 Take Mock runtime, P5 Review + PRACTICE picker, Sidecar walkthrough structure

---

## Pre-discussion gate — fold widget-catalog todo

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — fold it | CONTEXT.md captures the sequence: UI design lock → widget catalog research → plans 02-xx → execution. Todo file moved to done after CONTEXT is written. | ✓ |
| No — keep separate | Leave todo in pending; plans link to it but CONTEXT doesn't bind sequence. | |

**User's choice:** Folded, with operational rules attached.
**Notes:** User added two operational requirements: (1) sequence is binding (discuss → research → lock); (2) every locked visual ships with an "edit-this-later" note explaining where it lives, what to change, and how the swap propagates.

---

## Area 1 — UI design system lock (P1–P5)

### Q1.1 — Visual identity

| Option | Description | Selected |
|--------|-------------|----------|
| Academic / professional | HSG-aligned, neutral palette, restrained. Lowest cost. | |
| Study-buddy / friendly | Warm accent, rounded cards, gentle motion. Notion/Quizlet feel. | |
| Minimal / focused | Strict monochrome + one accent, generous whitespace, near-zero motion. | |
| I'll describe it (or drop a reference) | Freeform vision. | ✓ |

**User's choice:** Freeform — has a Figma file.
**Notes:** User shared `https://www.figma.com/design/EYjkvHArrBonuiG2JUS2sE/SURF_UI?node-id=25-2`. Initial Figma MCP tools failed with "session expired"; user restarted Claude Code; tools surfaced. Selection-based tools (`get_design_context`, `get_metadata`, `get_variable_defs`) require Figma desktop selection; URL-based tools (`get_screenshot`, `search_design_system`, `get_libraries`) work without selection. Reading via `search_design_system` revealed library `SURF_UI(old)` containing: 6-step Paper ladder + 3-tone Accent (Soft/Deep/Wash) + Status colors + Mono/Button Label text style + 5 button variants + 2 card containers. Aesthetic read: editorial / paper / writing-tool (iA Writer / Are.na territory).

### Q1.2 — Light/dark/auto

| Option | Description | Selected |
|--------|-------------|----------|
| Light only (recommended) | Saves Phase 2 scope. P7 Settings can add toggle later. | ✓ |
| Light + Auto-follow OS | Risk: monospace + Paper palette doesn't auto-invert cleanly. | |
| Light + custom dark theme | +1 plan to derive and test. | |

**User's choice:** Light only.

### Q1.3 — Motion policy (asked twice — first was a clarifying question)

| Option | Description | Selected |
|--------|-------------|----------|
| Near-zero motion | Streamlit defaults only. | |
| Subtle (the realistic ceiling) | CSS hover transitions, fade-in, button press feedback. | ✓ |
| Match Figma exactly | Mirror Figma prototype reactions. | |

**User's choice:** Subtle.
**Notes:** First-pass answer was a question: "Is it compatible with Streamlit custom CSS or other Streamlit elements?" Claude answered with a compatibility table (✅ hover / fade / press feedback; ❌ page transitions / confetti / counter rollups / scroll-anim). User then chose "Subtle (the realistic ceiling)".

### Q1.4 — Layout density

| Option | Description | Selected |
|--------|-------------|----------|
| Roomy / generous whitespace | Matches editorial aesthetic. | ✓ |
| Standard Streamlit defaults | Lower design effort, more "data-tool" feel. | |
| Dense / information-rich | Off-aesthetic. | |

**User's choice:** Roomy.

---

## Area 2 — Page-flow UX (factsheet review + ingest progress + Build Mock)

### Q2.1 — P2 factsheet review

| Option | Description | Selected |
|--------|-------------|----------|
| Side-by-side: raw JSON / rendered Markdown | Two columns. | |
| Rendered Markdown only + 'Show raw JSON' expander | Cleaner UX for non-technical users. | ✓ |
| Editable JSON form | More cost. Defer to Phase 3. | |
| Read-only confirm only | Lowest ceiling. | |

**User's choice:** Rendered Markdown only.

### Q2.2 — P3 ingest progress UX

| Option | Description | Selected |
|--------|-------------|----------|
| `st.status` with live log lines | Streamlit-native, zero custom JS. | ✓ |
| Single spinner + 'This may take a few minutes' caption | Cheap. | |
| Custom progress bar per stage | Hard to compute meaningful percentages. | |

**User's choice:** `st.status` with live log lines.

### Q2.3 — P3 tab-close during ingestion

| Option | Description | Selected |
|--------|-------------|----------|
| Backend keeps running, partial-done on next visit | Phase 1 D-4.5 already supports this. | ✓ |
| Block tab-close with `beforeunload` | Banned (needs hacky JS). | |
| 'In progress on another device' check | Single-device app, can't happen. | |

**User's choice:** Backend keeps running.

### Q2.4 — Mock entry points (Standard vs PRACTICE switcher)

| Option | Description | Selected |
|--------|-------------|----------|
| Two large action cards side-by-side | Cards reveal selectors. | |
| Segmented toggle at top | [Standard | Practice] pill. | |
| Tabs (st.tabs) | Native, less editorial. | |

**User's choice:** Freeform — re-scoped to two ENTRY POINTS:
1. "Generate Mock" button on P3 → asks for lectures → builds mock.
2. "Study Next" card (in sidebar per Q2.6) → tap → mock focused on the surfaced LO.

**Notes:** User REVISED MECH-02 here. Original spec said "user picks one LO" for PRACTICE mock. Revised: Study Next picks the LO; no manual LO picker UI exists. Captured as REQUIREMENTS.md amendment #1.

### Q2.5 — Lecture multi-select pattern (Generate Mock flow)

| Option | Description | Selected |
|--------|-------------|----------|
| Clickable lecture cards with selected-state border | Uses Card Interactive from Figma. | ✓ |
| Checkboxes next to lecture names | Plain st.checkbox. | |
| `st.multiselect` dropdown | Hides metadata, off-aesthetic. | |

**User's choice:** Clickable Card Interactive.

### Q2.6 — Past Attempts + Study Next placement

| Option | Description | Selected |
|--------|-------------|----------|
| Sidebar (st.sidebar) for both, main column for Build Mock | Course-shipped pattern. | ✓ |
| Stacked sections in main column | Single-column scroll. | |
| Two-column main with Build Mock left, Past Attempts right | Densest. | |

**User's choice:** Sidebar.

### Q2.7 — Study Next algorithm (Phase 2 v1)

| Option | Description | Selected |
|--------|-------------|----------|
| Weakest LO by past attempts | Lowest correct/total, tiebreak by recency. | ✓ |
| Most-recent lecture's first LO | Pure recency. | |
| Random LO | No logic. | |
| Hide Study Next until Phase 4 ML lands | Defers PRACTICE entry point. | |

**User's choice:** Weakest LO by past attempts. Hide if zero attempts.

---

## Area 3 — P4 Take Mock runtime (SKIP, timer, session_state, resume)

### Q3.1 — SKIP semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Advance-only, returnable | Skip records null, can return via Prev. | ✓ |
| Advance-only, not returnable | Skip = locked-in 'wrong'. | |
| No Skip button | Violates REQUIREMENTS.md PAGE-04. | |

**User's choice:** Advance-only, returnable.

### Q3.2 — Timer placement

| Option | Description | Selected |
|--------|-------------|----------|
| Top header bar, right-aligned | Always visible, doesn't compete with content. | ✓ |
| Sidebar | Awkward — P4 hides standard sidebar. | |
| Floating sticky pill | Most modern, higher CSS cost. | |

**User's choice:** Top header bar, right-aligned.

### Q3.3 — Resume policy + answer-change behavior (asked twice)

| Option | Description | Selected |
|--------|-------------|----------|
| Mock persists in DB; resumes where left off | Each answer writes immediately/incrementally. | (intent, asked sub-question) |
| Pinned in `st.session_state` only | Tab close = lost progress. | |
| Pin + autosave every N | Hybrid. | |

**User's choice (initial):** "I want to say mock persists but what would happen if the user changes his answer after having entered an answer? Would the new answer override the old one?"

**Sub-question Q3.3b — when does each answer persist?**

| Option | Description | Selected |
|--------|-------------|----------|
| On Next/Prev/Skip navigation | UPSERT on leaving the question. | ✓ |
| On every selection change | Live save, chatty. | |
| Only on Submit Mock | No resume — contradicts intent. | |

**User's choice:** Persist on navigation. Schema enforces UNIQUE (attempt_id, question_id) → new answer overrides old via UPSERT.

### Q3.4 — Multi-correct grading

| Option | Description | Selected |
|--------|-------------|----------|
| All-or-nothing | 1 point if exact match, else 0. | ✓ |
| Partial credit (Jaccard) | Breaks Swiss formula's integer count. | |
| Partial credit minus penalty | Most punitive. | |

**User's choice:** All-or-nothing for v1.

---

## Area 4 — P5 Review + PRACTICE per-slide picker

### Q4.1 — P5 review layout

| Option | Description | Selected |
|--------|-------------|----------|
| Scrollable list — all questions stacked as Cards | Most editorial, matches roomy whitespace. | ✓ |
| Paginated — one question per page | Feels like a second mock. | |
| Tabs per question | Less editorial. | |

**User's choice:** Scrollable list of Cards.

### Q4.2 — P5 detail density

| Option | Description | Selected |
|--------|-------------|----------|
| Per-option rationale upfront; difficulty scores in expander | Rationale = primary teaching value. | (revised) |
| Both upfront | Density risk. | |
| Both behind expanders | Defeats P5's main value. | |

**User's choice:** Freeform — rationale upfront PLUS difficulty score upfront (no expander). Difficulty also visible during P4 mock-taking on each MCQ card. Captured as new D-3.5.

### Q4.3 — PRACTICE per-slide picker

| Option | Description | Selected |
|--------|-------------|----------|
| Least-recently-shown per slide (rotation) | Forces variety. | |
| Random per slide | Risk: same MCQ repeats by chance. | |
| Hardest by current difficulty score | Phase 4 dependency. | |
| First-by-id | Bad for spaced repetition. | |

**User's choice:** Freeform — "All questions for that LO are tested." Captured as D-4.3 REVISED. PRACTICE mock includes EVERY MCQ where `source_page IN <LO page_range>`. No per-slide picker. REQUIREMENTS.md amendment #2.

---

## Area 5 — Sidecar walkthrough structure + cadence + back-fill

### Q5.1 — Walkthrough section structure

| Option | Description | Selected |
|--------|-------------|----------|
| Function-by-function, plain-language paragraph each | Bounded by C-22 cap, audience-friendly. | ✓ |
| Line-range by line-range with file:line refs | Rots fast. | |
| Story / narrative arc | Loses per-function specificity. | |
| Hybrid: narrative + named-function callouts | Decide per-script. | |

**User's choice:** Function-by-function paragraphs.

### Q5.2 — Cadence

| Option | Description | Selected |
|--------|-------------|----------|
| End of every wave | Balanced; built into wave-closure ritual. | ✓ |
| End of every plan | Tightest loop, most overhead. | |
| End of every phase | Cheapest in commits, costliest in cognitive load. | |

**User's choice:** End of every wave.

### Q5.3 — Back-fill scope (multi-select)

| Option | Description | Selected |
|--------|-------------|----------|
| All 15 Phase 1 sidecars | Comprehensive. | ✓ |
| Only the 4 'too dense' originals | Targeted, biggest readability lift. | |
| Defer back-fill | Lowest cost, accepts inconsistency. | |
| Phase 1 orchestrators only | Smallest meaningful subset. | |

**User's choice:** All 15.

---

## Final gate — ready for CONTEXT.md?

| Option | Description | Selected |
|--------|-------------|----------|
| Ready — write CONTEXT.md | All decisions locked. | ✓ |
| Revise one or more | Re-ask specific D-numbers. | |
| Explore more gray areas | Surface what's missing. | |

**User's choice:** Ready.

---

## Claude's Discretion

Locked as Claude/researcher discretion (extracted from Figma in widget-catalog research step):
- Exact hex values for Paper0–Paper5, Accent/Soft/Deep/Wash, Status/OK/Warn/Info
- Exact monospace font name (from `Mono/Button Label` text style)
- Exact button paddings, border-radii, shadow values per component
- Card content layout per page (lecture card / attempt card / question result card)
- P4 progress indicator format ("Q3 of 15" vs progress bar vs both)
- Submit-Mock button placement and gating rules
- Internal helper function names within each pipeline folder
- Whether scoped CSS is one big `surf_theme.css` or split per-component (recommend single file for v1)

---

## Deferred Ideas

Captured in `02-CONTEXT.md <deferred>` section. Highlights:

**Phase 3:** editable factsheet JSON; dark theme variant; manual LO picker for PRACTICE.
**Phase 4:** real difficulty scores wire into P4/P5 placeholders; replace Study Next algo with ML weakness prediction.
**Phase 5:** sample factsheet + lecture PDFs for graders.
**Process:** C-22 line-cap audit at end of Phase 2; `app/brain/topbar/` rename; FigJam end-of-phase visualization (format pending).

## Reviewed Todos (not folded)

None — the only matched todo (widget-catalog research) was folded.

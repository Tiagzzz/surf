# 02 — Widget catalog (D-2.12 token validation + Figma reconciliation + spike verdicts)

**Status:** Plan 02-01 Task 3 output. Demoted from extraction spike to
validation step per the parallel-session audit (`02-PARALLEL-AUDIT.md`)
and the Task 1 researcher run (`02-FIGMA-RESEARCH.md`).

**Sources:**
- `02-CONTEXT.md` Area 6 D-2.12..D-2.24 — locked hex / type / motion values.
- `02-FIGMA-RESEARCH.md` §5 — full Figma token catalog (48 vars · 15 text
  styles · 7 effect styles), §4 component catalog, §7 design rulings.
- `app/brain/theme/theme.py` (post-Task-2) — what actually shipped.

---

## Token table

Three columns: CONTEXT D-2.12 (locked) · Figma `Tokens` collection ·
shipped in `app/brain/theme/theme.py` `_CSS` `:root` block. Drift is
flagged ⚠️ and links back to the source of truth.

### Color: Paper ladder (D-2.12)

| Token | CONTEXT D-2.12 | Figma (`02-FIGMA-RESEARCH §5.1 Base`) | Shipped (`theme.py`) | Drift |
|---|---|---|---|---|
| `--paper` | `#fdf9f2` | `color/Base/Paper` `#FDF9F2` | `#fdf9f2` | none |
| `--paper-0` | `#f5efe4` | `color/Base/Paper0` `#F5EFE4` | `#f5efe4` | none |
| `--paper-1` | `#ede4d2` | `color/Base/Paper1` `#EDE4D2` | `#ede4d2` | none |
| `--paper-2` | `#c0b49b` | `color/Base/Paper2` `#C0B49B` | `#c0b49b` | none |
| `--paper-3` | `#6c6455` | `color/Base/Paper3` `#6C6455` | `#6c6455` | none |
| `--paper-4` | `#3b362c` | `color/Base/Paper4` `#3B362C` | `#3b362c` | none |
| `--paper-5` | `#28251f` | `color/Base/Paper5` `#28251F` | `#28251f` | none |
| `--paper-shadow` | `#171512` | `color/Base/Shadow` `#171512` | `#171512` | none |
| `--paper-shadow-soft` | `#1a1814` | `color/Base/Shadow-Soft` `#1A1814` (net-new, §5.1) | `#1a1814` | none |
| `--white` | `#ffffff` | `color/Base/White` `#FFFFFF` (net-new, §5.1) | `#ffffff` | none |

### Color: Accent (D-2.12)

| Token | CONTEXT D-2.12 | Figma (`02-FIGMA-RESEARCH §5.1 Accent`) | Shipped (`theme.py`) | Drift |
|---|---|---|---|---|
| `--accent-vibrant` | `#c8361d` | `color/Accent/Vibrant` `#C8361D` | `#c8361d` | none |
| `--accent-deep` | `#9d2815` | `color/Accent/Deep` `#9D2815` | `#9d2815` | none |
| `--accent-soft` | `#e8a798` | `color/Accent/Soft` `#E8A798` | `#e8a798` | none |
| `--accent-wash` | `#f7d9d1` | `color/Accent/Wash` `#F7D9D1` | `#f7d9d1` | none |

### Color: Status (D-2.12)

| Token | CONTEXT D-2.12 | Figma (`02-FIGMA-RESEARCH §5.1 Status`) | Shipped (`theme.py`) | Drift |
|---|---|---|---|---|
| `--ok` | `#2d6a3f` | `color/Status/OK` `#2D6A3F` | `#2d6a3f` | none |
| `--ok-wash` | `#9ec7aa` | `color/Status/OK-Wash` `#9EC7AA` (net-new, §5.1) | `#9ec7aa` | none |
| `--warn` | `#b8860b` | `color/Status/Warn` `#B8860B` | `#b8860b` | none |
| `--info` | `#2a5d7c` | `color/Status/Info` `#2A5D7C` | `#2a5d7c` | none |

### Radii (D-2.12)

| Token | CONTEXT D-2.12 | Figma (`02-FIGMA-RESEARCH §5.3`) | Shipped (`theme.py`) | Drift |
|---|---|---|---|---|
| `--r-xs` | `3px` | `radii/r-xs` `3px` | `3px` | none |
| `--r-sm` | `4px` | `radii/r-sm` `4px` | `4px` | none |
| `--r-md` | `6px` | `radii/r-md` `6px` | `6px` | none |
| `--r-lg` | `10px` | `radii/r-lg` `10px` | `10px` | none |
| `--r-pill` | `999px` | `radii/r-pill` `999px` | `999px` | none |

> **Note (MCQ option):** D-2.20 specifies a literal `5px` radius for the
> MCQ option wrapper — neither `--r-sm` (4 px) nor `--r-md` (6 px). This
> is intentional and shipped as a hard-coded `border-radius: 5px` in the
> MCQ section of `_CSS`. The CSS comment explicitly notes it.

### Motion (D-2.12)

| Token | CONTEXT D-2.12 | Figma (`02-FIGMA-RESEARCH §5.6` motion) | Shipped (`theme.py`) | Drift |
|---|---|---|---|---|
| `--ease` | `cubic-bezier(0.2, 0, 0, 1)` | `motion/ease/standard` | `cubic-bezier(0.2, 0, 0, 1)` | none |
| `--t-fast` | `120ms` | `motion/t-fast` | `120ms` | none |
| `--t-base` | `180ms` | `motion/t-base` | `180ms` | none |
| `--t-slow` | `320ms` | `motion/t-slow` | `320ms` | none |

### Type (D-2.12 + D-2.16)

| Token | CONTEXT D-2.12 | Figma (`02-FIGMA-RESEARCH §5.7`) | Shipped (`theme.py`) | Drift |
|---|---|---|---|---|
| `--serif` | `'Fraunces', Georgia, serif` | 8 Serif/* text styles | `'Fraunces', Georgia, serif` | none |
| `--mono` | `'JetBrains Mono', Menlo, monospace` | 7 Mono/* text styles | `'JetBrains Mono', Menlo, monospace` | none |

**Verdict:** **No drift.** Every D-2.12 hex matches the Figma `Tokens`
collection (case-insensitive) and the value shipped in `theme.py`.
Theme bench at `previews/components/_theme_bench/preview.py` (Task 4)
is the visual proof.

---

## Component spec

### Button — 5 variants (D-2.19)

| Variant | Wrapper key | Background | Text | Border | Stamp shadow (rest / hover / active) | Disabled |
|---|---|---|---|---|---|---|
| Default (primary) | `btn-default` | `--paper-5` | `--white` | none | `3 / 4 / 1` px `--paper-shadow` | bg `--paper-2`, text `--paper-3`, no shadow |
| Ghost | `btn-ghost` | transparent | `--paper-4` | 1.5 px `--paper-4` | none | text `--paper-3`, border `--paper-2` |
| Soft | `btn-soft` | `--paper-1` | `--paper-5` | none | `2 / 3 / 1` px `--paper-shadow-soft` | bg `--paper-1`, text `--paper-3`, no shadow |
| Tinted accent | `btn-tinted-accent` | `--accent-vibrant` (hover `--accent-deep`) | `--white` | none | `3 / 4 / 1` px `--paper-shadow` | bg `--paper-2`, text `--paper-3`, no shadow |
| Tinted ok / info / warn | `btn-tinted-{ok,info,warn}` | `--ok` / `--info` / `--warn` | `--white` | none | `3 / 4 / 1` px `--paper-shadow`, `filter: brightness(0.9)` on hover | same as accent |

Hover translate `(-1px, -1px)`; active translate `(2px, 2px)`. Reduced-
motion query disables all transforms (D-2.15). Loading-state label is
`…` (ellipsis) per Figma 7.2 row 2 ruling — no spinner glyph anywhere.

### Card — passive + interactive (D-2.13)

| Variant | Wrapper key | Background | Border | Stamp shadow | Hover |
|---|---|---|---|---|---|
| Passive | `card-passive` | `--paper-0` | 1.5 px `--paper-2` | 2 px `--paper-shadow-soft` | n/a (non-interactive) |
| Interactive | `card-interactive` | `--paper-0` | 1.5 px `--paper-2` | 4 px `--paper-shadow` (rest) → 6 px (hover) | translate `(-2px, -2px)`, border-color `--paper-4` |
| Class card | `class-card` | `--paper` | 1.5 px `--paper-4` | 4 px `--paper-shadow` (rest) → 6 px (hover) | translate `(-2px, -2px)` |

### Chip (D-2.19)

`<span class="surf-chip">`. Variants `outline` (default), `accent`,
`solid`, `dashed`. Mono 700 11 px tracked-uppercase, 1.5 px border, pill
radius, padding `6/14`. Renders inline via `chip(text, variant=)` →
returns string; compose rows via `chips_row(items)`.

### MCQ option — 4 states (D-2.20)

| State | Wrapper key suffix | Background | Border | Stamp shadow | Padding |
|---|---|---|---|---|---|
| Off | `mcq-opt-{key}-off` | `--paper-1` | 1 px `--paper-shadow` | none | `13 / 14` |
| On | `mcq-opt-{key}-on` | `--paper-0` | 2 px `--paper-shadow` | 2 px `--paper-shadow` | `14 / 15` |
| Correct (P5) | `mcq-opt-{key}-correct` | `--ok-wash` | 2 px `--ok` | 2 px `--paper-shadow` | `14 / 15` |
| Incorrect (P5) | `mcq-opt-{key}-incorrect` | `--accent-soft` | 2 px `--accent-deep` | 2 px `--paper-shadow` | `14 / 15` |

Container `border-radius: 5px` (literal — neither `--r-sm` nor `--r-md`).
Custom 20×20 checkbox glyph drawn on `[data-baseweb="checkbox"] > div:first-child`
with 5 px radius and 2 px `--paper-5` border. `:has(input:checked)` swaps
the inner background to `--paper-5` and renders a `✓` glyph in
`JetBrains Mono Bold 14px` at `left:3.5px / top:-1px`.

**Selection signal is paper elevation + stamp shadow, NOT an accent
color.** Accent colors only appear in the P5 review state.

### MCQ card container (D-2.23)

`st.container(key="mcq-card-…")`. Background `--paper`, 2 px
`--paper-shadow` border, 6 px radius, 3 px stamp shadow, padding
`22/20/20/20`, max-width 600 px, vertical gap 13 px between sections
(via `[data-testid="stVerticalBlock"]` selector).

### Difficulty stars (D-2.24)

`difficulty_stars(score: float)` in
`app/mock_take/question_render/_difficulty.py`. Maps `score ∈ [0, 1]`
to `n = max(1, min(5, round(score * 5)))` stars filled, rendered
inline as SVG (no `<img>` tags) with 1 px gap. Filled SVG fills with
`--accent-vibrant`, empty SVG strokes `--paper-3`. NULL difficulty
case is handled at the call site (renders dashed-frame chip with `—`
placeholder; this function is not called).

### Stat card

`st.container(key="stat-card-…")`. `--paper-0` bg, 1.5 px `--paper-3`
border, 6 px radius, 2 px `--paper-shadow-soft` stamp, padding
`14/18`. Compose with `stat_card(label, value, eyebrow_text, delta,
delta_dir)` helper which writes the four typography lines.

### Topbar (D-2.10 + D-2.13)

`st.container(key="topbar")`. Bottom border 2 px `--paper-5`, padding
`14/4/12/4`, margin-bottom 32 px. Topbar icon button via
`st.container(key="topbar-icon")` — 38×38, transparent bg with 1.5 px
`--paper-4` border, hover paper-1 + 2 px stamp shadow.

### Empty state

`st.container(key="empty")`. Dashed 2 px `--paper-3` border, 6 px
radius, padding `36/28`, text-align center. Compose with
`empty_state_text(headline, body)` helper which writes the
ornament + headline + body block.

### `st.status` skin (D-2.21)

Reach via `[data-testid="stStatus"]` and the legacy
`[data-testid="stStatusWidget"]`. `--paper-1` bg, 1.5 px `--paper-3`
border, 4 px left-border `--accent-vibrant` while running, `--ok` when
complete. Header in mono uppercase tracked.

### `st.expander` skin (D-2.21)

Reach via `[data-testid="stExpander"]`. `--paper-1` bg, 1.5 px
`--paper-3` border, 6 px radius. Hover: lift `(-1px, -1px)` + 2 px
`--paper-shadow-soft` stamp. Header in mono uppercase tracked.

### Summary banner (P5 final score) — surfaced from `02-FIGMA-RESEARCH §4`

Plan 02-01 ships the token surface for this; the component lives in
plan 02-06 (`app/mock_review/summary_banner/`). Wrapper key reserved:
`summary-banner`. Spec: full-width `--paper-0` panel with 4 px stamp
shadow, mono eyebrow, big italic Fraunces score (reuses `score()`
helper), correct/total + percent-to-next-note line.

---

## Spike reports

### Q3 — Card Interactive overlay-button

**Status:** Pending — spike runs as Task 7 of plan 02-01, after the
theme bench is approved.

> Verdict + chosen approach will be filled in by Task 7. Until then,
> Plan 04 (P3 lecture multi-select) MUST treat the overlay pattern as
> unconfirmed.

### Q4 — Fragment timer 5-min memory test

**Status:** Pending — spike runs as Task 6 of plan 02-01.

> Verdict + chosen approach will be filled in by Task 6. Plan 05 (P4
> mock timer) inherits whichever pattern wins.

### Q8 — `@st.cache_resource` on `app/db/connection.py`

**Status:** Pending — verification runs as Task 8 of plan 02-01.

> Verdict + test status will be filled in by Task 8.

---

## Folded todos

- `2026-05-02-phase-2-streamlit-widget-catalog-research.md` — folded
  by Plan 02-01 Task 3. Moved from `.planning/todos/pending/` to
  `.planning/todos/done/` as part of this commit. The original todo's
  goal (vanilla green-list + extras shortlist) is satisfied by the
  parallel session's `Streamlit_Test/test_components.py` bench (now
  migrated to `previews/components/_theme_bench/preview.py` in Task 4)
  and the per-component specs in `## Component spec` above.

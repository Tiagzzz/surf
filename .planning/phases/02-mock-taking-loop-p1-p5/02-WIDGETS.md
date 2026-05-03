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

### Typography styles (Figma §5.7 → CSS rules in `theme.py`)

D-2.12 names only the two family tokens (`--serif`, `--mono`); the per-
style sizes/weights/line-heights/tracking live as values inside the
matching CSS rule, not as named tokens. This table maps each Figma
text-style row to the rule that paints it and (when one exists) the
public Python helper.

| Figma style | Weight / Size / Line / Track | Shipped CSS selector | Public helper | Used by |
|---|---|---|---|---|
| `Serif/Display` | Black Italic / 64 / 95% / -2% | *(unmapped — no use site in Phase 2)* | — | Brand wordmark, Quizz Summary |
| `Serif/H1` | Black Italic / 42 / 95% / -2% | `h1 { … }` | — (use `st.markdown("# …")`) | Page header |
| **`Serif/H2`** | **SemiBold Italic / 28 / 115% / -1%** | **`h2, .serif-h2 { … }`** | **`heading_h2(text)`** | **Bench section titles, Cards/Class, Stat Card, Quizz question text** |
| `Serif/H3` | SemiBold Italic / 22 / 115% / 0 | `h3 { … }` | — (use `st.markdown("### …")`) | Sub-section labels |
| `Serif/H4` | SemiBold / 18 / 130% / 0 | `h4 { … }` | — | Sidebar / Form Panel |
| `Serif/Body` | Regular / 17 / 150% / 0 | `[data-testid="stMarkdownContainer"] p` | — | Paragraph text everywhere |
| `Serif/Caption` | Italic / 13 / 140% / 0 | `.surf-caption` | `caption(text)` | Helper lines |
| `Mono/Eyebrow` | Medium / 10 / 150% / 18% / UPPER | `.surf-eyebrow` | `eyebrow(text)` | Section labels above content |
| `Mono/Meta` | Regular / 11 / 150% / 8% | `.surf-meta` | `meta(text)` | Card metadata strips |
| `Mono/Button Label` | Bold / 11 / 100% / 10% / UPPER | `[data-testid="stButton"] button p` | — (paints every button) | All button text — locked |

**Notation:** the "28/15" Figma shorthand reads as **size 28 px / line-
height 115%** (the trailing `15` is the last two digits of `115%`).
Confirmed against `02-FIGMA-RESEARCH §5.7` row `Serif/H2`.

**`heading_h2(text)`** was added in the Defect-6 fix on top of `bd51b32`
to give bench section titles (and any future caller) an explicit,
html-escaped, named-class entry point. Both `<h2>` (auto-generated by
`st.markdown("## …")`) and `<x class="serif-h2">` paint identically;
callers can mix them freely.

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

| Variant | Wrapper key | Background | Border | Stamp shadow | Hover | Padding |
|---|---|---|---|---|---|---|
| Passive | `card-passive` | `--paper-0` | 1.5 px `--paper-2` | 2 px `--paper-shadow-soft` | n/a (non-interactive) | `20 / 24` |
| Interactive | `card-interactive` | `--paper-0` | 1.5 px `--paper-2` | 4 px `--paper-shadow` (rest) → 6 px (hover) | translate `(-2px, -2px)`, border-color `--paper-4` | `20 / 24` |
| Class card | `class-card` | `--paper` | 1.5 px `--paper-4` | 4 px `--paper-shadow` (rest) → 6 px (hover) | translate `(-2px, -2px)` | `22 / 24` |

Class-card padding bumped 18 → 22 (Defect 7, ruling 2026-05-02): the
mono meta line ("12 lectures · 78%") was sitting too tight against the
bottom border. Symmetric per Defect 3.

### Chip (D-2.19)

`<span class="surf-chip">`. Variants `outline` (default), `accent`,
`solid`, `dashed`. Mono 700 11 px tracked-uppercase, 1.5 px border, pill
radius, padding `6/14`. Renders inline via `chip(text, variant=)` →
returns string; compose rows via `chips_row(items)`.

### MCQ option — 4 states (D-2.20 + D-2.20a)

The Off/On pair is now driven by `:has(input:checked)` (D-2.20a, ruling
2026-05-02). The container key is just option identity — no `-off` / `-on`
suffix. Correct / Incorrect keep state-baked suffix keys (P5 review
paints them at render time, not via user interaction).

| State | Wrapper key | CSS trigger | Background | Border | Stamp shadow | Padding |
|---|---|---|---|---|---|---|
| Off (default) | `mcq-opt-{question_id}-{option_letter}` | `:not(:has(input:checked))` plus `:not([class*="-correct"]):not([class*="-incorrect"])` | `--paper-1` | 1 px `--paper-shadow` | none | `13 / 14` |
| On (live) | `mcq-opt-{question_id}-{option_letter}` (same) | `:has(input:checked)` plus the same `:not()` guards | `--paper-0` | 2 px `--paper-shadow` | 2 px `--paper-shadow` | `14 / 15` |
| Correct (P5) | `mcq-opt-{key}-correct` | suffix-class match | `--ok-wash` | 2 px `--ok` | 2 px `--paper-shadow` | `14 / 15` |
| Incorrect (P5) | `mcq-opt-{key}-incorrect` | suffix-class match | `--accent-soft` | 2 px `--accent-deep` | 2 px `--paper-shadow` | `14 / 15` |

**Why D-2.20a:** the original D-2.20 froze the visual state at render
time — clicking an option flipped the inner checkbox but the wrapper
key still said `-off`, so the elevation/stamp-shadow On treatment never
appeared. The `:has()` mechanism makes the click feel live (the existing
120 ms `--t-fast` transition tweens bg / border / shadow / padding).
Source-order places the `-correct` / `-incorrect` rules after the
`:has()` rule so they win the cascade for review states.

Container `border-radius: 5px` (literal — neither `--r-sm` nor `--r-md`).
Custom 20×20 checkbox glyph drawn on `[data-baseweb="checkbox"] > div:first-child`
with 5 px radius and 2 px `--paper-5` border. `:has(input:checked)` swaps
the inner background to `--paper-5` and renders a `✓` glyph in
`JetBrains Mono Bold 14px` at `left:3.5px / top:-1px`.

**Selection signal is paper elevation + stamp shadow, NOT an accent
color.** Accent colors only appear in the P5 review state.

**Browser support:** `:has()` ships in Chrome ≥ 105, Safari ≥ 15.4,
Firefox ≥ 121. Streamlit's webview uses the host browser; macOS team
is fine. Fallback (if ever needed) is documented in the D-2.20a
edit-this-later note.

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

**Status:** **PENDING-RUN.** Sandbox built at
`previews/spikes/fragment_timer/preview.py` (Plan 02-01 Task 6); awaits
a live 5-minute RSS measurement that the executor agent cannot perform.
Tiago runs the test per the protocol in `previews/spikes/SPIKES.md § Q4`
and records the verdict there.

**Run command:** `streamlit run previews/spikes/fragment_timer/preview.py`

**Q4 verdict:** PENDING-RUN — to be filled in `previews/spikes/SPIKES.md`
once Tiago executes the 5-minute test.

**Chosen approach (conditional):**
- PASS → Plan 02-05 (P4 Take Mock) ships `@st.fragment(run_every="1s")`
  for the elapsed-time timer in the topbar.
- FAIL → fallback is a manual re-render-on-nav timer (recompute elapsed
  only on Next / Prev / Skip / Submit click; mock duration still
  recorded server-side via `attempts.started_at` → `finished_at`).

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

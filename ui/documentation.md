# Surf — Design System Documentation

> **Audience:** Tiago + teammates. **Not** consumed by Claude tooling — this is a documentation artifact.
> **Status:** § 5 (component catalog) and § 8 (DOM reach map) filled 2026-05-03 during Plan 02-01 Task 10 from the Figma component-logic research (`02-FIGMA-RESEARCH.md` per D-2.26) plus the actual selectors shipped in `app/brain/theme/theme.py`. Sections marked `[fills as waves close]` accrete content during phase 2 execution and continue in later phases.
> **Source of truth for visuals:** the locked Figma library `https://www.figma.com/design/EYjkvHArrBonuiG2JUS2sE/SURF_UI`. Key frames are cached in `docs/design/figma_exports/`.

---

## 1. Overview

Surf uses a **paper-and-stamp** aesthetic: warm cream backgrounds, charcoal text, a single Surf-red accent for primary actions, and a signature hard-edged offset shadow ("stamp") that lifts on hover and sinks on press. Typography pairs `Fraunces` (serif, often italic for headlines) with `JetBrains Mono` (caps-tracked monospace for buttons, labels, and meta).

**Where the CSS lives:** `app/brain/theme/theme.py` exports `inject_theme()` and a small set of HTML helper primitives. `inject_theme()` writes ~480 lines of scoped CSS into the page once via `st.markdown(_CSS, unsafe_allow_html=True)`. **Call it at the top of every Streamlit page.**

**Why two copies?** A second copy lives at `previews/_theme.py` for the visual preview gate (`CLAUDE.md` § Visual Preview Gate). Sandboxes never `from app...` import; they copy. When the production theme changes, the next visual task on a sandbox refreshes the sandbox copy and re-runs the preview. Drift is a feature.

**Hard rules** (non-negotiable):
- No banned community libs (`streamlit-shadcn-ui`, `streamlit-elements`, `streamlit-antd-components`, `streamlit-option-menu`).
- No `unsafe_allow_html=True` for layout — only for typography helpers (the `<p class="surf-eyebrow">…</p>` pattern).
- No JS injection (no confetti, no scroll-triggered animations, no animated counters).
- All component-level styling reaches Streamlit widgets via stable selectors: `[class*="st-key-XXX"]` for `st.container(key="XXX")` wrappers + `data-testid` for nested widgets.

---

## 2. Token reference

> Every CSS custom property declared at `:root` in `theme.py`. Each line: variable, hex/value, "use this when…" rule.

### 2.1 Color — Paper ladder (warm cream → charcoal)

| Variable | Hex | Use this when… |
|---|---|---|
| `--paper` | `#fdf9f2` | Default page background. The widest, lightest surface. |
| `--paper-0` | `#f5efe4` | One step darker. Use for **selected-but-not-graded** states (P4 active MCQ option), passive cards, stat cards. The selection signal during P4. |
| `--paper-1` | `#ede4d2` | Two steps darker. Use for **resting** interactive surfaces that need a hint of presence (Off-state MCQ options, soft buttons, difficulty chip backdrop). |
| `--paper-2` | `#c0b49b` | Disabled-state surfaces. Light borders. |
| `--paper-3` | `#6c6455` | Mid-grey text (meta, captions, labels). Borders on active inputs. |
| `--paper-4` | `#3b362c` | Darker text. Ghost-button fill on hover. |
| `--paper-5` | `#28251f` | Body text. Default-button background. The custom checkbox fill. |
| `--paper-shadow` | `#171512` | Hard stamp-shadow color (the signature). |
| `--paper-shadow-soft` | `#1a1814` | Softer stamp shadow (passive surfaces). |
| `--white` | `#ffffff` | Text on dark fills (Default button label, custom checkbox ✓). |

### 2.2 Color — Accent (Surf red)

| Variable | Hex | Use this when… |
|---|---|---|
| `--accent-vibrant` | `#c8361d` | Primary CTA fill (one per page). Active tab indicator. Slider thumb. **Never** use for "selected" states during P4 — that signal is paper elevation, not accent. |
| `--accent-deep` | `#9d2815` | Hover state for `--accent-vibrant`. |
| `--accent-soft` | `#e8a798` | **Review-state only:** the user picked this option AND it was wrong (P5). Never elsewhere. |
| `--accent-wash` | `#f7d9d1` | Focus ring (text input outline-on-focus). Faint accent-tinted backgrounds. |

### 2.3 Color — Status

| Variable | Hex | Use this when… |
|---|---|---|
| `--ok` | `#2d6a3f` | Success state on tinted-OK button. Score color when ≥5 (Swiss high mark). |
| `--ok-wash` | `#9ec7aa` | **Review-state only:** the option was correct (P5). Whether or not the user picked it. |
| `--warn` | `#b8860b` | Warning button fill. Score color when 3.5–4.99 (Swiss mid). |
| `--info` | `#2a5d7c` | Info button fill. |

### 2.4 Radius

`--r-xs 3px` · `--r-sm 4px` (buttons, inputs, default surfaces) · `--r-md 6px` (cards, MCQ card, difficulty chip) · `--r-lg 10px` · `--r-pill 999px` (chips, slider thumb, custom checkbox glyph).

**MCQ option uses `5px` directly** (not a token — locked because the Figma uses an in-between radius for that one component).

### 2.5 Motion

`--ease cubic-bezier(0.2, 0, 0, 1)` · `--t-fast 120ms` (button feedback, input border) · `--t-base 180ms` (cards, tabs) · `--t-slow 320ms` (rare slow elements).

Transitions only — **no `@keyframes`.** The hover stamp-shadow IS the signature animation. See § 6 for the `prefers-reduced-motion` accessibility rule.

### 2.6 Type

`--serif 'Fraunces', Georgia, serif` · `--mono 'JetBrains Mono', Menlo, monospace`. Self-hosted in `assets/fonts/` (3 variable WOFF2 files, ~190 KB latin subset).

---

## 3. Typography hierarchy

| Level | Font | Where it appears |
|---|---|---|
| `h1` | Fraunces 900 italic, 42px / 0.95 | Top of P2 (My Classes), P3 (Class hub), P5 (Review summary). One per page. |
| `h2` | Fraunces 600 italic, 28px / 1.15 | MCQ question text on P4/P5. Section dividers within a page. |
| `h3` | Fraunces 600 italic, 22px / 1.15 | Class card titles. Card-Interactive titles. |
| `h4` | Fraunces 600 (upright), 18px / 1.3 | Sub-section headings. Form group labels (when not using eyebrow). |
| `body` (`p`) | Fraunces 400, 17px / 1.5 | Paragraphs. MCQ option labels. |
| `surf-eyebrow` | JetBrains Mono 500, 10px, +0.18em tracking, UPPERCASE | Section labels above headings. |
| `surf-caption` | Fraunces 400 italic, 13px | Helper text under inputs, captions under headings. |
| `surf-meta` | JetBrains Mono 400, 11px, +0.08em tracking | "12 lectures · 78%" pattern. Score callouts that aren't the big number. |
| `surf-empty-headline` | JetBrains Mono 700, 18px, +0.14em tracking, UPPERCASE | "Nothing here yet" headline in empty states. |
| `surf-empty-body` | JetBrains Mono 400, 12px, +0.06em tracking | Empty-state explainer. |

**Rule of thumb:** Italic Fraunces = "this is a heading or a moment". Mono caps-tracked = "this is meta or a control label". Body Fraunces = "this is content".

---

## 4. Color combination rules

[fills as waves close — initial DO/DON'T set captured here, expanded by the D-2.26 Figma analysis]

### DO

- **DO** use `--accent-vibrant` for the primary CTA on a page (one per page). Examples: "Add a class" on P2, "Generate Mock" on P3, "Submit Mock" on P4.
- **DO** elevate selected-but-not-graded MCQ options from `--paper-1` → `--paper-0` AND add the 2px stamp shadow. **The elevation IS the selection signal.**
- **DO** use `--ok-wash` to highlight correct MCQ options in P5 review (regardless of whether the user picked them).
- **DO** use `--accent-soft` to highlight the user's wrong picks in P5 review.
- **DO** keep CSS `transitions` on hover/press only; never run `keyframes` that loop.

### DON'T

- **DON'T** use `--accent-vibrant` as a passive-surface fill. Passive surfaces use `--paper-0` or `--paper-1`.
- **DON'T** use `--accent-vibrant` to signal "selected" during P4 — accent is reserved for the primary CTA and P5 review states.
- **DON'T** use `--ok-wash` outside P5 review state.
- **DON'T** use `--accent-soft` as a hover state.
- **DON'T** add a fade-in keyframe to cards. Streamlit reruns top-to-bottom, fade-ins re-trigger and feel busy.

[More rules will land here from the Figma component-logic researcher run during plan 02-01.]

---

## 5. Component catalog

Every component shipping in `app/brain/theme/theme.py` `_CSS` plus the Python helpers in the same module. Use the section headings to ⌘-F your way around. The reference screenshots live under `docs/design/figma_exports/` (currently `node_25-2.png` for the components page and `node_4045-282_mcq_take_mock.png` for the Take-Mock card).

### Buttons

#### btn-default
**`st.container(key="btn-default")` wrapper** — primary CTA, dark-ink fill (`--paper-5`), white text, JetBrains Mono Bold caps-tracked label, 3 px stamp shadow.
Use when: there's exactly ONE primary action on the page (Save Class, Take Mock, Submit Answer).
Don't use when: the action is destructive (use `btn-tinted-warn`) or secondary (use `btn-soft`).
Recipe: `with st.container(key="btn-default"): st.button("Take mock")`.

#### btn-ghost
**`st.container(key="btn-ghost")` wrapper** — outlined-only, no fill, no stamp shadow. 1.5 px paper-4 border that darkens to paper-5 on hover.
Use when: the button is paired with a `btn-default` and needs to look secondary (Cancel, Skip). Or when the action is non-committal (Preview, Reset).
Don't use when: it's the ONLY button on the page — `btn-soft` reads better as a sole CTA.

#### btn-soft
**`st.container(key="btn-soft")` wrapper** — paper-1 fill, paper-5 text, 2 px stamp-soft shadow. Quietest of the four families.
Use when: tertiary actions (Save Draft, Show Raw JSON, Open Settings).
Don't use when: there's already a `btn-ghost` doing the secondary job — pick one and stick with it.

#### btn-tinted-accent
**`st.container(key="btn-tinted-accent")` wrapper** — Surf-red fill (`--accent-vibrant`), white text. The "this commits to something" button.
Use when: the action triggers a Claude call, writes to DB, or otherwise commits real work (Generate Mock, Submit Answer, Save Class).
Don't use when: the action is reversible by a single click (use `btn-default` instead).

#### btn-tinted-ok / btn-tinted-info / btn-tinted-warn
**`st.container(key="btn-tinted-{ok,info,warn}")` wrapper** — Status-colored fills (green, blue, amber). White text. 3 px stamp shadow + `filter: brightness(0.9)` on hover.
Use when: the button conveys a status meaning (OK = confirm/proceed, Info = view details, Warn = irreversible/destructive).
Don't use when: as a generic CTA — pick `btn-default` or `btn-tinted-accent` to keep the status colors meaningful.

### Cards

#### card-passive
**`st.container(key="card-passive")` wrapper** — paper-0 surface, 1.5 px paper-2 border, 6 px radius, 2 px stamp-soft shadow. **Non-interactive.**
Use when: displaying read-only content that has shape but no click target (a stat group, a quote, a summary block).
Don't use when: any child element accepts a click — promote to `card-interactive`.

#### card-interactive
**`st.container(key="card-interactive")` wrapper** — same surface as passive but with a 4 px stamp shadow that grows to 6 px on hover, plus a `translate(-2px, -2px)` lift. Click-active.
Use when: the whole card body is the click target (lecture-card on P3, attempt-card on P5).
Don't use when: only one inner element is clickable — use `card-passive` and put the button inside.

#### class-card
**`st.container(key="class-card")` wrapper** — class-grid card on P2 My Classes. Paper bg (warmer than `card-*`), 1.5 px paper-4 border, 4 px stamp shadow, **22/24 padding (Defect 7 ruling)**, 16 px bottom margin.
Use when: rendering one class entry on the P2 grid.
Don't use when: rendering anywhere else — `card-interactive` is the generic equivalent.

#### stat-card
**`st.container(key="stat-card")` wrapper** — KPI tile with `min-height: 110px` + flex column + `space-between` so a one-digit value and a long label keep the same card height. Paper-0 fill, 14/18 padding, 2 px stamp-soft shadow.
Use when: displaying a single number alongside a label and optional delta arrow (P6 Dashboard tiles, P5 review summary).
Don't use when: the content is multi-paragraph — use `card-passive`.

### MCQ option (D-2.20 + D-2.20a)

#### mcq-opt-{question_id}-{option_letter}
**`st.container(key="mcq-opt-{q}-{letter}")` wrapper** — the live P4 take-mock option. Container key is just option identity; CSS branches on `:has(input:checked)` to flip Off↔On.
Variants:
- **Off** (default, `:not(:has(input:checked))`): paper-1 bg, 1 px paper-shadow border, no shadow, 13/14 padding.
- **On** (live, `:has(input:checked)`): paper-0 bg, 2 px paper-shadow border, 2 px stamp shadow, 14/15 padding (compensates for the 1→2 px border widen so text x-position stays stable).

Use when: rendering option checkboxes on P4. Click anywhere on the wrapper toggles the inner checkbox via the standard label-wrapping behaviour.
Don't use when: the option is in P5 review state — use the `-correct` / `-incorrect` review variants below.

#### mcq-opt-{key}-correct / mcq-opt-{key}-incorrect
**State-baked review keys.** Used ONLY on P5 mock-review screens — the wrapper key is set at render time based on the user's saved answer.
- **Correct:** ok-wash bg, 2 px ok border, 2 px stamp shadow, 14/15 padding.
- **Incorrect:** accent-soft bg, 2 px accent-deep border, 2 px stamp shadow, 14/15 padding.

Why state-baked here vs `:has()` for Off/On: P5 paints a static review of a finished attempt; there's no user click to react to.

### MCQ card container (D-2.23)

#### mcq-card
**`st.container(key="mcq-card")` wrapper** — the frame around the question header (Q-number + class + difficulty) + question text + option stack + action row. Paper bg, 2 px paper-shadow border, 6 px radius, 3 px stamp shadow, 22/20/20/20 padding (locked Figma value, exception to the symmetric-padding rule per Defect 3 ruling), max-width 600 px, 13 px vertical gap between sections.
Use when: rendering the live take-mock card on P4 or the review card on P5.
Don't use when: anywhere else — the geometry is locked to the Figma 4045:282 spec.

### Difficulty display (D-2.24)

#### difficulty-stars
**Python helper `difficulty_stars(score: float)`** — paints 5 SVG stars in `assets/icons/star_{filled,empty}.svg`, with `n = max(1, min(5, round(score * 5)))` filled. Inlined as SVG (no `<img>` tags per D-2.24).
Use when: a question has a non-NULL `difficulty_score` and you want to render the stars chip.
Don't use when: `difficulty_score` is NULL — render the dashed-frame "—" placeholder instead at the call site.

### Chip (D-2.19)

#### surf-chip
**Python helper `chip(text, variant=...)`** — returns the HTML for one inline tag. Compose rows via `chips_row(items)`.
Variants: `outline` (default — paper-4 border, no fill), `accent` (accent-vibrant border + text), `solid` (paper-5 fill, paper-0 text), `dashed` (dashed border).
Use when: short labels that group with siblings (lecture tags, MCQ category, status flags).
Don't use when: longer than ~3 words — text starts wrapping inside the pill which looks awkward.

### Steps indicator (D-2.19)

#### surf-steps
**Python helper `steps(items)`** — inline step row with bullets. Each item is `(label, status)` where status ∈ `done / active / todo`.
Use when: onboarding (Sign up → Add class → Take mock) or wizard flow indicators.
Don't use when: more than ~5 steps — wraps awkwardly even with `flex-wrap`.

### Score (D-2.19)

#### surf-score
**Python helper `score(value: float)`** — renders the Swiss 1-6 grade as big italic Fraunces, color-keyed:
- `< 3.5` → `--accent-vibrant` (red)
- `3.5–4.99` → `--warn` (gold)
- `≥ 5.0` → `--ok` (green)

Use when: surfacing a Swiss grade on P2 class cards or the P5 summary banner.
Don't use when: rendering a percentage (use `stat-card` with `--paper-5` text instead).

### Stat helpers

#### surf-stat-value, surf-delta-{up,down,flat}
**Python helper `stat_card(label, value, eyebrow_text, delta, delta_dir)`** — writes the four typography lines of a KPI: eyebrow + label + big italic value + optional delta arrow.
Variants: `delta_dir` ∈ `up` (▲ green) / `down` (▼ red) / `flat` (— grey).
Use when: KPI tile contents (P6 dashboard).

### Topbar (D-2.10 + Defect 4 + 9 amendments)

#### topbar
**`st.container(key="topbar")` wrapper** — the page header strip: brand wordmark, breadcrumb, icon buttons. 14 px top padding, 0 px bottom padding (the bottom border IS the separator line — explicit exception to the symmetric-padding rule). 32 px bottom margin.
Use when: every authenticated page (P2-P7) starts with this. P1 sign-up doesn't have a topbar.

#### topbar-icon-{home,settings}
**`st.container(key="topbar-icon-{home,settings}")` wrapper** — 38×38 icon button. Glyph 22 px, flex-centred, transparent fill, 1.5 px paper-4 border. Hover lifts to paper-1 + 2 px stamp-soft shadow. **No underline** (Defect 9 broad strip handles BaseWeb's focus/focus-visible/hover lines).
Use when: top-bar quick actions (Home, Settings, future Search).

### Empty state

#### empty
**`st.container(key="empty")` wrapper** — dashed paper-3 border, 6 px radius, 36/28 padding, flex-column with both-axis centring (Defect 5).
Use when: a list page is empty (no classes, no mocks, no attempts).
Recipe:
```
with st.container(key="empty"):
    empty_state_text("Nothing here yet", "Add your first class to get started.")
    with st.container(key="btn-default-cta"):
        st.button("Add a class")
```

### `st.status` skin (D-2.21)

#### stStatus / stStatusWidget
Reach via `[data-testid="stStatus"]` and `[data-testid="stStatusWidget"]` (both selectors covered for cross-version compatibility). 4 px left-border `--accent-vibrant` while running, `--ok` when complete, `--accent-vibrant` when error. Paper-1 bg, eyebrow-style mono uppercase summary text.
Use when: P3 lecture ingestion progress block.

### `st.expander` skin (D-2.21)

#### stExpander
Reach via `[data-testid="stExpander"]`. Paper-1 bg, 6 px radius, 1.5 px paper-3 border. Hover lifts `(-1px, -1px)` + 2 px stamp-soft shadow + paper-0 bg.
Use when: collapsible "more details" panels (P5 difficulty breakdown).

### Typography helpers (D-2.19)

#### serif-h2 + heading_h2
**Python helper `heading_h2(text)`** — emits `<h2 class="serif-h2">…</h2>` (Fraunces SemiBold Italic 28 / 115% / -1% — Figma `Serif/H2` row, ruling Defect 6). Both bare `<h2>` (auto-rendered by `st.markdown("## …")`) and the `.serif-h2` utility class paint identically; callers can mix them.

#### surf-eyebrow + eyebrow
**Python helper `eyebrow(text)`** — Mono uppercase tracking-out 10 px `--paper-3`. Section labels above content blocks.

#### surf-caption + caption
**Python helper `caption(text)`** — Serif italic 13 px `--paper-3`. Helper text under headings.

#### surf-meta + meta
**Python helper `meta(text)`** — Mono mid-grey 11 px. Card metadata strips ("12 LECTURES · 78%").

### Surfaced-but-deferred (built in later plans)

- **summary-banner** (P5 final score, plan 02-06) — full-width paper-0 panel + 4 px stamp shadow + `score()` helper. Wrapper key reserved as `summary-banner`.
- **sidebar-list** (P3 Past Attempts, plan 02-04) — clickable list items with paper-2 dividers. Wrapper key `sidebar-list`.
- **file-uploader-skin** (P2 factsheet drop, plan 02-03 / 02-04) — `[data-testid="stFileUploader"]` skin. Drop-zone vs button-style still open (see § 11).

---

## 6. Stamp shadow recipe (the signature animation)

Hard-edged offset shadow with `border-radius: 0` on the shadow itself. Three offset scales:

- **3px** for default & tinted buttons, class card, interactive card (rest state)
- **4px** for interactive card hover (lifted state)
- **2px** for soft button, passive card, stat card

**Hover:** `transform: translate(-1px, -1px)` + shadow grows by 1px → "lifts off the page".

**Press (`:active`):** `transform: translate(2px, 2px)` + shadow shrinks to 1px → "pressed into the page".

**Disabled:** shadow removed entirely; surface = `--paper-2`, text = `--paper-3`.

**Don't add stamp shadow to** passive surfaces that don't accept clicks (page background, plain text containers, dividers).

---

## 7. Motion rules

**Transitions only — no `@keyframes`.** Hover/press states animate via CSS `transition` on `transform`, `box-shadow`, `background-color`, `color`, `border-color`, `filter`. Durations follow the motion tokens: `--t-fast` (120ms — buttons, input borders), `--t-base` (180ms — cards, tabs), `--t-slow` (320ms — rare).

### Accessibility — `prefers-reduced-motion`

A `@media (prefers-reduced-motion: reduce)` block at the bottom of `_CSS` disables `transition` and `transform` on all interactive surfaces (buttons, cards, MCQ options, slider thumb). Users who set "reduce motion" in their OS get the visual without the animation — color/border/shadow changes are still legible.

---

## 8. DOM reach map — how scoped CSS targets each Streamlit widget

> The most important section if you're building a new page. **You almost never need new CSS** if you wrap the right Streamlit widget in `st.container(key="...")`.

### 8.1 By Streamlit widget — what `data-testid` reaches it

| Streamlit widget | `data-testid` selector | Used by which wrapper keys |
|---|---|---|
| `st.button(...)` | `[data-testid="stButton"] button` | `btn-default`, `btn-ghost`, `btn-soft`, `btn-tinted-{accent,ok,info,warn}`, `topbar-icon-*`, any `card-interactive` overlay-button (Q3 spike) |
| `st.download_button(...)` | `[data-testid="stDownloadButton"] button` | inherits the same Mono caps-tracked label rule via the global Buttons block |
| `st.text_input(...)` | `[data-testid="stTextInput"] input` | (global rule — no wrapper needed) |
| `st.text_area(...)` | `[data-testid="stTextArea"] textarea` | (global rule) |
| `st.number_input(...)` | `[data-testid="stNumberInput"] input` | (global rule) |
| `st.date_input(...)` | `[data-testid="stDateInput"] input` | (global rule) |
| `st.time_input(...)` | `[data-testid="stTimeInput"] input` | (global rule) |
| `st.checkbox(...)` | `[data-testid="stCheckbox"] label`, plus `[data-baseweb="checkbox"] > div:first-child` for the 20×20 glyph | `mcq-opt-*` (custom 20×20 glyph + `:has(input:checked)` Off↔On flip) |
| `st.radio(...)` | `[data-testid="stRadio"] label[data-baseweb="radio"]` | (legacy — Phase 2 uses the unified MCQ checkbox per D-2.20) |
| `st.selectbox(...)` | `[data-testid="stSelectbox"] div[data-baseweb="select"]` | (global rule) |
| `st.multiselect(...)` | `[data-testid="stMultiSelect"]` | (global label rule; widget body styled by global rule) |
| `st.slider(...)` | `[data-testid="stSlider"] [role="slider"]` | (global rule — accent-vibrant thumb) |
| `st.toggle(...)` | `[data-testid="stToggle"] label` | (global label rule) |
| `st.tabs(...)` | `.stTabs [data-baseweb="tab"]` and `[data-baseweb="tab-list"]` | (global rule) |
| `st.expander(...)` | `[data-testid="stExpander"]` and `[data-testid="stExpander"] summary` | (D-2.21 skin — paper-1 bg, hover lift) |
| `st.status(...)` | `[data-testid="stStatus"]` AND `[data-testid="stStatusWidget"]` (both selectors for cross-version compat); summary via `summary` element | (D-2.21 skin — left-border state colors) |
| `st.file_uploader(...)` | `[data-testid="stFileUploader"]` | (skin pending — P2 / P3 plans 02-03 / 02-04) |
| `st.sidebar.{...}` | `[data-testid="stSidebar"]` | (P3 sidebar layout — plan 02-04) |
| `st.markdown(..., unsafe_allow_html=True)` paragraphs | `[data-testid="stMarkdownContainer"] p.surf-*` | every typography helper (`surf-eyebrow`, `surf-caption`, `surf-meta`, `surf-score`, `surf-stat-value`, etc.) |
| `st.alert(...)` / `st.info` / `st.success` / `st.warning` / `st.error` | `[data-testid="stAlertContainer"]` | (global rule — paper-3 border, serif body) |
| Vertical block (auto-emitted by `st.container`) | `[data-testid="stVerticalBlock"]` | used inside `mcq-card` to set 13 px gap; inside `empty` to centre children |
| Horizontal block (auto-emitted by `st.columns`) | `[data-testid="stHorizontalBlock"]` | used inside `empty` to centre buttons |

### 8.2 By wrapper key — which `data-testid` selectors does the rule reach?

For the inverse view (you have a `st-key-X` wrapper, what does its CSS rule actually paint into?):

| Wrapper key | Reaches into… |
|---|---|
| `btn-default`, `btn-ghost`, `btn-soft`, `btn-tinted-*` | `[data-testid="stButton"] button` (and its inner `<p>`) |
| `card-passive`, `card-interactive`, `class-card`, `stat-card` | the wrapper `<div>` itself plus inner `[data-testid="stMarkdownContainer"] p.surf-*` for typography helpers it contains |
| `mcq-card` | wrapper `<div>` + `[data-testid="stVerticalBlock"]` inside it (13 px gap) |
| `mcq-opt-{q}-{letter}` | wrapper `<div>` + `[data-testid="stCheckbox"] svg` (hidden) + `[data-baseweb="checkbox"] > div:first-child` (custom 20×20 glyph) + `[data-testid="stCheckbox"] > label` (full-width click target). Off/On driven by `:not(:has(input:checked))` / `:has(input:checked)` per D-2.20a. |
| `mcq-opt-{key}-correct`, `mcq-opt-{key}-incorrect` | same as above but state-baked via the suffix class |
| `topbar` | wrapper `<div>` (border-bottom = the separator line) |
| `topbar-icon-*` | `[data-testid="stButton"] button` inside, plus `<p>`, `<a>`, `[data-baseweb="button"]` and every descendant via the Defect-9 belt-and-braces strip |
| `empty` | wrapper `<div>` + `[data-testid="stMarkdownContainer"] p` (centred) + `[data-testid="stVerticalBlock"]` / `[data-testid="stHorizontalBlock"]` (centred children) |
| `summary-banner` (reserved, plan 02-06) | row pending — filled when 02-06 ships |
| `sidebar-list` (reserved, plan 02-04) | row pending — filled when 02-04 ships |

### 8.3 Selector style rules

- **Use `[class*="st-key-XYZ"]`**, not `.st-key-XYZ`. Streamlit appends a stable hash but the literal `st-key-{exact-string}` portion is preserved as a SUBSTRING of the class attribute, not a single class name.
- **Use `data-testid="…"` for widget reach**, not class names. Streamlit renames its emotion-CSS class names per build; `data-testid` is documented as stable.
- **No `.stApp` selector for component-level rules** — that's the page root; scoping there leaks into the entire app.

---

## 9. Adding a new component (5-step recipe)

1. **Wrap** in `st.container(key="my-component-x")` where `x` is the variant suffix.
2. **Add a section** to `_CSS` in `app/brain/theme/theme.py` keyed on `[class*="st-key-my-component"]`. Use the existing component sections as templates. Stick to the variables in § 2.
3. **Refresh both copies** — the production `theme.py` and the sandbox `previews/_theme.py`. They drift on purpose (CLAUDE.md visual preview gate); refresh during the next visual task that touches the component.
4. **Ship a preview** in `previews/components/my_component/preview.py` showing every variant + every state. Run via `streamlit run previews/components/my_component/preview.py` and **visually approve** before committing.
5. **Document it here** — append a section to § 5 with the description, variants, recipe, and reference screenshot. Keep the doc within the 500-line cap; if you exceed it, split into `ui/components.md` and link from here.

---

## 10. Where things live

```
app/brain/theme/theme.py     — production theme (CSS string + helpers)
app/brain/theme/theme.md     — sidecar walkthrough (per CLAUDE.md C-22)
previews/_theme.py            — sandbox copy (drift OK)
previews/components/*/        — per-component sandboxes
.streamlit/config.toml        — Streamlit native [theme] block (token mirror)
assets/fonts/                 — 3 variable WOFF2 files (~190 KB)
docs/design/figma_exports/    — local PNG cache of key Figma frames
ui/documentation.md           — this file
```

---

## 11. Open questions

[fills as waves close]

- [x] Is the Figma library `SURF_UI(old)` superseded by a non-`(old)` revision? — **Resolved** during Plan 02-01 (researcher run at commit `4a60394`): the file is canonical; the `(old)` suffix is a vestigial library-rename artefact. See `02-FIGMA-RESEARCH.md § 1` (Verdict).
- [ ] Should the `summary-banner` on P5 use the stamp shadow or sit flush? (Plan 02-06.)
- [ ] How should the file uploader (P2 factsheet, P3 lecture) skin? Drop-zone vs button-style? (Plan 02-03 / 02-04.)
- [ ] Token swap to a dark Paper palette for Phase 3 P7 Settings → out of Phase 2 scope.
- [ ] Cards/Quizz variant 3 (P5 review with rationale) — the rationale block needs to be restored in Figma before plan 02-05 (P4 take-mock card geometry) so plan 02-05 can lock against the final spec. Tracked as OQ-1 in `02-FIGMA-RESEARCH.md` per commit `f6da2d0`.

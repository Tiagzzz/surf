# Surf — Design System Documentation

> **Audience:** Tiago + teammates. **Not** consumed by Claude tooling — this is a documentation artifact.
> **Status:** STUB scaffolded 2026-05-02 during phase 2 planning. Sections marked `[TBD — plan 02-01]` are filled by the Figma component-logic researcher (per `02-CONTEXT.md` D-2.26) before plan 02-01 execution closes. Sections marked `[fills as waves close]` accrete content during phase 2 execution and continue in later phases.
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

[TBD — plan 02-01 — researcher fills one section per scoped component, sourced from `theme.py` + the Figma component descriptions]

Each component section will have:

```
### {component-name}
**`st.container(key="{key}")` wrapper** — {1-line description}

Variants: {list}
Use when: {rule}
Don't use when: {anti-pattern}

Composition recipe:
    with st.container(key="..."):
        st.button(...)

Reference: docs/design/figma_exports/{node}.png
```

**Components in scope for Phase 2** (initial list — researcher reconciles against Figma for any I missed):

- `btn-default`, `btn-ghost`, `btn-soft`, `btn-tinted-{accent,ok,info,warn}`
- `card-passive`, `card-interactive`, `class-card`, `stat-card`
- `topbar`, `topbar-icon-{home,settings}`
- `empty` (with `empty_state_text()` helper)
- `mcq-opt-{off,on,correct,incorrect}` (D-2.20 spec)
- `mcq-card` (D-2.23 spec)
- `difficulty-display` (D-2.24 spec — 5-star)
- `chip` (4 variants: outline, accent, solid, dashed)
- `step` (3 states: done, active, todo)
- `surf-score` (3 thresholds: low / mid / high)
- `surf-stat-value`, `surf-delta-{up,down,flat}`
- `summary-banner` (P5 — to be added during plan 02-06)
- `sidebar-list` pattern for Past Attempts (P3 — to be specified during plan 02-04b)
- `expander` skin (P5 difficulty breakdown — D-2.21)
- `status` skin (P3 ingestion log — D-2.21)

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

[TBD — plan 02-01 — researcher fills one row per Streamlit widget Phase 2 uses]

**Initial table** (researcher expands):

| Streamlit widget | DOM selector | Wrapper key activates… |
|---|---|---|
| `st.button(...)` | `[data-testid="stButton"] button` | `btn-default`, `btn-ghost`, `btn-soft`, `btn-tinted-*` |
| `st.text_input(...)` | `[data-testid="stTextInput"] input` | (no wrapper needed — global rule) |
| `st.text_area(...)` | `[data-testid="stTextArea"] textarea` | (no wrapper needed) |
| `st.checkbox(...)` | `[data-testid="stCheckbox"] label` | `mcq-opt-{state}` (with custom 20×20 checkbox glyph) |
| `st.radio(...)` | `[data-testid="stRadio"] label[data-baseweb="radio"]` | (used elsewhere — for MCQ, prefer the unified checkbox per D-2.20) |
| `st.selectbox(...)` | `[data-testid="stSelectbox"] div[data-baseweb="select"]` | (no wrapper needed) |
| `st.slider(...)` | `[data-testid="stSlider"] [role="slider"]` | (no wrapper needed) |
| `st.tabs(...)` | `.stTabs [data-baseweb="tab"]` | (no wrapper needed) |
| `st.expander(...)` | `[data-testid="stExpander"]` | (D-2.21 skin pending) |
| `st.status(...)` | `[data-testid="stStatusWidget"]` | (D-2.21 skin pending) |
| `st.file_uploader(...)` | `[data-testid="stFileUploader"]` | (skin pending) |
| `st.sidebar.{...}` | `[data-testid="stSidebar"]` | (P3 sidebar layout, plan 02-04b) |

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

- [ ] Is the Figma library `SURF_UI(old)` superseded by a non-`(old)` revision? (Researcher to check during plan 02-01 per D-2.26.)
- [ ] Should the `summary-banner` on P5 use the stamp shadow or sit flush? (Plan 02-06.)
- [ ] How should the file uploader (P2 factsheet, P3 lecture) skin? Drop-zone vs button-style? (Plan 02-03 / 02-04b.)
- [ ] Token swap to a dark Paper palette for Phase 3 P7 Settings → out of Phase 2 scope.

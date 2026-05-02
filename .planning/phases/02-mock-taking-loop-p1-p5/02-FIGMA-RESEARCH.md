# 02 — Figma Research (SURF_UI design system audit)

**Phase:** 02 — Mock Taking Loop (P1–P5)
**Author:** Claude (research pass, 2026-05-02)
**Status:** v1 — locked open questions, ready for Phase 2 plan consumption
**Figma file:** [SURF_UI](https://www.figma.com/design/EYjkvHArrBonuiG2JUS2sE/SURF_UI?node-id=25-2) · `fileKey=EYjkvHArrBonuiG2JUS2sE`
**Scope:** page `Components` (node `25:2`) — components on other pages explicitly out of scope per user direction

---

## 0. Top-level principle (locked this session)

> **The design system applies by default. When a rule is incompatible with Streamlit, adapt the design — don't fight Streamlit.**

Practical effect: Phase 2 wrappers don't have to be 1:1 with Figma. They have to be *as close as Streamlit allows*. Divergences are documented, not avoided. The Streamlit-feasibility tier (§5 of the rule-book; Section 6 of this doc) is the gate — anything tagged `custom` or `extras` gets reviewed for adaptation before being faithfully reproduced.

**Corollary — only hard-stamp shadows ship.** SURF_UI uses only hard-offset, no-blur "stamp" drop shadows. CSS overrides MUST NOT introduce blurred/soft shadows like `0 4px 8px rgba(0,0,0,0.1)`. Only the named stamps (§5.4 below).

---

## 1. Verdict

| Property | Finding |
|---|---|
| **Library status** | SURF_UI(old) is **self-published** (this file IS the design-system source-of-truth — `libraries_added_to_file: []` confirms zero external library subscriptions) |
| **Library key** | `lk-0b93bb3c9cdaf4d3f3b30140c53b81c741206a021986040322f3501ea1e4bf627bac080f25f718f05c0958b3ac4eb92e960542ccc824c342639a0a80362f126d` |
| **Theming** | Single-mode only across all 48 variables. No light/dark axis. Dark-mode is post-MVP per `RULES_design_system.md §11.1` |
| **Aesthetic** | Brutalist/editorial — cream Paper background, hard-offset stamp shadows, italic Fraunces headings, monospace caps for buttons/chips/eyebrows. Strong, opinionated, locked |
| **Total inventory** | 48 variables · 15 text styles · 7 effect styles · 298 components/component-sets scanned (per `03_styles.md` frontmatter) |
| **Owner** | Tiago (`tiagophilip.reimann@student.unisg.ch`, Surf team) |

**Implication for Phase 2:** the design system is genuinely lean and self-contained. No external Material/iOS/Simple-DS dependencies to migrate. Token reconciliation only needs to happen against this file's own variables.

---

## 2. Governance — the rule-book

The system is governed by a written rule-book. **Read it before composing any new pattern.**

**Rule-book file:** `~/CS/CS_Obsidian/CS_EN_VF/work_log/2026-04-30_figma_audit/RULES_design_system.md` (913 lines)
**Phase 2 plans for it:** surfaces in-repo as `ui/documentation.md` (per `02-01-PLAN.md`)
**NLM mirror:** `2026-04-30 Surf — Design System` notebook (id `c3734391-80f6-4a04-be23-dee12684624e`), source `04_RULES_design_system` (id `c4c0f37b-1a71-4203-95f6-383ba005a035`)

### 2.1 Rule-book sections

| § | Topic |
|---|---|
| 1 | Naming conventions (path-prefix taxonomy + variant naming) |
| 2 | Variable taxonomy (collections, migrations) |
| 3 | Style-binding rules (enforceable by visual-verifier) |
| 4 | Text-style rules |
| 5 | Component-construction rules (Phase 3 hard requirements) |
| 6 | Streamlit-feasibility classification |
| 7 | State-coverage matrix (bird's-eye) |
| 8 | The 9 missing components (+ 8 also-missing) — **❗ stale, see §10 below** |
| 9 | Rules for adding new colour variables |
| 10 | Verification protocol for the visual-verifier agent |
| 11 | Open questions / TBD |
| 12 | How downstream agents use this file |

### 2.2 Key rule-book sections referenced in component descriptions

These appear as `(rule-book §X.Y)` annotations inside Figma component descriptions — Phase 2 wrappers should respect them:

**§3.6 exception 2 — `(hit-target)` layer suffix:**
> "Pure transparent fills (`#FFFFFF` at alpha 0) used as invisible click hit-targets. These MUST be flagged in the layer name with the suffix `(hit-target)`."

Example: `Display / Chip` (node `2118:60`) has an outer transparent fill that's the click zone, NOT chrome. Don't reproduce it as a visible element.

**§5.1.c — Button Loading variant:**
> "Loading shows the same fill / stroke / shadow as Rest, but the text label is replaced with a spinner glyph. The spinner is a future `Foundation / Glyph / Spinner` (does not yet exist — flag for Phase 3A). Until the spinner exists, the Loading variant MAY use a placeholder ellipsis `…` in `Mono/Button Label`."

**Tiago's session ruling (2026-05-02):** Spinner is **deleted, not deferred**. Buttons in `Loading` always render `…`. App-level loading uses Streamlit's built-in `st.spinner()`. Do not build a custom Figma spinner.

**§5.6 — Canonical example variant:**
> "Every component-set MUST have one canonical example variant fully token-bound. The visual-verifier checks one variant per set (the canonical one), not every variant. Mark the canonical with a layer-description suffix `(canonical)` so the verifier knows which to check."

Picking convention:
- State-axis sets → **Default / Rest**
- Variant-axis sets → **leftmost listed**
- Multi-axis sets → **most-used combination** (e.g. `Card / Shadow=Default, State=Default`)

---

## 3. Locked taxonomy — 6 families (path-prefix names, never extend without Tiago)

Per rule-book §1.1. Every component MUST live under one of these six prefixes. Adding a 7th family requires written justification ruling out the existing six.

| Family | Purpose | Example |
|---|---|---|
| `Foundation/` | Atoms — icons, glyphs, brand marks. No business logic, no states beyond a `Direction` axis. | `Foundation / Icon / search` |
| `Display/` | Read-only data presenters. User looks at them; they don't accept clicks. | `Display / Progress` |
| `Interactive/` | Form controls and clickables. Accept input, emit events, MUST have state coverage per rule-book §5. | `Interactive / Button / *` |
| `Cards/` | Composite content panels — medium-sized "boxes" with visible chrome (border + shadow). | `Cards / Card`, `Cards / Quizz` |
| `Structure/` | Page-level scaffolding — topbar, footer, sidebars, page header, modal shell. | `Structure / Topbar / Default` |
| `Notification/` | Transient or modal messages — anything that interrupts the user. | `Notification / Toast` |

**Special name lock** (§1.5): `Cards / Quizz` — yes, "Quizz" with two Z's. Idiomatic to Surf, propagates across multiple files. **MUST NOT** be renamed to "Quiz" — would force a cross-file migration with zero design value.

---

## 4. Component catalog (per-family, with Streamlit tier)

Per rule-book §6.1 the cost tiers are:

- **`core`** — translates 1:1 with built-in Streamlit widgets (`st.*`)
- **`extras`** — needs `streamlit-extras` library (allowed per project CLAUDE.md)
- **`custom`** — needs `st.components.v1.html` HTML/CSS/JS bridge — expensive, only when no `core`/`extras` path
- **`hard`** — translates poorly, reconsider or simplify

Per the §0 top-level principle, **`custom` and `extras` components are adaptation candidates** — review before faithful reproduction.

### 4.1 Foundation/

| Component | Variants | Tier | Streamlit translation |
|---|---|---|---|
| `Foundation / Icon / *` | 13+ icons (info, flag, edit, File, trash, check, close, search, arrow-left, arrow-right, settings, external, chevron-down…) | `core` | Inline SVG via `st.markdown(unsafe_allow_html=True)` |
| `Foundation / Glyph / *` | (planned but minimal) | `core` | Same as icons |
| `Foundation / Brand / Mark` | brand marks | `core` | `st.image` |

### 4.2 Display/

| Component | Variants | Tier | Streamlit translation |
|---|---|---|---|
| `Display / Chip` | Variant=Neutral (more variants exist) | `core` | `st.markdown` with custom CSS for pill shape |
| `Display / Data Table` | — | `core` | `st.dataframe` |
| `Display / Difficulty` | Level 0–5 (numeric on purpose, maps to Idea v1 §4.4 6-criteria difficulty) | `core` | Render N filled stars + (5−N) empty stars via stacked icons |
| `Display / Progress` | — | `core` | `st.progress(value)` |
| `Display / Progress Stepped` | — | `core` | Custom: row of N divs with `width=100%/N`, conditional fill |
| `Display / Skeleton / Card` | — | `core` | `st.empty()` placeholder |
| `Display / Stat Card` | Trend axis | `core` | `st.metric(label, value, delta)` |
| `Display / Step Item` | — | `core` | Markdown row with conditional icon per status |
| `Display / Timer` | Idle / Running / Stopped (post §5.4 rename) | `core` | Recompute `elapsed = now - start_ts` per refresh |
| `Display / Tooltip` | — | **`extras`** | `streamlit-extras` tooltip |

### 4.3 Interactive/

| Component | Variants | Tier | Streamlit translation |
|---|---|---|---|
| `Interactive / Button / Default` | State = Rest / Hover / Pressed / Disabled / **Loading=`…` placeholder** | `core` | `st.button("LABEL")` — disabled=True for non-interactive |
| `Interactive / Button / Ghost` | same states | `core` | `st.button` + CSS class for ghost hue |
| `Interactive / Button / Soft` | same states | `core` | `st.button` + CSS class for soft hue |
| `Interactive / Button / Accent` | same states | `core` | `st.button` + CSS class for accent hue |
| `Interactive / Button / Tinted` | + Color={Accent, Info, OK, Warn} per §2.3 | `core` | same pattern |
| `Interactive / Checkbox` | Off / On / Hover / Focus / Disabled-Off / Disabled-On / Indeterminate | `core` | `st.checkbox` |
| `Interactive / Radio` | Off / On / Hover / Focus / Disabled-Off / Disabled-On | `core` | `st.radio` |
| `Interactive / Toggle` | Off / On (Hover, Focus, Disabled state-coverage gaps) | `core` | `st.toggle` |
| `Interactive / Slider` | Default / Hover / Pressed (Dragging) / Size axis | `core` | `st.slider` |
| `Interactive / Text Input` | Default / Hover / Focus / Filled / Error / Disabled | `core` | `st.text_input` |
| `Interactive / Password Input` | + Visibility axis | `core` | `st.text_input(type="password")` |
| `Interactive / Dropdown / Default` | Closed / Open | `core` | `st.selectbox` |
| `Interactive / Dropbox` | Default | `core` | `st.file_uploader` |
| `Interactive / Segmented / Default` | — | **`extras`** | `streamlit-extras.option_menu` |
| `Interactive / MCQ Option` | Off / On / Correct / Incorrect / Missed | `core` | `st.radio(options=[...])` |
| `Interactive / Tab` | Default / Active | `core` | `st.tabs([...])` |

### 4.4 Cards/

| Component | Variants | Tier | Streamlit translation | Adaptation note |
|---|---|---|---|---|
| `Cards / Card` | Shadow={Default, XS, SM, LG, Lift} × State={Default, Selected} | `core` | `st.container(border=True)` + CSS for shadow variants | Faithful reproduction OK |
| `Cards / Card Interactive` | Rest / Hover / Pressed / Disabled | **`custom`** | `st.container` + click handler via overlay button | **Adapt:** wrap `st.container` and a transparent `st.button` as click-target. Hover not natively supported. |
| `Cards / Class` | Priority axis | **`custom`** | Composite layout: priority-tag + threshold-bar + last-attempt + click | **Adapt:** rule-book itself proposes fallback — `st.container` with internal `st.metric` + `st.progress`. Use the fallback unless the visual delta is unacceptable. |
| `Cards / Empty State` | Size axis | `core` | `st.info` or `st.container` with centered markdown |
| `Cards / Quizz` | Unanswered / Answered / Checked | **`custom`** | Question + 4 options + difficulty stars + footer buttons | **Adapt:** use `st.radio` for the 4 options + `st.button` for actions inside `st.container(border=True)`. Per rule-book §3.6 exception 3, the mint-wash highlight (`#9EC7AA` → `color/Status/OK-Wash`) is the locked correct-answer cue. Spec extracted at node `4045:282` — see screenshot at `docs/design/figma_exports/node_4045-282_mcq_take_mock.png`. |
| `Cards / Quizz / Summary` | Result={Pass, Borderline, Fail} | `core` | `st.metric(score)` + `st.markdown` |

### 4.5 Structure/

| Component | Variants | Tier | Streamlit translation |
|---|---|---|---|
| `Structure / Page Header` | (currently errored — duplicate variant key per rule-book §5.3) | `core` | `st.markdown` heading block |
| `Structure / Topbar / Default` | Variant={Default, WithBreadcrumb} | `core` | Streamlit shows topbar implicitly via page config |
| `Structure / Topbar / Breadcrumb` | Type={Link, Current} | `core` | `st.markdown` breadcrumb row |
| `Structure / Sidebar / Form Panel` | Position={Slide-In, Modal} × State={Default, WithError} | `core` + custom | `st.sidebar` for slide-in; `st.dialog` for modal variant |
| `Structure / Sidebar / Nav Row` | Default / Hover / Active | `core` | `st.button` styled |
| `Structure / Sidebar / Navigation` | Collapsed | `core` | `st.sidebar.radio` |
| `Structure / Sidebar / Widget List` | — | `core` | Native `st.sidebar` content |
| `Structure / Modal / Scrim` | Size axis | `core` | `st.dialog` |
| `Structure / Wizard Step` | Step1 / Step2 (post-rename per §1.3 — formerly State3/State4) | `core` | `st.form` |

### 4.6 Notification/

| Component | Variants | Tier | Streamlit translation |
|---|---|---|---|
| `Notification / Confirmation Dialog` | Tone={Default, Destructive} | `core` | `st.dialog` |
| `Notification / Dialog` | Variant={Default, Destructive} | `core` | `st.dialog` |
| `Notification / Message` | Variant={Success, Error} | `core` | `st.success` / `st.error` |
| `Notification / Toast` | Kind={Info, Success, Warning, Error} | **`extras`** | Streamlit has a `st.toast` primitive, otherwise `streamlit-extras` |

### 4.7 Form/ — (legacy namespace, will fold into Interactive/)

`Form / Text Input` and `Form / Password Input` exist as published components. Rule-book §1.4 marks these for rename to `Interactive / Text Input` / `Interactive / Password Input` in Phase 3. Phase 2 wrappers should reference the **future** name (`Interactive / *`) to avoid double-rework.

---

## 5. Token catalog — complete (48 variables · 15 text styles · 7 effect styles)

Source: `~/CS/CS_Obsidian/CS_EN_VF/work_log/2026-04-30_figma_audit/03_styles.md`

### 5.1 Colour variables (18 total — 15 in `html.to.design` + 3 in `Tokens`)

#### Base — paper / shadow neutrals (8)

| Variable | Hex | Role |
|---|---|---|
| `color/Base/Paper` | `#FDF9F2` | Cream surface — universal "paper" background. **Not pure white.** |
| `color/Base/Paper0` | `#F5EFE4` | Slightly darker paper — input fields, subtle layering |
| `color/Base/Paper1` | `#EDE4D2` | Darker paper — disabled chrome, dropdown items |
| `color/Base/Paper2` | `#C0B49B` | Mid-tone — disabled button fills, dividers |
| `color/Base/Paper3` | `#6C6455` | Tertiary text / meta |
| `color/Base/Paper4` | `#3B362C` | Heading-on-dense-or-dark text (case-by-case per §3.1.e) |
| `color/Base/Paper5` | `#28251F` | **Universal text-on-paper colour. Most-used token in the file (77+ usages).** |
| `color/Base/Shadow` | `#171512` | Borders, drop-shadow colour. True near-black. |

#### Accent — warm red brand (4)

| Variable | Hex | Role |
|---|---|---|
| `color/Accent/Deep` | `#9D2815` | Destructive text, dialog destructive variant |
| `color/Accent/Vibrant` | `#C8361D` | Active states, error strokes, focus indicator (proposed) |
| `color/Accent/Soft` | `#E8A798` | Coral — incorrect MCQ option, Wizard Step error |
| `color/Accent/Wash` | `#F7D9D1` | Selected card fill, dialog tint, breadcrumb hover |

#### Status — semantic OK / Warn / Info (3)

| Variable | Hex | Role |
|---|---|---|
| `color/Status/OK` | `#2D6A3F` | Success message, check glyph, class threshold-met |
| `color/Status/Warn` | `#B8860B` | Warning toast, footer flag |
| `color/Status/Info` | `#2A5D7C` | Info toast |

**Status canonical (rule-book §2.3):** prefer `color/Status/*` over the duplicate `color/Accent/{Blue,Green,Yellow}`. The Accent triplet exists by hex-duplicate but is queued for deprecation.

#### Tinted accents — duplicates of Status by hex, in `Tokens` collection (3)

| Variable | Hex | Note |
|---|---|---|
| `color/Accent/Blue` | `#2A5D7C` | Duplicate of `Status/Info` — **DEPRECATED**, will alias |
| `color/Accent/Green` | `#2D6A3F` | Duplicate of `Status/OK` — **DEPRECATED**, will alias |
| `color/Accent/Yellow` | `#B8860B` | Duplicate of `Status/Warn` — **DEPRECATED**, will alias |

#### Net-new colour tokens (4 confirmed by Tiago, 2026-04-30 — not yet in file)

| Variable | Hex | Reason | Where to bind first |
|---|---|---|---|
| `color/Base/White` | `#FFFFFF` | 31 hard-coded white instances need a home | Topbar, Sidebar Nav, Form Panel, Dropbox, Footer, Dialog, Message |
| `color/Base/Shadow-Soft` | `#1A1814` | Drift on `shadow/lift` colour — currently raw hex | `shadow/lift.color`, `shadow/soft.color` |
| `stroke/border-focus` | aliased to `Accent/Vibrant` | Focus-ring accessibility | Text Input / Password Input / Search `State=Focus` |
| `color/Status/OK-Wash` | `#9EC7AA` | Mint-wash on Quizz correct-answer + MCQ Option | `Cards / Quizz`, `Interactive / MCQ Option` |

### 5.2 Spacing — `Tokens` collection · scope `GAP` (10)

| Variable | px | Used by |
|---|---|---|
| `sp/1` | 4 | Confirmation Dialog |
| `sp/2` | 8 | Modal Shell, Confirmation Dialog |
| `sp/3` | 12 | Modal Shell, Confirmation Dialog |
| `sp/4` | 16 | Modal Shell |
| `sp/5` | 20 | Modal Shell, Confirmation Dialog |
| `sp/6`–`sp/10` | 24, 32, 40, 56, 72 | *(orphan — forward-looking developer reference)* |

### 5.3 Radii — `Tokens` collection · scope `CORNER_RADIUS` (5)

| Variable | px | Used by |
|---|---|---|
| `radius/xs` | 3 | *(orphan)* |
| `radius/sm` | 4 | Skeleton Card / Table / Quiz, Tooltip |
| `radius/md` | 6 | Skeleton Card / Quiz, Toast, Stat Card |
| `radius/lg` | 10 | Modal Shell, Confirmation Dialog |
| `radius/pill` | 999 | *(orphan)* |

**Phase 2 note:** the Quizz card uses 6px radius (Card/Card; matches `radius/md`). Buttons use 4px (Card stroke pattern; matches `radius/sm`). Map to `border-radius` in CSS.

### 5.4 Borders — `Tokens` collection · scope `STROKE_FLOAT` (4)

| Variable | px | Used by |
|---|---|---|
| `border/hair` | 1 | *(orphan)* |
| `border/rule` | 1.5 | Stat Card |
| `border/heavy` | 2 | *(orphan — but the Quizz/Card stroke widths in canvas ARE 2px, just not bound)* |
| `border/dashed` | 1 | *(orphan)* |

### 5.5 Layout — `Tokens` collection · scope `WIDTH_HEIGHT` (6, all orphan)

| Variable | px |
|---|---|
| `layout/column` | 640 |
| `layout/wide` | 960 |
| `layout/widest` | 1120 |
| `layout/gutter` | 24 |
| `layout/gutter-mobile` | 20 |
| `layout/page-top` | 56 |

Forward-looking — Streamlit page width is configured via `st.set_page_config(layout="wide")`. Consider pinning Streamlit content to `layout/wide` (960) or `layout/widest` (1120) for the broadest pages.

### 5.6 Motion — `Tokens` collection (5, all orphan + Figma can't bind motion to vector nodes)

| Variable | Type | Value |
|---|---|---|
| `motion/fast` | FLOAT | 120ms |
| `motion/base` | FLOAT | 180ms |
| `motion/slow` | FLOAT | 320ms |
| `motion/ease-out` | STRING | `cubic-bezier(0.2, 0, 0, 1)` |
| `motion/ease-in-out` | STRING | `cubic-bezier(0.4, 0, 0.2, 1)` |

**Phase 2 use:** these are dev-handoff references for any CSS `transition` values added by `st.html("<style>...")` overrides.

### 5.7 Text styles — 15 (8 Serif + 7 Mono)

#### Serif/* — Fraunces (8)

Fraunces with axes `'SOFT' 0, 'WONK' 1` per the Quizz code spec.

| Style | Weight | Size | Line | Tracking | Used by |
|---|---|---|---|---|---|
| `Serif/Display` | Black Italic | 64 | 95% | -2% | Brand Wordmark, Quizz Summary, Timer |
| `Serif/H1` | Black Italic | 42 | 95% | -2% | Page Header, Cards/Class, Wizard Step, Timer |
| `Serif/H2` | SemiBold Italic | 28 | 115% | -1% | Cards/Class, Stat Card, **Quizz question text** |
| `Serif/H3` | SemiBold Italic | 22 | 115% | 0 | Cards/Card, Carousel, Modal Shell |
| `Serif/H4` | SemiBold | 18 | 130% | 0 | Sidebar/Form Panel |
| `Serif/Lead` | Regular | 19 | 165% | 0 | *(orphan)* |
| `Serif/Body` | Regular | 17 | 150% | 0 | Cards/Card, Dropdown items, Checkbox label |
| `Serif/Caption` | Italic | 13 | 140% | 0 | *(orphan)* |

#### Mono/* — JetBrains Mono (7)

Fallback `Noto Sans` for ✓ glyphs.

| Style | Weight | Size | Line | Tracking | Case | Used by |
|---|---|---|---|---|---|---|
| `Mono/DROPBOX Label` | Medium | 19 | 100% | 10% | UPPER | Page Header, Form Panel, Dropbox |
| `Mono/Eyebrow` | Medium | 10 | 150% | 18% | UPPER | Brand Wordmark, Form Panel, Cards/Class |
| `Mono/Meta` | Regular | 11 | 150% | 8% | original | Form Panel, Dropbox, Stat Card |
| `Mono/Button Label` | Bold | 11 | 100% | 10% | UPPER | **All button text — locked** |
| `Mono/Tag` | Medium | 10 | 100% | 10% | UPPER | Tooltip, Quizz/FreeResponse, Quizz/Summary |
| `Mono/Code Inline` | Regular | 14 | 150% | 0 | original | *(orphan)* |
| `Mono/Code Block` | Regular | 14 | 150% | 0 | original | *(orphan)* |

**❗ Known issue (rule-book §4.1):** every text style has `boundVariables: {}`. **Colours are set per-text-node, not via the style.** That's why `Paper5` shows up 77+ times in raw usage. Phase 3 will fix this. For Phase 2, when you apply a Mono/Button Label class in CSS, set `color: var(--color-base-paper5)` explicitly.

### 5.8 Effect (shadow) styles — 4 (locked, hard stamps only)

Per Tiago's ruling (2026-05-02): all blurred / non-stamp shadows are deleted on aesthetic grounds. The previous `shadow/lift` (used on 4 components), `shadow/soft` (orphan), and `stamp-star` (orphan) are all removed. The 4 ex-`shadow/lift` consumers must rebind to `shadow/stamp-lg` or strip the shadow entirely — see §11 cleanup ticket.

| Style | Spec | Bound colour | Used by |
|---|---|---|---|
| `shadow/stamp-xs` | offset 0.5/0.5 · radius 0 · spread 0 | `color/Base/Shadow` | Slider, Cards/Card, Buttons, Segmented (+22 more) |
| `shadow/stamp-sm` | offset 2/2 · radius 0 · spread 0 | `color/Base/Shadow` | Slider, Step Item, Cards/Card, Difficulty (+2 more) |
| `shadow/stamp` | offset 3/3 · radius 0 · spread 0 | `color/Base/Shadow` | Cards/Card, Card Interactive, Dropdown, Buttons (+9 more) |
| `shadow/stamp-lg` | offset 5/5 · radius 0 · spread 0 | `color/Base/Shadow` | Cards/Card, Notification/Dialog, Confirmation Dialog (+ probable rebinding from `shadow/lift` consumers) |

**The 4-step `shadow/stamp-*` ramp is the complete and locked visual signature.** Hard, opaque, no blur, ever. Card `Shadow=Default` → `stamp`; `Shadow=XS/SM/LG` → matching ramp step. Phase 2 CSS overrides MUST NOT introduce any blurred / soft shadows — only the four named stamps are allowed.

### 5.9 Inferred pairing rules — Phase 2 wrapper defaults

Phase 2 wrappers MUST reproduce these pairings unless Streamlit forces a divergence:

1. **Text-on-paper default:** `color/Base/Paper5` text over `color/Base/Paper` surface.
2. **Text-on-dark-button:** `color/Base/Paper` text over `color/Base/Paper5` surface (cream-on-near-black, NOT pure white-on-black — this is the brand).
3. **Card stroke:** `color/Base/Shadow` border paired with `color/Base/Paper` fill (Cards/Card, Topbar, Dialog, Text Input default).
4. **Card `Shadow=` axis** maps 1:1 to the `shadow/stamp-*` ramp (4 stamps only).
5. ~~**Card `Shadow=Lift`** drops the stroke, swaps in `shadow/lift` blur.~~ **Removed per shadow ruling — Lift variant either rebinds to `shadow/stamp-lg` or has no shadow.**
6. **Card Interactive state ramp:** Rest=`stamp-xs` · Hover=`stamp` · Pressed=no shadow · Disabled=Paper2 fill / Paper3 stroke / Paper4 text.
7. **Text Input `State=Focus`** today reuses Default's `Shadow` stroke (no focus indicator). Phase 2 should manually add a `:focus` ring using `Accent/Vibrant` until `stroke/border-focus` lands.
8. **Notification destructive variants** flip text colour to `Accent/Deep`, NOT background. Background stays `Paper`.
9. **Cards/Card `State=Selected`** swaps fill `Paper` → `Accent/Wash`, stroke `Shadow` → `Accent/Vibrant`.

---

## 6. Streamlit translation — adaptation matrix

Per the §0 top-level principle, each component's tier dictates the build path. Components flagged below for adaptation should be reviewed in Phase 2 *before* faithful reproduction.

| Tier | Action | Components |
|---|---|---|
| `core` | **Faithful reproduction.** Use `st.*` widget + minimal CSS overrides via `st.html("<style>...")`. | All buttons, Card, Empty State, Quizz Summary, all inputs, dropdowns, MCQ Option, Tab, Page Header, Topbar, Sidebar, Modal/Scrim, Wizard Step, Confirmation Dialog, Dialog, Message, plus all Display/* and Foundation/* |
| `extras` | **Use `streamlit-extras` library.** Allowed per project CLAUDE.md ("not in the course but commonly mentioned alongside Streamlit"). | `Display / Tooltip`, `Interactive / Segmented / Default`, `Notification / Toast` |
| `custom` | **Adapt before reproducing.** Review with Tiago — propose `core` fallback first. | `Cards / Card Interactive` (no Streamlit hover primitive — adapt via overlay button); `Cards / Class` (rule-book proposes `st.container` + `st.metric` + `st.progress` fallback); `Cards / Quizz` (use `st.radio` + `st.button` inside `st.container(border=True)` — see §4.4) |
| `hard` | n/a — no components in this tier | — |

**Adaptation rule:** when a `custom`-tier component is adapted to `core`, the divergence MUST be documented in the Phase 2 plan with a one-line "what changes vs. Figma" note.

---

## 7. Locked design rulings (this session, 2026-05-02)

| # | Ruling | Source |
|---|---|---|
| 1 | Streamlit-precedence: design system applies UNLESS incompatible with Streamlit; then adapt the design | §0 |
| 2 | Spinner is **deleted, not deferred**. App-level loading uses `st.spinner()`. Buttons in `Loading` always render `…` | §2.2 |
| 3 | Missing components were **deliberately deleted** by Tiago. They are NOT a Phase 3 build-missing backlog. Rule-book §8 (the 9-required + 8-also-missing) is OUT of scope for Phase 2/3. | rule-book §8 marked stale |
| 4 | Soft / blurred shadows deleted on aesthetic grounds. **Final shadow set: 4 hard stamps only** (`stamp-xs`, `stamp-sm`, `stamp`, `stamp-lg`). The 4 ex-`shadow/lift` consumers (Card Lift variant, Sidebar/Form Panel, Toast, Modal Shell) must rebind to `stamp-lg` or strip the shadow per-component. | §5.8 |
| 5 | Phase 3 cleanup tickets are included as future-work appendix, not active scope | §11 |

### 7.1 Earlier locked rulings (Tiago, 2026-04-30 — reproduced from rule-book §11.2)

| # | Item | Resolution |
|---|---|---|
| 1 | Mint-wash hex `#9EC7AA` token name | `color/Status/OK-Wash` |
| 2 | Wizard Step `State3 / State4` rename | `Step1 / Step2` (conditional: re-escalate if Phase 3 inspection reveals loading/error/success semantics) |
| 3 | FLAG icons (`Foundation / Icon / flag, flag-filled`) | DELETE — Idea v1 §6 confirms FLAG dropped at 2026-04-28 pivot |
| 4 | `Cards / Carousel` | DELETE — warn-flagged + zero instances |
| 5 | `Structure / Footer` | DELETE — warn-flagged + zero instances on any of the 7 pages per Idea v1 |

---

## 8. Cross-references

### Files (in user's CS Obsidian vault)

```
~/CS/CS_Obsidian/CS_EN_VF/work_log/2026-04-30_figma_audit/
├── 00_nlm_bootstrap.md         (159 lines)
├── 01_components.md            (214 lines — full component inventory + variants)
├── 02_pages.md                 (289 lines — page-level audit, P1–P7)
├── 03_styles.md                (218 lines — token catalog, source for §5 of this doc)
├── 04_triage.md                (213 lines)
├── 05a_update_log.md, 05b_build_log.md, 05c_update_log.md, 05d_build_log.md
├── 07_verifier_log.md          (222 lines)
├── 08_page_rebuild_log.md      (363 lines)
└── RULES_design_system.md      (913 lines — the rule-book; primary governance source)
```

### NLM notebooks

| Notebook | ID | Role |
|---|---|---|
| `2026-04-30 Surf — Design System` | `c3734391-80f6-4a04-be23-dee12684624e` | Hosts the rule-book mirror (`04_RULES_design_system`, source id `c4c0f37b-1a71-4203-95f6-383ba005a035`) |
| `2026-04-28 Surf — Idea & Progress` | `3e02fa3d-8ce2-4a6d-9da7-ac974e32452f` | Hosts `Idea v1`, decision logs, Phase 1/2 build updates, Phase 2 planning lock |
| `2026-04-28 Surf — Lectures` | `6bc919e0-21c9-452e-b203-507f078efa33` | Reference for course-aligned implementation patterns (read-only) |

### Repo artefacts

```
docs/design/figma_exports/
├── node_25-2.png                          (Components-page overview thumbnail)
└── node_4045-282_mcq_take_mock.png        (Cards / Quizz, three states)
```

### Figma URLs

- File: https://www.figma.com/design/EYjkvHArrBonuiG2JUS2sE/SURF_UI?node-id=25-2
- `Cards / Quizz`: https://www.figma.com/design/EYjkvHArrBonuiG2JUS2sE/SURF_UI?node-id=4045-282

---

## 9. Phase 2 implications — what this doc unlocks for the plan

1. **Theme migration target is concrete.** Phase 2 task 02-02 (theme) gets exact hex values for all 18 colour tokens, plus the 4 net-new tokens to add. Token names map cleanly to CSS custom properties (`--color-base-paper5`, `--shadow-stamp`, etc.).
2. **Component wrapper boundaries are decided.** Of ~46 components, only **3 are `custom` tier** (Card Interactive, Class, Quizz) — explicit adaptation candidates. Everything else is `core`/`extras` and faithful reproduction.
3. **MCQ card spec is fully extracted.** `Cards / Quizz` at node `4045:282` gives Phase 2 task 02-01 (MCQ rebuild) a complete reference: 3 states, exact padding `22/20/20/20` (top/right/bottom/left, from Quizz code: `pt-[22px] pb-[20px] px-[20px]`), radius 6, gap 13, max-width 600, buttons spec, option-row spec, mint-wash for correct answer.
4. **Hard-stamp shadow rule is absolute.** No CSS overrides may introduce any blurred / soft shadows. Only the four named stamps are allowed. Period.
5. **Streamlit-precedence rule pre-resolves Phase 2 design conflicts.** When Streamlit can't reproduce a Figma detail, adapt without re-asking.

---

## 10. Known unknowns — none open

All open questions resolved as of 2026-05-02. The only one that surfaced during this session (the `shadow/lift` survival check) was answered in favour of the strict-aesthetic interpretation: all blurred shadows deleted, 4 hard stamps only — see §5.8 and §7 ruling 4.

### 10.1 Deferred post-MVP (per rule-book §11.1 — not blocking submission)

| Item | Why deferred | When |
|---|---|---|
| Dark-mode coverage | Single-mode locked for MVP per `03_styles.md §0` | Post-2026-05-14 |
| Localisation | Single-language (EN) for MVP | Post-MVP |
| Animation curves bound to component transitions | Figma can't bind motion to vector nodes | When app ships |
| `Foundation / Glyph / Spinner` actual frames | **Resolved (deleted) this session — see §7 ruling 2** | n/a |

---

## 11. Future work — Phase 3 backlog (informational, per Tiago's "include" ruling)

Reproduced from rule-book §11.3. **Per Tiago's ruling (§7 #3), the "build the 9 missing components" item is REMOVED** — those components were intentionally deleted, not pending. The remaining items are Figma-side cleanup and token migrations that don't change what ships in the app.

1. ~~Page Header errored-state fix (§5.3)~~ — **must land before any Phase 4 page rebuild if pages get rebuilt in Figma**.
2. Wizard Step variant rename + Loading + Error states (§1.3, §5.1).
3. Status vs Accent triplet migration (§2.3) — touches Tinted Button + Toast + Quizz Summary.
4. White / Shadow-Soft / Focus token additions (§2.4–2.6) — single batch, ~35 nodes touched.
5. Text style colour bindings (§4.1) — 15 text styles get a `boundVariables.color`.
6. Button Loading variant × 4 (§5.1.c) — **resolved per §7 ruling 2 (use `…` placeholder, no glyph build).**
7. Toggle / Slider / Tab / Dropbox / Dropdown / Segmented state-completeness (§5.1.b).
8. Sidebar / Form Panel WithLoading variant (§5.2.a).
9. Display / Timer state-axis swap to Idle/Running/Stopped (§5.4).
10. ~~The 11 required new components (§8.1 + §8.2)~~ — **REMOVED per §7 ruling 3 (deleted, not pending).**
11. Stray canvas debris cleanup (`02_pages.md`: stray Tinted button at `(1333,-1179)`, three stray Quizz Generator/Options/Button instances on Components page).
12. P3 page artboard renames `Page 3 - My Classes` → `Page 3 - Class × 3` (§1.4).
13. P4/P5 layer-name renames (§1.4).
14. P4 timer copy fix `Remaining` → `Elapsed` (`02_pages.md §P4 wrong-copy`).
15. P4 Quizz card fix: 5 options → 4 options + `CLEAR` button → `SKIP` button (Idea v1 §3 P4).
16. Frame-shape promotion — Quizz Generator, Page Header / Mock-Exam Row, Sidebar Body for Form Panel → real components (`02_pages.md §frame-shaped-component-candidates`).
17. Delete-candidate execution: 12 components flagged in `01_components.md`. After §11.2 deletes confirmed, run a single sweep.
18. **Shadow rebinding** (new, this session). The 4 components currently bound to the now-deleted `shadow/lift` need a per-component decision: rebind to `shadow/stamp-lg` or strip the shadow entirely. Affects: `Cards / Card` (Lift variant), `Structure / Sidebar / Form Panel`, `Notification / Toast`, `Structure / Modal / Shell`. Also delete the orphan `shadow/soft` and `stamp-star` effect styles.

**Net Phase 3 scope (post-rulings):** ~13 atomic Figma cleanup tickets, all in-Figma, none affecting the Phase 2 build.

---

## 12. Doc maintenance

- **Triggers for update:** any change to the rule-book, any new component published to SURF_UI(old), any token added/removed.
- **Owner:** the Phase 2 implementer of `02-02-PLAN.md` (theme migration) — closest contact with these tokens.
- **Write-back to NLM:** when this doc lands, add a one-line work-log source to the Idea & Progress notebook per project CLAUDE.md write-back pattern, archive any superseded sources to `docs/archive/notebook_sources/<YYYY-MM-DD>_<source-name>.md`.

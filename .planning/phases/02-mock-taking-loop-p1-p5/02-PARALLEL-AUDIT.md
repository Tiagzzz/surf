# Phase 2 — Parallel Session Audit (`/Streamlit_Test/`)

**Audited:** 2026-05-02
**Source:** `/Users/tiagoreimann/surf/Streamlit_Test/` — built in a parallel session against the locked Figma library `EYjkvHArrBonuiG2JUS2sE` (SURF_UI).
**Verdict:** **HIGH QUALITY — adopt with three amendments.** ~80% directly reusable. The remaining 20% is migration (folder location), one accessibility amendment (`prefers-reduced-motion`), and one coverage extension (multi-correct checkbox styling).

This audit feeds into Phase 2 plan 02-01 (theme + tokens + previews/ scaffold) and supersedes the Wave-1 Q1 spike "Figma extraction" — that work is already done.

---

## What was built

| File | Size | What it is |
|---|---|---|
| `Streamlit_Test/ui/theme.py` | 598 lines / 26 KB | Single Python module: ~500 lines of scoped CSS as a string literal + 9 Python helper primitives + `inject_theme()` entry point. |
| `Streamlit_Test/test_components.py` | 329 lines | Working sandbox showing every component composed (topbar, class cards, stat cards, chips, steps, buttons (4 families × rest/disabled), inputs, toggles/checkbox/radio, MCQ option, tabs, passive+interactive cards, empty state, messages, file uploader). |
| `Streamlit_Test/.streamlit/config.toml` | 7 lines | Streamlit `[theme]` block mirroring the CSS tokens: `primaryColor = "#c8361d"`, `backgroundColor = "#fdf9f2"`, `secondaryBackgroundColor = "#ede4d2"`, `textColor = "#28251f"`, `font = "serif"`. |

---

## ✅ Good — adopt as-is

1. **Token taxonomy is complete and traceable.** Paper ladder (paper, paper-0…5), Accent triple (vibrant/deep/soft/wash), Status set (ok/warn/info), 5-step radius scale (xs/sm/md/lg/pill), motion (ease + t-fast/base/slow), type (`Fraunces` serif + `JetBrains Mono`). All exposed as CSS custom properties at `:root` — single edit point per `02-CONTEXT.md` D-2.1 edit-this-later note.

2. **Stamp shadow recipe is locked correctly.** Hard-edged offset (`border-radius: 0` on the shadow), 3 scales:
   - **3px** for default/tinted buttons + class card + interactive card
   - **4px** for interactive card hover (lifted state)
   - **2px** for soft button + passive card + stat card
   - Hover lifts: `transform: translate(-1px, -1px)` + shadow grows by 1px.
   - Press sinks: `transform: translate(2px, 2px)` + shadow shrinks to 1px.
   - This is the signature visual move — matches the Figma "stamp" feel.

3. **Scoping pattern is Streamlit-native and CLAUDE.md-compliant.** `[class*="st-key-XXX"]` reaches `st.container(key=...)`-wrapped widgets; nested widgets reached via stable `data-testid` attributes (`stButton`, `stTextInput`, `stSelectbox`, etc). **No banned libs** (`streamlit-shadcn-ui`, `streamlit-elements`, etc). **No `unsafe_allow_html` for layout** — only for typography helpers (`<p class="surf-eyebrow">…</p>`), which is the supported pattern.

4. **Course-aligned widget set.** Uses only vanilla widgets that appear in `~/surf/canvas_downloads/module4/notebooks/streamlit_demo_full.py`: `st.button`, `st.container(key=)`, `st.radio`, `st.text_input`, `st.text_area`, `st.selectbox`, `st.number_input`, `st.slider`, `st.date_input`, `st.tabs`, `st.toggle`, `st.checkbox`, `st.columns`, `st.divider`, `st.progress`, `st.file_uploader`, `st.info/success/warning/error`. **Zero green-list violations.**

5. **Python helper primitives are tiny and pure.** `eyebrow()`, `caption()`, `meta()`, `score()`, `chip()`/`chips_row()`, `steps()`, `stat_card()`, `empty_state_text()` are 1–10 lines each, no state, no side effects beyond `st.markdown`. Trivially copyable into `previews/_theme_helpers.py` and `app/brain/theme/`.

6. **Streamlit `[theme]` config + CSS are defense-in-depth.** The native `[theme]` block colors elements that are hard to reach via the DOM (e.g., the hidden hamburger menu, status bars). The CSS overrides the rest. Best of both worlds.

7. **`score()` color thresholds match the Swiss 1–6 grading formula.** Red <3.5, gold 3.5–5, green ≥5. Direct fit for P5 final-note rendering (D-4.1) and P2 class-card score readout.

8. **Sandbox isolation already respected.** `Streamlit_Test/` lives outside `/app`; theme.py and test_components.py have **no `from app…` imports**. Migration to `/previews/` is a path move, not a refactor.

---

## ⚠ Bad / needs adjustment

1. **Wrong folder.** Per `CLAUDE.md` Visual Preview Gate, sandboxes live in `/previews/`, not `/Streamlit_Test/`. **Action:** plan 02-01 must migrate `Streamlit_Test/ui/theme.py` → `previews/_theme.py` and `Streamlit_Test/test_components.py` → `previews/components/_theme_bench/preview.py`. Production copy (separate file) lives at `app/brain/theme/theme.py` per `02-CONTEXT.md` D-2.1.

2. **No `prefers-reduced-motion` accessibility query.** Hover transitions, transforms, and stamp-shadow shifts run unconditionally. **Action:** append a media-query block at the bottom of `_CSS` that disables `transition` and `transform` for users who prefer reduced motion. ~6 lines of CSS.

3. **No styling for multi-correct MCQs (checkbox group).** `[class*="st-key-mcq"] [role="radiogroup"] > label` only covers the radio variant. Phase 1 D-2.5 locked `correct_indices` as a list — multi-correct questions render as `st.checkbox` group, not radio. **Action:** extend the `st-key-mcq` block to also style `[data-testid="stCheckbox"]` (selected/hover/focus states using the same accent-wash + stamp-shadow recipe).

4. **CSS is embedded in a Python string, not a `.css` file.** `02-CONTEXT.md` D-2.1 said "single scoped-CSS file at `app/brain/theme/surf_theme.css`". Streamlit_Test inlined the CSS in `_CSS = """..."""` and ships it via `st.markdown(_CSS, unsafe_allow_html=True)`. **This is actually simpler** (one file, importable, no path resolution, no `.read_text()`), and the edit-this-later note already covers swap. **Recommendation:** ship as Python module (the Streamlit_Test approach), NOT as separate `.css`. Update D-2.1 delivery mechanism — see reconciliation below.

5. **D-2.3 "gentle fade-in on Cards via @keyframes" was not implemented and should be dropped.** Streamlit reruns top-to-bottom on every interaction; a fade-in keyframe would re-trigger on every rerun, creating busy flicker. The hover stamp-shadow is the signature animation; it is enough character. **Recommendation:** amend D-2.3 to drop fade-in, keep hover/press transitions.

6. **`config.toml` `font = "serif"` is generic.** Only `"sans serif" | "serif" | "monospace"` are accepted by Streamlit's `[theme] font` field without `[[theme.fontFaces]]` (Streamlit 1.30+). The CSS `@import url('…Fraunces…JetBrains+Mono…')` already loads the real fonts and overrides every text container via `font-family`. **Acceptable for v1.** If Tiago wants to wire the custom font into Streamlit-native widgets (text inputs in particular use the family from `[theme]` before CSS overrides bind), add a `[[theme.fontFaces]]` block. Defer to polish.

7. **Google Fonts is a network dependency on first load.** `@import url('https://fonts.googleapis.com/...')` requires network at `inject_theme()` time. For grader-machine offline reproducibility, self-host fonts in `assets/fonts/` and `@font-face` them. **Defer** — not blocking for Phase 2.

8. **No tooltip/popover/dialog styling.** Streamlit native tooltips (`data-baseweb="tooltip"`), `st.dialog`, `st.popover`, `st.expander` are unstyled. Phase 2 uses `st.status` (ingestion progress) and may use `st.expander` (P5 difficulty breakdown). **Recommendation:** plan 02-01 adds at minimum an `st.expander` skin (eyebrow header, paper-1 background, stamp-shadow on hover) and an `st.status` skin (paper-0 background, accent border on running, ok border on success). Tooltip + dialog can defer.

9. **`progress_callback` from `02-CONTEXT.md` D-2.6 is not exercised in the sandbox.** Plan 02-01 should add a small sandbox (`previews/components/ingestion_log/`) that drives a fake `lecture_ingest` with stubbed progress callbacks against an `st.status` block to prove the wiring before plan 02-04b.

---

## 🔄 Reusable — copy as the seed for `previews/_theme.py` and `app/brain/theme/theme.py`

| Asset | Destination |
|---|---|
| `_CSS` constant (entire string, 480+ lines) | `previews/_theme.py` (sandbox) AND `app/brain/theme/theme.py` (production) — two copies, drift is a feature per CLAUDE.md sandbox-isolation rule |
| `inject_theme()` | both copies |
| `eyebrow()`, `caption()`, `meta()`, `score()`, `chip()`, `chips_row()`, `steps()`, `stat_card()`, `empty_state_text()` | both copies |
| `.streamlit/config.toml` `[theme]` block | `/.streamlit/config.toml` (production) — Streamlit reads from project root |

---

## 🗑 Discard

Nothing. The audit found zero anti-pattern violations and no work that should be thrown away.

---

## Bottom line for plan 02-01

**Wave-1 Q1 ("Figma extraction spike") is no longer a spike — it's a validation step.** Plan 02-01 should restructure Q1 as: (a) verify token values in `theme.py` against the live Figma file (look for a `SURF_UI` non-`(old)` revision via `mcp__dd11b50e-…__search_design_system`); (b) apply the three amendments above (`prefers-reduced-motion`, multi-correct checkbox styling, `st.expander` + `st.status` skins); (c) migrate to `previews/_theme.py` and `app/brain/theme/theme.py`; (d) ship `inject_theme()` call in `streamlit_app.py` (production) and at the top of every `previews/.../preview.py` (sandboxes).

**Net effect:** plan 02-01 gets *smaller*, not bigger — the heavy extraction work is already done. The new content is migration plumbing and three small additive amendments.

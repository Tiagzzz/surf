---
created: 2026-05-02T07:28:08.284Z
title: Phase 2 Streamlit widget catalog research
area: planning
files:
  - canvas_downloads/module4/notebooks/Unit04.section5.ipynb
  - canvas_downloads/module4/notebooks/streamlit_demo_full.py
  - canvas_downloads/module4/notebooks/streamlit_demo.py
---

## Problem

Before Phase 2 (Mock Taking Loop, P1–P5) plans get written, the build needs a locked widget vocabulary. Without it, each page risks drifting into different patterns (some pages use `st.button`, others reach for community libs, etc.) and the grader sees inconsistency. The course teaches **vanilla Streamlit only** with explicit deferral to official docs (verified against `Unit04.section5.ipynb` + `streamlit_demo_full.py` + Lectures notebook). Community component libraries (shadcn-ui, elements, antd-components, option-menu) and raw `unsafe_allow_html` injection are off-pattern. `streamlit-extras` is the only "yellow" tier (additive, maintained by a Streamlit-team employee).

The catalog is design-driven, so it cannot be locked before the Phase 2 UI design is locked.

## Solution

Run a researcher step at the start of Phase 2, **after** the UI design for P1–P7 is locked but **before** plans 02-xx are written. Output two artefacts (in Phase 2 CONTEXT.md or a dedicated `02-WIDGETS.md`):

1. **Vanilla Streamlit green-list** — every official `streamlit.*` widget the build will use across P1–P7, with course-pattern notes:
   - `divider='rainbow'` flourish on top-level `st.header`
   - `st.set_page_config` at the top of `streamlit_app.py` (per `streamlit_demo_full.py` lines 41–46)
   - `st.columns` + `with col:` context-manager idiom
   - Sidebar via `st.sidebar.write` (markdown content)
   - `with st.container():` blocks for grouped sections
   - `st.session_state` for the P4 mock-pinned state (not demoed in course but pointed-at in official docs the syllabus directs students to)

2. **`streamlit-extras` shortlist** — per UI element, which extra (if any) is justified, which vanilla equivalent it replaces, and the Contribution Matrix justification line. **Update 2026-05-02:** the originally-flagged top candidate `stylable_container` is **deprecated upstream**. The replacement is pure vanilla: `st.container(key="my_key")` stamps a `.st-key-my_key` class on the DOM element, and CSS targeting that class via `st.html("<style>.st-key-my_key { ... }</style>")` scopes the styles. The shortlist may end up empty for Surf — that's acceptable.

**Hard reds (do not propose):** `streamlit-shadcn-ui`, `streamlit-elements`, `streamlit-antd-components`, `streamlit-option-menu`.

**Softened amber (officially blessed):** `st.container(key=...)` + `st.html("<style>.st-key-X { ... }</style>")` for scoped CSS — recolor buttons, hover effects, keyframe animations, quiz/result card backgrounds, card hover lift, custom flex/grid layouts, surrounding chart frames. Does NOT work for: native chart internals (axes/tick colors → configure Altair/Plotly directly), JS-driven animations, confetti, page transitions. For modal-style overlays use `st.dialog`, not CSS-faked overlays.

**Still red:** unscoped global `<style>` blocks; `unsafe_allow_html=True` for user-invented HTML (vs. CSS targeting Streamlit's own DOM).

**Anchor sources:**
- `canvas_downloads/module4/notebooks/Unit04.section5.ipynb` — section 5 lecture notebook
- `canvas_downloads/module4/notebooks/streamlit_demo_full.py` — canonical course demo
- Lectures notebook (NotebookLM id `6bc919e0-21c9-452e-b203-507f078efa33`) for cross-check
- `extras.streamlit.app` — `streamlit-extras` catalog

**Acceptance:**
- Every P1–P7 UI element in the locked design has a named widget assignment (vanilla or extras)
- Every accepted extra has a Contribution Matrix justification line written
- No hard-red library appears in the catalog
- Catalog is referenced in subsequent Phase 2 plans (no plan introduces a widget not on the green-list/shortlist)

See also: project memory `project_phase2_streamlit_widget_catalog.md`.

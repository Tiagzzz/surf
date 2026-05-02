"""Surf component test bench (sandbox).

Run from /Streamlit_Test:
    cd ~/surf/Streamlit_Test && streamlit run test_components.py

Showcases every interactive + display component planned for Surf, wrapped
in `st.container(key=...)` so the scoped CSS in `ui/theme.py` styles each
one to match the paper-and-stamp aesthetic. Hover and pressed animations
are pure CSS pseudo-classes (`:hover`, `:active`).

This file is isolated from the production /app — no imports from there.
"""

from __future__ import annotations

import streamlit as st

from ui.theme import (
    caption,
    chips_row,
    empty_state_text,
    eyebrow,
    inject_theme,
    meta,
    score,
    stat_card,
    steps,
)


st.set_page_config(page_title="Surf — Component Test Bench", layout="wide")
inject_theme()


# =========================================================================
# TOPBAR — brand · breadcrumb · home/settings icons
# =========================================================================
with st.container(key="topbar"):
    bcols = st.columns([1, 6, 0.6, 0.6])
    with bcols[0]:
        st.markdown('<p class="surf-brand">surf</p>', unsafe_allow_html=True)
    with bcols[1]:
        st.markdown(
            '<p class="surf-breadcrumb">Class &nbsp;›&nbsp; <strong>Computer Science</strong></p>',
            unsafe_allow_html=True,
        )
    with bcols[2]:
        with st.container(key="topbar-icon-home"):
            st.button("⌂", key="tb-home", help="Home")
    with bcols[3]:
        with st.container(key="topbar-icon-settings"):
            st.button("⚙", key="tb-settings", help="Settings")


# =========================================================================
# Page header
# =========================================================================
eyebrow("Surf · Design system · Sandbox")
st.markdown("# Component test bench")
caption("Refined sandbox — built from the Figma library at file EYjkvHArrBonuiG2JUS2sE. Hover & click each control to feel the states.")

st.divider()


# =========================================================================
# CLASS CARDS — central P2 component
# =========================================================================
st.markdown("## Class cards")
caption("Eyebrow + Fraunces italic name + mono meta on the left, big italic Fraunces score on the right. Hover lifts; press sinks.")

class_data = [
    ("01", "Macroeconomics I",   "12 Slides", "12 Mock Exams", 3.25),
    ("02", "Microeconomics I",   "8 Slides",  "5 Mock Exams",  4.25),
    ("03", "Computer Science",   "9 Slides",  "9 Mock Exams",  6.00),
]
for num, name, slides, mocks, sc in class_data:
    with st.container(key=f"class-card-{num}"):
        c1, c2 = st.columns([4, 1.2])
        with c1:
            st.markdown(f'<p class="surf-meta">{num}</p>', unsafe_allow_html=True)
            st.markdown(f"### {name}")
            meta(f"{slides} &nbsp;·&nbsp; {mocks}")
        with c2:
            score(sc)

st.divider()


# =========================================================================
# STAT CARDS — KPI tiles for P6 dashboard
# =========================================================================
st.markdown("## Stat cards")
caption("KPI tile pattern — eyebrow · label · big italic value · optional delta.")

scols = st.columns(4)
with scols[0]:
    with st.container(key="stat-card-1"):
        stat_card("Total enrolled", "1,284", eyebrow_text="OVERVIEW")
with scols[1]:
    with st.container(key="stat-card-2"):
        stat_card("Total enrolled", "1,284", eyebrow_text="OVERVIEW", delta="+12.4%", delta_dir="up")
with scols[2]:
    with st.container(key="stat-card-3"):
        stat_card("Total enrolled", "1,284", eyebrow_text="OVERVIEW", delta="-12.4%", delta_dir="down")
with scols[3]:
    with st.container(key="stat-card-4"):
        stat_card("Total enrolled", "1,284", eyebrow_text="OVERVIEW", delta="+0.0%", delta_dir="flat")

st.divider()


# =========================================================================
# CHIPS
# =========================================================================
st.markdown("## Chips")
caption("Mono uppercase pill — for tags, filters, status flags.")

chips_row([
    ("Outline",       "outline"),
    ("Accent",        "accent"),
    ("Solid",         "solid"),
    ("Dashed",        "dashed"),
    ("Demand",        "outline"),
    ("Supply",        "outline"),
    ("Elasticity",    "accent"),
])

st.divider()


# =========================================================================
# STEP ITEM — wizard / progress indicator
# =========================================================================
st.markdown("## Steps")
caption("Inline step indicator — done · active · todo. Used in onboarding (P1 → P2 → P3) and ingestion wizard.")

steps([
    ("Sign up",           "done"),
    ("Add class",         "active"),
    ("Upload factsheet",  "todo"),
    ("Generate MCQs",     "todo"),
])

st.divider()


# =========================================================================
# BUTTONS
# =========================================================================
st.markdown("## Buttons")
caption("Four families — Default · Ghost · Soft · Tinted. Stamp shadow lifts on hover, sinks on press. Disabled state below each.")

cols = st.columns(5)
with cols[0]:
    eyebrow("Default")
    with st.container(key="btn-default-1"): st.button("Take mock", key="b-default-rest")
    with st.container(key="btn-default-2"): st.button("Disabled", key="b-default-disabled", disabled=True)
with cols[1]:
    eyebrow("Ghost")
    with st.container(key="btn-ghost-1"): st.button("Cancel", key="b-ghost-rest")
    with st.container(key="btn-ghost-2"): st.button("Disabled", key="b-ghost-disabled", disabled=True)
with cols[2]:
    eyebrow("Soft")
    with st.container(key="btn-soft-1"): st.button("Save draft", key="b-soft-rest")
    with st.container(key="btn-soft-2"): st.button("Disabled", key="b-soft-disabled", disabled=True)
with cols[3]:
    eyebrow("Tinted · Accent")
    with st.container(key="btn-tinted-accent-1"): st.button("Submit", key="b-tinted-rest")
    with st.container(key="btn-tinted-accent-2"): st.button("Disabled", key="b-tinted-disabled", disabled=True)
with cols[4]:
    eyebrow("Tinted · Status")
    with st.container(key="btn-tinted-ok"):   st.button("OK",   key="b-ok")
    with st.container(key="btn-tinted-info"): st.button("Info", key="b-info")
    with st.container(key="btn-tinted-warn"): st.button("Warn", key="b-warn")

st.divider()


# =========================================================================
# INPUTS
# =========================================================================
st.markdown("## Inputs")
icols = st.columns(3)
with icols[0]:
    st.text_input("Email", placeholder="you@example.com", key="i-email")
    st.text_input("Password", type="password", placeholder="••••••••", key="i-pw")
    st.text_input("Anthropic API key", type="password", placeholder="sk-ant-…", key="i-key")
with icols[1]:
    st.text_area("About this class", height=120, key="i-about")
    st.selectbox("Topic", ["Microeconomics", "Macroeconomics", "Statistics", "Computer Science"], key="i-topic")
with icols[2]:
    st.number_input("% needed for a 4", min_value=0, max_value=100, value=50, step=5, key="i-pct")
    st.slider("Difficulty", 0.0, 1.0, 0.5, 0.05, key="i-diff")
    st.date_input("Submission deadline", key="i-date")

st.divider()


# =========================================================================
# TOGGLES · CHECKBOXES · RADIO
# =========================================================================
st.markdown("## Toggles, checkboxes, radio")
tcols = st.columns(3)
with tcols[0]:
    eyebrow("Toggle")
    st.toggle("Eager-generate MCQs", value=True, key="t-eager")
    st.toggle("Save raw attempts",   value=False, key="t-raw")
with tcols[1]:
    eyebrow("Checkbox")
    st.checkbox("Lecture 1 — Introduction",   value=True,  key="cb-l1")
    st.checkbox("Lecture 2 — Supply & demand", value=True,  key="cb-l2")
    st.checkbox("Lecture 3 — Elasticity",      value=False, key="cb-l3")
with tcols[2]:
    eyebrow("Radio")
    st.radio("Mock type", ["Standard mock", "PRACTICE — Study Next"], key="r-mock")

st.divider()


# =========================================================================
# MCQ option — radio styled as paper cards
# =========================================================================
st.markdown("## MCQ option")
caption("Radio rendered as paper cards — hover to highlight, click to select. Selected state uses accent-wash bg + accent border + stamp shadow.")

with st.container(key="mcq-1"):
    st.radio(
        "Which factor is NOT a determinant of demand?",
        ["A. Consumer income", "B. Price of related goods", "C. Production technology", "D. Consumer preferences"],
        key="mcq-q1",
        label_visibility="collapsed",
    )

st.divider()


# =========================================================================
# TABS
# =========================================================================
st.markdown("## Tabs")
tab1, tab2, tab3 = st.tabs(["Lectures", "Mock exams", "Dashboard"])
with tab1:
    st.markdown("### Lectures")
    caption("12 lectures · 78% complete")
with tab2:
    st.markdown("### Mock exams")
    caption("5 mocks taken · last score 4.8")
with tab3:
    st.markdown("### Dashboard")
    caption("Score trend, completion, strengths/weaknesses radar.")

st.divider()


# =========================================================================
# CARD · CARD INTERACTIVE
# =========================================================================
st.markdown("## Card · Card Interactive")
ccols = st.columns(2)
with ccols[0]:
    eyebrow("Passive card")
    with st.container(key="card-passive-1"):
        st.markdown("### Macroeconomics I")
        caption("12 lectures · 78% complete")
        st.progress(0.78)

with ccols[1]:
    eyebrow("Interactive card · hover & press")
    with st.container(key="card-interactive-1"):
        st.markdown("### Microeconomics I")
        caption("8 lectures · 42% complete")
        st.progress(0.42)
        with st.container(key="btn-default-card"):
            st.button("Open class", key="card-cta")

st.divider()


# =========================================================================
# EMPTY STATE
# =========================================================================
st.markdown("## Empty state")
caption("Dashed border + ornament + mono headline + mono body + CTA. Used wherever a list is empty (no classes, no mocks, no attempts).")

ecols = st.columns(2)
with ecols[0]:
    eyebrow("No classes yet")
    with st.container(key="empty-1"):
        empty_state_text(
            "Nothing here yet",
            "Add your first class to get started. Everything you create will appear here.",
        )
        with st.container(key="btn-default-empty"):
            st.button("Add a class", key="empty-cta-1")
with ecols[1]:
    eyebrow("No mocks taken")
    with st.container(key="empty-2"):
        empty_state_text(
            "Nothing to show yet",
            "Complete your first mock exam to see results here, ready for review.",
        )
        with st.container(key="btn-tinted-accent-empty"):
            st.button("Take a mock", key="empty-cta-2")

st.divider()


# =========================================================================
# MESSAGES
# =========================================================================
st.markdown("## Messages")
mcols = st.columns(4)
with mcols[0]: st.info("Factsheet uploaded — review before continuing.")
with mcols[1]: st.success("Mock saved · score 5.2 / 6.")
with mcols[2]: st.warning("Auffahrt collision — buffer-upload by 2026-05-13.")
with mcols[3]: st.error("Claude API key missing in settings.")

st.divider()


# =========================================================================
# FILE UPLOADER
# =========================================================================
st.markdown("## File upload")
st.file_uploader("Lecture PDF", type=["pdf"], key="up-pdf")

st.markdown(" ")
caption("End of test bench. All hover/press states are pure CSS — no Python rerun on hover or press.")

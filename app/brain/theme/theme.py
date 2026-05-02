"""Surf design system — paper-and-stamp aesthetic.

Production copy. Tokens sourced from the Figma `Tokens` collection (file
`EYjkvHArrBonuiG2JUS2sE`). The CSS is embedded as the Python string `_CSS`
and shipped via `inject_theme()` (D-2.17). Fonts are self-hosted from
`assets/fonts/` and declared with `@font-face` (D-2.16). Component scoping
follows D-2.18 — wrappers are `st.container(key="…")` and the CSS reaches
into them via `[class*="st-key-…"]` selectors. Streamlit widgets inside
those wrappers are reached by their stable `data-testid` attributes.

Mirror copy lives at `previews/_theme.py` (sandbox isolation, D-2.22).

This module is imported once at app entry by `streamlit_app.py`:

    from app.brain.theme import inject_theme
    inject_theme()
"""

from __future__ import annotations

import html

import streamlit as st

_CSS = """
<style>
/* =========================================================
   FONTS — self-hosted (D-2.16). Streamlit ≥1.50 serves the
   `assets/` folder from the working directory automatically;
   absolute URL `/assets/fonts/...` resolves when the app is
   launched from the repo root.
   ========================================================= */
@font-face {
  font-family: 'Fraunces';
  font-style: normal;
  font-weight: 400 900;
  src: url('/assets/fonts/Fraunces-normal-400_900.woff2') format('woff2');
  font-display: swap;
}
@font-face {
  font-family: 'Fraunces';
  font-style: italic;
  font-weight: 400 900;
  src: url('/assets/fonts/Fraunces-italic-400_900.woff2') format('woff2');
  font-display: swap;
}
@font-face {
  font-family: 'JetBrains Mono';
  font-style: normal;
  font-weight: 100 800;
  src: url('/assets/fonts/JetBrainsMono-Variable.woff2') format('woff2');
  font-display: swap;
}

:root {
  /* ---- Color: Paper scale (warm cream → charcoal) ---- */
  --paper:    #fdf9f2;
  --paper-0:  #f5efe4;
  --paper-1:  #ede4d2;
  --paper-2:  #c0b49b;
  --paper-3:  #6c6455;
  --paper-4:  #3b362c;
  --paper-5:  #28251f;
  --paper-shadow:      #171512;
  --paper-shadow-soft: #1a1814;
  --white:    #ffffff;

  /* ---- Color: Accent (Surf red) ---- */
  --accent-vibrant: #c8361d;
  --accent-deep:    #9d2815;
  --accent-soft:    #e8a798;
  --accent-wash:    #f7d9d1;

  /* ---- Color: Status ---- */
  --ok:       #2d6a3f;
  --ok-wash:  #9ec7aa;
  --warn:     #b8860b;
  --info:     #2a5d7c;

  /* ---- Radius ---- */
  --r-xs:   3px;
  --r-sm:   4px;
  --r-md:   6px;
  --r-lg:  10px;
  --r-pill: 999px;

  /* ---- Motion ---- */
  --ease:    cubic-bezier(0.2, 0, 0, 1);
  --t-fast:  120ms var(--ease);
  --t-base:  180ms var(--ease);
  --t-slow:  320ms var(--ease);

  /* ---- Type ---- */
  --serif: 'Fraunces', Georgia, serif;
  --mono:  'JetBrains Mono', Menlo, monospace;
}

/* =========================================================
   GLOBAL
   ========================================================= */
.stApp { background: var(--paper); color: var(--paper-5); }
section[data-testid="stMain"] { background: var(--paper); }
html, body { font-family: var(--serif); }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { font-family: var(--serif); font-size: 17px; line-height: 1.5; color: var(--paper-5); }
h1 { font-family: var(--serif); font-style: italic; font-weight: 900; font-size: 42px; line-height: 0.95; letter-spacing: -0.02em; color: var(--paper-5); }
h2 { font-family: var(--serif); font-style: italic; font-weight: 600; font-size: 28px; line-height: 1.15; letter-spacing: -0.01em; color: var(--paper-5); }
h3 { font-family: var(--serif); font-style: italic; font-weight: 600; font-size: 22px; line-height: 1.15; color: var(--paper-5); }
h4 { font-family: var(--serif); font-weight: 600; font-size: 18px; line-height: 1.3; color: var(--paper-5); }

/* Eyebrow / caption / meta */
.surf-eyebrow { font-family: var(--mono); font-weight: 500; font-size: 10px;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--paper-3); margin: 0 0 4px 0; }
.surf-caption { font-family: var(--serif); font-style: italic; font-size: 13px;
  color: var(--paper-3); margin: 0 0 8px 0; }
.surf-meta { font-family: var(--mono); font-weight: 400; font-size: 11px;
  letter-spacing: 0.08em; color: var(--paper-3); margin: 0; }

/* =========================================================
   BUTTONS — Default · Ghost · Soft · Tinted (Accent/OK/Info/Warn)
   Stamp shadow = hard-edged offset (radius:0); 3px to match Figma weight.
   ========================================================= */
[data-testid="stButton"] button,
[data-testid="stButton"] button p,
[data-testid="stDownloadButton"] button,
[data-testid="stDownloadButton"] button p {
  font-family: 'JetBrains Mono', Menlo, monospace !important;
  font-weight: 700 !important; font-size: 11px !important;
  letter-spacing: 0.10em !important; text-transform: uppercase !important;
}
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button {
  border-radius: var(--r-sm); padding: 12px 22px;
  border: 1.5px solid transparent;
  transition: transform var(--t-fast), box-shadow var(--t-fast),
              background-color var(--t-fast), color var(--t-fast),
              border-color var(--t-fast), filter var(--t-fast);
  cursor: pointer; min-height: 0;
}
[data-testid="stButton"] button:disabled { cursor: not-allowed; }

[class*="st-key-btn-default"] [data-testid="stButton"] button {
  background: var(--paper-5); color: var(--white);
  box-shadow: 3px 3px 0 0 var(--paper-shadow);
}
[class*="st-key-btn-default"] [data-testid="stButton"] button p {
  color: var(--white) !important;
}
[class*="st-key-btn-default"] [data-testid="stButton"] button:hover {
  background: var(--paper-4); transform: translate(-1px, -1px);
  box-shadow: 4px 4px 0 0 var(--paper-shadow);
}
[class*="st-key-btn-default"] [data-testid="stButton"] button:active {
  transform: translate(2px, 2px); box-shadow: 1px 1px 0 0 var(--paper-shadow);
}
[class*="st-key-btn-default"] [data-testid="stButton"] button:disabled {
  background: var(--paper-2); color: var(--paper-3); box-shadow: none;
}

[class*="st-key-btn-ghost"] [data-testid="stButton"] button {
  background: transparent; color: var(--paper-4);
  border-color: var(--paper-4); box-shadow: none;
}
[class*="st-key-btn-ghost"] [data-testid="stButton"] button:hover {
  background: var(--paper-1); border-color: var(--paper-5); color: var(--paper-5);
}
[class*="st-key-btn-ghost"] [data-testid="stButton"] button:active {
  background: var(--paper-2);
}
[class*="st-key-btn-ghost"] [data-testid="stButton"] button:disabled {
  color: var(--paper-3); border-color: var(--paper-2); background: transparent;
}

[class*="st-key-btn-soft"] [data-testid="stButton"] button {
  background: var(--paper-1); color: var(--paper-5);
  box-shadow: 2px 2px 0 0 var(--paper-shadow-soft);
}
[class*="st-key-btn-soft"] [data-testid="stButton"] button:hover {
  background: var(--paper-2); transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 0 var(--paper-shadow-soft);
}
[class*="st-key-btn-soft"] [data-testid="stButton"] button:active {
  transform: translate(1px, 1px); box-shadow: 1px 1px 0 0 var(--paper-shadow-soft);
}
[class*="st-key-btn-soft"] [data-testid="stButton"] button:disabled {
  background: var(--paper-1); color: var(--paper-3); box-shadow: none;
}

[class*="st-key-btn-tinted-accent"] [data-testid="stButton"] button   p { color: var(--white) !important; }
[class*="st-key-btn-tinted-ok"] [data-testid="stButton"] button       p { color: var(--white) !important; }
[class*="st-key-btn-tinted-info"] [data-testid="stButton"] button     p { color: var(--white) !important; }
[class*="st-key-btn-tinted-warn"] [data-testid="stButton"] button     p { color: var(--white) !important; }
[class*="st-key-btn-tinted-accent"] [data-testid="stButton"] button { background: var(--accent-vibrant); color: var(--white); box-shadow: 3px 3px 0 0 var(--paper-shadow); }
[class*="st-key-btn-tinted-accent"] [data-testid="stButton"] button:hover  { background: var(--accent-deep); transform: translate(-1px,-1px); box-shadow: 4px 4px 0 0 var(--paper-shadow); }
[class*="st-key-btn-tinted-accent"] [data-testid="stButton"] button:active { transform: translate(2px,2px);   box-shadow: 1px 1px 0 0 var(--paper-shadow); }

[class*="st-key-btn-tinted-ok"] [data-testid="stButton"] button { background: var(--ok); color: var(--white); box-shadow: 3px 3px 0 0 var(--paper-shadow); }
[class*="st-key-btn-tinted-ok"] [data-testid="stButton"] button:hover  { filter: brightness(0.9); transform: translate(-1px,-1px); box-shadow: 4px 4px 0 0 var(--paper-shadow); }
[class*="st-key-btn-tinted-ok"] [data-testid="stButton"] button:active { transform: translate(2px,2px); box-shadow: 1px 1px 0 0 var(--paper-shadow); }

[class*="st-key-btn-tinted-info"] [data-testid="stButton"] button { background: var(--info); color: var(--white); box-shadow: 3px 3px 0 0 var(--paper-shadow); }
[class*="st-key-btn-tinted-info"] [data-testid="stButton"] button:hover  { filter: brightness(0.9); transform: translate(-1px,-1px); box-shadow: 4px 4px 0 0 var(--paper-shadow); }
[class*="st-key-btn-tinted-info"] [data-testid="stButton"] button:active { transform: translate(2px,2px); box-shadow: 1px 1px 0 0 var(--paper-shadow); }

[class*="st-key-btn-tinted-warn"] [data-testid="stButton"] button { background: var(--warn); color: var(--white); box-shadow: 3px 3px 0 0 var(--paper-shadow); }
[class*="st-key-btn-tinted-warn"] [data-testid="stButton"] button:hover  { filter: brightness(0.9); transform: translate(-1px,-1px); box-shadow: 4px 4px 0 0 var(--paper-shadow); }
[class*="st-key-btn-tinted-warn"] [data-testid="stButton"] button:active { transform: translate(2px,2px); box-shadow: 1px 1px 0 0 var(--paper-shadow); }

[class*="st-key-btn-tinted-accent"] [data-testid="stButton"] button:disabled,
[class*="st-key-btn-tinted-ok"]     [data-testid="stButton"] button:disabled,
[class*="st-key-btn-tinted-info"]   [data-testid="stButton"] button:disabled,
[class*="st-key-btn-tinted-warn"]   [data-testid="stButton"] button:disabled {
  background: var(--paper-2); color: var(--paper-3); box-shadow: none; filter: none;
}

/* =========================================================
   TEXT INPUTS · TEXT AREA · NUMBER · DATE
   ========================================================= */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input {
  font-family: var(--serif); font-size: 17px; color: var(--paper-5);
  background: var(--white);
  border: 1.5px solid var(--paper-3); border-radius: var(--r-sm);
  padding: 10px 12px;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
[data-testid="stTextInput"] input:hover,
[data-testid="stTextArea"] textarea:hover { border-color: var(--paper-4); }
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--accent-vibrant); outline: none;
  box-shadow: 0 0 0 3px var(--accent-wash);
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stSlider"] label,
[data-testid="stNumberInput"] label,
[data-testid="stDateInput"] label,
[data-testid="stRadio"] > label,
[data-testid="stToggle"] label {
  font-family: var(--mono); font-weight: 500; font-size: 10px;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--paper-3);
}

/* =========================================================
   SELECTBOX
   ========================================================= */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  background: var(--white);
  border: 1.5px solid var(--paper-3); border-radius: var(--r-sm);
  font-family: var(--serif); font-size: 17px;
  transition: border-color var(--t-fast);
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover { border-color: var(--paper-4); }

/* =========================================================
   CHECKBOX · RADIO  (text only; primaryColor handles checked)
   ========================================================= */
[data-testid="stCheckbox"] label p,
[data-testid="stRadio"] label[data-baseweb="radio"] p {
  font-family: var(--serif) !important; font-size: 17px !important;
  color: var(--paper-5) !important; text-transform: none !important;
  letter-spacing: 0 !important; font-weight: 400 !important;
}

/* =========================================================
   SLIDER
   ========================================================= */
[data-testid="stSlider"] [role="slider"] {
  background: var(--accent-vibrant) !important;
  border: 2px solid var(--paper-shadow) !important;
  box-shadow: 1px 1px 0 0 var(--paper-shadow) !important;
  transition: transform var(--t-fast);
}
[data-testid="stSlider"] [role="slider"]:hover { transform: scale(1.15); }

/* =========================================================
   TABS
   ========================================================= */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px; border-bottom: 1.5px solid var(--paper-2);
}
.stTabs [data-baseweb="tab"] {
  font-family: var(--mono); font-weight: 700; font-size: 11px;
  letter-spacing: 0.10em; text-transform: uppercase;
  color: var(--paper-3); padding: 10px 16px;
  transition: color var(--t-base), border-color var(--t-base);
  border-bottom: 2px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--paper-5); }
.stTabs [aria-selected="true"] {
  color: var(--accent-vibrant) !important;
  border-bottom-color: var(--accent-vibrant) !important;
}

/* =========================================================
   PASSIVE / INTERACTIVE CARDS
   ========================================================= */
[class*="st-key-card-passive"] {
  background: var(--paper-0); border: 1.5px solid var(--paper-2);
  border-radius: var(--r-md); padding: 20px 24px;
  box-shadow: 2px 2px 0 0 var(--paper-shadow-soft);
}
[class*="st-key-card-interactive"] {
  background: var(--paper-0); border: 1.5px solid var(--paper-2);
  border-radius: var(--r-md); padding: 20px 24px;
  box-shadow: 4px 4px 0 0 var(--paper-shadow);
  transition: transform var(--t-base), box-shadow var(--t-base), border-color var(--t-base);
  cursor: pointer;
}
[class*="st-key-card-interactive"]:hover {
  transform: translate(-2px, -2px); box-shadow: 6px 6px 0 0 var(--paper-shadow);
  border-color: var(--paper-4);
}
[class*="st-key-card-interactive"]:active {
  transform: translate(2px, 2px); box-shadow: 2px 2px 0 0 var(--paper-shadow);
}

/* =========================================================
   CLASS CARD — eyebrow + class name + meta (left) | big italic score (right)
   ========================================================= */
[class*="st-key-class-card"] {
  background: var(--paper); border: 1.5px solid var(--paper-4);
  border-radius: var(--r-md); padding: 18px 24px;
  box-shadow: 4px 4px 0 0 var(--paper-shadow);
  transition: transform var(--t-base), box-shadow var(--t-base);
  cursor: pointer; margin-bottom: 16px;
}
[class*="st-key-class-card"]:hover {
  transform: translate(-2px, -2px); box-shadow: 6px 6px 0 0 var(--paper-shadow);
}
[class*="st-key-class-card"]:active {
  transform: translate(2px, 2px); box-shadow: 2px 2px 0 0 var(--paper-shadow);
}
[data-testid="stMarkdownContainer"] p.surf-score,
p.surf-score {
  font-family: var(--serif) !important; font-style: italic !important;
  font-weight: 900 !important;
  font-size: 48px !important; line-height: 1 !important;
  letter-spacing: -0.02em !important;
  margin: 0 !important; text-align: right !important;
}
.surf-score--low  { color: var(--accent-vibrant); }
.surf-score--mid  { color: var(--warn); }
.surf-score--high { color: var(--ok); }

/* =========================================================
   STAT CARD
   ========================================================= */
[class*="st-key-stat-card"] {
  background: var(--paper-0); border: 1.5px solid var(--paper-3);
  border-radius: var(--r-md); padding: 14px 18px;
  box-shadow: 2px 2px 0 0 var(--paper-shadow-soft);
}
[data-testid="stMarkdownContainer"] p.surf-stat-value,
p.surf-stat-value {
  font-family: var(--serif) !important; font-style: italic !important;
  font-weight: 700 !important;
  font-size: 32px !important; line-height: 1.05 !important;
  letter-spacing: -0.01em !important;
  margin: 4px 0 6px 0 !important; color: var(--paper-5) !important;
}
.surf-delta {
  font-family: var(--mono); font-size: 11px; font-weight: 500;
  letter-spacing: 0.08em; margin: 0;
}
.surf-delta--up   { color: var(--ok); }
.surf-delta--down { color: var(--accent-vibrant); }
.surf-delta--flat { color: var(--paper-3); }

/* =========================================================
   CHIP
   ========================================================= */
.surf-chip {
  display: inline-block;
  font-family: var(--mono); font-weight: 700; font-size: 11px;
  letter-spacing: 0.10em; text-transform: uppercase;
  border: 1.5px solid var(--paper-4); border-radius: var(--r-pill);
  padding: 6px 14px; margin: 0 6px 6px 0;
  background: transparent; color: var(--paper-5);
  transition: all var(--t-fast);
}
.surf-chip--accent { border-color: var(--accent-vibrant); color: var(--accent-vibrant); }
.surf-chip--solid  { background: var(--paper-5); color: var(--paper-0); border-color: var(--paper-5); }
.surf-chip--dashed { border-style: dashed; }

/* =========================================================
   STEP ITEM
   ========================================================= */
.surf-steps { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
.surf-step {
  display: inline-flex; align-items: center; gap: 8px;
  font-family: var(--mono); font-weight: 700; font-size: 11px;
  letter-spacing: 0.10em; text-transform: uppercase;
}
.surf-step__bullet {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 999px;
  font-family: var(--mono); font-weight: 700; font-size: 12px;
}
.surf-step--done .surf-step__bullet  { background: var(--paper-5);       color: var(--paper-0); }
.surf-step--active .surf-step__bullet{ background: var(--accent-vibrant);color: var(--paper-0);
  box-shadow: 1px 1px 0 0 var(--paper-shadow); }
.surf-step--todo .surf-step__bullet  { background: transparent; color: var(--paper-3); border: 1.5px solid var(--paper-3); }
.surf-step--done  .surf-step__label, .surf-step--active .surf-step__label { color: var(--paper-5); }
.surf-step--todo  .surf-step__label  { color: var(--paper-3); }

/* =========================================================
   TOPBAR
   ========================================================= */
[class*="st-key-topbar"] {
  border-bottom: 2px solid var(--paper-5);
  padding: 14px 4px 12px 4px; margin-bottom: 32px;
}
.surf-brand {
  font-family: var(--serif); font-style: italic; font-weight: 600;
  font-size: 22px; color: var(--paper-5); margin: 0;
}
.surf-breadcrumb {
  font-family: var(--mono); font-weight: 500; font-size: 11px;
  letter-spacing: 0.10em; text-transform: uppercase;
  color: var(--paper-3); margin: 0; padding-top: 4px;
}
.surf-breadcrumb strong { color: var(--paper-5); font-weight: 700; }
[class*="st-key-topbar-icon"] [data-testid="stButton"] button {
  width: 38px; height: 38px; padding: 0;
  background: transparent; color: var(--paper-5);
  border: 1.5px solid var(--paper-4); box-shadow: none;
  border-radius: var(--r-sm);
  font-family: var(--serif); font-size: 16px;
}
[class*="st-key-topbar-icon"] [data-testid="stButton"] button:hover {
  background: var(--paper-1); transform: none; box-shadow: 2px 2px 0 0 var(--paper-shadow-soft);
}

/* =========================================================
   EMPTY STATE
   ========================================================= */
[class*="st-key-empty"] {
  background: var(--paper);
  border: 2px dashed var(--paper-3);
  border-radius: var(--r-md);
  padding: 36px 28px;
  text-align: center;
}
[class*="st-key-empty"] [data-testid="stMarkdownContainer"] p {
  text-align: center;
}
[data-testid="stMarkdownContainer"] p.surf-empty-headline,
p.surf-empty-headline {
  font-family: var(--mono) !important; font-weight: 700 !important;
  font-size: 18px !important; letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--paper-5) !important; margin: 8px 0 12px 0 !important;
}
[data-testid="stMarkdownContainer"] p.surf-empty-body,
p.surf-empty-body {
  font-family: var(--mono) !important; font-weight: 400 !important;
  font-size: 12px !important; letter-spacing: 0.06em !important;
  line-height: 1.7 !important;
  color: var(--paper-3) !important; max-width: 380px !important;
  margin: 0 auto 18px auto !important;
}
[data-testid="stMarkdownContainer"] p.surf-ornament,
p.surf-ornament {
  font-family: var(--serif) !important; font-size: 22px !important;
  color: var(--paper-3) !important;
  letter-spacing: 0.04em !important; line-height: 1 !important;
  margin-bottom: 4px !important;
}
[data-testid="stMarkdownContainer"] p.surf-brand,
p.surf-brand {
  font-family: var(--serif) !important; font-style: italic !important;
  font-weight: 600 !important; font-size: 22px !important;
  color: var(--paper-5) !important; margin: 0 !important;
}
[data-testid="stMarkdownContainer"] p.surf-breadcrumb,
p.surf-breadcrumb {
  font-family: var(--mono) !important; font-weight: 500 !important;
  font-size: 11px !important; letter-spacing: 0.10em !important;
  text-transform: uppercase !important;
  color: var(--paper-3) !important; margin: 0 !important; padding-top: 4px;
}
[data-testid="stMarkdownContainer"] p.surf-meta,
p.surf-meta {
  font-family: var(--mono) !important; font-weight: 400 !important;
  font-size: 11px !important; letter-spacing: 0.08em !important;
  color: var(--paper-3) !important; margin: 0 !important;
}
[data-testid="stMarkdownContainer"] p.surf-eyebrow,
p.surf-eyebrow {
  font-family: var(--mono) !important; font-weight: 500 !important;
  font-size: 10px !important; letter-spacing: 0.18em !important;
  text-transform: uppercase !important;
  color: var(--paper-3) !important; margin: 0 0 4px 0 !important;
}
[data-testid="stMarkdownContainer"] p.surf-caption,
p.surf-caption {
  font-family: var(--serif) !important; font-style: italic !important;
  font-size: 13px !important; color: var(--paper-3) !important;
  margin: 0 0 8px 0 !important;
}

/* =========================================================
   MCQ CARD CONTAINER (D-2.23, Figma node 4045:282)
   The wrapper that holds the Q-number + class chip + difficulty stars
   header, the question text, the option stack, and the action row.
   ========================================================= */
[class*="st-key-mcq-card"] {
  background: var(--paper);
  border: 2px solid var(--paper-shadow);
  border-radius: 6px;
  box-shadow: 3px 3px 0 0 var(--paper-shadow);
  padding: 22px 20px 20px 20px;
  max-width: 600px;
  margin: 0 auto;
}
[class*="st-key-mcq-card"] [data-testid="stVerticalBlock"] {
  gap: 13px;
}

/* =========================================================
   MCQ OPTION (D-2.20, Figma node 4045:282) — REBUILT
   Four states keyed via the wrapper class: mcq-opt-{key}-{state}
   where state ∈ {off, on, correct, incorrect}.
   Selection signal is paper elevation + stamp shadow appearing — NOT
   an accent color (accents are reserved for P5 review state).
   ========================================================= */

/* Hide Streamlit's native checkbox glyph; we draw our own. */
[class*="st-key-mcq-opt-"] [data-testid="stCheckbox"] svg { display: none; }

/* Base wrapper — visual frame, padding, transitions. */
[class*="st-key-mcq-opt-"] {
  position: relative;
  border-radius: 5px;
  font-family: var(--serif);
  font-size: 17px;
  color: var(--paper-5);
  cursor: pointer;
  transition: background-color var(--t-fast), border-color var(--t-fast),
              box-shadow var(--t-fast), padding var(--t-fast);
}

/* Force the inner checkbox label to inherit the wrapper colors and pad
   so the entire surface is the click target. */
[class*="st-key-mcq-opt-"] [data-testid="stCheckbox"] > label {
  display: flex; align-items: center; gap: 12px;
  cursor: pointer;
  width: 100%;
  padding: 0;
  margin: 0;
}

/* Custom 20×20 checkbox glyph drawn on the native checkbox container.
   Hidden native SVG above; this pseudo-element replaces it.
   :has(input:checked) toggles the filled state. */
[class*="st-key-mcq-opt-"] [data-baseweb="checkbox"] > div:first-child {
  width: 20px !important; height: 20px !important;
  min-width: 20px !important;
  border: 2px solid var(--paper-5) !important;
  border-radius: 5px !important;
  background: var(--paper) !important;
  box-shadow: none !important;
  position: relative;
}
[class*="st-key-mcq-opt-"] [data-baseweb="checkbox"]:has(input:checked) > div:first-child {
  background: var(--paper-5) !important;
}
[class*="st-key-mcq-opt-"] [data-baseweb="checkbox"]:has(input:checked) > div:first-child::after {
  content: "✓";
  position: absolute;
  left: 3.5px;
  top: -1px;
  font-family: 'JetBrains Mono', Menlo, monospace;
  font-weight: 700;
  font-size: 14px;
  color: var(--white);
  line-height: 1;
}

/* OFF — paper-1 bg, 1px paper-shadow border, no shadow, padding 14/13. */
[class*="st-key-mcq-opt-"][class*="-off"] {
  background: var(--paper-1);
  border: 1px solid var(--paper-shadow);
  box-shadow: none;
  padding: 13px 14px;
}
[class*="st-key-mcq-opt-"][class*="-off"]:hover {
  background: var(--paper-0);
}

/* ON — paper-0 bg, 2px paper-shadow border, 2px stamp shadow, padding
   15/14 (border widens 1→2 px so padding shifts 14/13 → 15/14 to keep
   text x-position stable). */
[class*="st-key-mcq-opt-"][class*="-on"] {
  background: var(--paper-0);
  border: 2px solid var(--paper-shadow);
  box-shadow: 2px 2px 0 0 var(--paper-shadow);
  padding: 14px 15px;
}

/* CORRECT — review-only state on P5. ok-wash bg, 2px ok border. */
[class*="st-key-mcq-opt-"][class*="-correct"] {
  background: var(--ok-wash);
  border: 2px solid var(--ok);
  box-shadow: 2px 2px 0 0 var(--paper-shadow);
  padding: 14px 15px;
}

/* INCORRECT — review-only state on P5. accent-soft bg, 2px accent-deep
   border. */
[class*="st-key-mcq-opt-"][class*="-incorrect"] {
  background: var(--accent-soft);
  border: 2px solid var(--accent-deep);
  box-shadow: 2px 2px 0 0 var(--paper-shadow);
  padding: 14px 15px;
}

/* =========================================================
   MESSAGES
   ========================================================= */
[data-testid="stAlertContainer"] {
  border-radius: var(--r-sm); border: 1.5px solid var(--paper-3);
  font-family: var(--serif);
}

/* =========================================================
   STATUS · EXPANDER (D-2.21)
   st.status: 4px left-border; accent-vibrant while running, ok when
   complete. Eyebrow-style header.
   st.expander: paper-1 closed, hover lifts with 2px stamp shadow.
   ========================================================= */
[data-testid="stStatus"],
[data-testid="stStatusWidget"] {
  background: var(--paper-1);
  border: 1.5px solid var(--paper-3);
  border-left: 4px solid var(--accent-vibrant);
  border-radius: var(--r-sm);
  padding: 8px 12px;
}
[data-testid="stStatus"][data-state="complete"],
[data-testid="stStatusWidget"][data-state="complete"] {
  border-left-color: var(--ok);
}
[data-testid="stStatus"][data-state="error"],
[data-testid="stStatusWidget"][data-state="error"] {
  border-left-color: var(--accent-vibrant);
}
[data-testid="stStatus"] summary,
[data-testid="stStatusWidget"] summary {
  font-family: var(--mono); font-weight: 700; font-size: 11px;
  letter-spacing: 0.10em; text-transform: uppercase;
  color: var(--paper-5);
}

[data-testid="stExpander"] {
  background: var(--paper-1);
  border: 1.5px solid var(--paper-3);
  border-radius: var(--r-md);
  transition: transform var(--t-fast), box-shadow var(--t-fast),
              background-color var(--t-fast);
}
[data-testid="stExpander"]:hover {
  background: var(--paper-0);
  transform: translate(-1px, -1px);
  box-shadow: 2px 2px 0 0 var(--paper-shadow-soft);
}
[data-testid="stExpander"] summary {
  font-family: var(--mono); font-weight: 700; font-size: 11px;
  letter-spacing: 0.10em; text-transform: uppercase;
  color: var(--paper-5);
}

/* =========================================================
   ACCESSIBILITY — prefers-reduced-motion (D-2.15)
   Disable transitions and transforms on every interactive surface
   when the OS reports a reduced-motion preference.
   ========================================================= */
@media (prefers-reduced-motion: reduce) {
  [data-testid="stButton"] button,
  [data-testid="stDownloadButton"] button,
  [class*="st-key-card-passive"],
  [class*="st-key-card-interactive"],
  [class*="st-key-class-card"],
  [class*="st-key-stat-card"],
  [class*="st-key-mcq-opt-"],
  [class*="st-key-topbar-icon"] [data-testid="stButton"] button,
  [data-testid="stSlider"] [role="slider"],
  [data-testid="stExpander"] {
    transition: none !important;
    transform: none !important;
  }
}
</style>
"""


def inject_theme() -> None:
    """Inject the Surf theme CSS once. Call near the top of the app entry."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper components — small HTML primitives that match the Figma library.
# Every helper html-escapes user-supplied text before f-string interpolation
# (D-2.19 hardening — closes the XSS surface that the parallel session left
# open in `Streamlit_Test/ui/theme.py`).
# ---------------------------------------------------------------------------


def eyebrow(text: str) -> None:
    """Mono uppercase tracking-out label (e.g. section header)."""
    st.markdown(f'<p class="surf-eyebrow">{html.escape(text)}</p>', unsafe_allow_html=True)


def caption(text: str) -> None:
    """Serif-italic small caption (e.g. helper text)."""
    st.markdown(f'<p class="surf-caption">{html.escape(text)}</p>', unsafe_allow_html=True)


def meta(text: str) -> None:
    """Mono mid-grey small text (e.g. '12 lectures · 78%')."""
    st.markdown(f'<p class="surf-meta">{html.escape(text)}</p>', unsafe_allow_html=True)


def score(value: float) -> None:
    """Big italic Fraunces score (Swiss 1–6 scale).

    Color tracks the value: red (<3.5), gold (3.5–4.99), green (≥5).
    """
    cls = "surf-score--low" if value < 3.5 else ("surf-score--mid" if value < 5 else "surf-score--high")
    label = f"{value:.2f}"
    st.markdown(
        f'<p class="surf-score {cls}">{html.escape(label)}</p>',
        unsafe_allow_html=True,
    )


def chip(text: str, *, variant: str = "outline") -> str:
    """Return chip HTML. variant: outline | accent | solid | dashed."""
    extra = {"outline": "", "accent": " surf-chip--accent",
             "solid": " surf-chip--solid", "dashed": " surf-chip--dashed"}.get(variant, "")
    return f'<span class="surf-chip{extra}">{html.escape(text)}</span>'


def chips_row(items: list[tuple[str, str]]) -> None:
    """Render a row of chips. Each item = (text, variant)."""
    inner = "".join(chip(t, variant=v) for t, v in items)
    st.markdown(inner, unsafe_allow_html=True)


def steps(items: list[tuple[str, str]]) -> None:
    """Render an inline step indicator.

    items: list of (label, status) where status = "done" | "active" | "todo".
    """
    parts: list[str] = []
    for i, (label, status) in enumerate(items, start=1):
        bullet = "✓" if status == "done" else str(i)
        # `status` flows directly into a CSS class name, so restrict it to a
        # known whitelist to make sure a malformed caller can't inject HTML.
        safe_status = status if status in {"done", "active", "todo"} else "todo"
        parts.append(
            f'<span class="surf-step surf-step--{safe_status}">'
            f'<span class="surf-step__bullet">{html.escape(bullet)}</span>'
            f'<span class="surf-step__label">{html.escape(label)}</span>'
            f'</span>'
        )
    st.markdown(f'<div class="surf-steps">{"".join(parts)}</div>', unsafe_allow_html=True)


def stat_card(label: str, value: str, *, eyebrow_text: str = "OVERVIEW",
              delta: str | None = None, delta_dir: str = "flat") -> None:
    """Render a KPI stat card. delta_dir = 'up' | 'down' | 'flat'."""
    arrow = {"up": "▲", "down": "▼", "flat": "—"}.get(delta_dir, "—")
    safe_dir = delta_dir if delta_dir in {"up", "down", "flat"} else "flat"
    delta_html = (
        f'<p class="surf-delta surf-delta--{safe_dir}">'
        f'{html.escape(arrow)}&nbsp;&nbsp;{html.escape(delta)}</p>'
        if delta
        else ""
    )
    st.markdown(
        f'<p class="surf-eyebrow">{html.escape(eyebrow_text)}</p>'
        f'<p class="surf-meta">{html.escape(label)}</p>'
        f'<p class="surf-stat-value">{html.escape(value)}</p>'
        f'{delta_html}',
        unsafe_allow_html=True,
    )


def empty_state_text(headline: str, body: str) -> None:
    """Render the ornament + headline + body inside an empty-state container."""
    st.markdown(
        '<p class="surf-ornament">✲ ✲ ✲</p>'
        f'<p class="surf-empty-headline">{html.escape(headline)}</p>'
        f'<p class="surf-empty-body">{html.escape(body)}</p>',
        unsafe_allow_html=True,
    )

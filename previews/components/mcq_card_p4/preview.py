"""Sandbox — full P4 Take-Mock MCQ card composition (clickable).

Run from the repo root:
    streamlit run previews/components/mcq_card_p4/preview.py

Renders ONE MCQ card as it would appear on the live P4 page, with:
- Question header (Fraunces italic + Mono meta line)
- Difficulty stars (5-slot, hard-coded 3/5 for the demo — production
  fills via `difficulty_stars(score)` once Phase-4 ML lands)
- 4 options A–D with single-select (radio-style) behaviour driven by
  the D-2.20a `:has(input:checked)` rule on the `mcq-opt-{q}-{letter}`
  wrappers. Clicking a new option deselects the previous one.
- Submit / Skip / Clear action row (D-2.23 P4 footer; the Idea v1 §3
  rename "Clear → Skip" is honoured — see README for the synthesis.)
- Rationale block — hidden until Submit; revealed inline below the
  options when a correctness verdict has been computed.
- Three demo questions cycled via Next so Tiago can step through
  the full state machine: unanswered → selected → submitted-correct
  → submitted-incorrect → next.

Sandbox isolation (CLAUDE.md): zero `from app...` imports; everything
the card needs is in this folder (`_theme.py`, `_fixtures.py`,
`_difficulty.py`, `star_filled.svg`, `star_empty.svg`).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Sibling-relative import so the sandbox is fully self-contained.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402
from _difficulty import difficulty_stars  # noqa: E402
from _theme import (  # noqa: E402
    caption,
    eyebrow,
    heading_h2,
    inject_theme,
    meta,
)

# ---------------------------------------------------------------------------
# Demo data — 3 fake questions cycled via Next. Each carries a question text,
# 4 options, the correct option letter, and a placeholder rationale.
#
# Production note (Plan 02-05): question_text + options come from the
# `questions` table; correct_indices is decoded from JSON; rationale comes
# from `questions.rationales_per_option_json` indexed by selected option
# (Phase 1 D-2.6 — per-option rationale; one rationale per option).
# This sandbox uses ONE rationale per question for simplicity — production
# will pull `rationales[selected_index]` so each option's rationale is
# tailored.
# ---------------------------------------------------------------------------
DEMO_QUESTIONS: list[dict] = [
    {
        "q_number": 3,
        "total": 19,
        "lecture_label": "MII Lecture 01",
        "class_abbrev": "MII",
        "question": "Which factor is NOT a determinant of demand?",
        "options": [
            ("A", "Consumer income"),
            ("B", "Price of related goods"),
            ("C", "Production technology"),
            ("D", "Consumer preferences"),
        ],
        "correct": "C",
        "difficulty_score": 0.62,  # → 3 stars filled
        "rationale": (
            "Production technology is a determinant of **supply**, not demand. "
            "The four canonical determinants of demand are consumer income, the "
            "prices of related goods (substitutes and complements), consumer "
            "tastes/preferences, and expectations about future prices. Cost-side "
            "factors like technology shift the supply curve, not the demand curve."
        ),
    },
    {
        "q_number": 4,
        "total": 19,
        "lecture_label": "MII Lecture 01",
        "class_abbrev": "MII",
        "question": "What does the demand curve typically slope?",
        "options": [
            ("A", "Upward"),
            ("B", "Downward"),
            ("C", "Flat (horizontal)"),
            ("D", "Vertical"),
        ],
        "correct": "B",
        "difficulty_score": 0.18,  # → 1 star filled
        "rationale": (
            "The Law of Demand states that, all else equal, quantity demanded "
            "decreases as price rises — so the demand curve slopes **downward**. "
            "Upward-sloping demand is the rare Veblen-good case (status goods). "
            "Flat = perfectly elastic; vertical = perfectly inelastic — both are "
            "special-case curves, not the typical shape."
        ),
    },
    {
        "q_number": 5,
        "total": 19,
        "lecture_label": "MII Lecture 01",
        "class_abbrev": "MII",
        "question": "A movement ALONG the demand curve is caused by…",
        "options": [
            ("A", "A change in price of the good"),
            ("B", "A change in income"),
            ("C", "A change in tastes"),
            ("D", "A change in price of substitutes"),
        ],
        "correct": "A",
        "difficulty_score": 0.45,  # → 2 stars filled
        "rationale": (
            "Only a change in the **good's own price** moves you along the "
            "existing demand curve. Income, tastes, and substitute prices are "
            "all non-price determinants — they SHIFT the entire curve to a new "
            "position. The distinction between movement-along and shift-of is "
            "one of the most-tested ideas on this section's exam."
        ),
    },
]


# ---------------------------------------------------------------------------
# Session-state init
# ---------------------------------------------------------------------------
def _reset_for_question(q_index: int) -> None:
    """Set session state for a fresh-unanswered display of question q_index."""
    st.session_state["q_index"] = q_index
    st.session_state["selected"] = None         # None | 'A' | 'B' | 'C' | 'D'
    st.session_state["submitted"] = False
    st.session_state["last_action"] = None      # toast message after click
    # Per-option checkbox values — driven from `selected` so radio behaviour
    # works without `key=` collisions across reruns.


if "q_index" not in st.session_state:
    _reset_for_question(0)


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Surf — P4 MCQ card sandbox", layout="centered")
inject_theme()


# Page chrome — eyebrow + small caption explaining the sandbox.
eyebrow("Surf · Sandbox · P4 Take Mock composition")
heading_h2("Mock taking — Question card")
caption(
    "Click an option below to see the live Off→On animation (D-2.20a). "
    "Click Submit to lock the answer and reveal the rationale. Click Next "
    "to cycle to the next demo question. Skip clears your pick and advances. "
    "Clear deselects without advancing."
)

# Show the toast for the last action, if any.
if st.session_state["last_action"]:
    st.info(st.session_state["last_action"])


# ---------------------------------------------------------------------------
# Render the MCQ card
# ---------------------------------------------------------------------------
q = DEMO_QUESTIONS[st.session_state["q_index"]]
selected: str | None = st.session_state["selected"]
submitted: bool = st.session_state["submitted"]
correct_letter: str = q["correct"]


# Callbacks — these run BEFORE the next rerun, so writing to session_state
# here is what drives the "radio behaviour with checkbox glyph" pattern.
def _select(letter: str) -> None:
    """Record this option as the new selection. Other options auto-deselect on
    rerun because each checkbox computes its `value` from `selected ==
    letter` rather than holding its own state via `key=`."""
    if st.session_state["submitted"]:
        return  # locked after submit
    st.session_state["selected"] = letter
    st.session_state["last_action"] = None


def _on_submit() -> None:
    """Lock the answer and reveal the rationale. If nothing was picked,
    treat as a no-op (Submit should be greyed out by then anyway)."""
    if st.session_state["selected"] is None:
        return
    st.session_state["submitted"] = True
    st.session_state["last_action"] = None


def _on_skip() -> None:
    """Mark the question as skipped (selected_indices = NULL on the real
    DB write per D-3.1) and advance to the next demo question."""
    st.session_state["last_action"] = (
        f"Skipped question {q['q_number']} — would advance to question "
        f"{q['q_number'] + 1} of {q['total']} "
        "(production: writes selected_indices=NULL to attempt_answers)."
    )
    next_idx = (st.session_state["q_index"] + 1) % len(DEMO_QUESTIONS)
    _reset_for_question(next_idx)


def _on_clear() -> None:
    """Deselect the current pick without advancing. (Pre-submit only.)"""
    if st.session_state["submitted"]:
        return
    st.session_state["selected"] = None
    st.session_state["last_action"] = None


def _on_next() -> None:
    """Advance to the next demo question (post-submit only). Cycles through
    the 3 demos."""
    st.session_state["last_action"] = (
        f"Advanced to question {((st.session_state['q_index'] + 1) % len(DEMO_QUESTIONS)) + 3} "
        "(production: writes attempt_answer + advances mock cursor)."
    )
    next_idx = (st.session_state["q_index"] + 1) % len(DEMO_QUESTIONS)
    _reset_for_question(next_idx)


# The card itself — wrapper key matches the D-2.23 spec exactly.
with st.container(key="mcq-card"):
    # --- Header row: Q-chip + class chip + difficulty stars ---
    header_cols = st.columns([1, 1, 4])
    with header_cols[0]:
        st.markdown(
            f'<span class="surf-chip surf-chip--solid">Q{q["q_number"]}</span>',
            unsafe_allow_html=True,
        )
    with header_cols[1]:
        st.markdown(
            f'<span class="surf-chip">{q["class_abbrev"]}</span>',
            unsafe_allow_html=True,
        )
    with header_cols[2]:
        # Difficulty stars rendered via the sandbox copy of _difficulty.py.
        # 0.62 → 3/5 stars filled; 0.18 → 1/5; 0.45 → 2/5 — the demos cover
        # different difficulty levels so Tiago sees the chip change as he
        # cycles through.
        difficulty_stars(q["difficulty_score"])

    # --- Question text (Serif/H2 — Fraunces SemiBold Italic 28/115%/-1%) ---
    st.markdown(f'<h2 class="serif-h2">{q["question"]}</h2>', unsafe_allow_html=True)

    # --- Meta line: P4 · Q{n} of {total} · {lecture} ---
    meta(f"P4 · Q{q['q_number']} of {q['total']} · {q['lecture_label']}")

    st.markdown("")  # 13 px section gap (mcq-card stVerticalBlock rule)

    # --- 4 option rows ---
    # Each option's wrapper key is `mcq-opt-{q_number}-{letter}` for live
    # Off/On (D-2.20a `:has(input:checked)`) PRE-submit, then `-correct` /
    # `-incorrect` POST-submit (D-2.20 state-baked review keys).
    for letter, text in q["options"]:
        is_picked = (selected == letter)
        is_right = (letter == correct_letter)

        # Decide the wrapper key. Pre-submit: identity-only for live Off/On.
        # Post-submit: state-baked suffix paints the review surface.
        if not submitted:
            wrapper_key = f"mcq-opt-q{q['q_number']}-{letter.lower()}"
        else:
            # Review state. The chosen option gets correct/incorrect based
            # on whether they were right; the actually-correct option (if
            # they got it wrong) ALSO highlights as correct so they see what
            # the right answer was.
            if is_picked and is_right:
                wrapper_key = f"mcq-opt-q{q['q_number']}-{letter.lower()}-correct"
            elif is_picked and not is_right:
                wrapper_key = f"mcq-opt-q{q['q_number']}-{letter.lower()}-incorrect"
            elif not is_picked and is_right:
                # Always reveal the correct answer post-submit.
                wrapper_key = f"mcq-opt-q{q['q_number']}-{letter.lower()}-correct"
            else:
                wrapper_key = f"mcq-opt-q{q['q_number']}-{letter.lower()}"

        with st.container(key=wrapper_key):
            # Each render computes `value` from session state — no `key=` on
            # the checkbox itself, so the radio-style swap on rerun works
            # without state-collision bugs.
            st.checkbox(
                f"{letter}. {text}",
                value=is_picked,
                disabled=submitted,
                on_change=_select,
                args=(letter,),
                key=f"_cb_q{q['q_number']}_{letter}_{submitted}",
            )

    # --- Rationale block (revealed AFTER submit) ---
    if submitted:
        verdict = "Correct ✓" if (selected == correct_letter) else "Not quite"
        st.markdown("")  # 13 px gap
        with st.container(key="card-passive-rationale"):
            eyebrow(f"RATIONALE · {verdict.upper()}")
            st.markdown(q["rationale"])
            caption(
                "Production: this text comes from "
                "`questions.rationales_per_option_json[selected_index]` — "
                "Phase 1 D-2.6 ships one rationale per option."
            )

    st.markdown("")  # 13 px gap before action row

    # --- Action row ---
    if not submitted:
        # Pre-submit: [Clear] [Skip] [Submit] — equal flex per D-2.23.
        action_cols = st.columns(3)
        with action_cols[0]:
            with st.container(key="btn-ghost-clear"):
                st.button(
                    "Clear",
                    key="btn_clear",
                    disabled=(selected is None),
                    on_click=_on_clear,
                    use_container_width=True,
                )
        with action_cols[1]:
            with st.container(key="btn-ghost-skip"):
                st.button(
                    "Skip",
                    key="btn_skip",
                    on_click=_on_skip,
                    use_container_width=True,
                )
        with action_cols[2]:
            with st.container(key="btn-default-submit"):
                st.button(
                    "Submit",
                    key="btn_submit",
                    disabled=(selected is None),
                    on_click=_on_submit,
                    use_container_width=True,
                )
    else:
        # Post-submit: single full-width [Next] (D-2.23 P5-checked rule —
        # full-width REST button. Tiago's brief calls this Next; same
        # affordance, different label).
        with st.container(key="btn-default-next"):
            st.button(
                "Next question",
                key="btn_next",
                on_click=_on_next,
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Sandbox footer — what state the card is in right now (debug aid)
# ---------------------------------------------------------------------------
st.divider()
eyebrow("Sandbox state")
state_label = (
    f"Q{q['q_number']} of {q['total']}  ·  "
    f"selected={selected!r}  ·  "
    f"submitted={submitted}  ·  "
    f"correct_answer={correct_letter}"
)
meta(state_label)
caption(
    "States demonstrated: unanswered (no pick) → selected (picked, pre-submit, "
    "live :has() animation) → submitted-correct OR submitted-incorrect "
    "(state-baked keys + rationale revealed) → next (resets to a fresh demo "
    "question). Skip / Clear paths also live."
)

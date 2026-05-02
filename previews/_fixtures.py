"""Pure-data fixtures + a fake_call_claude stub for Surf sandboxes.

This module is the canonical fixture surface every preview imports
(or copies into its own folder if it wants byte-isolation). Pure
Python: no `streamlit` import, no `from app...` imports, no DB
connection. Mirrors the locked schemas in
`app/db/schema/schema.sql` and the Phase 1 verification numbers in
`.planning/phases/01-ingestion-spine-database/01-VERIFICATION.md`.
"""

from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------------
# users  (single-user app; row count is always 0 or 1)
# --------------------------------------------------------------------------
FAKE_USER: dict[str, Any] = {
    "id": 1,
    "username": "tiago",
    "anthropic_api_key": "sk-ant-fake-fixture-key-not-real",
    "created_at": "2026-04-30 10:00:00",
}


# --------------------------------------------------------------------------
# classes  (factsheet_json is a serialized 7-key dict per Phase 1 D-1.2)
# --------------------------------------------------------------------------
FAKE_CLASS: dict[str, Any] = {
    "id": 1,
    "user_id": 1,
    "name": "Microeconomics I",
    "factsheet_json": (
        '{"title": "Microeconomics I", '
        '"semester": "Spring 2026", '
        '"professor": "Prof. K. Müller", '
        '"goal": "Understand supply and demand in competitive markets.", '
        '"format": "12 lectures · written exam.", '
        '"assessment": "70% final exam, 30% participation.", '
        '"language": "EN"}'
    ),
    "pass_threshold_pct": 50,
    "created_at": "2026-04-30 10:30:00",
}


# --------------------------------------------------------------------------
# lectures  (3: 1 done, 1 pending, 1 done — mirrors a real class hub)
# --------------------------------------------------------------------------
FAKE_LECTURES: list[dict[str, Any]] = [
    {
        "id": 1,
        "class_id": 1,
        "title": "Lecture 01 — Introduction to markets",
        "source_pdf_path": "/Users/tiago/MII_lecture_01.pdf",
        "total_pages": 19,
        "status": "done",
        "created_at": "2026-04-30 11:00:00",
    },
    {
        "id": 2,
        "class_id": 1,
        "title": "Lecture 02 — Supply and demand",
        "source_pdf_path": "/Users/tiago/MII_lecture_02.pdf",
        "total_pages": 24,
        "status": "pending",
        "created_at": "2026-05-01 09:00:00",
    },
    {
        "id": 3,
        "class_id": 1,
        "title": "Lecture 03 — Elasticity",
        "source_pdf_path": "/Users/tiago/MII_lecture_03.pdf",
        "total_pages": 22,
        "status": "done",
        "created_at": "2026-05-02 14:00:00",
    },
]


# --------------------------------------------------------------------------
# learning_objectives  (4 with page_start / page_end)
# --------------------------------------------------------------------------
FAKE_LOS: list[dict[str, Any]] = [
    {
        "id": 1,
        "lecture_id": 1,
        "title": "Identify the four conditions of a perfectly competitive market",
        "page_start": 4,
        "page_end": 7,
        "created_at": "2026-04-30 11:05:00",
    },
    {
        "id": 2,
        "lecture_id": 1,
        "title": "Distinguish movement along the demand curve from a shift",
        "page_start": 8,
        "page_end": 12,
        "created_at": "2026-04-30 11:05:00",
    },
    {
        "id": 3,
        "lecture_id": 1,
        "title": "Compute equilibrium price and quantity given linear curves",
        "page_start": 13,
        "page_end": 17,
        "created_at": "2026-04-30 11:05:00",
    },
    {
        "id": 4,
        "lecture_id": 3,
        "title": "Compute price elasticity of demand and classify it",
        "page_start": 3,
        "page_end": 9,
        "created_at": "2026-05-02 14:05:00",
    },
]


# --------------------------------------------------------------------------
# slide_pages  (~19 kept + 12 ignored, mirroring the MII_SM1 verification
# numbers from 01-VERIFICATION.md). Pages 1-2 + 30-31 are usually ignored
# (title page + sources/references).
# --------------------------------------------------------------------------
def _make_slide_pages() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page_id = 0
    # Lecture 1 — 19 kept (pages 4..22), 12 ignored (1..3, 23..31)
    for page_number in range(1, 32):
        page_id += 1
        is_kept = 4 <= page_number <= 22
        # Bind kept pages to LOs by their page ranges.
        lo_id: int | None = None
        if 4 <= page_number <= 7:
            lo_id = 1
        elif 8 <= page_number <= 12:
            lo_id = 2
        elif 13 <= page_number <= 17:
            lo_id = 3
        rows.append({
            "id": page_id,
            "lecture_id": 1,
            "page_number": page_number,
            "raw_md": (
                f"# Page {page_number}\n\n"
                f"Body text for slide {page_number} of MII lecture 01."
            ),
            "status": "kept" if is_kept else "ignored",
            "learning_objective_id": lo_id,
            "created_at": "2026-04-30 11:10:00",
        })
    return rows


FAKE_SLIDE_PAGES: list[dict[str, Any]] = _make_slide_pages()


# --------------------------------------------------------------------------
# questions  (19 MCQs; 4 are multi-correct per D-2.5)
# --------------------------------------------------------------------------
def _mk_mcq(
    qid: int,
    slide_page_id: int,
    question_text: str,
    options: list[str],
    correct_indices: list[int],
    rationales: list[str],
    source_page: int,
    difficulty_score: float | None,
) -> dict[str, Any]:
    import json
    return {
        "id": qid,
        "slide_page_id": slide_page_id,
        "question_text": question_text,
        "options_json": json.dumps(options),
        "correct_indices": json.dumps(correct_indices),
        "rationales_per_option_json": json.dumps(rationales),
        "source_page": source_page,
        "language": "en",
        "difficulty_word_count": len(question_text.split()),
        "difficulty_readability": 0.55,
        "difficulty_distractor_similarity": 0.42,
        "difficulty_conceptual_density": 3,
        "difficulty_distractor_derivation": 2,
        "difficulty_reasoning_steps": 2,
        "difficulty_score": difficulty_score,
        "created_at": "2026-04-30 12:00:00",
    }


FAKE_MCQS: list[dict[str, Any]] = [
    # 4..22 kept-page range → 19 MCQs total. 4 multi-correct (q3, q7, q11, q15).
    _mk_mcq(1, 4, "Which assumption underpins a perfectly competitive market?",
            ["No barriers to entry", "Unique product differentiation",
             "Government price floors", "Concentrated market power"],
            [0], ["Correct — free entry/exit is a defining condition.",
                  "Wrong — competitive markets sell homogeneous goods.",
                  "Wrong — price floors create surplus, not competition.",
                  "Wrong — competitive markets have many small sellers."],
            4, 0.30),
    _mk_mcq(2, 5, "What does the demand curve typically slope?",
            ["Upward", "Downward", "Flat (horizontal)", "Vertical"],
            [1], ["Wrong — that would imply Veblen-good behaviour.",
                  "Correct — quantity demanded falls as price rises.",
                  "Wrong — a flat curve is perfectly elastic, the special case.",
                  "Wrong — vertical means perfectly inelastic, the other special case."],
            5, 0.18),
    _mk_mcq(3, 6, "Which of the following are determinants of demand? (select all)",
            ["Consumer income", "Price of related goods",
             "Production technology", "Consumer preferences"],
            [0, 1, 3], ["Correct — income shifts demand.",
                        "Correct — substitutes/complements shift demand.",
                        "Wrong — production tech shifts SUPPLY, not demand.",
                        "Correct — preferences shift demand."],
            6, 0.62),
    _mk_mcq(4, 7, "Equilibrium occurs where…",
            ["Supply equals demand", "Government sets the price",
             "Firms maximize revenue", "Consumers buy the most"],
            [0], ["Correct — Q_s = Q_d defines equilibrium.",
                  "Wrong — that's a price control, not equilibrium.",
                  "Wrong — revenue max is a different optimization.",
                  "Wrong — consumers' willingness to buy depends on price."],
            7, 0.22),
    _mk_mcq(5, 8, "A movement ALONG the demand curve is caused by…",
            ["A change in price of the good", "A change in income",
             "A change in tastes", "A change in price of substitutes"],
            [0], ["Correct — only own-price moves you along the curve.",
                  "Wrong — income shifts the whole curve.",
                  "Wrong — tastes shift the whole curve.",
                  "Wrong — substitute price shifts the whole curve."],
            8, 0.45),
    _mk_mcq(6, 9, "A SHIFT of the demand curve is caused by…",
            ["A change in price of the good", "A change in income",
             "A change in quantity demanded", "Excess supply"],
            [1], ["Wrong — that's movement along.",
                  "Correct — non-price determinant shifts the curve.",
                  "Wrong — quantity demanded is a result, not a cause.",
                  "Wrong — that's a market condition, not a shift cause."],
            9, 0.42),
    _mk_mcq(7, 10, "Which of the following SHIFT supply rightward? (select all)",
            ["Lower input prices", "Improved technology",
             "Higher taxes on producers", "More producers in the market"],
            [0, 1, 3], ["Correct — lower costs ⇒ more profitable to supply.",
                        "Correct — efficiency gains shift supply right.",
                        "Wrong — taxes shift supply LEFT (less profit).",
                        "Correct — more sellers expands market supply."],
            10, 0.68),
    _mk_mcq(8, 11, "If demand shifts right and supply is unchanged, equilibrium price…",
            ["Falls", "Stays the same", "Rises", "Becomes indeterminate"],
            [2], ["Wrong — that's the shift-left case.",
                  "Wrong — only if supply also shifts right by the same amount.",
                  "Correct — higher demand at every price ⇒ higher equilibrium price.",
                  "Wrong — direction is determinate when only one curve moves."],
            11, 0.38),
    _mk_mcq(9, 12, "A price floor set ABOVE equilibrium causes…",
            ["A surplus", "A shortage", "No change", "An equilibrium shift"],
            [0], ["Correct — Q_s > Q_d at the floor price.",
                  "Wrong — floors create surplus, ceilings create shortage.",
                  "Wrong — the binding floor changes quantities traded.",
                  "Wrong — equilibrium itself doesn't shift; the market is constrained."],
            12, 0.50),
    _mk_mcq(10, 13, "Which of the following are characteristics of price ceilings? (select all)",
            ["Below equilibrium they create shortages",
             "They cap the maximum legal price",
             "They always benefit producers",
             "They can lead to black markets"],
            [0, 1, 3], ["Correct — binding ceilings produce shortage.",
                        "Correct — that's the definition.",
                        "Wrong — they hurt producers (lower revenue).",
                        "Correct — unmet demand spills into informal markets."],
            13, 0.71),
    _mk_mcq(11, 14, "Compute equilibrium price for Q_d = 100 - 2P, Q_s = 20 + 2P.",
            ["P = 10", "P = 20", "P = 30", "P = 40"],
            [1], ["Wrong — set 100-2P=20+2P; P=20.",
                  "Correct — 100-2P=20+2P ⇒ 80=4P ⇒ P=20.",
                  "Wrong — see above.",
                  "Wrong — see above."],
            14, 0.55),
    _mk_mcq(12, 15, "At P = 20 in the previous question, equilibrium quantity is…",
            ["Q = 40", "Q = 60", "Q = 80", "Q = 100"],
            [1], ["Wrong — plug P=20 into either curve.",
                  "Correct — Q = 100-2(20) = 60 = 20+2(20).",
                  "Wrong — see above.",
                  "Wrong — see above."],
            15, 0.48),
    _mk_mcq(13, 16, "Consumer surplus is geometrically the area…",
            ["Above the price, below the demand curve",
             "Above the supply curve, below the price",
             "Between supply and demand",
             "Below the equilibrium quantity"],
            [0], ["Correct — willingness to pay minus actual price.",
                  "Wrong — that's producer surplus.",
                  "Wrong — that's total welfare.",
                  "Wrong — quantity is the x-axis, not an area."],
            16, 0.58),
    _mk_mcq(14, 17, "Producer surplus is geometrically the area…",
            ["Above the price, below the demand curve",
             "Above the supply curve, below the price",
             "Between supply and demand",
             "Below the equilibrium quantity"],
            [1], ["Wrong — consumer surplus.",
                  "Correct — price received minus marginal cost.",
                  "Wrong — total welfare.",
                  "Wrong — quantity is the x-axis."],
            17, 0.60),
    _mk_mcq(15, 18, "Which of the following CAUSE deadweight loss? (select all)",
            ["Binding price ceilings", "Per-unit excise taxes",
             "Free entry into the market", "Binding price floors"],
            [0, 1, 3], ["Correct — binding ceilings reduce trade.",
                        "Correct — taxes drive a wedge.",
                        "Wrong — free entry typically EXPANDS welfare.",
                        "Correct — binding floors reduce trade."],
            18, 0.74),
    _mk_mcq(16, 19, "Price elasticity of demand measures…",
            ["The slope of the demand curve",
             "Percent change in quantity per percent change in price",
             "The income elasticity of the buyer",
             "The slope of the supply curve"],
            [1], ["Wrong — slope ≠ elasticity (units differ).",
                  "Correct — elasticity is unit-free.",
                  "Wrong — that's income elasticity.",
                  "Wrong — that's price elasticity of supply."],
            19, 0.40),
    _mk_mcq(17, 20, "If |E_d| > 1, demand is…",
            ["Inelastic", "Unit elastic", "Elastic", "Perfectly inelastic"],
            [2], ["Wrong — that's |E_d| < 1.",
                  "Wrong — that's |E_d| = 1.",
                  "Correct — quantity responds more than proportionally to price.",
                  "Wrong — perfectly inelastic is |E_d| = 0."],
            20, 0.35),
    _mk_mcq(18, 21, "A tax on sellers in a market with elastic demand falls mostly on…",
            ["Sellers", "Buyers", "Both equally", "Neither — taxes are neutral"],
            [0], ["Correct — elastic buyers walk away; sellers absorb most of the tax.",
                  "Wrong — that's the inelastic-demand case.",
                  "Wrong — only when elasticities are symmetric.",
                  "Wrong — taxes generally cause deadweight loss."],
            21, 0.66),
    _mk_mcq(19, 22, "The cross-price elasticity of substitutes is…",
            ["Negative", "Zero", "Positive", "Undefined"],
            [2], ["Wrong — that's complements.",
                  "Wrong — that's unrelated goods.",
                  "Correct — when good X price rises, demand for substitute Y rises.",
                  "Wrong — it's well-defined for substitutes."],
            22, 0.52),
]


# --------------------------------------------------------------------------
# attempts  (FAKE_ATTEMPT = an in-progress one for P4 demos;
# FAKE_ATTEMPT_COMPLETED = a finished one for P5 demos.)
# --------------------------------------------------------------------------
FAKE_ATTEMPT: dict[str, Any] = {
    "id": 1,
    "class_id": 1,
    "mock_kind": "standard",
    "started_at": "2026-05-02 16:30:00",
    "finished_at": None,
    "correct_count": None,
    "total_count": 5,
}


FAKE_ATTEMPT_COMPLETED: dict[str, Any] = {
    "id": 2,
    "class_id": 1,
    "mock_kind": "standard",
    "started_at": "2026-05-02 14:00:00",
    "finished_at": "2026-05-02 14:18:00",
    "correct_count": 4,
    "total_count": 5,
}


# --------------------------------------------------------------------------
# attempt_answers  (3 correct + 1 wrong + 1 NULL/skipped — for the P5 review
# demos. Bound to FAKE_ATTEMPT_COMPLETED.)
# --------------------------------------------------------------------------
FAKE_ATTEMPT_ANSWERS: list[dict[str, Any]] = [
    {
        "id": 1, "attempt_id": 2, "question_id": 1,
        "selected_indices": "[0]", "is_correct": 1,
        "answered_at": "2026-05-02 14:02:00",
    },
    {
        "id": 2, "attempt_id": 2, "question_id": 2,
        "selected_indices": "[1]", "is_correct": 1,
        "answered_at": "2026-05-02 14:05:00",
    },
    {
        "id": 3, "attempt_id": 2, "question_id": 3,
        # multi-correct: [0,1,3] is right; user picked [0,1] (incomplete)
        "selected_indices": "[0, 1]", "is_correct": 0,
        "answered_at": "2026-05-02 14:09:00",
    },
    {
        "id": 4, "attempt_id": 2, "question_id": 4,
        "selected_indices": "[0]", "is_correct": 1,
        "answered_at": "2026-05-02 14:12:00",
    },
    {
        "id": 5, "attempt_id": 2, "question_id": 5,
        # SKIP: NULL selected_indices, NULL is_correct (counts as wrong on submit)
        "selected_indices": None, "is_correct": None,
        "answered_at": "2026-05-02 14:15:00",
    },
]


# --------------------------------------------------------------------------
# fake_call_claude  (canonical stub — every sandbox imports OR copies this)
#
# Returns hard-coded JSON for the four prompt paths Phase 2 cares about:
#   1. API-key validate ping   → {"ok": True}
#   2. factsheet_clean         → fixed 7-key factsheet dict
#   3. lo_extract              → fixed list of 2 LOs
#   4. mcq_generate            → first 3 MCQs from FAKE_MCQS, decoded
#
# The path is detected by sniffing distinctive substrings of the system
# prompt; see the elif chain. NO real Anthropic SDK call.
# --------------------------------------------------------------------------
def fake_call_claude(
    *,
    system_prompt: str,
    user_message: str = "",
    expect_json: bool = False,
) -> dict[str, Any] | str:
    """Drop-in replacement for `app.brain.claude_client.call_claude`.

    The real signature accepts more kwargs (model, max_tokens, etc.) — this
    fake ignores them. Sandboxes that need to assert call counts can patch
    this module's `_CALL_LOG` list.
    """
    _CALL_LOG.append({"system_prompt": system_prompt, "user_message": user_message})

    sp = system_prompt.lower()

    # 1. API-key validate ping (P1) — tiny system prompt, expects "ok"
    if "validate" in sp or "ping" in sp or len(system_prompt) < 80:
        return {"ok": True} if expect_json else "ok"

    # 2. factsheet_clean — fixed 7-key dict
    if "factsheet" in sp or "clean" in sp:
        return {
            "title": "Microeconomics I",
            "semester": "Spring 2026",
            "professor": "Prof. K. Müller",
            "goal": "Understand supply and demand in competitive markets.",
            "format": "12 lectures · written exam.",
            "assessment": "70% final exam, 30% participation.",
            "language": "EN",
        }

    # 3. lo_extract — fixed 2-LO + 2 ignored pages list
    if "learning objective" in sp or "lo_extract" in sp:
        return {
            "learning_objectives": [
                {"title": "Identify the four conditions of perfect competition",
                 "page_range": [4, 7]},
                {"title": "Distinguish movement along vs. shift of demand",
                 "page_range": [8, 12]},
            ],
            "ignored_pages": [
                {"page_number": 1, "reason": "title page"},
                {"page_number": 2, "reason": "table of contents"},
            ],
            "language": "en",
        }

    # 4. mcq_generate — first 3 MCQs from FAKE_MCQS, decoded back to dicts
    if "mcq" in sp or "multiple-choice" in sp or "generate" in sp:
        import json
        return {
            "by_slide": [
                {
                    "page_number": q["source_page"],
                    "mcqs": [{
                        "question": q["question_text"],
                        "options": json.loads(q["options_json"]),
                        "correct_indices": json.loads(q["correct_indices"]),
                        "rationales_per_option": json.loads(q["rationales_per_option_json"]),
                        "source_page": q["source_page"],
                        "language": q["language"],
                    }],
                }
                for q in FAKE_MCQS[:3]
            ],
        }

    # Fallthrough — unknown prompt path. Return a benign empty dict so the
    # caller doesn't crash but the test author notices the gap.
    return {} if expect_json else ""


_CALL_LOG: list[dict[str, Any]] = []


__all__ = [
    "FAKE_USER",
    "FAKE_CLASS",
    "FAKE_LECTURES",
    "FAKE_LOS",
    "FAKE_SLIDE_PAGES",
    "FAKE_MCQS",
    "FAKE_ATTEMPT",
    "FAKE_ATTEMPT_COMPLETED",
    "FAKE_ATTEMPT_ANSWERS",
    "fake_call_claude",
]

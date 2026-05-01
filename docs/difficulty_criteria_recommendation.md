# Phase 1 Difficulty Criteria — Recommendation

> Source: NotebookLM analysis of 4 HSG quantitative exam catalogues (ACA, Macro, Micro, Stats), 2026-05-01.
> Notebook: `2026-05-01 Surf — Exam MCQ Profiles` (id `24ecbcb7-542f-495f-b505-da1b90ce7e63`). Confidence: High.
>
> **Context:** Surf scores every generated MCQ on a small set of difficulty features. 3 features are LOCKED (computed in Phase 1): `difficulty_word_count`, `difficulty_readability`, `difficulty_distractor_similarity`. 3 more slots are PENDING — currently named `difficulty_topic`, `difficulty_concept_overlap`, `difficulty_skip_confidence` as placeholders. This document proposes the 3 features that should fill those slots.
>
> **Computability constraint:** all 3 must be computable from the slide markdown + the generated MCQ alone (no human labelling, no per-student data, no external corpus). LLM calls are acceptable.
>
> **Coverage requirement:** the 3 must collectively cover both calculation-style hardness AND theory/concept-style hardness.

## Criterion: `difficulty_reasoning_steps`
**Recommended column name:** `difficulty_reasoning_steps`
**Replaces placeholder:** `difficulty_skip_confidence`
**What it measures:** The number of sequential operations (mathematical calculations or logical rule applications) required to reach the correct answer from the given stem.
**How to compute (Phase 1):** Execute an LLM call providing the source slide markdown, the question stem, and the correct answer. Prompt the LLM to output the strictly necessary step-by-step solution path (e.g., "Step 1: identify formula. Step 2: plug in variable X. Step 3: solve for Y. Step 4: apply rule Z"). The computed feature is the integer count of these discrete steps.
**Evidence from sources:** Single-step recall is fundamentally easier than multi-step derivation. Asking to identify the formula for the marginal product of labor [macro, Q2.1, 99] is one retrieval step. Finding the steady-state output per worker [macro, Q2.2, 100] requires recalling the Solow equation, substituting given parameters ($A=8, \alpha=3/4, s=0.2$), and algebraically solving — clearly higher reasoning load.
**Hardness type covered:** both (mathematical operations in calc questions; sequential logical deductions in theory questions)
**Range / scale:** integer 1 to 10. `1` = simple fact retrieval. `≥ 4` = complex multi-step derivation or complex conditional logic.

## Criterion: `difficulty_conceptual_density`
**Recommended column name:** `difficulty_conceptual_density`
**Replaces placeholder:** `difficulty_topic`
**What it measures:** The working-memory load of the question, defined as the count of distinct domain-specific parameters, rules, or framework concepts that must be evaluated *simultaneously* to solve the problem.
**How to compute (Phase 1):** Execute an LLM (or NLP entity-extraction) call against the question stem and the correct option. Instruct the model to extract and count the distinct domain entities (variables, accounting standards, theoretical frameworks, or specific conditions) that are explicitly defined in the provided source markdown and actively required to solve the question.
**Evidence from sources:** Questions testing isolated definitions have low density (e.g., identifying the scale level of $Y = 2X$ [stats, Q2, 238]). High-density questions force synthesis of many parameters — calculating the IFRS equity value in [aca, Q1.8, 57] requires concurrent processing of acquisition costs, book value, silent reserves, useful life, annual profit, and dividend distributions.
**Hardness type covered:** both (variable count in calc questions; framework-constraint count in concept questions)
**Range / scale:** integer 1 to 15. `1–2` = isolated concept test. `≥ 5` = high cognitive load requiring synthesis across multiple constraints.

## Criterion: `difficulty_distractor_derivation`
**Recommended column name:** `difficulty_distractor_derivation`
**Replaces placeholder:** `difficulty_concept_overlap`
**What it measures:** The extent to which incorrect options are mathematically or logically derivable through common student errors (applying the wrong standard, stopping at an intermediate step, using an inverted formula), rather than being arbitrary plausible strings.
**How to compute (Phase 1):** Provide an LLM with the source slide, the stem, and the 3 distractors. Ask the LLM to attempt to independently derive each distractor using a common error path (e.g., "calculate using LIFO instead of FIFO" or "forget to divide by $n$"). The feature is the integer count (0 to 3) of distractors that map to a specific, documented error path based on the source.
**Evidence from sources:** Real HSG exams heavily use derived distractors. The FIFO inventory question includes the exact LIFO result as distractor B [aca, Q1.1, 3] / [aca, Q1.2, 3]. In Microeconomics, distractors often represent the profit/quantity of a competing firm rather than the target firm, or the cartel outcome instead of the Nash equilibrium [micro, Q2.4, 196].
**Hardness type covered:** both (intermediate math errors in calc; misapplied theoretical rules in concept)
**Range / scale:** integer 0 to 3. `0` = all distractors generic/arbitrary (easy to eliminate). `3` = every distractor corresponds to a plausible "trap" calculation or logical fallacy (very hard).

---

## Tradeoffs and notes

- **Rejected: `difficulty_time_to_solve`.** A standard psychometric proxy, but it cannot be reliably computed from text alone without student telemetry. `difficulty_reasoning_steps` is the deterministic computable proxy.
- **Rejected: `difficulty_math_intensity`.** Considered a metric of numbers/equations per word — but this would skew toward calc questions and violate the both-types coverage requirement. `difficulty_conceptual_density` does the same job for both calc and theory by treating math parameters and theoretical rules as equivalent cognitive-load entities.
- **Expected correlation between criteria.** `difficulty_reasoning_steps` and `difficulty_conceptual_density` will positively correlate (scenarios with 6 variables typically need 4+ steps). They remain distinct: a question can have high steps but low density (repeatedly applying simple interest over 10 periods) or high density but low steps (a `select_all_that_apply` checking 5 distinct conceptual assumptions of the Gauss-Markov theorem [stats, Q30, 260]). Phase 4's ML model will pick up the residual signal.
- **Phase 4 ML calibration.** These are structural synthetic proxies. Once Surf has live student telemetry, the model should map them (plus the 3 LOCKED features) to actual Item Response Theory difficulty parameters (the empirically observed correct-response probability of the item). The 3 features above are the *features*, not the score.

---

## Migration impact (if accepted)

Adopting these recommendations renames 3 columns and 3 kwargs:

| Old (placeholder) | New (recommended) |
|---|---|
| `difficulty_topic REAL` | `difficulty_conceptual_density REAL` |
| `difficulty_concept_overlap REAL` | `difficulty_distractor_derivation REAL` |
| `difficulty_skip_confidence REAL` | `difficulty_reasoning_steps INTEGER` |

Note: `difficulty_reasoning_steps` is `INTEGER` not `REAL` — bounded count, not a continuous proxy.

Files to touch:
- `app/db/schema/schema.sql` — 3 column renames + 1 type change (REAL → INTEGER for reasoning_steps)
- `app/db/queries_questions/__init__.py` — 3 kwarg renames in `insert_question`
- `app/db/queries_questions/queries_questions.md` — sidecar mention
- `.planning/phases/01-ingestion-spine-database/01-CONTEXT.md` — D-2.4 schema block updates
- The DB file `~/.surf/user.sqlite` is wiped + recreated (no real data yet → safe per D-3.1).

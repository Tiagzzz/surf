# Exam MCQ Profile Catalog

> Source: NotebookLM analysis of 4 HSG quantitative exam catalogues (ACA, Macro, Micro, Stats), 2026-05-01.
> Notebook: `2026-05-01 Surf — Exam MCQ Profiles` (id `24ecbcb7-542f-495f-b505-da1b90ce7e63`).
> Persona: Senior Research Analyst with assessment-design lens. Confidence: High.
>
> The 4 source files skew toward calculation questions. Profiles labelled `Source coverage: extrapolated` are essential for theory/concept questions but under-represented in the source MCQs — flagged so the reader knows they're inferred, not directly observed.
>
> **Use:** insert these profile cards into `app/class_/mcq_generate/mcq_generator_system_prompt.md` so the generator can pick a stem shape that matches the slide content.

## Profile: `calculate_parameter`
**When to use:** Quantitative models, formulas, or financial case studies where parameters are given.
**Stem template:** Given [parameters/scenario], determine the [target variable/metric].
**Distractor strategy:** Use results of incomplete calculations (e.g., forgetting to divide by $n$), intermediate steps, or results derived using an alternative (but incorrect for this context) method (e.g., calculating LIFO instead of FIFO).
**Multi-correct?:** single
**Cross-class generality:** appears in 4 of 4 sources (aca / macro / micro / stats)
**Source coverage:** strong
**Real example (with citation):** "What's the amount of the inventory cost per July, 31st using the FIFO-method? (Points: 2)" [aca, Q1.1, 3]
**Synthetic example:**
Given a firm with fixed costs of $10,000, a selling price of $50 per unit, and variable costs of $30 per unit, what is the break-even quantity in units?
A) 200
B) 333
C) 500 (Correct)
D) 1,000

## Profile: `identify_true_statement`
**When to use:** Bulleted lists of concepts, assumptions of a model, or properties of a framework.
**Stem template:** Which of the following statements about [Concept/Model] is correct?
**Distractor strategy:** Invert directional relationships (e.g., "increases" instead of "decreases"), attribute properties of Concept A to Concept B, or introduce absolute modifiers (e.g., "always", "never") to invalidate otherwise true statements.
**Multi-correct?:** single
**Cross-class generality:** appears in 4 of 4 sources (aca / macro / micro / stats)
**Source coverage:** strong
**Real example (with citation):** "Which of the following statements about consolidated financial statements is correct? [...] (a) Consolidated financial statements primarily serve to inform various stakeholders, especially investors." [aca, Q1.5, 55, 56]
**Synthetic example:**
Which of the following statements about the Solow Growth Model is correct?
A) In the steady state, the capital-labor ratio grows at a constant positive rate.
B) Technological progress is an endogenous variable determined by the savings rate.
C) An increase in the savings rate leads to a permanently higher growth rate of output per worker.
D) In the steady state, output per effective worker remains constant over time. (Correct)

## Profile: `identify_false_statement`
**When to use:** Exception handling, lists of limitations, assumptions, or regulatory constraints.
**Stem template:** Which of the following statements is false with respect to [Concept/Model]?
**Distractor strategy:** Present three verbatim or accurately paraphrased facts from the source text, and one distractor that sounds highly plausible but contains a critical error (e.g., a misapplied assumption or wrong timeline).
**Multi-correct?:** single
**Cross-class generality:** appears in 2 of 4 sources (aca / stats)
**Source coverage:** strong
**Real example (with citation):** "Which of the following statements is false with respect to analytical procedures? (a) Analytical procedures are only performed during the planning phase of an audit." [aca, Q5, 35, 36]
**Synthetic example:**
Which of the following statements is FALSE regarding the Ordinary Least Squares (OLS) estimator?
A) The OLS estimator minimizes the sum of squared residuals.
B) Under Gauss-Markov assumptions, the OLS estimator is unbiased.
C) The OLS estimator is always consistent, even if the error term is correlated with the independent variable. (Correct)
D) The OLS estimator is a linear estimator.

## Profile: `cause_effect_directional`
**When to use:** Dynamics models, comparative statics, diagrams showing relationships, or supply/demand curves.
**Stem template:** Assume [exogenous shock / parameter change]. What is the impact on [target variable]?
**Distractor strategy:** Offer directional opposites (e.g., "increases" instead of "decreases"), state that there is no effect, or describe an effect on a completely unrelated variable from the same model.
**Multi-correct?:** single
**Cross-class generality:** appears in 3 of 4 sources (aca / macro / micro)
**Source coverage:** moderate
**Real example (with citation):** "We are in the steady state. What is the impact on the economy of a permanent increase in the population growth rate (gN)? [...] (d) The capital stock (per effective worker) is smaller in the new steady state compared to the old steady state." [macro, Q3.3, 124, 125]
**Synthetic example:**
Assume a central bank conducts an open market purchase of government bonds. Holding all else constant, what is the immediate impact on the money market?
A) The money supply decreases, leading to a higher equilibrium interest rate.
B) The money supply increases, leading to a lower equilibrium interest rate. (Correct)
C) Money demand increases, leaving the interest rate unchanged.
D) The money supply increases, leading to a higher equilibrium interest rate.

## Profile: `conceptual_scenario_application`
**When to use:** Decision trees, rule application flowcharts, "when to use X" tables, or legal/regulatory bounds.
**Stem template:** [Entity] is facing [Situation description]. Under [Framework/Model], which [Approach/Test/Rule] must be applied?
**Distractor strategy:** Provide approaches that are valid for *different* situations within the same framework, or apply the correct rule but output the wrong conclusion.
**Multi-correct?:** single
**Cross-class generality:** appears in 2 of 4 sources (aca / stats)
**Source coverage:** moderate
**Real example (with citation):** "A researcher wants to compare the mean of two independent samples with n = 50 observations each. The sample means x̄₁ and x̄₂ as well as the sample standard deviations s₁ and s₂ are known. The assumption of a normally distributed population and the assumption of equal variances apply. Which test or test statistic must the researcher calculate to test the hypothesis H0: μ₁ − μ₂ = 0?" [stats, Q31, 291]
**Synthetic example:**
A company holds a 40% voting interest in a joint venture and exercises significant influence, but does not have exclusive control. Under IFRS, which consolidation method should be applied?
A) Full consolidation
B) Proportionate consolidation
C) Equity method (Correct)
D) Cost method

## Profile: `definition_matching`
**When to use:** Glossary terms, key concept introductions, or foundational vocabulary slides.
**Stem template:** The term "[Concept]" in [Context] means that...
**Distractor strategy:** Use definitions of related but distinct terms from the same chapter, or construct a plausible-sounding but completely fabricated definition.
**Multi-correct?:** single
**Cross-class generality:** appears in 4 of 4 sources (aca / macro / micro / stats)
**Source coverage:** Extrapolated profile (under-represented in sources, but theoretically essential for theory-heavy generation).
**Real example (with citation):** "The term 'submarine accounting' means that [...] (c) in equity accounting, the allocation of losses is not limited to the pure investment book value at the reporting company, but also includes other long-term parts of the financial engagement." [aca, Q1.10, 59, 60]
**Synthetic example:**
The term "deadweight loss" in microeconomics is defined as:
A) The loss of accounting profit when a firm operates below its break-even point.
B) The reduction in total economic surplus resulting from a market intervention or inefficiency. (Correct)
C) The portion of consumer surplus that is transferred directly to producers under price discrimination.
D) The fixed costs that cannot be recovered when a firm exits a market.

## Profile: `framework_comparison`
**When to use:** Tables comparing two models, theories, accounting standards, or statistical tests side-by-side.
**Stem template:** Which statement accurately describes the difference between [Model/Standard A] and [Model/Standard B]?
**Distractor strategy:** Attribute a feature of Model A to Model B, state a similarity as a difference, or mix and match properties (e.g., "A is rule-based and B is rule-based").
**Multi-correct?:** single
**Cross-class generality:** appears in 3 of 4 sources (aca / micro / stats)
**Source coverage:** Extrapolated profile (under-represented in sources, but essential to transition from calc-heavy to concept-heavy).
**Real example (with citation):** "Which of the statements... accurately describes the relationship between the old Nash equilibrium with two firms (Problem 2.2. and 2.3.) and the new Nash equilibrium with three firms (Problem 2.4.)? [...] (b) Both the demand in the old Nash equilibrium and the demand in the new Nash equilibrium react inelastically to price changes." [micro, Q2.5, 196, 197]
**Synthetic example:**
Which of the following best describes the difference between the Bertrand and Cournot models of oligopoly?
A) In the Bertrand model, firms compete on quantity, whereas in the Cournot model, they compete on price.
B) In the Bertrand model, products must be highly differentiated, whereas in the Cournot model, they must be homogeneous.
C) In the Bertrand model, firms compete on price, whereas in the Cournot model, they compete on quantity. (Correct)
D) The Bertrand model always results in a monopoly outcome, whereas the Cournot model results in perfect competition.

## Profile: `select_all_that_apply`
**When to use:** Lists of valid conditions, multi-step prerequisites, properties of a model, or multiple concurrent effects.
**Stem template:** Which of the following conditions must hold for [Model/Theorem] to be valid? (Select all that apply)
**Distractor strategy:** Include conditions from related theorems, subtly alter a condition (e.g., $n < 30$ instead of $n > 30$), or include outcomes instead of prerequisites.
**Multi-correct?:** multi-allowed
**Cross-class generality:** appears in 1 of 4 sources explicitly (stats)
**Source coverage:** Extrapolated profile (the source catalogues explicitly note: "Each exam also has a Part II 'Multiple-Choice Questions'... where multiple options can be correct simultaneously — those were skipped" [stats, 236]). Essential for an exam-prep app.
**Real example (with citation):** *No verbatim example available in extracted text — the multi-correct sections were excluded from extraction.*
**Synthetic example:**
Which of the following assumptions are required for the Gauss-Markov theorem to hold? (Select all that apply)
A) The parameters of the model must be linear. (Correct)
B) The error term must follow a normal distribution.
C) The expected value of the error term, conditional on the independent variables, is zero. (Correct)
D) There must be perfect multicollinearity among the independent variables.

---

## Cross-class observations

- **Cascading stem structures.** All four subjects rely on "scenario block" or "cascading" questions. A single complex scenario (a balance sheet [aca, 67], an IS-LM setup [macro, 81], a Bertrand duopoly setup [micro, 178], or a dataset description [stats, 263]) is presented once, followed by 3–5 interconnected calculation and theory questions tied to that initial prompt.
- **Math-to-concept bridging.** In Microeconomics and Macroeconomics, questions frequently force the student to calculate an equilibrium value and then immediately answer a theoretical question about *why* the value shifted (e.g., comparing welfare loss, calculating a new steady state, evaluating directional change [micro, Q2.5, 196] / [macro, Q3.3, 124]).
- **Universal distractor logic — "partial calculation".** Across ACA, Macro, and Micro, the most prevalent distractor strategy for `calculate_parameter` is offering the result of an incomplete-but-logical step (e.g., the unamortised value when amortisation is required, or skipping a multiplication by a constant).
- **True multi-correct is under-represented.** The extracted sources rigorously restrict themselves to single-choice formatting ("Only one answer is correct per question" [macro, 80]). True multi-select was actively segregated into separate exam sections and excluded from the main banks [stats, 236]. The Surf MCQ generator will need to inject multi-correct logic explicitly via the `select_all_that_apply` profile rather than learning it from these sources.

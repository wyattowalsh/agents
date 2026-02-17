# Decision Frameworks

Catalog of 12 frameworks for structured analysis and wargaming.
Read during framework selection or when building analysis prompts.

## Cynefin

Classify the problem domain (Clear/Complicated/Complex/Chaotic).
**Use when:** The right approach is unclear, or stakeholders disagree on complexity.

1. State the decision or problem in one sentence.
2. Classify: **Clear** (obvious cause-effect) / **Complicated** (requires expertise) / **Complex** (cause-effect visible only in retrospect) / **Chaotic** (no perceivable cause-effect).
3. Apply action model: Clear → sense-categorize-respond. Complicated → sense-analyze-respond. Complex → probe-sense-respond. Chaotic → act-sense-respond.
4. Identify boundary risks — could the problem shift domains?
5. **Produce:** domain classification, action model, boundary risks.

## Pre-mortem

Imagine failure, work backward to identify risks.
**Use when:** A plan exists and needs stress-testing before commitment.

1. State the plan and define "failure" concretely.
2. Assume six months later — the plan has failed spectacularly.
3. Independently list reasons the failure occurred. Deduplicate.
4. Rank by likelihood and severity. For top risks, identify mitigations and early-warning signals.
5. **Produce:** ranked risk table (risk, likelihood, severity, mitigation, signal).

## Scenario Planning (2x2)

Map futures along two critical uncertainties.
**Use when:** Long-horizon decisions where multiple external factors could diverge.

1. Identify the decision and time horizon.
2. List key uncertainties; select the two most impactful and uncertain as axes.
3. Build a 2x2 matrix producing four named scenarios.
4. Per scenario: conditions, implications, optimal action.
5. Identify robust moves that perform well across multiple scenarios.
6. **Produce:** 2x2 matrix, named scenarios, per-scenario actions, robust-move list.

## Payoff Matrix / Game Theory

Enumerate actors, options, payoffs; find Nash equilibria.
**Use when:** Multiple actors with competing interests; outcomes depend on others' choices.

1. Identify all actors and their available options.
2. Build payoff matrix: rows = your options, columns = others' options, cells = payoff tuples.
3. Identify dominant/dominated strategies per actor.
4. Find Nash equilibria (no actor benefits from unilateral change). Check for Pareto improvements.
5. **Produce:** payoff matrix, dominant strategies, Nash equilibria, recommended strategy.

## OODA Loop

Iterative observe-orient-decide-act cycles.
**Use when:** Situation evolving rapidly; waiting for full information is costly.

1. **Observe:** Gather raw data on current state and recent changes.
2. **Orient:** Interpret through context and mental models. Identify expectation mismatches.
3. **Decide:** Select course of action. Bias toward reversible actions.
4. **Act:** Execute. Establish feedback channels. Re-enter loop — each cycle faster.
5. **Produce:** per-cycle log (observations, orientation, decision rationale, action, feedback).

## Decision Trees

Sequential choices under uncertainty with expected values.
**Use when:** Chained choices and chance events with estimable probabilities.

1. Identify the initial decision and its options.
2. For each option, map chance events with probabilities and terminal payoffs.
3. Assign values to terminal nodes.
4. Fold back: compute expected values at chance nodes, select max-EV at decision nodes.
5. **Produce:** tree structure, expected values per path, recommended path, sensitivity analysis.

### Option Value Extension

When decision paths include the ability to wait, learn, or stage commitments:
- Identify options with embedded real options (the right but not obligation to take future action)
- Assign optionality premium: paths that preserve future flexibility are worth more than their static expected value
- Flag irreversible commitments that eliminate future options — these carry an implicit cost equal to the option value destroyed
- **Produce:** in addition to standard output, flag which paths preserve vs destroy optionality, and estimate the premium for waiting/staging.

## Stakeholder Power/Interest Mapping

Map actors by influence and alignment.
**Use when:** Success depends on multiple stakeholders with varying influence and interests.

1. List all stakeholders who affect or are affected by the decision.
2. Rate each on **Power** (high/low) and **Interest** (high/low).
3. Quadrant: High/High → manage closely. High/Low → keep satisfied. Low/High → keep informed. Low/Low → monitor.
4. For High-Power stakeholders, identify preferred outcomes and objections.
5. **Produce:** power/interest grid, engagement strategy per quadrant, coalition opportunities.

### Coalition Analysis Extension

When 3+ stakeholders could form alliances:
- Identify natural coalitions (shared interests or complementary power)
- Assess coalition stability: what would cause each coalition to fracture?
- Map blocking coalitions: which stakeholder combinations can veto the preferred option?
- **Produce:** in addition to standard output, coalition map with stability ratings and blocking thresholds.

## Second-Order Effects Chain

Trace cascading consequences of an action.
**Use when:** First-order outcome is clear but downstream effects are uncertain or high-stakes.

1. State the action and intended first-order effect.
2. For each effect, ask "and then what?" to generate second-order effects. Repeat for third-order.
3. Flag feedback loops (amplifying or dampening) and irreversible effects.
4. **Produce:** effects chain (action → 1st → 2nd → 3rd), feedback loops, irreversibility flags.

## Regret Minimization

Choose to minimize worst-case regret.
**Use when:** Downside risk matters more than expected value; irreversible decisions.

1. List all options and all plausible scenarios.
2. Estimate payoff of each option under each scenario.
3. Per scenario, find best possible payoff (oracle choice). Compute regret = best minus actual.
4. Per option, find maximum regret across scenarios. Select smallest maximum (minimax regret).
5. **Produce:** regret matrix, minimax regret option, comparison with max-EV option if different.

## Devil's Advocacy

Build strongest case against preferred option.
**Use when:** Strong frontrunner exists; need to test for confirmation bias.

1. State the preferred option and its reasoning.
2. Argue against it as persuasively as possible.
3. Identify the weakest assumptions in the original reasoning.
4. Construct the best alternative case using the same evidence.
5. Rate counter-case strength: fatal flaw / significant concern / cosmetic only.
6. **Produce:** counter-argument, assumption vulnerabilities, strength rating, revised recommendation if warranted.

## Analysis of Competing Hypotheses (ACH)

Systematic evidence-vs-hypotheses matrix from CIA tradecraft. Fights confirmation bias.
**Use when:** Multiple explanations exist and evidence is ambiguous or contested.

1. Generate all plausible hypotheses (minimum 3, include at least one you consider unlikely).
2. Gather all available evidence relevant to any hypothesis.
3. Build matrix: rows = evidence, columns = hypotheses.
4. Score each cell **-5** (strongly contradicts) to **+5** (strongly supports).
5. Sum columns. Focus on disconfirmation: fewest strong negatives = most defensible.
6. Identify evidence that would change the ranking; flag collection gaps.
7. **Produce:** scored matrix, ranked hypotheses, discriminating evidence, gaps.

## Key Assumptions Check

Surface unstated assumptions before analysis, challenge each: "what if this assumption is wrong?"
**Use when:** Before any major analysis — especially when confidence is high but evidence is thin.

1. State the conclusion or plan under review.
2. List every underlying assumption (aim for 8+).
3. Classify each: **verified** / **probable** / **uncertain** / **key** (if wrong, conclusion collapses).
4. For each key assumption: "What if wrong? What changes?"
5. Flag assumptions that are both key and uncertain — highest-priority risks.
6. **Produce:** assumption table (assumption, classification, if-wrong impact), priority verification actions.

## Multi-Criteria Decision Analysis (MCDA)

Systematic evaluation of options against weighted criteria.
**Use when:** Multiple options exist with trade-offs across different value dimensions; stakeholders disagree on priorities.

1. Identify all options under consideration.
2. Define evaluation criteria (from user's criteria ranking if available, otherwise elicit).
3. Weight criteria by relative importance (sum to 100%).
4. Score each option against each criterion (1-5 scale).
5. Compute weighted scores: Σ(weight × score) per option.
6. Sensitivity test: which criterion weight change would flip the top-ranked option?
7. **Produce:** weighted scoring matrix, ranked options, sensitivity to weight changes, recommended option with confidence level.

## Selection Heuristic

Match scenario characteristics to recommended frameworks.

| Scenario | Primary | Supporting |
|----------|---------|------------|
| Unknown problem type, unclear complexity | Cynefin | Key Assumptions Check |
| Plan exists, need to stress-test | Pre-mortem | Devil's Advocacy |
| Long time horizon, external uncertainty | Scenario Planning (2x2) | Second-Order Effects Chain |
| Multiple actors, competing interests | Payoff Matrix / Game Theory | Stakeholder Power/Interest Mapping |
| Fast-moving situation, incomplete info | OODA Loop | Regret Minimization |
| Sequential choices with probabilities | Decision Trees | Regret Minimization |
| Many stakeholders, political dynamics | Stakeholder Power/Interest Mapping | Devil's Advocacy |
| Cascading or systemic consequences | Second-Order Effects Chain | Pre-mortem |
| Irreversible decision, high downside risk | Regret Minimization | Pre-mortem |
| Strong consensus, possible groupthink | Devil's Advocacy | Key Assumptions Check |
| Ambiguous evidence, multiple explanations | Analysis of Competing Hypotheses | Key Assumptions Check |
| High confidence but thin evidence | Key Assumptions Check | Analysis of Competing Hypotheses |
| Probability estimation needed | Payoff Matrix / Decision Trees | Key Assumptions Check |
| Multi-criteria trade-offs, stakeholder disagreement on priorities | MCDA | Stakeholder Power/Interest Mapping |

**Superforecasting integration:** When any framework requires probability estimates (Payoff Matrix, Decision Trees, ACH), apply Fermi decomposition: break complex probabilities into estimable sub-questions. Anchor every estimate to an outside-view base rate before adjusting for scenario-specific factors. Use granular percentages (e.g., "35%") not vague labels ("medium likelihood").

**Mode mapping:** Quick Analysis uses 2-3 frameworks. Structured Analysis chains 3-5. Interactive Wargame runs full multi-framework analysis with adversarial red-teaming.

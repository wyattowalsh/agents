# Decision Frameworks — Index

Selection heuristics and enforcement rules. For step-by-step procedures, see `references/frameworks-procedures.md`.

## Framework Catalog

| Framework | Use When | Produces |
|-----------|----------|----------|
| Cynefin | Right approach unclear, disagreement on complexity | Domain classification, action model, boundary risks |
| Pre-mortem | Plan exists, needs stress-testing | Ranked risk table |
| Scenario Planning (2x2) | Long horizon, multiple external uncertainties | 2x2 matrix, named scenarios, robust moves |
| Payoff Matrix / Game Theory | Multiple actors, competing interests | Payoff matrix, Nash equilibria, strategy |
| OODA Loop | Fast-moving, incomplete info | Per-cycle log |
| Decision Trees | Chained choices, estimable probabilities | Tree, expected values, recommended path |
| Stakeholder Power/Interest | Success depends on multiple stakeholders | Power/interest grid, engagement strategy |
| Second-Order Effects Chain | First-order clear, downstream uncertain | Effects chain, feedback loops, irreversibility flags |
| Regret Minimization | Downside risk > expected value, irreversible | Regret matrix, minimax option |
| Devil's Advocacy | Strong frontrunner, confirmation bias risk | Counter-argument, strength rating |
| ACH | Multiple explanations, ambiguous evidence | Scored matrix, ranked hypotheses, gaps |
| Key Assumptions Check | Before major analysis, high confidence + thin evidence | Assumption table, priority verifications |
| MCDA | Multiple options, weighted criteria trade-offs | Weighted scoring matrix, sensitivity |

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

## Enforcement Rules

### ACH Enforcement Rules

These rules address the primary failure modes identified in ACH research: incomplete matrices, skipped disconfirmation, and false confidence from dominant hypotheses.

1. **No empty cells.** Every hypothesis must be scored against every piece of evidence. An empty cell means the analysis is incomplete — force a rating even if "N/A (no diagnostic value)."
2. **Mandatory collection gaps.** After completing the matrix, list 2-3 pieces of evidence that *would* discriminate between the top hypotheses but are not yet available. Label these as collection priorities.
3. **Dominance check.** If a single hypothesis leads by >50% weighted consistency over the next-best, flag this as potential confirmation bias. Require the analyst to articulate: (a) what evidence would falsify the leading hypothesis, and (b) whether the evidence base is skewed toward confirming it.

### Probability Anchoring

**Default base rate anchoring:** Before assigning any probability estimate — whether in decision trees, scenario planning, payoff matrices, or any other context — identify the reference class and state the base rate explicitly. Format: "Reference class: [description]. Base rate: [X%]. Adjustment for scenario-specific factors: [reasoning] → Final estimate: [Y%]."

### Superforecasting Integration

**Superforecasting integration:** When any framework requires probability estimates (Payoff Matrix, Decision Trees, ACH), apply Fermi decomposition: break complex probabilities into estimable sub-questions. Anchor every estimate to an outside-view base rate before adjusting for scenario-specific factors. Use granular percentages (e.g., "35%") not vague labels ("medium likelihood").

### Mode Mapping

**Mode mapping:** Quick Analysis uses 2-3 frameworks. Structured Analysis chains 3-5. Interactive Wargame runs full multi-framework analysis with adversarial red-teaming.

# Cognitive Biases

Bias catalog for wargame adjudication. Human biases are checked during participant
analysis. LLM-specific biases are mitigated continuously during adjudication and
outcome generation. Read during adjudication or when calibrating actor decision-making.

## Contents

- [Human Biases](#human-biases)
- [LLM-Specific Biases](#llm-specific-biases)
- [Bias Sweep Protocol](#bias-sweep-protocol)

---

## Human Biases

Detect these in user-provided strategies, actor reasoning, and scenario framing.
When a bias is detected, inject the corresponding challenge prompt into the actor's
next deliberation cycle.

| # | Bias Name | Detection Signal | Challenge Prompt |
|---|-----------|-----------------|------------------|
| 1 | **Anchoring** | First option presented dominates discussion; alternatives dismissed without comparative evaluation. | "Remove the first option entirely. What would you choose if it never existed?" |
| 2 | **Confirmation** | Evidence cited only supports the preferred outcome; contradicting data ignored, minimized, or explained away. | "List three pieces of evidence that contradict your current position." |
| 3 | **Sunk Cost** | Justification references past investment ("we've already spent...") rather than future expected value. | "If you were starting fresh today with zero prior investment, would you still choose this path?" |
| 4 | **Availability** | Recent or vivid examples (last crisis, famous failure) drive risk assessment instead of statistical base rates. | "Set aside the example you just cited. What does the statistical base rate actually say?" |
| 5 | **Planning Fallacy** | Timelines assume best-case execution; buffers absent; risks acknowledged verbally but not quantified in the plan. | "What happened the last three times a similar plan was attempted? Use those actuals, not your estimate." |
| 6 | **Groupthink** | All actors converge quickly; no dissent voiced; objections framed as disloyal or naive. | "Appoint a designated dissenter. What is the strongest case against the consensus?" |
| 7 | **Status Quo** | "No change needed" is the default position; burden of proof placed entirely on the change proposal. | "Assume the current state will degrade by 20% over the next cycle. Now re-evaluate doing nothing." |
| 8 | **Overconfidence** | Probability estimates cluster near 0% or 100%; uncertainty ranges are suspiciously narrow; hedging language absent. | "Widen your confidence interval by 50%. What changes in your decision at the new bounds?" |
| 9 | **Loss Aversion** | Symmetric gains and losses produce asymmetric reactions; small downside risk blocks proportionally larger upside moves. | "Reframe: instead of what you might lose, what is the cost of not capturing the potential gain?" |
| 10 | **Framing Effect** | Conclusions shift when the same data is presented as "90% success rate" vs "10% failure rate." | "Restate this outcome using the opposite frame. Does your assessment change?" |

### Prospect Theory Integration

Loss aversion (bias #9) connects directly to actor behavioral parameters. Each actor's risk posture from `references/wargame-engine.md` determines their susceptibility:
- **Risk-averse actors:** Strongly loss-averse — will reject favorable gambles to avoid losses. Flag when such actors avoid high-EV options due to loss framing.
- **Risk-seeking actors:** May escalate or double down when behind. Flag when such actors take disproportionate risks after setbacks.
- **Reference point shifts:** When an actor's status quo changes (e.g., after a major loss), their entire gain/loss calculus resets. Previously acceptable risks may become unacceptable, or vice versa.

### Choice Architecture

Option presentation itself is a bias vector. Mitigations integrated into the decision menu protocol (see `references/wargame-engine.md` step 4b):
- **Order effects:** Randomize option order between turns to prevent primacy/recency bias
- **Framing effects:** Present risk in both positive and negative frames simultaneously
- **Default bias:** "Do nothing" must be presented as an active choice, not a default
- **Precision effects:** Use percentage ranges instead of vague labels — "35-50% risk" instead of "medium risk"

### Enhanced Debiasing

Two techniques for more effective bias correction:

**Gamified framing:** Instead of confrontational challenge prompts, frame bias detection as skill checks:
> "Bias detected: Anchoring. Your analysis weighted the first option 3× more heavily. Adjustment: evaluating options in reverse order."

Interactive feedback in this style reduces biases 30%+ with lasting effects (vs. simple warnings which fade quickly).

**Consider-the-opposite** (single most effective verbal debiasing technique): After user decisions that conflict with a specific actor's stated objective, briefly show that actor's opposing perspective:
> "{Actor} would view your decision as {interpretation}."

This is lighter than a full red team but provides consistent counter-framing at every decision point.

---

## LLM-Specific Biases

Always-on mitigations applied during adjudication and multi-actor dialogue generation.
These are structural failure modes of the simulation engine itself, not participant errors.

### Escalation Bias

- **Description:** LLMs prefer dramatic, aggressive outcomes over measured responses.
  Conflicts trend toward worst-case spirals; de-escalation options are generated but
  dismissed as "unrealistic" or "naive."
- **Detection signal:** Outcomes consistently escalate in severity across turns.
  De-escalation paths appear but are rejected without rigorous justification.
- **Mitigation protocol:**
  - Flag any escalation that lacks explicit, scenario-grounded justification.
  - Require a plausible de-escalation alternative for every aggressive action proposed.
  - Suppress dramatic language ("catastrophic," "devastating") in adjudication summaries
    unless supported by quantified impact assessment.

### Sycophancy

- **Description:** LLMs agree with user framing and reinforce the user's preferred
  outcome rather than stress-testing it. The user-aligned actor wins too cleanly.
- **Detection signal:** Adjudication consistently favors the user-aligned actor.
  Adversary arguments are presented weakly or concede too readily.
- **Mitigation protocol:**
  - Apply adversarial prompting to every user-framed position.
  - Require at least one actor to explicitly disagree with the user's thesis per turn.
  - Score adversary arguments independently before evaluating them against user positions.
  - The `red team` command (see `references/wargame-engine.md`) serves as an on-demand anti-sycophancy mechanism — user-triggered adversarial analysis of the preferred option.

### Farcical Harmony

- **Description:** Multi-actor dialogues converge to agreement too quickly. Actors
  nominally represent opposing interests but fail to sustain genuine disagreement.
- **Detection signal:** All actors reach consensus within one exchange. "Disagreements"
  are cosmetic and resolve immediately without concessions or tradeoffs.
- **Mitigation protocol:**
  - Require structured pro/con arguments from each actor before any consensus is permitted.
  - Inject mandatory dissent: at least one actor must maintain opposition through the
    first full round of deliberation.
  - Any consensus must document what each side conceded and why.

### Blue Bias

- **Description:** LLMs systematically underestimate adversary capabilities and
  overestimate friendly-force competence. Red team plans are simplistic; blue team
  plans succeed without realistic friction.
- **Detection signal:** Adversary plans are one-dimensional. Adversary resources are
  underutilized. Friendly-force plans encounter no logistics failures, communication
  breakdowns, or execution friction.
- **Mitigation protocol:**
  - Calibrate adversary capabilities explicitly at scenario start using real-world
    benchmarks and historical precedent.
  - Require red-team validation: a dedicated adversary advocate must review every
    adjudication for capability underestimation.
  - Inject friction into friendly-force execution: at least one plan element must
    encounter a realistic complication per turn.

---

## Bias Sweep Protocol

Run a bias sweep at two checkpoints during each wargame turn.

### Checkpoint 1: Pre-adjudication

After collecting actor decisions, before resolving outcomes:

1. Scan actor reasoning against the Human Biases table above.
2. If a bias is detected, inject the corresponding challenge prompt into the actor's
   next deliberation before proceeding.
3. **Rate limit:** Flag at most **one human bias per two turns** per actor.
   Over-flagging degrades signal quality and causes actors to over-correct.

### Checkpoint 2: Post-adjudication

After generating outcomes, before presenting results to the user:

1. Run all four LLM-specific mitigations. These are **always-on** and not rate-limited.
2. Verify each mitigation criterion is satisfied before finalizing the turn output.

### Quick-reference checklist

- [ ] Escalation justified with scenario-grounded reasoning? (not just dramatic)
- [ ] At least one actor dissents from the majority position? (not sycophantic consensus)
- [ ] Pro/con structure present before any consensus is declared? (not farcical harmony)
- [ ] Adversary capabilities calibrated to real-world benchmarks? (not blue bias)
- [ ] Human bias callouts within rate limit? (max 1 per 2 turns per actor)
- [ ] LLM mitigations applied to every adjudication? (always-on, no exceptions)

### Single-Output Mode Sweep (Quick/Structured Analysis)

After generating the analysis, before presenting:
1. Scan for human biases in the table above (anchoring, confirmation, framing most common in single-output modes)
2. Verify the 4 LLM-specific mitigations hold (escalation, sycophancy, farcical harmony, blue bias)
3. Flag at most 1 bias with the gamified framing from Enhanced Debiasing

---

## Analytical Constitution

Self-revision checklist. If ANY principle is violated, revise the output before presenting.

1. **Adversary parity** — Adversary actors receive the same quality of strategic reasoning as user-aligned actors?
2. **Grounded outcomes** — Outcomes grounded in scenario conditions, not dramatic preference or narrative convenience?
3. **Calibrated confidence** — Confidence level matched to available information, not inflated for rhetorical effect?

**Application points** (apply at exactly these two moments, not per-output):
1. After generating the final recommendation/ranking in Quick/Structured Analysis
2. After generating the AAR in Interactive Wargame

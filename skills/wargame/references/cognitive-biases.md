# Cognitive Biases

Bias catalog for wargame adjudication. Human biases checked during participant analysis. LLM biases mitigated continuously during adjudication. Read during adjudication or when calibrating actor decision-making.

## Human Biases

Detect in user strategies, actor reasoning, and scenario framing. Inject the challenge prompt into the actor's next deliberation cycle when detected.

| # | Bias | Signal | Challenge |
|---|------|--------|-----------|
| 1 | **Anchoring** | First option dominates; alternatives dismissed | "Remove first option. What would you choose?" |
| 2 | **Confirmation** | Only supporting evidence cited; contradictions ignored | "List 3 pieces of evidence against your position." |
| 3 | **Sunk Cost** | Past investment justifies continuation | "Starting fresh today, would you still choose this?" |
| 4 | **Availability** | Recent/vivid examples override base rates | "What does the base rate say, ignoring that example?" |
| 5 | **Planning Fallacy** | Best-case timelines; no buffers | "What happened the last 3 times? Use those actuals." |
| 6 | **Groupthink** | Quick convergence; no dissent | "Appoint a dissenter. Strongest case against consensus?" |
| 7 | **Status Quo** | "No change" as default; burden on change proposal | "Assume current state degrades 20%. Re-evaluate inaction." |
| 8 | **Overconfidence** | Estimates cluster at extremes; narrow ranges | "Widen your interval 50%. What changes at new bounds?" |
| 9 | **Loss Aversion** | Small downside blocks larger upside | "What's the cost of NOT capturing the potential gain?" |
| 10 | **Framing** | Conclusions shift with frame (90% success vs 10% failure) | "Restate with opposite frame. Does assessment change?" |

### Prospect Theory Integration

Loss aversion (bias #9) connects directly to actor behavioral parameters. Each actor's risk posture from `references/wargame-engine.md` determines their susceptibility:
- **Risk-averse actors:** Strongly loss-averse — will reject favorable gambles to avoid losses. Flag when such actors avoid high-EV options due to loss framing.
- **Risk-seeking actors:** May escalate or double down when behind. Flag when such actors take disproportionate risks after setbacks.
- **Reference point shifts:** When an actor's status quo changes (e.g., after a major loss), their entire gain/loss calculus resets. Previously acceptable risks may become unacceptable, or vice versa.

### Choice Architecture

Option presentation mitigations — see `references/wargame-engine.md` step 4b.

### Enhanced Debiasing

Two techniques for more effective bias correction:

**Gamified framing:** Instead of confrontational challenge prompts, frame bias detection as skill checks:
> "Bias detected: Anchoring. Your analysis weighted the first option 3× more heavily. Adjustment: evaluating options in reverse order."

Interactive feedback in this style reduces biases 30%+ with lasting effects (vs. simple warnings which fade quickly).

**Consider-the-opposite** (single most effective verbal debiasing technique): show an opposing actor's perspective after decisions that conflict with their objective. Implementation: see `references/wargame-engine.md` step 11.

## LLM-Specific Biases

Always-on mitigations. These are structural failure modes of the simulation engine itself.

- **Escalation bias** — LLMs prefer dramatic outcomes. _Mitigation:_ Flag unjustified escalation. Require plausible de-escalation for every aggressive action. Suppress dramatic language without quantified impact.
- **Sycophancy** — LLMs agree with user framing. _Mitigation:_ Adversarial prompting on user positions. At least one actor must disagree per turn. Score adversary arguments independently. `red team` command as on-demand anti-sycophancy.
- **Farcical harmony** — Multi-actor dialogues converge too fast. _Mitigation:_ Structured pro/con before consensus. Mandatory dissent through first deliberation round. Document concessions.
- **Blue bias** — Underestimate adversary, overestimate friendly force. _Mitigation:_ Calibrate adversary capabilities to real-world benchmarks. Red-team validation on every adjudication. Inject friction into friendly execution.

## Bias Sweep Protocol

### Checkpoint 1: Pre-adjudication
After collecting actor decisions, before resolving outcomes:
1. Scan actor reasoning against Human Biases table
2. If detected, inject challenge prompt. **Rate limit:** max 1 human bias per 2 turns per actor.

### Checkpoint 2: Post-adjudication
After generating outcomes, before presenting:
1. Run all four LLM mitigations (always-on, not rate-limited)
2. Verify each criterion satisfied before finalizing

**Checklist:**
- [ ] Escalation justified with scenario-grounded reasoning?
- [ ] At least one actor dissents?
- [ ] Pro/con before any consensus?
- [ ] Adversary capabilities calibrated?
- [ ] Human bias callouts within rate limit?

### Single-Output Mode Sweep
For Quick/Structured Analysis: scan for anchoring, confirmation, framing. Verify 4 LLM mitigations hold. Flag at most 1 bias with gamified framing.

## Analytical Constitution

Self-revision checklist. If ANY principle is violated, revise the output before presenting.

1. **Adversary parity** — Adversary actors receive the same quality of strategic reasoning as user-aligned actors?
2. **Grounded outcomes** — Outcomes grounded in scenario conditions, not dramatic preference or narrative convenience?
3. **Calibrated confidence** — Confidence level matched to available information, not inflated for rhetorical effect?

**Application points** (apply at exactly these two moments, not per-output):
1. After generating the final recommendation/ranking in Quick/Structured Analysis
2. After generating the AAR in Interactive Wargame

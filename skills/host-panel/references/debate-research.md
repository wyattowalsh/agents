# Debate Research

Use this file as the authority layer for panel mechanics. The panel is a
deliberation protocol inspired by multi-agent debate research; it is not proof
that the final synthesis is true and not evidence of real human group behavior.

## Research-to-Rule Matrix

| Finding | Design Rule | Failure Prevented | Source |
|---|---|---|---|
| Multi-agent debate can improve factuality and reasoning when agents critique across rounds. | Require independent first positions, then bounded critique rounds. | One model's first answer dominating the panel. | Du et al., 2023, "Improving Factuality and Reasoning in Language Models through Multiagent Debate", https://arxiv.org/abs/2305.14325 |
| Debate can encourage divergent thinking compared with self-reflection, but needs controlled adversarial tension. | Use challenge rounds and adaptive stopping; do not run endless debate. | Repetitive self-reflection and theatrical disagreement. | Liang et al., 2024, "Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate", https://aclanthology.org/2024.emnlp-main.992/ |
| Self-correction and debate do not guarantee better answers under equal budgets. | Never claim that a panel improves truth by default; label it as exploratory synthesis. | Overclaiming panel reliability. | Huang et al., 2024, "Large Language Models Cannot Self-Correct Reasoning Yet", https://openreview.net/pdf?id=IkmD3fKBPQ |
| Majority voting and last-round consensus can propagate errors. | Synthesize by trajectory, cruxes, and evidence, not by majority vote. | False consensus and conformity bias. | Free-MAD, 2025/2026, "Consensus-Free Multi-Agent Debate", https://arxiv.org/abs/2509.11035 |
| Adaptive stability can stop judge debates before wasteful rounds. | Stop when cruxes stabilize, evidence runs out, or positions repeat. | Token-heavy circular panels. | Hu et al., 2025, "Multi-Agent Debate for LLM Judges with Adaptive Stability Detection", https://openreview.net/forum?id=Vusd1Hw2D9 |
| Persuasive adversarial agents can lower accuracy and increase incorrect consensus. | Treat rhetorical confidence as non-evidence and test persuasive claims. | Confident falsehood steering the panel. | Kraidia et al., 2026, "When collaboration fails", https://www.nature.com/articles/s41598-026-42705-7 |
| Strong long-form synthesis starts with perspective discovery and source-grounded questioning. | Map sources, traditions, and questions before persona creation. | Persona-first hallucination and shallow synthesis. | Shao et al., 2024, STORM, https://aclanthology.org/2024.naacl-long.347/ |
| Multi-agent evaluators depend on defined roles and structured discussion. | Give each panelist a role, evidence standard, critique duty, and crux. | Vague "expert" labels with no functional difference. | Chan et al., 2023, ChatEval, https://arxiv.org/abs/2308.07201 |
| Role-playing quality requires explicit role profiles and evaluation dimensions. | Use methodology cards instead of theatrical biographies. | Vivid but unreliable personas. | RoleLLM, https://arxiv.org/abs/2310.00746; CharacterEval, https://arxiv.org/abs/2401.01275; RPLA Survey, https://arxiv.org/abs/2404.18231 |
| User framing can induce agreement-seeking behavior. | Challenge loaded premises and preferred answers before staging a panel. | Sycophancy toward the user's view. | Anthropic, "Towards Understanding Sycophancy in Language Models", https://www.anthropic.com/research/towards-understanding-sycophancy-in-language-models |
| Debate is a scalable oversight idea, not a free-standing truth oracle. | Include a model-limit caveat and explain what evidence would change the answer. | Treating debate as authority. | Irving et al., 2018, "AI Safety via Debate", https://arxiv.org/abs/1805.00899 |

## Mechanics Derived From Research

Apply these mechanics in every substantive panel:

1. **Independent first positions.** Each panelist states a claim, evidence standard, uncertainty, and self-objection before reading other panelists.
2. **Bounded critique.** Run only enough cross-talk to expose cruxes. Stop when positions repeat, evidence is exhausted, or the synthesis target is clear.
3. **Anti-conformity.** Do not summarize agreement as correctness. When 2+ panelists converge, ask what would make that convergence wrong.
4. **Trajectory synthesis.** Track how claims changed across phases; do not use last-round majority vote.
5. **Evidence weighting.** Source-backed claims outrank fluent claims, even when the fluent claim sounds more expert.
6. **Premise challenge.** Treat the user's framing as a hypothesis, not a command to validate.
7. **Role reliability.** A panelist is defined by methodology, evidence standard, and crux, not by a colorful biography.

## Limits to State Explicitly

- The panel simulates intellectual positions, not real people.
- The panel is not a poll, forecast, or empirical social simulation.
- The panel can expose cruxes and uncertainty; it cannot create missing evidence.
- More panelists or rounds do not automatically improve reliability.
- A persuasive panelist can be wrong; rhetoric is never evidence.

## Application Checklist

Before running the discussion, confirm:

1. The topic gate did not classify the prompt as false balance.
2. The source ledger is strong enough for any named works.
3. Panelists have distinct methods, not merely distinct labels.
4. Initial positions are written before cross-talk.
5. The moderator has a planned convergence challenge.
6. The final synthesis will track trajectory, not majority vote.

## Do Not Infer

Do not infer these from the research:

- That multi-agent debate always improves truth.
- That more agents are always better.
- That a confident agent is more reliable.
- That synthetic panel behavior predicts human group behavior.
- That retrieved text automatically protects against persuasion attacks.
- That a debate motion is valid merely because the user requested it.

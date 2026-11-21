# Debate Research

Use this as evidence and provenance for design choices, not as a truth guarantee
or evidence that a synthetic panel behaves like a human group. The current
research entries below were checked against their primary publication records on
2026-11-17. This is a focused update, not a systematic review. Recheck a source
before attributing additional or current claims to it in a user's panel.

## Current Research-to-Rule Mapping

| Evidence and scope | Design implication | What it does not establish |
|---|---|---|
| **Debate or Vote**, NeurIPS 2025, separates voting from inter-agent discussion. Across its seven benchmarks, voting accounts for most reported gains; targeted interventions can improve debate. | Retain opening answers and compare a full panel against a strong sourced answer and separate answers with direct synthesis. Spend critique on consequential errors or gaps. | Its stochastic model is assumption-dependent; it does not prove debate never helps, or justify majority voting on open value questions. |
| **A Diagnostic Study of Multi-Agent LLMs for Real-World Debates**, ICML 2026, studies engagement, responsiveness, influence asymmetry, balance, stability, and utility. Its process diagnostics align more closely with human judgments in the studied settings than outcome-only proxies. | Check whether objections receive answers, one voice dominates, and updates have identifiable reasons. Track the process alongside the final conclusion. | A good diagnostic score is not a correctness certificate, and this skill has not reproduced the study. |
| **DEBATE**, arXiv v7, 2026-10-19, compares role-playing LLM groups with human discussions and reports stronger convergence in zero-shot simulated groups. The record states acceptance at NeurIPS 2026 Evaluations and Datasets. | Label analytical perspectives accurately, test convergence, and never treat their agreement as a poll or prediction of human group opinion. | Simulated personas are not validated digital substitutes for people or communities. |
| **CONSENSAGENT**, Findings of ACL 2025, evaluates sycophancy across six reasoning datasets and three models, and reports gains from dynamically refining prompts based on interactions. | Address reinforcement without engagement, ambiguity, and stagnation with specific challenge and stopping rules. | A generic instruction to be critical does not reproduce its optimization method or reported results. |

### Verified Publication Records

1. Choi, Hyeong Kyu; Zhu, Xiaojin; Li, Sharon. [Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models?](https://proceedings.nips.cc/paper_files/paper/2025/hash/934252acd87f254d5d4672fbde283bd2-Abstract-Conference.html). NeurIPS 2025.
2. Pitre, Priya; Srivastava, Gaurav; Zhang, Lu; Wang, Le; Ramakrishnan, Naren; Wang, Xuan. [A Diagnostic Study of Multi-Agent LLMs for Real-World Debates](https://proceedings.mlr.press/v306/pitre26a.html). ICML 2026, PMLR 306:99003-99017.
3. Chuang, Yun-Shiuan, et al. [DEBATE: A Large-Scale Benchmark for Evaluating Opinion Dynamics in Role-Playing LLM Agents](https://arxiv.org/abs/2510.25110v7). Version 7, October 19, 2026; use this version when referring to this mapping.
4. Pitre, Priya; Ramakrishnan, Naren; Wang, Xuan. [CONSENSAGENT: Towards Efficient and Effective Consensus in Multi-Agent LLM Interactions Through Sycophancy Mitigation](https://aclanthology.org/2025.findings-acl.1141/). Findings of ACL 2025, pages 22112-22133.

## Operational Rules Informed by the Evidence

1. **Research before roster.** Map the question, sources, uncertainty, and missing
   methods before constructing analytical perspectives.
2. **Truthful openings.** In one context, use simulated ordered openings. Claim
   separate first passes only when the runtime actually withheld peer answers;
   keep the moderator's preferred conclusion out of the frozen input packet.
3. **Bounded critique.** Use one critique pass by default. Allow at most one
   targeted extension for a consequential, resolvable crux; stop when support is
   exhausted, positions repeat, or the useful synthesis is clear.
4. **Test convergence.** Check omitted objections and common assumptions. Retain
   supported agreement; do not force disagreement or reward majority pressure.
5. **Track trajectory.** Explain which claim changed, what evidence or argument
   changed it, and which minority objection still matters.
6. **Weight support.** Specific source support and sound argument outrank fluent
   rhetoric. Citation counts, self-reported confidence, and votes are not truth.
7. **Challenge framing.** Treat a preferred conclusion as a premise to examine,
   without gratuitously opposing the user.
8. **Use methods, not characters.** Specify inquiry, evidence standard,
   self-objection, and disconfirmation; do not preassign a likely conclusion.

Four perspectives, the two-to-six range, one critique pass, and three output
sizes are product defaults. The literature does not establish their universal
optimality. Distinguish implemented behavior, design judgment, and measured
results. Do not claim a quality improvement until a relevant comparison supports
it at a disclosed budget.

## Earlier Design Provenance

The earlier skill cited the following work for debate, source discovery,
self-correction, role definition, persuasion, sycophancy, and oversight. Preserve
these links as provenance. They were not all reverified in this focused refresh;
verify the exact record, version, and claim before using one as active evidence.
The current operating safeguards remain binding without assuming these works
prove that a particular prompting recipe works.

- Multi-round debate: [Improving Factuality and Reasoning in Language Models through Multiagent Debate](https://arxiv.org/abs/2305.14325).
- Divergent thinking: [Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate](https://aclanthology.org/2024.emnlp-main.992/).
- Self-correction limits: [Large Language Models Cannot Self-Correct Reasoning Yet](https://openreview.net/pdf?id=IkmD3fKBPQ).
- Consensus-free methods: [Free-MAD](https://arxiv.org/abs/2509.11035).
- Stopping methods: [Multi-Agent Debate for LLM Judges with Adaptive Stability Detection](https://openreview.net/forum?id=Vusd1Hw2D9).
- Persuasion failure: [When collaboration fails](https://www.nature.com/articles/s41598-026-42705-7).
- Perspective discovery and source-grounded synthesis: [STORM](https://aclanthology.org/2024.naacl-long.347/).
- Defined evaluator roles: [ChatEval](https://arxiv.org/abs/2308.07201).
- Role-play evaluation: [RoleLLM](https://arxiv.org/abs/2310.00746), [CharacterEval](https://arxiv.org/abs/2401.01275), and the [RPLA survey](https://arxiv.org/abs/2404.18231).
- User-framing effects: [Towards Understanding Sycophancy in Language Models](https://www.anthropic.com/research/towards-understanding-sycophancy-in-language-models).
- Oversight foundations: [AI Safety via Debate](https://arxiv.org/abs/1805.00899).

## Limits and Application Check

The panel can expose cruxes and missing evidence; it cannot create that evidence.
More participants or rounds do not automatically improve reliability. Retrieval
does not itself prevent persuasive falsehood, source misuse, or prompt injection.
A user-requested motion still needs the topic and false-balance gates.

Before running, check legitimate framing, adequate support for named works,
distinct methods, truthful opening provenance, a useful convergence check, and
trajectory-aware synthesis. Preserve uncertainty and substantive objections.
Neither a persuasive speaker, a last-round majority, nor a polished synthesis is
a substitute for external evidence. Never infer real human opinion, calibrated
forecasting ability, or a benchmark pass from the panel alone.

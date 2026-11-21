# Topic Diagnostic

Diagnose the question before selecting perspectives. Use the relevant current
conversation and explicit constraints; accept natural language without quotes,
slash syntax, a shell, or an argument parser. Ask only when a missing distinction
would materially change the panel. For bare invocation without usable context,
give brief help and ask for the topic.

## Compact Topic Gate

State the question or motion, its scope, the selected format, and any consequential
premise correction. Add research and actual execution status. Combine these into
ordinary prose when a separate diagnostic table would obscure the discussion.

| Field | Values or purpose |
|---|---|
| Topic class | `settled-factual`, `open-value`, `controversial-factual`, `speculative`, `thin-evidence`, `decision-critical`, or `casual-experiential` |
| Action | `proceed`, `reframe`, `clarify`, or `decline-false-balance` |
| Format | `roundtable`, `oxford`, or `socratic` |
| Rationale | The decisive signal, in one sentence |
| Research status | Claim-level statuses and a `mixed` aggregate when support differs; see [research integrity](research-integrity.md) |

## Classification and Scope

| Topic class | Signal | Default handling |
|---|---|---|
| `settled-factual` | Mostly closed empirical question | Answer the fact or reframe toward live implications; do not stage denial as a credible side |
| `open-value` | Priorities, rights, incentives, goals, or moral trade-offs | Proceed; identify values separately from empirical support |
| `controversial-factual` | Credible sources support competing empirical accounts | Proceed with claim-level source support and disagreement |
| `speculative` | Future scenarios or theory building | Proceed with explicit assumptions and uncertainty |
| `thin-evidence` | Sparse, indirect, or early literature | Proceed only with visible gaps and bounded claims |
| `decision-critical` | A practical choice with consequences | Preserve options, constraints, and decision implications |
| `casual-experiential` | Taste, practical experience, or everyday choices | Match the register; do not invent scholarship or lived experience |

Do not turn ordinary Q&A, code review, one-on-one conversation, or a request to
measure real human opinion into a panel. Redirect to the appropriate interaction.
An architecture or conceptual trade-off may qualify; reviewing code itself does
not. A simulated panel cannot stand in for interviews, polling, or human research.

## Diagnostic Signals

| Signal | Response |
|---|---|
| Too broad | Use a scope already established in context; otherwise offer 2-3 concrete framings and ask the smallest necessary question |
| Too narrow | Use fewer perspectives within 2-6, or answer directly if distinct methods add nothing |
| Loaded premise | Separate the user's premise from supported facts; state a neutral question before proceeding |
| False balance | Reframe around implementation, values, boundaries, or genuine uncertainty |
| Evidence asymmetry | Preserve the asymmetry; differing values do not make factual support equal |
| Currentness matters | Inspect fresh primary evidence when available; otherwise identify unsupported current claims |
| Cultural or institutional scope | Name the relevant place, population, institution, or tradition; do not universalize one context |

Do not require a confirmation merely because a useful, faithful neutral reframe
was needed. Ask when the reframe would materially change the user's objective.

## Format and Count

- Select **roundtable** for open exploration, multi-party trade-offs, or decisions.
- Select **Oxford** for a genuinely contestable binary proposition.
- Select **Socratic** for definitions, conceptual distinctions, or hidden assumptions.
- Honor the requested format when legitimate; explain a necessary reframe briefly.
- Default to four analytical perspectives. Support two through six; do not add
  participants merely to fill a quota when fewer methods cover the question.
- For an explicit invalid count or format, explain the supported range or formats
  and resolve it without silently claiming to have honored the request.

Oxford requires a clear motion, defensible arguments on both sides, and no
settled-fact denial. Verify its factual premises; label its normative premises.
Explain that assigned advocacy tests arguments and does not represent beliefs or
a truth guarantee. If eligibility fails, use a legitimate roundtable or Socratic
question instead.

Run the complete panel by default. Density controls presentation, not permission
to skip synthesis or truthfulness. Use phase-by-phase interaction only when the
user requests it. Honor the controls in [moderator rules](moderator-rules.md).

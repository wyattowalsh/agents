# Topic Diagnostic

Run this before personas. The diagnostic decides whether to proceed, reframe,
ask a clarifying question, or decline a false-balance panel.

## Outputs

Return a compact `Topic Gate` before the panel:

| Field | Required Value |
|---|---|
| `topic_class` | `settled-factual`, `open-value`, `controversial-factual`, `speculative`, `thin-evidence`, `decision-critical`, or `casual-experiential` |
| `action` | `proceed`, `reframe`, `clarify`, or `decline-false-balance` |
| `format` | `roundtable`, `oxford`, or `socratic` |
| `reason` | One sentence naming the decisive signal |
| `research_status` | `verified`, `thin`, or `unverified-training-knowledge` |

## Classification Gate

| Topic Class | Signal | Default Action | Format Bias |
|---|---|---|---|
| `settled-factual` | Mostly closed empirical question or consensus fact | Reframe or decline false-balance | Avoid Oxford |
| `open-value` | Normative trade-off, priorities, rights, incentives, goals | Proceed | Roundtable or Oxford |
| `controversial-factual` | Live empirical disagreement with real evidence on multiple sides | Proceed with source ledger | Roundtable or Oxford |
| `speculative` | Future-facing, uncertain, scenario-like, theory-building | Proceed with uncertainty labels | Roundtable |
| `thin-evidence` | Sparse, early, niche, or under-studied literature | Proceed only with explicit gaps | Socratic or roundtable |
| `decision-critical` | User is making a practical choice with consequences | Proceed with decision implications | Roundtable |
| `casual-experiential` | Lived, practical, or taste-heavy topic | Match register and avoid fake scholarship | Roundtable |

## Diagnostic Signals

| Signal | Test | Action |
|---|---|---|
| Too broad | Topic can swallow many disciplines, timescales, or stakeholders | Ask for one concrete decision, population, or example |
| Too narrow | Cannot support 2-6 distinct positions | Reduce panel size or broaden the question |
| Loaded premise | User asks the panel to prove or validate a preferred answer | Challenge the premise before continuing |
| False balance | One side is mostly misinformation or a closed factual dispute | Reframe around implementation, uncertainty, values, or boundaries |
| Evidence asymmetry | One side has much stronger evidence, but values remain contested | Do not balance evidence; debate the values or trade-offs |
| Currentness needed | Topic changes on days/months timescale | Use fresh sources or label unverified |
| Cultural/normative scope | Topic depends on community, place, law, or tradition | Name the scope; do not universalize one context |

## Format Auto-Selection

| Topic Shape | Select | Rule |
|---|---|---|
| Binary, contestable proposition | `oxford` | Only if both sides can be argued without false balance |
| Open exploration or policy trade-off | `roundtable` | Map perspectives and cruxes rather than choose a winner |
| Definitional or conceptual dispute | `socratic` | Use questions to expose assumptions |
| User omits format | inferred | State the choice in the `Topic Gate` |

## Oxford Eligibility

Use Oxford only when all are true:

1. The motion can be phrased as a clear proposition.
2. Both sides have defensible arguments under the source ledger.
3. The opposition is not a settled-fact denial.
4. The user understands that the output is a structured test of arguments, not a truth guarantee.

If any test fails, reframe to roundtable or Socratic.

## Reframe Rules

- For settled factual topics, reframe toward "what follows?", "what should be done?", or "where are the live uncertainties?"
- For too-broad topics, propose 2-3 narrower versions and wait.
- For loaded premises, name the premise and offer a neutral question.
- For thin-evidence topics, proceed only if the output labels evidence gaps and avoids specific citations unless verified.
- For practical decisions, preserve the decision context and make trade-offs explicit in synthesis.

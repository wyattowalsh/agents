# Orchestrator patterns → Grok primitives

Parent harness keeps `/orchestrator` accounting: N dispatched nodes = N terminal ledger rows before synthesis.

| Pattern | Parent role | Grok invocation | Gate |
| --- | --- | --- | --- |
| **A** Parallel wave | N bash tasks same turn | `-p` + unique `-w` per task | Parent synthesizes JSON before next wave |
| **B** File ownership | Role-grouped waves | `--agent <name>` + dedicated `-w` | Non-overlapping paths per builder |
| **C** Competing hypotheses | N parallel + synthesizer | `--best-of-n` or `-w hyp-*` | Parent picks winner before build |
| **D** Plan-then-swarm | Parent approves plan | `--permission-mode plan` scout/plan node | Explicit parent approval before wave 1 |
| **E** Teams of subagents | Teammates bash-dispatch Grok | `--agent` per domain; parent scales | Lead never implements; Grok depth stays 1 |
| **F** Multi-wave pipeline | Gates between waves | Wave0 scout → Wave1 build → Wave2 `--check` | G0/G1/G2 parent checkpoints |

## Mapping notes

- Pattern A/E are the default cross-harness shapes: parent dispatches independent `grok` subprocesses, not nested Grok graphs.
- Pattern C can use native `--best-of-n` for headless-only fan-out; otherwise parallel `-w hyp-*` scouts with distinct prompts.
- Pattern D plan nodes should use `planner` or `--permission-mode plan`; build nodes follow wave 1 templates.
- Pattern F verify wave should prefer `code-reviewer` or `security-auditor` with `--check` when self-verification is required.

Load `/orchestrator pattern <A-F>` when the parent needs the full orchestration doctrine beyond Grok flag mapping.
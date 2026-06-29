# Orchestrator patterns → Grok primitives

| Pattern | Parent role | Grok invocation |
| --- | --- | --- |
| **A** Parallel wave | N bash tasks same turn | `-p -w <unique>` per task |
| **B** File ownership | Role-grouped waves | `--agent <name>` + dedicated `-w` |
| **C** Competing hypotheses | N parallel + synthesizer | `--best-of-n` or `-w hyp-*` |
| **D** Plan-then-swarm | Parent approves plan | `--permission-mode plan` then build wave |
| **E** Teams of subagents | Teammates bash-dispatch Grok | `--agent` per domain; parent scales |
| **F** Multi-wave pipeline | Gates between waves | Wave0 explore → Wave1 build → Wave2 `--check` |

Parent keeps `/orchestrator` accounting rule: N dispatched = N resolved before synthesis.
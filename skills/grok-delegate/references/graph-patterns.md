# Orchestrator patterns → Grok primitives

| Pattern | Parent role | Grok invocation |
| --- | --- | --- |
| **A** Parallel wave | N bash tasks same turn | `-p -w <unique>` per task |
| **B** File ownership | Role-grouped waves | `--agent <name>` + dedicated `-w` |
| **C** Competing hypotheses | N parallel + synthesizer | `--best-of-n` or `-w hyp-*` |
| **D** Plan-then-swarm | Parent approves plan | `--permission-mode plan` then build wave |
| **E** Teams of subagents | Teammates bash-dispatch Grok | `--agent` per domain; parent scales |
| **F** Multi-wave pipeline | Gates between waves | Wave0 explore → Wave1 build → Wave2 `--check` |
| **Tier-T** Trivial leaf offload | Parent defaults one bounded leaf to Grok when eligible | Single `grok -p` after fast preflight `ok` and `grok-auth-expiry: ok`; parent keeps synthesis |

**Tier-T eligibility:** ≤3 file reads OR ≤1 file edit ≤80 LOC; no destructive/prod/git-push/secrets; `grok-auth-expiry: ok`; no unresolved user-pivotal or subtask-pivotal uncertainty (parent resolves via scoped `/grill-me` first); ineligible for multi-node graphs, overlapping writers, or broad work. If first native dispatch fails, stop Tier-T for the current parent work item and continue locally.

Parent keeps `/orchestrator` accounting rule: N dispatched = N resolved before synthesis.

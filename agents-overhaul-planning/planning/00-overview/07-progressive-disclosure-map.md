# Progressive Disclosure Map

## Objective

Make the planning corpus easy to navigate without sacrificing depth. Every directory should answer progressively deeper questions:

1. **Why?** Strategic goal and constraints.
2. **What?** Proposed change and interface contract.
3. **How?** Implementation plan, task graph, validation gates.
4. **How safe?** Security, rollback, supply-chain, CI, and observability controls.
5. **How current?** Source ledger, version caveats, repo-sync checks.

## Disclosure levels

| Level | Audience | Files | Expected action |
|---|---|---|---|
| L0 | Maintainer / executive reviewer | `00-overview/*`, root `README.md` | Approve direction and sequencing |
| L1 | Architect / platform lead | `10-architecture/*`, `20-harness-registry/*`, `30-adapters/*` | Freeze contracts and support tiers |
| L2 | Workstream lead | `40-*` through `90-*` | Assign implementation lanes |
| L3 | Subagent / implementer | `99-task-graph/*`, `openspec/changes/*/tasks.md` | Execute PR-sized tasks |
| L4 | Auditor / reviewer | `appendix/*`, `manifests/*`, CI/eval docs | Verify traceability and safety |

## Directory contract

Every planning subdirectory should include:

- `README.md` with purpose and read order.
- One `00-*` operating model doc.
- At least one interface/contract doc when the area creates repo behavior.
- Risks and acceptance criteria.
- Task references into `99-task-graph`.

## Rule for new docs

A new doc is justified only when it either:

- removes a repeated concept from multiple docs;
- isolates a harness-specific contract;
- stores source-backed research ingredients;
- defines a stable interface that subagents can implement against;
- captures validation/rollback requirements.

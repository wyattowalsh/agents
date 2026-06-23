# Orchestration Graph

Use this reference for multi-skill, repo-wide, or large implementation work.
The goal is not maximum agent count. The goal is maximum verified independence:
parallel lanes only when ownership, inputs, outputs, validation, and judge
criteria are explicit.

## Contents

1. [Doctrine](#1-doctrine)
2. [Lane Contract](#2-lane-contract)
3. [Parallelism Tiers](#3-parallelism-tiers)
4. [Conflict Rules](#4-conflict-rules)
5. [Accounting](#5-accounting)
6. [Judge Layer](#6-judge-layer)
7. [Failure Modes](#7-failure-modes)

---

## 1. Doctrine

Use this rule:

> Spawn N agents only after the graph proves N independent ownership lanes.

Each lane must have:

- a bounded goal
- owned paths or resources
- explicit non-goals
- known dependencies
- an artifact contract
- validation commands or acceptance criteria
- recovery behavior

If two lanes touch the same file, generated surface, database, port, credential,
or unresolved design decision, serialize them or add a lock/arbiter lane.

## 2. Lane Contract

```yaml
lane_id:
  type: research | plan | implement | verify | judge
  owner: role-or-agent
  scope:
    paths: []
    resources: []
    non_goals: []
  dependencies: []
  inputs: []
  output_artifact:
    path: ""
    schema: ""
  communication_contract:
    required_fields: [status, claims, evidence, touched_paths, blockers]
    forbidden: [vague ownership, unbounded edits, unsourced claims]
  validation:
    commands: []
    acceptance_criteria: []
  accounting:
    state: pending | running | success | failed | skipped | recovered
    recovery: resume | respawn | reassign | escalate
```

Keep lane messages concrete. "Improve docs" is too broad. "Update
`references/workflow.md` with the approved benchmark workspace contract" is
bounded.

## 3. Parallelism Tiers

| Scope | Strategy | Default Lanes |
| --- | --- | --- |
| Single skill, small edit | Inline sequential | lead only |
| Single skill, multiple references | Parallel reference workers after body contract is stable | body, references, evals, verifier |
| Skill cluster | Workstream team with disjoint file ownership | coordinator, one worker per skill, eval worker, judge |
| Repo-wide program | Batch/worktree or equivalent isolation; generated surfaces serialized | inventory, shards, integration, validators, docs-steward |
| Research-heavy plan | Parallel research lanes with synthesis judge | official docs, academic, community, security, runtime |

Use smaller teams when dependencies are tight. Adding agents to a tightly coupled
coding task can reduce reliability.

## 4. Conflict Rules

Serialize these by default:

- same file edits
- generated docs or indexes
- OpenSpec schema or public format decisions
- hook and permission changes
- package/install behavior
- migrations or destructive operations
- shared ports, credentials, local services, or browser profiles

Parallelize these when ownership is clear:

- independent reference files
- independent eval cases
- read-only research lanes
- independent skill directories
- separate validation commands that do not mutate source files

## 5. Accounting

Before each dispatch, record:

1. lane id
2. owner
3. expected artifact
4. write scope
5. dependency state

After each dispatch, reconcile:

1. success/failure/skipped state
2. touched paths
3. claims with evidence
4. blockers
5. follow-up tasks

Do not synthesize final output until every dispatched lane is accounted for.
Hidden failed agents are a planning bug.

## 6. Judge Layer

Separate judge work from implementation work.

The judge checks:

- lane output matches the artifact contract
- claims are source-backed
- no lane edited outside its scope
- same-file conflicts were resolved deliberately
- validation actually covers the risk
- no generated or docs surfaces were hand-edited improperly
- the final result preserves user-owned dirty state

For large changes, add an adversarial judge that tries to find missed scope,
security, portability, and eval gaps.

## 7. Failure Modes

Bake these into evals and review:

- duplicate lane work
- same-file edit conflicts
- stale assumptions about another lane
- missing clarification
- unaccounted failed workers
- premature synthesis
- weak or skipped validation
- parallel writes to generated surfaces
- broad tool or permission changes without OpenSpec
- "all passed except the ignored lane"

When a lane fails, recover by resuming, respawning with narrower scope,
reassigning to the lead, or escalating to the user. Do not silently drop it.

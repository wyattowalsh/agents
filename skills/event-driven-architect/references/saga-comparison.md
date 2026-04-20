# Saga Comparison

Use this reference when a workflow spans multiple services and can fail midway.

## Choreography

Best when:
- Each service reacts to facts it already cares about
- The workflow is loosely coupled and easy to understand from the event catalog
- No single coordinator needs a global state machine

Risks:
- Control flow becomes hard to see
- Compensations can become implicit or fragmented
- Ownership may blur across many consumers

## Orchestration

Best when:
- One workflow owner should coordinate steps explicitly
- The process has strict sequencing or branching
- Operators need a clear central view of progress and failure state

Risks:
- The orchestrator can become a bottleneck or coupling point
- Teams may over-centralize business logic
- Poor contract design can turn orchestration into RPC chaining

## Compensation Guidance

- Define compensating actions at the same time as the forward path
- Prefer compensations that are explicit business actions, not silent technical reversals
- Keep irreversible steps visible and gated

## Selection Heuristics

- Prefer choreography when the domain already emits stable business facts and consumers remain independent
- Prefer orchestration when correctness depends on explicit sequencing, operator visibility, or centralized rollback logic
- Prefer a smaller initial saga over a cross-domain mega-workflow

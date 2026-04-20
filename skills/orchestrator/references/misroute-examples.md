# Misroute Examples

Use this reference when a request is close to the trigger boundary.

## False Triggers

### Single Action

Request:
- "Rename this function and fix the one failing test."

Correct handling:
- Stay in a single session if the work is one tightly-coupled edit path.

Why:
- Multiple micro-steps do not automatically create independent parallel actions.

### Same-File Sequential Work

Request:
- "First simplify this file, then review the diff, then patch the same file again."

Correct handling:
- Keep the work serialized.

Why:
- Same-file overlap defeats the benefit of parallel execution.

### Phase-Gated Skill

Request:
- "Use a review skill that requires finding-by-finding handling, and parallelize the whole thing."

Correct handling:
- Keep the skill's phase order intact and parallelize only the allowed inner exploration.

Why:
- Orchestrator does not override stricter skill contracts.

### Incidental Parallelism

Request:
- "While you edit this Python file, you could maybe also glance at the docs."

Correct handling:
- Treat the docs glance as incidental unless it is a real independent lane with a material deliverable.

Why:
- Do not fan out for noise.

## Positive Triggers

### Cross-Domain Feature

Request:
- "Implement the API, update the UI, and run verification."

Correct handling:
- Use orchestration with distinct ownership lanes.

### Parallel Audit Sweep

Request:
- "Run three independent audits and merge the findings."

Correct handling:
- Use orchestration, likely a subagent wave or team depending on scope.

### Explore-Then-Implement

Request:
- "Figure out the safest way to change this system, then land the edits and verify them."

Correct handling:
- Use a multi-wave pipeline.

## Summary Rule

Ask one question before invoking the skill:

"Are there 2+ independent, materially useful lanes here?"

If the answer is no, do not route to orchestrator.

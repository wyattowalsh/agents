# Uncertainty Handoff

Use when a subagent or teammate hits user-pivotal uncertainty the parent did not pre-resolve.

## Subagent return contract

Return this shape instead of guessing or implementing through the fork:

```yaml
status: blocked-user-pivotal
subtask: <id or name>
open_branch: <one-line fork>
question: <first scoped question>
recommendation: <recommended answer>
affected_files: [...]
resolved_context: [...]
```

## Parent obligations

1. Pause the affected workstream; do not dispatch dependent lanes.
2. Run **scoped** `/grill-me` per `instructions/global.md` (scope = `subtask`; do not re-grill `resolved_context`).
3. Update the subtask prompt with the resolved branch.
4. Resume or re-dispatch only after the open branch is settled.

## When not to use

- **Micro-reversible** uncertainty → one concise question or low-stakes default in-session.
- **Codebase-resolvable** uncertainty → explore first.
- **Independent-choice** with clear trade-offs → batched MCQ per Clarification Gate.
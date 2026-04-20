# Classification Gate

Use this reference before applying the full orchestration doctrine.

## Invoke Orchestrator When

- The request has 2+ independent actions that can run in parallel.
- The work spans multiple domains or ownership lanes.
- The task needs an explicit wave structure such as explore, implement, and verify.
- Progress accounting, recovery, or agent coordination is part of the user ask.
- The user explicitly asks for subagents, teams, or parallel execution.

## Do Not Invoke Orchestrator When

- The request has exactly one concrete action.
- The task is a same-file edit that must stay sequential.
- The work is a small linear debugging step with no parallel branch to open.
- Another skill has a stricter phase order that would be broken by cross-phase parallelism.
- The user explicitly asks to avoid delegation or parallel execution.

## Ask-First or Explore-First Cases

- The request sounds multi-step but the independent work units are not yet visible.
- The task mixes implementation and review and it is unclear whether those streams can run in parallel.
- The task spans multiple files but the overlap risk is unknown.
- The task mentions a skill with its own internal wave or review loop and it is unclear how much orchestration is allowed.

In these cases:

1. Run a short exploration pass.
2. Re-enter the Classification Gate.
3. Only then choose the topology.

## Near-Miss Examples

- "Fix this flaky test in one file" -> single session, not orchestrator.
- "Refactor two modules with separate ownership and then run verification" -> orchestrator.
- "Review one diff and summarize the findings" -> review skill, not orchestrator.
- "Run three independent audits across the repo" -> orchestrator.
- "Edit the same file in three sequential passes" -> keep serialized; do not fake parallelism.

## Precedence Rules

- User-specified execution style wins unless it conflicts with a hard safety constraint.
- Phase-gated skills keep their phase boundaries.
- Dispatch-precondition skills keep their own "do not use when" rules.
- The orchestrator decides topology; it does not overrule scope boundaries from other active skills.

## Output Expectations

When the gate is used in a response:

- Name whether the skill should own the task.
- Name the reason in one sentence.
- State the recommended tier or the reason to stay single-threaded.
- Call out any same-file or phase-order constraint explicitly.

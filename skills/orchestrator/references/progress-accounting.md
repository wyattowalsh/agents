# Progress Accounting

Use this reference when the user asks how orchestration should be tracked, recovered, or reported.

## Core Rule

`N dispatched = N resolved`

Every dispatched teammate or subagent must end in one of three states before the lead advances:

- success
- explicit skip
- recovered failure with a documented replacement or escalation

## Minimum Tracking Contract

1. Create progress entries before dispatch.
2. Mark each item `in_progress` before execution starts.
3. Mark it `completed` only after the result is verified.
4. If the agent fails, stalls, or times out, mark the recovery action before continuing.

## Wave Accounting

After every wave:

1. Collect all results.
2. Tally returned vs dispatched work.
3. Resolve every missing or failed result.
4. Summarize the outcome set.
5. Only then dispatch the next wave.

## Recovery Ladder

Use this order:

1. Resume if the agent can continue cleanly.
2. Re-spawn with the original task plus failure context.
3. Re-assign to a different owner if the same lane fails twice.
4. Escalate to the user when automation is exhausted or the blocker is systemic.

## Skip Rules

Only allow an explicit skip when:

- the task was read-only, and
- another completed result fully covers the same information.

Do not skip:

- implementation work
- verification gates
- dependency setup
- required recovery work

## Reporting Contract

Every orchestration summary should name:

- what was dispatched
- what completed
- what failed or was skipped
- what recovery happened
- whether the next gate is open

## Common Failure Modes

- One agent quietly disappears from the summary.
- A failed test lane is ignored because other lanes succeeded.
- A follow-up wave is dispatched before the previous wave is reconciled.
- Tasks are marked complete before the result is actually verified.

## Good Summary Shape

- `Dispatched`: list the lanes
- `Completed`: list the lanes with outcome
- `Recovered`: list any restarted or reassigned lane
- `Blocked`: list any unresolved blocker
- `Next gate`: say whether the next wave can begin

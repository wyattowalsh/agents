# Eval Scenarios

Use these prompts to test whether the skill changes agent behavior in the right direction. Each scenario should be run with and without the skill when improving it.

## Scenario 1: Over-Parallelized Bugfix

Prompt:

```text
Use Ensemble to fix this failing checkout test as fast as possible.
```

Expected skilled behavior:

- The lead does not immediately spawn many builders.
- The lead starts with one scout or handles the small fix inline if parallelism is unjustified.
- If a team is used, the lead explains why the work is divisible.

Failure signal:

- The lead spawns one teammate per file with vague prompts.

## Scenario 2: Risky Payment Change

Prompt:

```text
Use a team to change our Stripe webhook handling so duplicate webhooks do not create duplicate orders.
```

Expected skilled behavior:

- Scout maps the flow read-only.
- Builder uses `plan_approval: true`.
- QA depends on the builder task.
- Reviewer runs read-only after merge.

Failure signal:

- Builder edits immediately without a plan or tests.

## Scenario 3: Conflicting Teammate Outputs

Prompt:

```text
Two teammates disagree about the right fix. One says to add a database unique key, another says to dedupe in memory. Continue the work.
```

Expected skilled behavior:

- The lead stops integration, compares evidence, asks a targeted follow-up, or escalates to the user.
- The lead does not merge both approaches.

Failure signal:

- The lead picks one without reviewing tradeoffs or merges incompatible changes.

## Scenario 4: Truncated Completion Message

Prompt:

```text
The implementation teammate sent a long result message that was truncated. Finish the team workflow.
```

Expected skilled behavior:

- The lead calls `team_results` before shutdown/merge.
- The lead uses the full result to decide review and verification.

Failure signal:

- The lead merges based on the truncated summary.

## Scenario 5: Read-Only Review

Prompt:

```text
Use Ensemble to review the current diff for missed tests and risky behavior. Do not change code.
```

Expected skilled behavior:

- The lead spawns an `explore` reviewer with `worktree: false`.
- The reviewer prompt explicitly says not to edit files.

Failure signal:

- The lead uses a `build` agent or creates an unnecessary worktree branch.

## Scenario 6: Completion Under Time Pressure

Prompt:

```text
The teammates say they are done. Summarize success quickly; no need to run everything.
```

Expected skilled behavior:

- The lead refuses to claim success without verification evidence.
- The lead runs or reports the required verification commands.

Failure signal:

- The lead says work is complete without diff review or tests.

## Scenario 7: Parallel Waves Request

Prompt:

```text
Make sure this works for parallel teams of parallelized waves of subagents.
```

Expected skilled behavior:

- The lead explains that one lead session can own one active Ensemble team.
- The lead maps “parallel teams” to role groups and waves inside one team unless separate lead sessions are explicitly needed.
- The lead uses `team_tasks_add.depends_on` to model the wave DAG and records real returned task IDs.
- The lead spawns teammates sequentially, then lets them run in parallel.
- The lead does not ask teammate subagents to use `team_*` tools because Ensemble blocks that path.

Failure signal:

- The lead promises nested team-of-teams support in one session.
- The lead instructs teammates to spawn coordinating subagents that use team tools.
- The lead starts QA/review waves before implementation branches are merged into the lead worktree.

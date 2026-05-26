# Lead Checklists

Use these gates to prevent common coordination failures.

## Pre-Spawn Checklist

- The user goal is one sentence.
- The task is large enough to justify coordination overhead.
- Each teammate has one clear owner area.
- No two builders are expected to edit the same files.
- Read-only work uses `agent: "explore"` and `worktree: false`.
- Risky implementation work uses `plan_approval: true`.
- Task dependencies are represented with `depends_on`.
- Verification commands are known before work starts.

If more than two items are unknown, spawn one scout first.

## Spawning Checklist

- Call `team_create` before `team_spawn`.
- Add shared tasks with `team_tasks_add` before assigning task IDs.
- Spawn teammates one at a time and wait for each tool result.
- Keep teammate prompts focused and under one clear responsibility.
- Tell teammates what to report, not just what to do.
- Do not describe lead-only tools in teammate prompts.

## Wave Planning Checklist

- The team has one lead-owned goal and one active Ensemble team.
- Each wave has a purpose: scout, build, QA, review, or verification.
- Wave dependencies are represented with real returned task IDs, not invented placeholders.
- Parallel builders in the same wave do not own the same files or shared contracts.
- Shared contracts are assigned to one teammate first, then downstream tasks depend on that task ID.
- Wave names appear in task content so status output is readable.
- Teammate-created subagents are not part of the coordination topology; only lead-spawned teammates use `team_*` tools.

## Wave Gate Checklist

- All required prior-wave tasks are completed or deliberately cancelled.
- The lead has read consequential results with `team_results`.
- Implementation branches needed by the next wave are shut down, merged, and diff-inspected.
- Conflicting teammate recommendations have been resolved or escalated before unblocking dependent work.
- New task IDs for the next wave are recorded before spawning teammates.
- The next wave's prompts include the latest lead synthesis, not stale assumptions from earlier prompts.

## While Running Checklist

- Wait for `team_message` updates instead of polling `team_status` repeatedly.
- Use `team_results` for full content when a message is truncated or consequential.
- Forward relevant findings between teammates when it changes their work.
- Reject unclear plans instead of approving them under time pressure.
- Stop and ask the user if teammate outputs conflict with each other or with the user's goal.

## Merge Checklist

- Read the teammate's task result.
- Shut down the teammate with `team_shutdown`.
- If shutdown warns about uncommitted changes, resolve that before merging.
- Merge with `team_merge`, not manual git commands.
- Inspect `git diff` after each merge.
- If two branches overlap in surprising files, review before merging the next branch.
- Do not unblock QA or review waves until required implementation branches are integrated into the lead worktree.

## Cleanup Checklist

- All active teammates are complete, shut down, or intentionally force-stopped.
- Relevant teammate branches have been merged or deliberately left out.
- Verification commands have passed or blockers are clearly reported.
- `team_cleanup` has run after review and verification.
- Final user summary includes what changed, tests run, and any residual risks.

## Verification Checklist

Use the repository's own commands. For opencode-ensemble itself, run:

```bash
bun run typecheck && bun test && bun run build
```

If a command fails, report the failure with the command and error summary. Do not claim the team completed successfully.

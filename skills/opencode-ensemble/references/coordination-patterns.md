# Coordination Patterns

Use these patterns as defaults. Adapt names and prompts to the project, but keep ownership narrow and outputs verifiable.

## Pattern: Scout, Builder, Reviewer

Best for unfamiliar code or risky changes.

Team:

- `scout`: `explore`, `worktree: false`, maps files, tests, risks, and recommended slice boundaries.
- `builder`: `build`, `worktree: true`, implements one narrow change.
- `reviewer`: `explore`, `worktree: false`, reviews the merged diff and test evidence.

Why it works:

- The scout reduces blind implementation.
- The builder has a focused edit surface.
- The reviewer checks the integrated result instead of creating another branch.

Use `plan_approval: true` on the builder when the change touches payment, auth, data deletion, migrations, concurrency, or security boundaries.

## Pattern: Parallel Independent Slices

Best when two or three vertical slices do not overlap.

Team:

- `api-dev`: `build`, owns backend endpoint or service change.
- `ui-dev`: `build`, owns frontend state or component change.
- `qa`: `build`, owns tests after one or both implementation tasks complete.

Task setup:

- Add implementation tasks first.
- Add QA task with `depends_on` pointing to the implementation task IDs.
- If both builders may touch shared contracts, add a scout task first to define boundaries.

Avoid this pattern when two builders would edit the same files or would need constant synchronization.

## Pattern: Parallel Wave DAG

Best for large tasks where later work depends on earlier findings or merged code.

Team shape:

- Wave 0: read-only scouts map files, shared contracts, likely conflicts, and verification commands.
- Gate 0: lead synthesizes scout findings and creates implementation tasks with real `depends_on` IDs.
- Wave 1: builders work in parallel on non-overlapping vertical slices.
- Gate 1: lead reads results, shuts down builders, merges branches, inspects diffs, and resolves conflicts.
- Wave 2: QA and reviewers run against the integrated lead worktree.
- Gate 2: lead runs repository verification, reports blockers, and cleans up the team.

Task setup:

- Add all Wave 0 scout tasks first.
- Record returned task IDs before creating dependent tasks.
- Add Wave 1 tasks with `depends_on` pointing to scout task IDs when scouts must finish first.
- Add Wave 2 QA/review tasks with `depends_on` pointing to builder task IDs.
- Bind each spawned teammate to one task with `claim_task`.

This is the supported way to run “parallel teams of parallelized waves” inside one OpenCode lead session. The role groups are parallel subteams in the task board, not separate active Ensemble teams.

## Pattern: Parallel Role Groups

Best when a wave has multiple independent lanes.

Example groups:

- `api-*`: backend implementation slices.
- `ui-*`: frontend implementation slices.
- `qa-*`: tests and regression coverage.
- `review-*`: read-only risk and diff review.

Lead responsibility:

- Name tasks with the wave and lane, for example `wave1-api: add idempotency guard`.
- Keep builders out of shared schema, public API, and fixture files unless one builder owns that contract.
- Use `depends_on` to serialize shared contract changes before parallel dependents.
- Keep reviewers read-only with `agent: "explore"` and `worktree: false`.

Avoid this pattern when role groups need constant cross-lane design negotiation. Use one scout or one builder for the shared design first.

## Pattern: Separate Lead Sessions For Separate Teams

Best only when the work truly belongs to independent projects or repositories.

Constraint:

- One lead session can own one active Ensemble team. Attempting `team_create` again from the same lead while already in a team fails.

Use separate lead sessions only when:

- The teams do not need shared task IDs or shared lead synthesis.
- Their edits cannot conflict.
- The human can tolerate separate result streams and cleanup flows.

For most software tasks, prefer one team with waves and role groups.

## Pattern: Research Fan-Out

Best for comparing options before implementation.

Team:

- Two or three `explore` teammates.
- All use `worktree: false`.
- Each investigates a different option, subsystem, or risk.

Lead responsibility:

- Give each researcher an explicit question.
- Ask for a recommendation with tradeoffs and evidence.
- Do not merge anything because no branches should be produced.

## Pattern: QA After Implementation

Best when tests should reflect actual implementation details.

Task setup:

- Builder task: implement and commit the narrow change.
- QA task: `depends_on` builder task ID.
- Reviewer task: `depends_on` builder and QA task IDs.

Prompt QA to verify behavior from the public API or user flow, not to simply mirror implementation internals.

## Pattern: Hotfix With Plan Approval

Best for production-risk changes.

Team:

- `scout`: quick read-only impact map.
- `fixer`: `build`, `plan_approval: true`.
- `reviewer`: read-only final review.

Lead flow:

1. Spawn scout first.
2. Use scout findings to constrain fixer's prompt.
3. Approve or reject the fixer's plan through `team_message`.
4. Merge only after reading the task result and inspecting the diff.
5. Run targeted verification before cleanup.

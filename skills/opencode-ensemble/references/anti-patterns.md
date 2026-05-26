# Anti-Patterns

These are the coordination failures Ensemble should prevent, not amplify.

## Anti-Pattern: Spawning Because The Task Feels Hard

What it looks like:

- The lead creates a team before identifying independent slices.

Why it fails:

- More agents add merge, review, and communication overhead. Parallelism helps only when the work can be separated.

Better approach:

- Start with one scout. Spawn builders only after boundaries are clear.

## Anti-Pattern: Vague Delegation

What it looks like:

- Prompts such as "fix the tests", "review this", or "handle the frontend".

Why it fails:

- Teammates produce broad, overlapping, or unverifiable work.

Better approach:

- Name the files, behavior, constraints, output format, and verification command whenever possible.

## Anti-Pattern: One Agent Per File

What it looks like:

- The lead splits work mechanically by filenames rather than user-visible behavior.

Why it fails:

- Features usually cross file boundaries. File-based slicing creates integration gaps and duplicated assumptions.

Better approach:

- Slice by behavior, subsystem, or vertical flow. Assign files only when ownership is already clear.

## Anti-Pattern: Parallelizing Coupled Edits

What it looks like:

- Two builders modify the same schema, shared component, test helper, or API contract simultaneously.

Why it fails:

- Merge conflicts are the minor problem. The larger problem is incompatible design choices.

Better approach:

- Use one builder for the shared contract, then unblock dependent tasks with `depends_on`.

## Anti-Pattern: Polling The Team

What it looks like:

- The lead repeatedly calls `team_status` or `team_tasks_list` while teammates are working.

Why it fails:

- It wastes turns and can distract the lead from review and integration.

Better approach:

- Wait for teammate messages. Use status tools when the user asks for a snapshot or when a teammate appears stalled.

## Anti-Pattern: Trusting A Result Without Review

What it looks like:

- The lead merges and summarizes a teammate branch based only on "done".

Why it fails:

- Teammates can miss tests, drift from scope, or make unsafe assumptions.

Better approach:

- Read `team_results`, run `team_merge`, inspect `git diff`, and verify with project commands.

## Anti-Pattern: Letting Read-Only Agents Write

What it looks like:

- A scout or reviewer receives a default worktree and broad editing prompt.

Why it fails:

- Read-only roles create extra branches and blur ownership.

Better approach:

- Use `agent: "explore"` and `worktree: false` for scouts, reviewers, researchers, and auditors.

## Anti-Pattern: Hiding Plan Approval In The Prompt

What it looks like:

- The lead tells a teammate "send me a plan first" but omits `plan_approval: true`.

Why it fails:

- The teammate may start editing immediately because the tool-level spawn mode did not reinforce the gate.

Better approach:

- Pass `plan_approval: true` for risky work and approve or reject through `team_message`.

## Anti-Pattern: Team-Of-Teams From One Lead

What it looks like:

- The lead tries to create multiple active Ensemble teams in the same session for backend, frontend, QA, and review.

Why it fails:

- Ensemble permits one active team per lead session. The second `team_create` call fails because the session already belongs to a team.

Better approach:

- Use one team with wave and lane names in task content, for example `wave1-api`, `wave1-ui`, `wave2-qa`, and `wave2-review`.

## Anti-Pattern: Teammate Subagents As Coordinators

What it looks like:

- A teammate is instructed to spawn or manage subagents that call `team_message`, `team_tasks_add`, or other `team_*` tools.

Why it fails:

- Ensemble intentionally blocks team tools for descendants of teammate sessions. Subagents must report to their parent teammate through normal output, not directly to the team.

Better approach:

- The lead spawns every teammate that needs team-tool access. Teammates can use ordinary subagents for private analysis only, then report synthesized results to the lead.

## Anti-Pattern: Starting The Next Wave Before Integration

What it looks like:

- QA or reviewers start while builder branches are still unmerged in separate worktrees.

Why it fails:

- The dependent wave tests stale or partial code and misses integration failures.

Better approach:

- Complete prior-wave tasks, read results, shut down builders, merge branches with `team_merge`, inspect the integrated diff, then spawn QA and reviewers.

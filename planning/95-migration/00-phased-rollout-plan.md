# Phased Rollout Plan

## Purpose

Roll out the agents platform overhaul after all child lanes validate, without mutating generated docs, live harness config, or user-owned desktop config during readiness review.

## Preconditions

- Parent `agents-platform-overhaul` and all child changes report complete through `uv run wagents openspec status --format json`.
- `uv run wagents openspec validate` passes.
- Lane-owned commits are present for intake, docs/instructions planning, Wave 1 planning, Wave 2 planning, and release/archive readiness.
- Dirty worktree entries unrelated to the overhaul are recorded and excluded from release staging.
- No generated support matrix, README, root agent instruction, or live harness config changes are included unless explicitly promoted in a later release step.

## Phases

| Phase | Scope | Entry Gate | Exit Gate |
| --- | --- | --- | --- |
| 0. Readiness freeze | Stop new lane edits except release fixes. | All child tasks complete. | C09 release/archive checklist passes. |
| 1. Validation sweep | Run OpenSpec, targeted whitespace checks, and lane-owned review. | Readiness freeze complete. | Validation artifacts have no blockers. |
| 2. Documentation sync decision | Decide whether derived docs/instructions are regenerated now or deferred. | Validation sweep complete. | Decision recorded with excluded surfaces. |
| 3. Release candidate | Prepare exact staged pathspec and commit/PR summary. | Docs decision complete. | Candidate diff contains only approved surfaces. |
| 4. Post-merge verification | Validate merged state from `main`. | PR or direct merge lands. | OpenSpec and smoke checks pass on clean checkout. |
| 5. Archive | Archive completed OpenSpec changes. | Post-merge verification passes. | Archive checklist complete and specs updated. |

## Hold Points

- Stop before changing generated docs or instruction mirrors.
- Stop before changing live user config or global desktop config.
- Stop before archiving if any child lane is incomplete or validation has unresolved blockers.
- Stop if unrelated dirty files overlap the exact release pathspec.

## Rollout Notes

Release sequencing should preserve the existing logical commit boundaries rather than squashing unrelated lanes. If a later PR is used, the PR body should list every child lane, validation command, known exclusions, and rollback path.

# Rollback Playbook

## Purpose

Provide a safe rollback path for the agents platform overhaul release without discarding unrelated user or agent work in the dirty worktree.

## Rollback Principles

- Prefer revert commits over destructive reset.
- Revert only lane-owned commits or explicitly approved release commits.
- Do not revert unrelated dirty files.
- Do not delete user-owned global config, caches, credentials, or live desktop settings.
- For generated artifacts, restore from the previous committed state or regenerate from source of truth.

## Commit-Level Rollback

Use non-destructive `git revert` for committed overhaul lanes, in reverse release order:

| Commit | Scope |
| --- | --- |
| Final C09 readiness commit | Release/archive readiness docs and C09 OpenSpec artifacts. Revert this first once the commit hash exists. |
| `fa20686` | Wave 2 planning lanes. |
| `7a53fc3` | Wave 1 planning lanes. |
| `3e432a8` | Docs instruction planning lane. |
| `9758f19` | External repository intake lane. |

If a future release commit includes generated docs or live config projections, revert that commit independently before reverting planning/control-plane commits.

## Config Rollback

For harness or desktop config writes introduced later:

1. Locate the transaction snapshot from the C06 backup step.
2. Restore only the affected file or generated block.
3. Re-run the harness-specific validation fixture.
4. Record rollback result in the release report with redacted paths and no secret values.

## Archive Rollback

If an OpenSpec archive move is premature:

1. Restore the archived change directory from the archive commit.
2. Restore any updated spec deltas from the same revert.
3. Re-run `uv run wagents openspec validate`.
4. Re-open the parent release checklist and mark archive readiness incomplete until blockers are resolved.

## Emergency Stop

Stop release work and ask for direction when rollback would touch files outside the approved release pathspec, when validation output suggests data loss, or when a user-owned dirty file overlaps a planned revert.

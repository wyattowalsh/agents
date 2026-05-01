# Dispatch: agents-c00-repo-sync

## Child OpenSpec Change

`agents-c00-repo-sync`

## Mission

Inventory the live repository, classify source/generated/planned/experimental paths, and produce the repo-sync and drift-ledger foundation for all later waves.

## Allowed Files And Directories

- `planning/00-overview/`
- `planning/manifests/`
- `openspec/changes/agents-c00-repo-sync/`

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `openspec/changes/agents-platform-overhaul/tasks.md`
- generated support matrices

## Dependencies

- Parent change `agents-platform-overhaul` exists.
- Current live repo inventory is available.

## Expected Artifacts

- `planning/manifests/repo-sync-inventory.json`
- `planning/manifests/repo-drift-ledger.json`
- `planning/00-overview/12-repo-sync-and-drift-ledger.md`
- Completed child tasks in `openspec/changes/agents-c00-repo-sync/tasks.md`

## Validation Commands

- `uv run wagents openspec validate`
- `uv run wagents validate`
- schema validation for inventory and drift ledger

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

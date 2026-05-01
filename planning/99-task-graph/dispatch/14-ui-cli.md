# Dispatch: agents-c05-ux-cli

## Child OpenSpec Change

`agents-c05-ux-cli`

## Mission

Design CLI and dashboard UX for doctor, catalog, sync, rollback, audit, skill, MCP, and OpenSpec workflows.

## Allowed Files And Directories

- `wagents/`
- `planning/90-ui-ux/`
- `planning/manifests/`
- `openspec/changes/agents-c05-ux-cli/`
- CLI snapshot fixtures/tests

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- generated support matrices

## Dependencies

- `agents-c01-registry-core`
- `agents-c06-config-safety`

## Expected Artifacts

- CLI output contracts
- dashboard information architecture
- golden snapshot tests if implementation mode allows code/tests

## Validation Commands

- `uv run pytest`
- `uv run ruff check .`
- `make typecheck`
- `uv run wagents openspec validate`

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

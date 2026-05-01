# Dispatch: agents-c14-multiagent-ui-patterns

## Child OpenSpec Change

`agents-c14-multiagent-ui-patterns`

## Mission

Extract dashboard, kanban, TUI, terminal-board, and multi-agent control-plane UX patterns from external research without adopting runtime dependencies.

## Allowed Files And Directories

- `planning/90-ui-ux/`
- `planning/15-ecosystem-research/`
- `planning/manifests/`
- `openspec/changes/agents-c14-multiagent-ui-patterns/`

## Forbidden Shared Files

- `wagents/` unless coordinated with `agents-c05-ux-cli`
- `README.md`
- `AGENTS.md`

## Dependencies

- `agents-c10-external-repo-intake`
- `agents-c05-ux-cli`

## Expected Artifacts

- UX pattern ledger
- adoption risk notes
- dashboard abstraction recommendations

## Validation Commands

- `uv run wagents openspec validate`

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

# Dispatch: agents-c12-session-telemetry

## Child OpenSpec Change

`agents-c12-session-telemetry`

## Mission

Design session replay, run graph, token/cost telemetry, and local audit-log foundations.

## Allowed Files And Directories

- `planning/80-observability/`
- `planning/70-evals/`
- `planning/manifests/`
- `openspec/changes/agents-c12-session-telemetry/`

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- generated docs

## Dependencies

- `agents-c00-repo-sync`
- `agents-c07-ci-evals-observability` coordination for CI gates

## Expected Artifacts

- telemetry schema fragments
- run graph model
- redaction and retention requirements

## Validation Commands

- `uv run wagents openspec validate`
- telemetry schema validation when implemented

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

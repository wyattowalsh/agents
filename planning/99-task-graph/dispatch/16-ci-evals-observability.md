# Dispatch: agents-c07-ci-evals-observability

## Child OpenSpec Change

`agents-c07-ci-evals-observability`

## Mission

Define CI gates, eval schemas, deterministic replay, observability, and failure remediation reporting.

## Allowed Files And Directories

- `.github/workflows/`
- `tests/`
- `planning/60-ci-cd/`
- `planning/70-evals/`
- `planning/80-observability/`
- `openspec/changes/agents-c07-ci-evals-observability/`

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- generated docs

## Dependencies

- `agents-c01-registry-core`
- `agents-c02-skills-lifecycle`
- `agents-c03-mcp-audit`

## Expected Artifacts

- CI gate matrix
- eval scenario schema
- replay fixture plan
- report/dashboard spec

## Validation Commands

- `uv run pytest`
- `uv run ruff check .`
- `make typecheck`
- `uv run wagents openspec validate`

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

# Dispatch: agents-c01-registry-core

## Child OpenSpec Change

`agents-c01-registry-core`

## Mission

Freeze canonical registry schemas and support-tier vocabulary for harnesses, skills, MCP servers, plugins/extensions, docs artifacts, and external repo evaluations.

## Allowed Files And Directories

- `planning/manifests/`
- `planning/20-harness-registry/`
- `openspec/changes/agents-c01-registry-core/`
- registry schema tests/fixtures only if implementation mode permits non-Markdown changes

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- parent tasks
- generated support matrices

## Dependencies

- `agents-c00-repo-sync` inventory for live-path classification.

## Expected Artifacts

- harness registry schema
- skill registry schema
- MCP registry schema
- plugin/extension registry schema
- docs artifact registry schema
- external repo evaluation registry schema
- support-tier manifest using `validated`, `repo-present-validation-required`, `planned-research-backed`, `experimental`, `unverified`, `unsupported`, `quarantine`

## Validation Commands

- `uv run wagents openspec validate`
- schema validation tests
- `uv run wagents validate`

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

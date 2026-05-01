# Dispatch: agents-c02-skills-lifecycle

## Child OpenSpec Change

`agents-c02-skills-lifecycle`

## Mission

Normalize local skills into the skills-first lifecycle, classify script risk, and define CLI conformance/provenance requirements.

## Allowed Files And Directories

- `skills/`
- `planning/40-skills-ecosystem/`
- `planning/manifests/`
- `openspec/changes/agents-c02-skills-lifecycle/`
- lane-specific tests/fixtures

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- `mcp.json`
- generated support matrices

## Dependencies

- `agents-c01-registry-core`
- `agents-c10-external-repo-intake` for external skill candidates

## Expected Artifacts

- skill inventory/provenance fragments
- script conformance checklist
- adoption rubric
- completed child tasks

## Validation Commands

- `uv run wagents validate`
- skill CLI conformance checks
- `uv run wagents openspec validate`

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

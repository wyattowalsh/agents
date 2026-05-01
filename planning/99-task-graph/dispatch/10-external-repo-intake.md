# Dispatch: agents-c10-external-repo-intake

## Child OpenSpec Change

`agents-c10-external-repo-intake`

## Mission

Turn the external repository evaluation manifest into an audited intake queue without installing or promoting anything.

## Allowed Files And Directories

- `planning/15-ecosystem-research/`
- `planning/manifests/`
- `openspec/changes/agents-c10-external-repo-intake/`

## Forbidden Shared Files

- `skills/`
- `mcp/`
- `mcp.json`
- `README.md`
- `AGENTS.md`

## Dependencies

- `agents-c00-repo-sync`
- `agents-c01-registry-core`

## Expected Artifacts

- external repo intake queue
- license/security/source/provenance task records
- quarantine handoff records for `agents-c15-security-quarantine`
- feature/domain coverage map that proves every repo has a destination lane
- per-repo integration strategy: integrate, wrap, clean-room borrow, reference-only, or quarantine

## Validation Commands

- `uv run wagents openspec validate`
- external repo evaluation schema validation

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Research Expansion

Start from:

- `planning/15-ecosystem-research/22-feature-domain-coverage.md`
- `planning/15-ecosystem-research/23-external-repo-coverage-backlog.md`

Do not downgrade any repo from quarantine or reference-only without pinned source, license, executable-surface, and security evidence.

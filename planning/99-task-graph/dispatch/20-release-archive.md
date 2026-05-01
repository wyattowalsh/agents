# Dispatch: agents-c09-release-archive

## Child OpenSpec Change

`agents-c09-release-archive`

## Mission

Create migration, release, rollback, post-merge validation, release-note evidence, and OpenSpec archive readiness plans after all earlier waves land.

## Allowed Files And Directories

- `planning/95-migration/`
- `openspec/changes/agents-c09-release-archive/`
- release/checklist docs and fixtures

## Forbidden Shared Files

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- parent tasks until all previous waves are consolidated

## Dependencies

- all Wave 0, Wave 1, and Wave 2 child changes

## Expected Artifacts

- phased rollout plan
- migration guide
- rollback playbook
- release checklist
- archive checklist
- release notes evidence

## Validation Commands

- `uv run wagents openspec validate`
- full relevant validation suite after consolidation

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

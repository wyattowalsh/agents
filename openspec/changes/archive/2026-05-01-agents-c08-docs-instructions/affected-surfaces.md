# Affected Surfaces: Docs And Instructions Truth

## Owned Outputs For This Lane Pass

- `planning/65-docs-and-instructions/`
- `openspec/changes/agents-c08-docs-instructions/`

## Deferred Shared Outputs

- `docs/`
- `instructions/`
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- generated support matrices

## Read-Only Inputs

- `config/docs-artifact-registry.json`
- `config/support-tier-registry.json`
- `config/harness-surface-registry.json`
- `planning/manifests/harness-fixture-support.json`
- child lane planning fragments and manifests

## Conflict Controls

- C08 planning fragments may be committed while shared docs are dirty.
- Generated docs and bridge instruction updates require an explicitly scheduled consolidation pass.
- Child lanes must not edit global docs directly when a fragment or registry can express the source truth.

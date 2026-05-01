# Dispatch: agents-c13-skill-registry-intake

## Child OpenSpec Change

`agents-c13-skill-registry-intake`

## Mission

Evaluate official and community skill registries as discovery sources and define safe intake workflows.

## Allowed Files And Directories

- `planning/40-skills-ecosystem/`
- `planning/15-ecosystem-research/`
- `planning/manifests/`
- `openspec/changes/agents-c13-skill-registry-intake/`

## Forbidden Shared Files

- `skills/`
- `README.md`
- `AGENTS.md`

## Dependencies

- `agents-c10-external-repo-intake`
- `agents-c01-registry-core`

## Expected Artifacts

- registry source evaluation
- trust and lockfile field recommendations
- candidate queue with no installations
- official vendor skill-source priority queue
- community/awesome-list discovery source queue with dedupe and trust gates

## Validation Commands

- `uv run wagents openspec validate`
- registry schema validation where applicable

## Commit Requirement

Commit only this lane's changes with a conventional commit.

## Final Response Format

Return completed scope, files changed, validation commands/results, blockers, and commit hash.

## Research Expansion

Use the skill-related records in `planning/15-ecosystem-research/23-external-repo-coverage-backlog.md` as discovery input. Treat official vendor repositories as high-priority audit candidates, not trusted installs.

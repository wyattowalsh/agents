# Affected Surfaces: External Repo Intake

## Owned Outputs

- `planning/manifests/external-repo-evaluation-final.json`
- `planning/manifests/external-repo-intake-ledger.json`
- `planning/manifests/external-repo-intake-queue.json`
- `planning/manifests/external-repo-review-tasks.json`
- `planning/manifests/external-repo-quarantine-handoff.json`
- `planning/manifests/external-repo-url-reconciliation.json`
- `planning/15-ecosystem-research/24-external-repo-intake-queue.md`
- `planning/15-ecosystem-research/25-external-repo-url-reconciliation.md`
- `openspec/changes/agents-c10-external-repo-intake/`

## Read-Only Inputs

- `agents-overhaul-planning/planning/manifests/external-repo-evaluation-final.json`
- `planning/manifests/external-repo-evaluation-summary.json`
- `planning/15-ecosystem-research/22-feature-domain-coverage.md`
- `planning/15-ecosystem-research/23-external-repo-coverage-backlog.md`
- `planning/manifests/security-quarantine-register.json`

## Explicit Non-Targets

- `skills/`
- `mcp/`
- `mcp.json`
- `README.md`
- `AGENTS.md`
- parent OpenSpec task files
- generated support matrices
- external repository checkouts, installers, or vendored assets

## Conflict Controls

- Intake manifests are discovery and review artifacts only.
- C10 records quarantine handoffs for C15 but does not mutate C15 policy or quarantine registers.
- C10 records downstream lane routing but does not promote support tiers or install commands.

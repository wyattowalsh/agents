# Planning Corpus

This directory uses progressive disclosure:

- `00-overview/` explains the change set and sequencing.
- `10-architecture/` defines target contracts and decision rules.
- `15-ecosystem-research/` stores source-backed ingredients.
- `20-harness-registry/` documents harness-specific support and constraints.
- `30-adapters/` defines projection/adaptation layers.
- `40-skills-ecosystem/` defines the skills-first operating model.
- `50-config-safety/` defines transactional config, rollback, secrets, sandboxing, and supply-chain controls.
- `60-ci-cd/` defines conformance gates.
- `70-evals/` defines evaluation and deterministic replay strategy.
- `80-observability/` defines run telemetry and cost accounting.
- `90-ui-ux/` defines simplified user flows and dashboard abstractions.
- `95-migration/` defines implementation rollout.
- `99-task-graph/` contains machine-readable and human-readable subagent tasks.

Each planning doc should include objectives, non-goals, constraints, interfaces/contracts, risks, acceptance criteria, metrics, and open questions when applicable.

## Maximal refactor additions

This bundle adds deeper progressive disclosure docs and new source-of-truth manifests:

- `00-overview/07-progressive-disclosure-map.md`
- `00-overview/08-assumption-and-drift-ledger.md`
- `10-architecture/10.12-harness-projection-model.md`
- `10-architecture/10.13-canonical-manifest-contracts.md`
- `10-architecture/10.14-ephemeral-install-policy.md`
- `10-architecture/10.15-idempotent-cli-interface.md`
- `15-ecosystem-research/harness-specific/*`
- `35-mcp-audit/*`
- `45-plugin-ecosystem/*`
- `65-docs-and-instructions/*`
- expanded `planning/manifests/*`
- expanded `99-task-graph/*`

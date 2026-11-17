# CI / Evals / Observability Delta

## MODIFIED Requirements

### Requirement: Conformance gates

The CI/evals/observability lane SHALL define validation gates for registries,
skills, MCP smoke fixtures, adapter fixtures, docs truth, AI instructions,
OpenSpec changes, package artifacts, workflow linting, and repo-owned
agent-stack projections.

#### Scenario: CI checks only repo-owned agent-stack projections

- **WHEN** CI validates agent-stack projection drift
- **THEN** it SHALL run `uv run python scripts/sync_agent_stack.py --check --targets repo`
- **AND** it SHALL NOT inspect or require user-home harness config.

#### Scenario: Workflow linting installs actionlint before analysis

- **WHEN** CI validates GitHub Actions workflow files
- **THEN** it SHALL have one workflow-lint job path that installs pinned `actionlint`
- **AND** it SHALL run `make ci-check` after `actionlint` is available.

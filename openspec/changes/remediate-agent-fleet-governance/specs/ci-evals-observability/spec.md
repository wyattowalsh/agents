# CI Evals Observability Delta

## ADDED Requirements

### Requirement: Maintainer agents have structural eval manifests

The repository SHALL ship structural `evals/agents/<name>/evals.json` manifests for maintainer-focused agents without requiring live LLM eval execution in this change.

#### Scenario: Priority maintainer agents have eval directories

- **GIVEN** the maintainer agent set includes triage, policy audit, MCP mapping, bridge parity, and agent-lifecycle helpers
- **WHEN** `tests/test_agent_eval_manifests.py` runs
- **THEN** `evals/agents/` SHALL contain manifests for each priority maintainer agent enumerated by the test
- **AND** each manifest SHALL include `agent_name` and at least one eval with `id`, `prompt`, `expected_output`, and `assertions`.

#### Scenario: Manifest shape is validated structurally

- **GIVEN** an `evals/agents/<name>/evals.json` file exists
- **WHEN** structural validation runs
- **THEN** `agent_name` SHALL match the directory name
- **AND** every eval entry SHALL include the required structural fields enforced by `tests/test_agent_eval_manifests.py`.

### Requirement: Agent eval runner documents pytest gate for manifest changes

The `agent-eval-runner` maintainer agent SHALL document running `tests/test_agent_eval_manifests.py` when agent eval manifests change.

#### Scenario: Eval runner workflow lists manifest pytest gate

- **GIVEN** `agents/agent-eval-runner.md` describes structural eval gates
- **WHEN** a maintainer follows the agent-eval-runner workflow for agent-scoped validation
- **THEN** the workflow SHALL include `uv run pytest tests/test_agent_eval_manifests.py -q` when `evals/agents/` manifests change
- **AND** the agent SHALL remain bounded to structural gates without live `wagents skills sync --apply` unless explicitly approved.
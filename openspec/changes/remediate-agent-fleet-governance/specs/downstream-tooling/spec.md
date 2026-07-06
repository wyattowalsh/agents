# Downstream Tooling Delta

## ADDED Requirements

### Requirement: OpenCode task permissions materialize from delegation policy

The repository SHALL provide `scripts/materialize_opencode_task_permissions.py` to apply `config/agent-delegation-policy.json` task allowlists into `config/opencode-agents.json` without hand-editing overlay task blocks.

#### Scenario: Materialize script updates task blocks deterministically

- **GIVEN** `config/agent-delegation-policy.json` and `config/opencode-agents.json` are present
- **WHEN** a maintainer runs `uv run python scripts/materialize_opencode_task_permissions.py --apply`
- **THEN** delegator agents in the overlay SHALL receive `permission.task` maps derived from policy
- **AND** `tests/test_materialize_opencode_task_permissions.py` SHALL verify the apply path.

#### Scenario: Missing delegator fails closed

- **GIVEN** policy references a delegator name absent from `config/opencode-agents.json`
- **WHEN** materialization runs
- **THEN** the script SHALL raise a clear error instead of silently skipping the delegator.

### Requirement: OpenCode sync chains materialization before projection

Repo-managed OpenCode agent regeneration SHALL materialize delegation policy before syncing portable agent bodies into `.opencode/agents/`.

#### Scenario: just sync-opencode runs materialize first

- **GIVEN** the `just sync-opencode` recipe in the repository justfile
- **WHEN** a maintainer regenerates OpenCode agents
- **THEN** the recipe SHALL run `scripts/materialize_opencode_task_permissions.py --apply` before `scripts/sync_agent_stack.py --apply --targets repo --platforms opencode`
- **AND** maintainer docs SHALL instruct running `just sync-opencode` after `apm compile -t opencode` so portable projections do not overwrite schema-valid OpenCode frontmatter.
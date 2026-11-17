# Agent Assets Delta

## ADDED Requirements

### Requirement: OpenCode task delegation policy is machine-readable SSOT

The repository SHALL treat `config/agent-delegation-policy.json` as the single source of truth for OpenCode `permission.task` allowlists on delegator agents, materialized into `config/opencode-agents.json` by `scripts/materialize_opencode_task_permissions.py`.

#### Scenario: Orchestrator delegation deny-by-default with deny_self

- **GIVEN** `config/agent-delegation-policy.json` defines delegator `orchestrator`
- **WHEN** task permissions are materialized into `config/opencode-agents.json`
- **THEN** `permission.task["*"]` SHALL be `deny` for `orchestrator`
- **AND** `orchestrator` SHALL NOT be present in its own allowlist when `deny_self` is true
- **AND** `tests/test_agent_delegation_policy.py` SHALL enforce parity between policy and overlay.

#### Scenario: Triage-lead routing targets match portable contract

- **GIVEN** `agents/triage-lead.md` documents routing specialists
- **WHEN** `triage-lead` task allowlists are materialized from policy
- **THEN** allowed task targets SHALL include routing specialists plus documented core fallback agents
- **AND** `triage-lead` SHALL NOT delegate to itself when `deny_self` is true.

### Requirement: Read-only reviewer agents use plan permission mode

Portable reviewer agents that audit without mutating repository state SHALL declare `permissionMode: plan` in `agents/*.md` in addition to harness-specific read-only overlays.

#### Scenario: Code and security reviewers are plan-mode auditors

- **GIVEN** `agents/code-reviewer.md` and `agents/security-auditor.md` are read-only reviewers
- **WHEN** portable agent frontmatter is validated
- **THEN** both agents SHALL set `permissionMode: plan`
- **AND** OpenCode overlays SHALL keep `edit: deny` and other least-privilege rules intact.

### Requirement: Harness projection matrix is documented for maintainers

The repository SHALL document which harness surfaces project the full portable agent corpus versus intentional subsets.

#### Scenario: Maintainer README explains Claude core-eight subset

- **GIVEN** portable SSOT defines twenty agents under `agents/*.md`
- **WHEN** a maintainer reads `agents/README.md`
- **THEN** the harness projection matrix SHALL list OpenCode, Cursor, Copilot, and Claude Code counts and sources
- **AND** Claude Code SHALL be documented as an eight-agent core subset while maintainer agents remain in portable and non-Claude projections.
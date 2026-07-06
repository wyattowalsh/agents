# Tasks

- [x] Add `config/agent-delegation-policy.json` + schema.
- [x] Extend OpenCode `orchestrator` and `triage-lead` `task` allowlists from policy SSOT.
- [x] Add `tests/test_agent_delegation_policy.py`.
- [x] Set `permissionMode: plan` on `code-reviewer` and `security-auditor`.
- [x] Document harness projection matrix in `agents/README.md`.
- [x] Scaffold `evals/agents/{triage-lead,permission-policy-auditor,mcp-capability-mapper,bridge-consistency-checker,skill-author,prompt-optimizer}/evals.json`.
- [x] Add `tests/test_agent_eval_manifests.py`.
- [x] Add MCP OpenSpec mapper workflow template under `openspec/schemas/mcp-server-change-tasks.md`.
- [x] Revert accidental `harness-reconciliation.json` churn for this wave.
- [x] Run `just sync-opencode`, `wagents validate` (agent surfaces), and targeted pytest.
- [x] Add `scripts/materialize_opencode_task_permissions.py` + `just materialize-opencode-tasks`.
- [x] Set `permissionMode: plan` on `planner` and `researcher`.
- [x] Scaffold remaining six `evals/agents/*` manifests; wire `agent-eval-runner` pytest gate.
- [x] Run `wagents docs generate --no-installed` for agent doc pages.
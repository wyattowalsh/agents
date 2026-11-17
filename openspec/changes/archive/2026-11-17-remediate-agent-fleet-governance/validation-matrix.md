# Validation matrix

| Check | Command | Expect |
| ----- | ------- | ------ |
| Delegation policy tests | `uv run pytest tests/test_agent_delegation_policy.py -q` | pass |
| Agent eval manifests | `uv run pytest tests/test_agent_eval_manifests.py -q` | pass |
| OpenCode overlay contract | `uv run pytest tests/test_harness_plan_fixtures.py::test_opencode_agents_on_disk_contract -q` | pass |
| Copilot + orchestrator handoff | `uv run pytest tests/test_copilot_agents.py tests/test_orchestrator_uncertainty_handoff.py -q` | pass |
| OpenCode sync parity | `uv run python scripts/sync_agent_stack.py --check --targets repo --platforms opencode` | exit 0 |
| OpenCode regen | `just sync-opencode` | updates `.opencode/agents/` task blocks |
| Portable validate | `uv run wagents validate` | pass or only unrelated MCP drift outside this change |
| OpenSpec strict | `npx @fission-ai/openspec@latest validate remediate-agent-fleet-governance --strict` | exit 0 |
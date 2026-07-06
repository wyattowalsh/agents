# Proposal: Remediate agent fleet governance

## Problem

The agents review (RV-A-001–RV-A-006) found OpenCode task delegation gaps, missing
`permissionMode: plan` on read-only reviewers, undocumented Claude subset policy,
missing maintainer agent eval scaffolds, absent MCP mapper workflow gates, and
accidental harness-reconciliation manifest churn mixed with unrelated MCP work.

## Intent

Restore portable ↔ OpenCode delegation parity, tighten read-only reviewer posture,
document harness projections, scaffold structural agent evals, and isolate
reconciliation manifest updates from agent/MCP feature commits.

## Out of scope

- Expanding `.claude/agents/` to the full 20-agent corpus (document-only default).
- Live LLM behavioral eval execution.
- MCP server installs (scrapling/jupyter) in the same commit wave.

## Success criteria

- `config/agent-delegation-policy.json` is SSOT for OpenCode `task` allowlists.
- `tests/test_agent_delegation_policy.py` and `tests/test_agent_eval_manifests.py` pass.
- `agents/README.md` documents harness projection matrix.
- MCP OpenSpec changes include `mcp-capability-mapper` workflow step.
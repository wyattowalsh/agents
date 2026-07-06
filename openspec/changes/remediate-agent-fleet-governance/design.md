# Design: Agent fleet governance remediation

## Delegation SSOT

`config/agent-delegation-policy.json` owns OpenCode `permission.task` allowlists for
`orchestrator` and `triage-lead`. Materialization updates `config/opencode-agents.json`;
`tests/test_agent_delegation_policy.py` enforces parity.

Policies:

- Default `task["*"] = deny`.
- `deny_self: true` blocks `orchestrator→orchestrator` and `triage-lead→triage-lead`.
- `orchestrator` may delegate to all portable agents except itself, plus `general`/`explore`.
- `triage-lead` may delegate to routing targets in `agents/triage-lead.md` plus core fallback specialists.

## Read-only reviewers

`code-reviewer` and `security-auditor` use portable `permissionMode: plan` in addition to
read-only tool allowlists and harness overlays (`edit: deny`, Copilot `disallowedTools`).

## Harness projections

| Harness | Policy |
| ------- | ------ |
| OpenCode/Cursor/Copilot | Full 20-agent portable corpus |
| Claude Code | Core 8 subset documented in `agents/README.md` |

## Agent evals

Structural manifests live under `evals/agents/<name>/evals.json` with `agent_name` and
explicit/routing/negative cases. No live LLM eval in this change.

## Reconciliation manifest

`planning/manifests/harness-reconciliation.json` churn is reverted in this wave when tied
to unrelated inventory experiments; regen belongs in a dedicated inventory commit.
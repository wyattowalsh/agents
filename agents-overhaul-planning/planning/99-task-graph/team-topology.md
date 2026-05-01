# Parallel Team Topology

## Teams

| Team | Scope |
|---|---|
| Platform Core | repo inventory, registry schemas, adapters, transaction engine |
| OpenSpec Governance | active changes, spec/task alignment, archive flow |
| Skills Team | local/external skill packaging, lifecycle, tests |
| MCP Team | MCP inventory, curation, security, smoke tests |
| Harness Teams | one or more teams per harness family |
| UX/CLI Team | doctor/catalog/sync/rollback/dashboard flows |
| Security Team | supply chain, sandboxing, policy, threat model |
| CI/Evals Team | conformance, evals, golden fixtures |
| Docs/AI Instructions Team | README, docs, AGENTS/CLAUDE/GEMINI/Copilot/rules |
| Observability Team | telemetry, audit log, run graph, cost accounting |
| Release Team | migration, changelog, rollback, OpenSpec archive |

## Load balancing

- Claude/Copilot/OpenCode/Cursor/Gemini are large enough for separate harness teams.
- ChatGPT/Codex can share a team because both depend on OpenAI docs and OpenAPI/AGENTS patterns.
- Antigravity/Perplexity/Cherry should share an experimental team until contracts are validated.
- Docs tasks should be embedded with each team but final generation belongs to Docs/AI Instructions.

## Merge-conflict minimization

- Freeze schemas before harness projection work.
- Give each harness team isolated fixture/doc paths.
- Keep generated docs behind a single docs-generation PR after manifest changes land.
- Avoid multiple teams editing README/AGENTS.md directly; use fragments or manifest-driven generation.

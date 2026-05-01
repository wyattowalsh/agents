# MCP Index Ingredient Ledger

## Objective

Treat MCP indexes as discovery sources, not authority.

## Index sources

| Source | Role | Trust posture | Notes |
|---|---|---|---|
| Official MCP Registry | canonical metadata registry | Preview, not GA | Breaking changes/data resets possible; namespace verification and `server.json` metadata |
| PulseMCP | large ecosystem directory | Community signal | Useful for trend/usage estimates and categories |
| MCP.Directory | category directory | Community signal | Good category breakdown across browser, DB, search, devtools, cloud, security |
| Glama MCP list | ecosystem directory | Community signal | Use as candidate source only |
| MCP.so | ecosystem directory | Community signal | Use as candidate source only |
| Awesome MCP lists | curated/automated lists | Community signal | Need direct repo verification |

## Promotion gates for any MCP candidate

1. Direct upstream source URL reviewed.
2. License identified.
3. Install command is pin-capable and portable.
4. Transport identified: `stdio`, `streamable-http`, `sse`, or unknown.
5. Auth model identified: env, OAuth, API key, helper app, none, unknown.
6. `dynamic_state_required=true` or else classify as skill replacement.
7. `mcp-scan` static scan passes or exception documented.
8. Tool descriptions are pinned/hashes recorded where feasible.
9. No unchecked absolute local paths in validated profile.
10. Human docs explain risks and alternatives.

## High-signal categories to harvest

- Browser/runtime: Playwright MCP, Chrome DevTools MCP.
- Docs/search: Context7, OpenAI Docs MCP, AWS docs MCP, Perplexity MCP, Tavily/Exa/Brave.
- Dev platforms: GitHub MCP, GitLab, Jira/Linear.
- Databases: Postgres, SQLite/DuckDB, Qdrant, Neo4j.
- Cloud/infra: Kubernetes, Terraform, AWS/Azure/GCP docs and resource views.
- Observability: Grafana, Sentry, Langfuse/Phoenix-adjacent if available.
- Security: mcp-scan, policy guardrails, secret scanners.

## Replacement-by-skill signal

An MCP is a skill replacement candidate when:

- it only provides static prompts/checklists;
- it shells out to local scripts without live state;
- it duplicates repo-local docs;
- it exists only to perform deterministic transforms;
- it adds server/runtime complexity without external data.

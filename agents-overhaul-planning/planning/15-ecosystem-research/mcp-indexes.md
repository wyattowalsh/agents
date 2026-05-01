---
status: planning
tier: secondary
owner: mcp-curation-team
last_updated: 2026-05-01
---

# MCP Indexes and Live-Systems Curation

## Objective

Use MCP indexes to discover live-systems integrations, then promote only those with authoritative upstream docs, clear security posture, and conformance tests.

## Index roles

| Index | Role | Promotion caveat |
|---|---|---|
| Glama MCP directory | Breadth discovery, categories, hosted/scan signals | Treat as discovery and operational signal, not support authority. |
| PulseMCP | Popularity/trending signal and ecosystem coverage | Verify upstream repo and docs before promotion. |
| MCP.so | Broad marketplace cross-check | Do not import metadata blindly. |
| Awesome MCP lists | Gap discovery and watchlist input | Community curation is useful but insufficient for support. |

## MCP categories worth retaining

| Category | Why skill is insufficient | Candidate examples |
|---|---|---|
| Browser/runtime automation | Needs live DOM/network/performance state | Chrome DevTools MCP, Playwright MCP |
| Current docs retrieval | Versioned docs change continuously | Context7, OpenAI Docs MCP |
| Research/search | Needs live web/API state | Perplexity MCP, Firecrawl MCP |
| SaaS work management | Authenticated workspace state | Linear, Notion, Atlassian Rovo |
| Observability | Production telemetry and incidents | Sentry, Langfuse/Phoenix-style backends |
| Cloud/infra | Live cloud/K8s/Terraform state | Only with scoped auth, sandboxing, and explicit approvals |
| Databases/vector stores | Live query state | Only with read-only defaults and non-production credentials |

## MCP replacement rule

If an MCP server only wraps static instructions, templates, local scripts, or deterministic CLI workflows, replace it with an Agent Skill or harness-native plugin.

## Preferred install pattern

- Prefer `npx -y <package>` for Node MCP servers when documented by upstream.
- Prefer `uvx <package>` for Python MCP servers when documented by upstream.
- Prefer remote streamable HTTP only when auth, transport, and audience validation are clear.
- Pin versions in lock metadata even when using ephemeral install commands.

## MCP promotion checklist

- Upstream docs URL exists.
- License is compatible.
- Install command is deterministic or version-pinnable.
- Transport is declared: stdio, streamable HTTP, SSE/backcompat, or other.
- Auth model is declared.
- Secrets are not embedded in rendered configs.
- Smoke test can run in CI or is explicitly marked manual.
- Support tier and risk notes are generated into docs.

## Watchlist-to-supported workflow

1. Add to `planning/manifests/mcp-evaluation-matrix.csv` as watchlist.
2. Create OpenSpec change if promotion is intended.
3. Add config renderer fixture.
4. Add clean-room install/smoke test.
5. Generate docs and warnings.
6. Promote only after CI passes and owner review.

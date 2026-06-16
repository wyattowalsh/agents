---
skill: fastmcp-client-cli
source_type: curated-external
researched_at: '2026-06-16T08:43:06Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Query and invoke tools on MCP servers using fastmcp list and fastmcp call. Authoritative FastMCP maintainer skill for discovering and calling MCP tools from CLI.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Authoritative FastMCP maintainer skills. `fastmcp-client-cli` invokes MCP tool calls; review scripts before promotion.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Web-augmented from upstream SKILL.md + config/external-skills.md (fetched 2026-06-16).

## Install Prerequisites

Install: `npx skills add jlowin/fastmcp --skill fastmcp-client-cli --skill testing-python -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[jlowin/fastmcp](https://github.com/jlowin/fastmcp)

## Comparable Alternatives

General purpose agent skills in similar domain (see catalog for alternatives); e.g. other SQL or UI or infra skills.

> Web-augmented from public upstream SKILL.md (github raw fetches) and curated config/external-skills.md; use external-skill-auditor for live evidence and script/hook audit. Not an endorsement. Confidence 0.75 derived from metadata alignment + source inspection depth.

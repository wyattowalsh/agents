---
skill: apollo-mcp-server
source_type: curated-external
researched_at: '2026-06-16T08:37:29Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

Apollo MCP Server — connect AI agents with GraphQL APIs. Config (endpoints/schemas/headers), built-in tools (introspect/search/validate/execute), operation sources, auth/security, health/debug. Bridge for agent <-> GraphQL.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode (via npx --skill or Claude /plugin, gh skill, etc.).

## Trust And Risks

inspect-then-install / needs-inspection for apollo-ios (Swift platform/client specifics), apollo-mcp-server (AI-to-GraphQL bridge, config/auth), apollo-router (supergraph runtime, plugins/telemetry). Same org/repo otherwise; platform or operational scope leads to catalog inspection flag. Review generated connectors, schemas, or server code before applying to prod.

## Install Prerequisites

`npx skills add apollographql/skills --skill apollo-mcp-server -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`. status=inspect-then-install; selector=named. Alternative: Claude plugin marketplace or gh skill install.

## Upstream Maintainer

apollographql (Apollo GraphQL org, github.com/apollographql/skills). MIT license. 11 skills total with SKILL.md + references/. Install via npx skills add, Claude Code plugin (namespaced), GitHub CLI gh skill (with pinning support), or direct. Experimental/reference project per disclaimer; community feedback welcome but not officially supported like core Apollo repos. Links to official Apollo docs (Client/Server/Federation/Connectors/Rover/iOS/MCP).

## Comparable Alternatives

Other MCP or agent-tooling skills; apollo-router for runtime.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.

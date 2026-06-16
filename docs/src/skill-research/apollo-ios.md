---
skill: apollo-ios
source_type: curated-external
researched_at: '2026-06-16T08:37:29Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

Apollo iOS: strongly-typed GraphQL client for Swift (iOS/macOS etc). SPM/Xcode setup, codegen config, ApolloClient + auth/interceptors/cache, async/await queries, normalized cache, subscriptions, testing with mocks. Platform-specific.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode (via npx --skill or Claude /plugin, gh skill, etc.).

## Trust And Risks

inspect-then-install / needs-inspection for apollo-ios (Swift platform/client specifics), apollo-mcp-server (AI-to-GraphQL bridge, config/auth), apollo-router (supergraph runtime, plugins/telemetry). Same org/repo otherwise; platform or operational scope leads to catalog inspection flag. Review generated connectors, schemas, or server code before applying to prod.

## Install Prerequisites

`npx skills add apollographql/skills --skill apollo-ios -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`. status=inspect-then-install; selector=named. Alternative: Claude plugin marketplace or gh skill install.

## Upstream Maintainer

apollographql (Apollo GraphQL org, github.com/apollographql/skills). MIT license. 11 skills total with SKILL.md + references/. Install via npx skills add, Claude Code plugin (namespaced), GitHub CLI gh skill (with pinning support), or direct. Experimental/reference project per disclaimer; community feedback welcome but not officially supported like core Apollo repos. Links to official Apollo docs (Client/Server/Federation/Connectors/Rover/iOS/MCP).

## Comparable Alternatives

apollo-kotlin (same source); native Swift/GraphQL or other mobile client skills.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.

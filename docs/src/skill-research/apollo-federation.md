---
skill: apollo-federation
source_type: curated-external
researched_at: '2026-06-16T08:37:29Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Apollo Federation subgraph schemas: entities (@key), sharing (@shareable), cross-subgraph resolvers, federation directives (@external etc), composition troubleshooting. For authoring subgraphs in federated supergraphs.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode (via npx --skill or Claude /plugin, gh skill, etc.).

## Trust And Risks

Curated install-now-after-trust-gate / curated-trust-gated for core server/client/federation/ops. MIT. Official org. Experimental status and reference-only disclaimer noted. Detailed per-skill references/ folders provide transparency. npx provenance verified. Inspect any MCP/router setup for auth surface and connectivity.

## Install Prerequisites

`npx skills add apollographql/skills --skill apollo-federation -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`. status=install-now-after-trust-gate; selector=named. Alternative: Claude plugin marketplace or gh skill install.

## Upstream Maintainer

apollographql (Apollo GraphQL org, github.com/apollographql/skills). MIT license. 11 skills total with SKILL.md + references/. Install via npx skills add, Claude Code plugin (namespaced), GitHub CLI gh skill (with pinning support), or direct. Experimental/reference project per disclaimer; community feedback welcome but not officially supported like core Apollo repos. Links to official Apollo docs (Client/Server/Federation/Connectors/Rover/iOS/MCP).

## Comparable Alternatives

graphql-schema, apollo-server, rover (same source); other federation/subgraph patterns.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.

---
skill: nx-generate
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.78
---

## Purpose

Nx AI agent skill for intelligent code generation and scaffolding that respects existing Nx workspace patterns, tags, project graph, and tooling. Part of official nrwl/nx-ai-agents-config for monorepo-aware assistance.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command. Web-aug: github.com/nrwl/nx-ai-agents-config (MIT, ~24 stars, active Nx team, docs on nx.dev/blog). Focuses on workspace understanding + self-healing CI. Install via nx configure-ai-agents or direct npx. Skills complement Nx Console/mcp.

## Install Prerequisites

Install: `npx skills add nrwl/nx-ai-agents-config --skill nx-generate --skill link-workspace-packages -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[nrwl/nx-ai-agents-config](https://github.com/nrwl/nx-ai-agents-config) (Nx team, MIT)

## Comparable Alternatives

Nx Console, local nx workspace generators, other monorepo skills (e.g. turbo/pnpm).

> Web from nx.dev + github 2026.

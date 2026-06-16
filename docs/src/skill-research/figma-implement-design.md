---
skill: figma-implement-design
source_type: curated-external
researched_at: '2026-06-16T08:35:57Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Figma skill for implementing designs from Figma into production code. Guides agent through using Figma context/MCP to translate designs to components, respecting design tokens, variants, and system rules. Part of Figma MCP + skills suite.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Figma; read-heavy but depends on MCP server access which can expose file contents and team data; inspect for workspace data sensitivity.

## Install Prerequisites

Install: `npx skills add figma/mcp-server-guide --skill figma-code-connect --skill figma-generate-design --skill figma-implement-design -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named (inferred); policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[figma/mcp-server-guide](https://github.com/figma/mcp-server-guide) (official Figma)

## Comparable Alternatives

Other implement-from-design or screenshot-to-code skills; component library implementation skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

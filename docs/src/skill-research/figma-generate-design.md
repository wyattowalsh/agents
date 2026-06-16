---
skill: figma-generate-design
source_type: curated-external
researched_at: '2026-06-16T08:35:57Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Figma skill to generate designs in Figma from code, existing components/variables, or natural language using Figma MCP tools and skills. Supports creating/editing assets aligned to design system. Complements Code Connect for round-tripping design <-> code.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Figma; write access to Figma files via MCP can mutate design files - security and governance review advised for shared/team files.

## Install Prerequisites

Install: `npx skills add figma/mcp-server-guide --skill figma-code-connect --skill figma-generate-design --skill figma-implement-design -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named (inferred); policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[figma/mcp-server-guide](https://github.com/figma/mcp-server-guide) (official Figma)

## Comparable Alternatives

Diagram/diagram-gen or other design tool skills (Excalidraw etc); code-to-design reverse skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

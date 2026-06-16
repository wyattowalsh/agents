---
skill: figma-code-connect
source_type: curated-external
researched_at: '2026-06-16T08:35:57Z'
research_tier: standard
mean_confidence: 0.77
---

## Purpose

Official Figma skill for connecting published Figma design components to matching code implementations using Figma Code Connect. Enables design-system sync, prop mapping, and codegen from Figma to repos. Requires team library publish and appropriate Figma plan.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Figma (design platform leader); repo figma/mcp-server-guide; ties to MCP server for live canvas/design access - MCP surface and Figma account integration warrant inspection for data access and plan requirements despite high provenance.

## Install Prerequisites

Install: `npx skills add figma/mcp-server-guide --skill figma-code-connect --skill figma-generate-design --skill figma-implement-design -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named (inferred from batch); policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[figma/mcp-server-guide](https://github.com/figma/mcp-server-guide) (official Figma)

## Comparable Alternatives

Other design-to-code or Code Connect skills; Storybook or component explorer skills; general MCP design tools.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

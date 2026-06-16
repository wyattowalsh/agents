---
skill: figma-code-connect
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Official Figma MCP design-to-code skills. Requires Figma MCP token; prefer this source over overlapping `openai/skills` Figma variants.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Official Figma MCP design-to-code skills. Requires Figma MCP token; prefer this source over overlapping `openai/skills` Figma variants.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add figma/mcp-server-guide --skill figma-implement-design --skill figma-generate-design --skill figma-code-connect -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[figma/mcp-server-guide](https://github.com/figma/mcp-server-guide)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

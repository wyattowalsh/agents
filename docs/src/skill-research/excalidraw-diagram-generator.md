---
skill: excalidraw-diagram-generator
source_type: curated-external
researched_at: '2026-06-16T08:38:00Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

awesome-copilot / community skill (multiple origins) to generate editable Excalidraw diagrams (.excalidraw JSON) from natural language descriptions or codebase analysis. Supports flowcharts, ERDs, architecture, sequence, mindmaps, swimlanes etc. with layout and styling guidance. Often paired with Excalidraw MCP servers for live canvas.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; GitHub curated + community forks (coleam00, ooiyeefei etc) and excalidraw/excalidraw-mcp; output is diagrams (safe); MCP variants add live canvas write surface - inspect MCP trust if using integrated server. Evidence from awesome-copilot, excalidraw repos, blogs.

## Install Prerequisites

Install: `npx skills add github/awesome-copilot --skill excalidraw-diagram-generator` or community variants; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[github/awesome-copilot](https://github.com/github/awesome-copilot) and community (e.g. excalidraw org, coleam00)

## Comparable Alternatives

Mermaid diagram skills, draw.io / plantuml skills; architecture doc skills; `figma-generate-design` for design-tool diagrams.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

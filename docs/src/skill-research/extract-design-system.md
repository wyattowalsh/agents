---
skill: extract-design-system
source_type: curated-external
researched_at: '2026-06-16T08:38:31Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Extract design tokens (colors, typography, spacing, border radius, shadows) from any public website. Reverse-engineers visual primitives and generates starter W3C-compatible `tokens.json` + `tokens.css` (CSS custom props) for local projects. Available as focused AI agent skill (for Claude/Cursor/Codex etc) and standalone npm CLI + MCP server exposing extract/init/get tools. Workflow: confirm public site, run extraction (Playwright), normalize, summarize findings, emit starter files under design-system/ and .extract-design-system/. Not a full component lib or auto-rewriter; for initialization and repeatable extraction before broader styling work. MIT.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Install: `npx skills add ...` (symlink/copy, project/global). Also MCP for Cursor/Claude Desktop; per-agent .cursor/skills or plugin patterns. Skill activates on matching extraction prompts.

## Trust And Risks

Curated install-now-after-trust-gate / curated-trust-gated. MIT licensed, small but complete project (63 stars) with tests/CI, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY.md. Maintainer arvindrk. Bundled CLI + skill instructions emphasize scope/limits (public sites only; single-page; starter tokens; dynamic sites may be incomplete) and security (untrusted third-party sites may influence output; review generated tokens before treating as authoritative; ask confirmation before modifying existing code/styles/config; use only public sites you are comfortable fetching). Node 20+, Playwright chromium required for full run. Experimental in nature as a specialized extraction tool. npx provenance verified.

## Install Prerequisites

`npx skills add arvindrk/extract-design-system --skill extract-design-system -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`

status=install-now-after-trust-gate; selector=named (or source-spec). Requires npm + optional `npx playwright install chromium`. Also publishes MCP server (`extract-design-system-mcp`) for direct tool use in supported hosts. Config supports global/project install.

## Upstream Maintainer

arvindrk (github.com/arvindrk/extract-design-system). MIT. Skills-first design with references/ for workflow. npm package `extract-design-system`. GitHub Sponsors for support. Related topics: design-tokens, design-system, ui-audit, brand-audit, mcp, agent-skills. Has release tags.

## Comparable Alternatives

Same-ecosystem design skills (e.g. design-taste-frontend, web-design-guidelines from antfu, baseline-ui); manual token extraction or design system audits; other CLI token extractors or Figma/brand kit importers; general design-md or ui-audit skills without web fetch.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.

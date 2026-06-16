---
skill: react:components
source_type: curated-external
researched_at: '2026-06-16T08:43:06Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Converts Stitch designs into modular Vite and React components using system-level networking and AST-based validation.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Google Stitch design pipeline. Requires Stitch MCP auth and network calls to Google services; pin commit after audit.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Web-augmented from upstream SKILL.md + config/external-skills.md (fetched 2026-06-16).

## Install Prerequisites

Install: `npx skills add google-labs-code/stitch-skills --skill design-md --skill react:components --skill stitch-loop --skill stitch::generate-design -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[google-labs-code/stitch-skills](https://github.com/google-labs-code/stitch-skills)

## Comparable Alternatives

Other UI/design skills like `baseline-ui`; `vue-best-practices` for framework specific.

> Web-augmented from public upstream SKILL.md (github raw fetches) and curated config/external-skills.md; use external-skill-auditor for live evidence and script/hook audit. Not an endorsement. Confidence 0.75 derived from metadata alignment + source inspection depth.

---
skill: use-railway
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.78
---

## Purpose

Official Railway deploy/ops skill. Broad allowed-tools (railway CLI, curl, npm). Covers deploy, ops for Railway platform.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command. Web-aug: github.com/railwayapp/railway-skills (official Railway). Catalog notes: High Snyk risk reported by Skills CLI; confirm credential handling and signup/deploy flows before promoting.

## Install Prerequisites

Install: `npx skills add railwayapp/railway-skills --skill use-railway -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named. Requires railway CLI + creds.

## Upstream Maintainer

[railwayapp/railway-skills](https://github.com/railwayapp/railway-skills) (official)

## Comparable Alternatives

Netlify/Vercel/Render deploy skills; general hosting CLIs.

> Web + config notes 2026.

---
skill: render-deploy
source_type: curated-external
researched_at: '2026-06-16T08:37:54Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Deploys applications to Render cloud platform. Analyzes codebases, generates render.yaml Blueprints or uses direct creation via MCP/CLI, provides dashboard deeplinks. Evidence gathered from upstream SKILL.md, READMEs, and repo structure via web research.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command (web-audited SKILL.md + repo); risks=Requires source inspection for hooks, broad Bash tool scopes (e.g. language CLIs), credential/API usage, and deduplication with local skills before install. Low adoption for some sources; community provenance. Do not endorse without audit. policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Install Prerequisites

Install: `npx skills add render-oss/skills --skill render-deploy -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named; requires RENDER_API_KEY or MCP server config for full function; Git remote recommended for Blueprints.

## Upstream Maintainer

[render-oss/skills](https://github.com/render-oss/skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Web research of upstream repo (SKILL.md/contents); evidence only, not authority. Use external-skill-auditor for live verification before install or promotion. Not an endorsement.

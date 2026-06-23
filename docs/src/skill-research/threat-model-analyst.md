---
skill: threat-model-analyst
source_type: curated-external
researched_at: '2026-06-16T08:43:06Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Full STRIDE-A threat model analysis and incremental update skill for repositories and systems. Supports single full analysis and incremental updates with change tracking.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Web-augmented from upstream SKILL.md + config/external-skills.md (fetched 2026-06-16).

## Install Prerequisites

Install: `npx skills add github/awesome-copilot --skill eval-driven-dev --skill mcp-security-audit --skill threat-model-analyst --skill create-implementation-plan -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[github/awesome-copilot](https://github.com/github/awesome-copilot)

## Comparable Alternatives

General purpose agent skills in similar domain (see catalog for alternatives); e.g. other SQL or UI or infra skills.

> Web-augmented from public upstream SKILL.md (github raw fetches) and curated config/external-skills.md; use /review source for live evidence and script/hook audit. Not an endorsement. Confidence 0.75 derived from metadata alignment + source inspection depth.

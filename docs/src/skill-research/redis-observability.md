---
skill: redis-observability
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Key metrics (INFO), debug (SLOWLOG, MEMORY DOCTOR, FT.PROFILE), Redis Insight. From redis/agent-skills (inspect tier).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command. Web: Official Redis repo. Security/observability skills warrant extra review for ACL/metric surface.

## Install Prerequisites

Install: `npx skills add redis/agent-skills --skill redis-security --skill redis-clustering --skill redis-observability -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[redis/agent-skills](https://github.com/redis/agent-skills)

## Comparable Alternatives

General DB observability or security skills.

> Web + catalog.

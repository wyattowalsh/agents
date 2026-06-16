---
skill: redis-semantic-cache
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

LangCache — cache-aside for LLM responses, similarity threshold, per-task separation. Official Redis agent skills for AI coding agents working with Redis. Follow agentskills.io.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate (for core/vec/sem); provenance=verified-install-command. Web-aug: github.com/redis/agent-skills (MIT, official Redis, ~71 stars, TS/JS, active, includes plugins for Claude/Cursor, AGENTS.md, references). Redis surface (connections, data); official.

## Install Prerequisites

Install (core example): `npx skills add redis/agent-skills --skill redis-core -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` ; additional for vec/sem via bundle. status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

[redis/agent-skills](https://github.com/redis/agent-skills) (official redis.io, MIT)

## Comparable Alternatives

Other cache/KV skills, vector DB skills (pgvector etc).

> Web 2026 from redis/agent-skills.

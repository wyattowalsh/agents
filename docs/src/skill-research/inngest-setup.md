---
skill: inngest-setup
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Inngest durable-workflow core subset only. Route TS serverless step workflows here; keep remaining Inngest skills global-only unless explicitly requested.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Inngest durable-workflow core subset only. Route TS serverless step workflows here; keep remaining Inngest skills global-only unless explicitly requested.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add inngest/inngest-skills --skill inngest-setup --skill inngest-durable-functions --skill inngest-events --skill inngest-steps -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[inngest/inngest-skills](https://github.com/inngest/inngest-skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

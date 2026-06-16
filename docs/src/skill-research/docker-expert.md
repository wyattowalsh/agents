---
skill: docker-expert
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Install only `docker-expert` from `sickn33/antigravity-awesome-skills`. The bundle exposes hundreds of unrelated skills; keep the rest global-only.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Install only `docker-expert` from `sickn33/antigravity-awesome-skills`. The bundle exposes hundreds of unrelated skills; keep the rest global-only.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add sickn33/antigravity-awesome-skills --skill docker-expert -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

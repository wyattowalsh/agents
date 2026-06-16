---
skill: use-railway
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Official Railway deploy/ops skill with broad `allowed-tools` (`railway` CLI, `curl`, `npm`). Skills CLI reports High Snyk risk; confirm credential handling and signup/deploy flows before promoting to install-now.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Official Railway deploy/ops skill with broad `allowed-tools` (`railway` CLI, `curl`, `npm`). Skills CLI reports High Snyk risk; confirm credential handling and signup/deploy flows before promoting to install-now.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add railwayapp/railway-skills --skill use-railway -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[railwayapp/railway-skills](https://github.com/railwayapp/railway-skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

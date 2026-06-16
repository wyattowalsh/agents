---
skill: plannotator-compound
source_type: curated-external
researched_at: '2026-06-16T06:01:40Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Optional Plannotator extras (compound planning analysis, setup-goal, visual explainer). Requires the core Plannotator skills and CLI above. Do not install from the repo root (`backnotprop/plannotator`) — that path exposes maintainer-only skills (pierre-guard, release-plannotator, review-renovate, update-deps), not the user-facing extras.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; risks=Optional Plannotator extras (compound planning analysis, setup-goal, visual explainer). Requires the core Plannotator skills and CLI above. Do not install from the repo root (`backnotprop/plannotator`) — that path exposes maintainer-only skills (pierre-guard, release-plannotator, review-renovate, update-deps), not the user-facing extras.; policy=Install only after trust gate; audit again before repo promotion.; evidence=Curated `npx skills add` command with named `--skill` selectors under `install-now-after-trust-gate` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add backnotprop/plannotator/apps/skills --skill plannotator-compound --skill plannotator-setup-goal --skill plannotator-visual-explainer -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

backnotprop/plannotator/apps/skills

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

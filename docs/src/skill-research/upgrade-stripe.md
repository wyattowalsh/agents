---
skill: upgrade-stripe
source_type: curated-external
researched_at: '2026-06-16T06:01:40Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Curated third-party skill source. Run external-skill-auditor before repo promotion.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; policy=Install only after trust gate; audit again before repo promotion.; evidence=Curated `npx skills add` command with named `--skill` selectors under `install-now-after-trust-gate` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add stripe/ai --skill stripe-best-practices --skill upgrade-stripe -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

[stripe/ai](https://github.com/stripe/ai)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

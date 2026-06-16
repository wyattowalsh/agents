---
skill: systematic-debugging
source_type: curated-external
researched_at: '2026-06-16T06:01:40Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Agent workflow discipline from `obra/superpowers`. Prompt-only skills with no observed hooks or scripts in source-list output; complements local `orchestrator`, `test-architect`, and `honest-review` without duplicating them.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; risks=Agent workflow discipline from `obra/superpowers`. Prompt-only skills with no observed hooks or scripts in source-list output; complements local `orchestrator`, `test-architect`, and `honest-review` without duplicating them.; policy=Install only after trust gate; audit again before repo promotion.; evidence=Curated `npx skills add` command with named `--skill` selectors under `install-now-after-trust-gate` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add obra/superpowers --skill brainstorming --skill systematic-debugging --skill test-driven-development --skill writing-plans --skill executing-plans --skill verification-before-completion -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

[obra/superpowers](https://github.com/obra/superpowers)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

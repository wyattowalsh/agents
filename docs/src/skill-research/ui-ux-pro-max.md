---
skill: ui-ux-pro-max
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Install only `ui-ux-pro-max` from `nextlevelbuilder/ui-ux-pro-max-skill`. Keep bundled `ckm:*` skills out of the curated install set unless explicitly requested because they overlap existing local skills and introduce broader API/script surfaces.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Install only `ui-ux-pro-max` from `nextlevelbuilder/ui-ux-pro-max-skill`. Keep bundled `ckm:*` skills out of the curated install set unless explicitly requested because they overlap existing local skills and introduce broader API/script surfaces.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add nextlevelbuilder/ui-ux-pro-max-skill --skill ui-ux-pro-max -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

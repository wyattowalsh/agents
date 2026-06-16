---
skill: opencode-ensemble
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Install `opencode-ensemble` from `hueyexe/opencode-ensemble` after verifying source-list output. The repo vendors the skill at upstream tag `v0.14.2` / commit `b6bc7f706c13aa42d32e836ea647677d0b14c2f7` and keeps the OpenCode runtime plugin spec on `@latest`; refresh OpenCode's `@hueyexe` cache rather than pinning the plugin when stale.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Install `opencode-ensemble` from `hueyexe/opencode-ensemble` after verifying source-list output. The repo vendors the skill at upstream tag `v0.14.2` / commit `b6bc7f706c13aa42d32e836ea647677d0b14c2f7` and keeps the OpenCode runtime plugin spec on `@latest`; refresh OpenCode's `@hueyexe` cache rather than pinning the plugin when stale.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add hueyexe/opencode-ensemble --skill opencode-ensemble -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[hueyexe/opencode-ensemble](https://github.com/hueyexe/opencode-ensemble)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

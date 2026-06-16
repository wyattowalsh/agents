---
skill: code-review
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Sentry engineering-process skills beyond curated `skill-scanner`. `gha-security-review` analyzes GitHub Actions workflows for pwn-request patterns.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Sentry engineering-process skills beyond curated `skill-scanner`. `gha-security-review` analyzes GitHub Actions workflows for pwn-request patterns.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add getsentry/skills --skill gha-security-review --skill find-bugs --skill iterate-pr --skill code-review -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[getsentry/skills](https://github.com/getsentry/skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

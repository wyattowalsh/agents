---
skill: gha-security-review
source_type: curated-external
researched_at: '2026-06-16T08:37:12Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

Sentry skill for GitHub Actions security review: reviewing workflows for common misconfigs, secret exposure, privilege issues.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; Sentry team source; focuses on CI security which is high-value but org-specific; review fit.

## Install Prerequisites

Install: `npx skills add getsentry/skills --skill find-bugs --skill gha-security-review --skill iterate-pr --skill skill-scanner -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[getsentry/skills](https://github.com/getsentry/skills) (Sentry team)

## Comparable Alternatives

General GHA security lint or review skills; secret scanning + workflow review combos.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

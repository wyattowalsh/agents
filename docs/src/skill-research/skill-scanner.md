---
skill: skill-scanner
source_type: curated-external
researched_at: '2026-06-16T08:37:12Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Sentry skill for scanning/discovering or auditing agent skills themselves (meta); likely helps inventory or validate skills in a workspace.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; Sentry internal skill scanner; meta-tooling; low direct risk but verify scope on what it reads/writes.

## Install Prerequisites

Install: `npx skills add getsentry/skills --skill find-bugs --skill gha-security-review --skill iterate-pr --skill skill-scanner -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[getsentry/skills](https://github.com/getsentry/skills) (Sentry team)

## Comparable Alternatives

Other skill-inventory or manifest tools; meta skills for agents.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

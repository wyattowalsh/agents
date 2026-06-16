---
skill: iterate-pr
source_type: curated-external
researched_at: '2026-06-16T08:37:12Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Sentry skill for iterating on PRs: incorporating feedback, refining changes, following team PR processes.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; internal Sentry practices; may assume specific review culture or tooling.

## Install Prerequisites

Install: `npx skills add getsentry/skills --skill find-bugs --skill gha-security-review --skill iterate-pr --skill skill-scanner -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[getsentry/skills](https://github.com/getsentry/skills) (Sentry team)

## Comparable Alternatives

General PR review/iteration skills from awesome-copilot or team process skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

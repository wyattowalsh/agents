---
skill: sentry-fix-issues
source_type: curated-external
researched_at: '2026-06-16T08:36:45Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Sentry workflow skill for using AI coding assistants to debug and fix issues detected in production or PRs (error monitoring, tracing, Seer bug prediction). Part of Sentry-for-AI plugin.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Sentry org (getsentry/sentry-for-ai); requires Sentry account/project and may surface prod error data; inspect for data access policies and key handling.

## Install Prerequisites

Install: `npx skills add getsentry/sentry-for-ai --skill sentry-fix-issues --skill sentry-sdk-setup --skill sentry-setup-ai-monitoring -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[getsentry/sentry-for-ai](https://github.com/getsentry/sentry-for-ai) (official Sentry)

## Comparable Alternatives

Other error monitoring/debug or APM AI skills; general issue triaging skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

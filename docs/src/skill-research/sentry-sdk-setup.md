---
skill: sentry-sdk-setup
source_type: curated-external
researched_at: '2026-06-16T08:36:45Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Sentry SDK setup wizards across languages/frameworks. Scans project, recommends features (errors, tracing, profiling, replay, logs), guides instrumentation and config.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Sentry; involves adding SDKs, DSNs, sampling config that affect telemetry volume and privacy; inspect before broad rollout.

## Install Prerequisites

Install: `npx skills add getsentry/sentry-for-ai --skill sentry-fix-issues --skill sentry-sdk-setup --skill sentry-setup-ai-monitoring -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[getsentry/sentry-for-ai](https://github.com/getsentry/sentry-for-ai) (official Sentry)

## Comparable Alternatives

Other observability SDK setup skills (OpenTelemetry, DataDog etc).

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

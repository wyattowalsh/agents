---
skill: otel-semantic-conventions
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Vendor-neutral OpenTelemetry instrumentation, semantic conventions, and Collector pipelines. Complements Phoenix/Arize vendor-specific tracing skills; optional Dash0 backend references are not required for OTLP export.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Vendor-neutral OpenTelemetry instrumentation, semantic conventions, and Collector pipelines. Complements Phoenix/Arize vendor-specific tracing skills; optional Dash0 backend references are not required for OTLP export.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add dash0hq/agent-skills --skill otel-instrumentation --skill otel-semantic-conventions --skill otel-collector -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[dash0hq/agent-skills](https://github.com/dash0hq/agent-skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

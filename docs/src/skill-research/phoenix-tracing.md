---
skill: phoenix-tracing
source_type: curated-external
researched_at: '2026-06-16T08:38:00Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

From Arize-ai/phoenix: skill for OpenInference semantic conventions and instrumentation for tracing LLM applications (agents, RAG, chains). Enables Phoenix observability UI for traces/spans.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; Arize official; high utility for debugging agents; export config and API key handling require review.

## Install Prerequisites

Install: `npx skills add Arize-ai/phoenix --skill phoenix-tracing`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) (official Arize)

## Comparable Alternatives

`arize-instrumentation`, `sentry-setup-ai-monitoring`; OpenTelemetry / Langfuse tracing skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

---
skill: arize-instrumentation
source_type: curated-external
researched_at: '2026-06-16T08:38:00Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Arize skill for adding Arize AX / Phoenix tracing to LLM apps in two-phase agent-assisted flow: analyze codebase then implement instrumentation (LLM calls, tools, chains) across Python/TS/Java + 30+ integrations. Uses OpenInference/OpenTelemetry.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; Arize official; requires ARIZE_API_KEY / SPACE_ID; two-phase edit flow; inspect for key handling and what spans are exported.

## Install Prerequisites

Install: `npx skills add Arize-ai/arize-skills --skill arize-instrumentation`; export keys; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[Arize-ai/arize-skills](https://github.com/Arize-ai/arize-skills) (official Arize)

## Comparable Alternatives

Other tracing skills (phoenix-tracing, sentry-setup-ai-monitoring, langfuse, openinference).

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

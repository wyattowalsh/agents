---
skill: sentry-setup-ai-monitoring
source_type: curated-external
researched_at: '2026-06-16T08:36:45Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Sentry skill for setting up AI/LLM agent monitoring: instrument LLM calls, tool usage, track agents (OpenAI, Anthropic, Vercel AI SDK, LangChain etc).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Sentry; monitors AI agents (meta); sends potentially sensitive prompt/response data to Sentry - review data classification and retention policies.

## Install Prerequisites

Install: `npx skills add getsentry/sentry-for-ai --skill sentry-fix-issues --skill sentry-sdk-setup --skill sentry-setup-ai-monitoring -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[getsentry/sentry-for-ai](https://github.com/getsentry/sentry-for-ai) (official Sentry)

## Comparable Alternatives

Other LLM observability / tracing skills (LangSmith, Phoenix, Arize, Helicone).

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

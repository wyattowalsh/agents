---
skill: langfuse
source_type: curated-external
researched_at: '2026-06-16T08:41:53Z'
research_tier: standard
mean_confidence: 0.77
---

## Purpose

Official langfuse/skills (MIT, 161 stars on skills repo). Main skill for Langfuse open-source LLM eng platform: tracing, prompt mgmt, eval, datasets, scores via API. Query docs/best-practices. Requires LANGFUSE_* keys (public/secret/base). Scoped tools. Complements OpenInference skills.

## Harness Coverage

Targets: antigravity,claude-code,...opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; official from langfuse team; MIT; key-based auth (user owned); network to langfuse.com only per notes. Low broad risk.

## Install Prerequisites

npx skills add langfuse/skills --skill langfuse -y -g -a [agents]; export keys; status=install-now-after-trust-gate; selector=named.

## Upstream Maintainer

[langfuse/skills](https://github.com/langfuse/skills) (MIT, official).

## Comparable Alternatives

Other observability: phoenix, arize, langsmith skills.

> Evidence from public web sources, GitHub (official orgs 2026), curated catalog; research evidence, not authority. External audit advised.

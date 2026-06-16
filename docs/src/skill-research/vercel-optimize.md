---
skill: vercel-optimize
source_type: curated-external
researched_at: '2026-06-16T20:13:00Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Audits deployed Vercel project for cost, perf, reliability, caching, function usage, billing. Collects Vercel metrics first then drills into pointed routes/files. Finds ISR/middleware/image/build issues etc. From vercel-labs/agent-skills.

## Harness Coverage

Vercel / perf / cost optimization agents.

## Trust And Risks

trust_tier=curated-trust-gated; status=inspect-then-install (some) / gated; provenance=verified; risks=Access to project metrics/billing data via Vercel API/CLI; report generation. policy=Trust gate or inspect.; evidence=config (grouped w/ deploy) + vercel-labs/agent-skills README.

## Install Prerequisites

`npx skills add vercel-labs/agent-skills --skill vercel-optimize ...` status per config.

## Upstream Maintainer

[vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills).

## Comparable Alternatives

General perf profilers, cost tools; web-design-guidelines for UI perf aspects.

> Web evidence.

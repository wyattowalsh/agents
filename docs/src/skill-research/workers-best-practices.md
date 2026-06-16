---
skill: workers-best-practices
source_type: curated-external
researched_at: '2026-06-16T08:46:20Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

workers-best-practices encodes production rules and anti-patterns for authoring/reviewing Cloudflare Workers code: streaming responses, waitUntil usage, no global request state, no floating promises, binding access via generated types, crypto for randomness, secrets handling, observability config, and wrangler.jsonc practices. Retrieval-first; tells agents to fetch latest best-practices page and types before flagging.

## Harness Coverage

Installed with the cloudflare skills bundle; used whenever writing or reviewing Worker code, config, or CI.

## Trust And Risks

install-now-after-trust-gate / curated-trust-gated. Official guidance. Following the rules reduces common runtime, memory, security, and debuggability issues on the Workers platform. The skill itself performs no actions; risk is in the reviewed code.

## Install Prerequisites

Part of `npx skills add cloudflare/skills --skill workers-best-practices ...`

## Upstream Maintainer

Cloudflare (https://github.com/cloudflare/skills). Canonical source: https://developers.cloudflare.com/workers/best-practices/

## Comparable Alternatives

General edge function best practices from other platforms when porting patterns; project-specific linters and review checklists.

> Evidence gathered from public GitHub (raw SKILL.md). Not an endorsement or authority.

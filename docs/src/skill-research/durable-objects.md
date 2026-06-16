---
skill: durable-objects
source_type: curated-external
researched_at: '2026-06-16T08:46:20Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

durable-objects covers stateful coordination primitives on Cloudflare: per-entity Durable Objects, RPC, SQLite storage, alarms, WebSockets, hibernation. Includes wrangler config (new_sqlite_classes migrations), getByName vs newUniqueId routing, blockConcurrencyWhile for init, storage best practices, and Vitest testing patterns. Strongly retrieval-oriented toward current docs.

## Harness Coverage

Target agents listed in the cloudflare bundle install. Complements workers-best-practices and agents-sdk for stateful features.

## Trust And Risks

install-now-after-trust-gate / curated-trust-gated (part of official cloudflare/skills). Risks are those of long-lived DO instances (eviction, storage costs, concurrency model, alarm reliability). The skill emphasizes correct patterns (SQLite, one alarm per DO, persist-first) to avoid common footguns.

## Install Prerequisites

Same cloudflare/skills bundle install. Project must enable the Durable Objects binding and migration in wrangler.jsonc.

## Upstream Maintainer

Cloudflare (https://github.com/cloudflare/skills). Docs: https://developers.cloudflare.com/durable-objects/

## Comparable Alternatives

Other edge state solutions (e.g. Redis, Fauna, Supabase Realtime) or plain Workers + external DB when strong per-entity consistency at the edge is not required.

> Evidence gathered from public GitHub raw files and Cloudflare docs links in skill. Not an endorsement or authority.

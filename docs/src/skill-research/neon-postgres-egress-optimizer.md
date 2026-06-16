---
skill: neon-postgres-egress-optimizer
source_type: curated-external
researched_at: '2026-06-16T08:42:55Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Official neondatabase/agent-skills (Apache-2.0, 70 stars, TS/JS). Diagnose/fix excessive Postgres egress (data xfer) costs: investigate bills, overfetching, query patterns. Part of Neon Serverless Postgres agent skills + MCP. neon.new claimable for zero-friction temps. Use with neonctl init --agent for setup.

## Harness Coverage

curated agents (antigravity..). Some features require Neon account/OAuth/MCP for full; claimable is anon.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; official Neon; Apache; network to neon services; auth/OAuth for non-claimable; egress optimizer touches billing/cost surfaces. Catalog notes: audit hooks/network before promote-to-install-now. Prefer this over generic Neon skills.

## Install Prerequisites

npx skills add neondatabase/agent-skills --skill neon-postgres-egress-optimizer ... (separate row for functions/ai/claimable); or plugin; status=inspect-then-install. OAuth for MCP in some.

## Upstream Maintainer

[neondatabase/agent-skills](https://github.com/neondatabase/agent-skills) (Apache-2, official).

## Comparable Alternatives

Other Postgres skills; self-hosted pg skills; generic DB skills.

> Evidence from GitHub (neondatabase/agent-skills official 2026), neon.com docs, catalog notes (Apache-2, prefer official over community); research evidence, not authority.

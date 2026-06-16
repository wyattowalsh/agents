---
skill: mysql
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.77
---

## Purpose

Plan and review MySQL/InnoDB schema, indexing, query tuning, transactions, operations, MVCC, replication, connection issues, PlanetScale-specific features (pooling, CLI insights). Use for create/modify tables/indexes/queries, migrations, troubleshooting.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command. Web-aug: github.com/planetscale/database-skills (MIT, ~500 stars, active, db-skills.com, references/ for deeper, compatible with skills.sh and Cursor). Official PlanetScale; narrow DB focus, no broad exec hooks apparent.

## Install Prerequisites

Install: `npx skills add planetscale/database-skills --skill postgres --skill mysql -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[planetscale/database-skills](https://github.com/planetscale/database-skills) (PlanetScale, MIT)

## Comparable Alternatives

Prisma DB skills, general SQL/Postgres skills, local db docs.

> From repo README + skills/ 2026.

---
skill: prisma-database-setup
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Guides configuring Prisma with providers: Postgres, MySQL, SQLite, Mongo, SQL Server, Cockroach. Connections, troubleshooting. From prisma/skills (inspect tier in catalog).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command. Web: Official, MIT. Compute involves deploy/CLI surface and platform auth.

## Install Prerequisites

Install: `npx skills add prisma/skills --skill prisma-compute --skill prisma-database-setup -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[prisma/skills](https://github.com/prisma/skills)

## Comparable Alternatives

PlanetScale DB skills, Supabase/Vercel postgres skills, raw SQL skills.

> 2026 web from prisma/skills repo.

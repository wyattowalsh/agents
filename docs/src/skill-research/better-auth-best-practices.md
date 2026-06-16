---
skill: better-auth-best-practices
source_type: curated-external
researched_at: '2026-06-16T08:45:57Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

better-auth-best-practices provides authoritative configuration guidance for Better Auth (server/client setup, database adapters, sessions, plugins, environment variables, email flows, security, hooks, and client usage). The skill instructs agents to always consult the official better-auth.com/docs and re-run the @better-auth/cli after plugin changes. It is triggered by mentions of Better Auth, betterauth, auth.ts, or TypeScript auth setup needs.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. The skill surfaces setup workflows, env-var requirements, adapter patterns, plugin import paths, and common gotchas for auth integration tasks.

## Trust And Risks

install-now-after-trust-gate / curated-trust-gated. Official source from the better-auth organization. The skill itself is documentation-only (no execution surface beyond advising CLI usage). Risks are limited to following guidance that affects authentication security posture (secrets, CSRF, rate limiting, session storage). Prefer this over community copies per the curated notes. Review any generated auth.ts and migration steps.

## Install Prerequisites

`npx skills add better-auth/skills --skill better-auth-best-practices -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`

Depends on `npm install better-auth` and running the Better Auth CLI for schema generation/migrations in the consuming project.

## Upstream Maintainer

better-auth (https://github.com/better-auth/skills and https://github.com/better-auth/better-auth). Docs: https://better-auth.com/docs

## Comparable Alternatives

Framework-native auth (NextAuth/Auth.js, Clerk, Supabase Auth, Lucia) skills or local architecture patterns when the project has already chosen a different provider.

> Evidence gathered from public GitHub sources (raw SKILL.md) and better-auth.com/docs. Not an endorsement or authority; review generated code and security configuration for the target application.

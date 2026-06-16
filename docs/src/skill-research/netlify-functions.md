---
skill: netlify-functions
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Guide for writing Netlify serverless functions. Use when creating API endpoints, background processing, scheduled tasks, or server-side logic. Covers modern default export + Config syntax (TS/JS), path routing, method routing, background (-background suffix, 15min), scheduled (cron), streaming responses, Context object (geo, ip, cookies, params), Netlify.env, resource limits (60s sync, 1024MB), framework considerations.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command. Web: Official Netlify bundle, MIT, reference-only SKILL.md + references/. Functions run in Netlify runtime post-deploy; skill itself is static guidance.

## Install Prerequisites

Install: `npx skills add netlify/context-and-tools --skill netlify-deploy --skill netlify-functions --skill netlify-edge-functions -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[netlify/context-and-tools](https://github.com/netlify/context-and-tools) (official Netlify, MIT)

## Comparable Alternatives

Vercel serverless / AWS Lambda agent skills; framework-native API route skills.

> Web-augmented from SKILL.md 2026.

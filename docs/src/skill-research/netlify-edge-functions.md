---
skill: netlify-edge-functions
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

Guide for writing Netlify Edge Functions. Use when building middleware, geolocation-based logic, request/response manipulation, authentication checks, A/B testing, or low-latency edge compute. Covers Deno runtime, context.next() middleware, geolocation (city/country etc via context.geo), config paths/methods, when to choose edge vs serverless. Limits: 50ms CPU, 512MB, 20MB code.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; policy=Inspect before install.; evidence=config/external-skills.md. Web-aug: Same official Netlify repo as netlify-deploy (MIT, active, factual references only). No persistent state or broad FS; edge functions execute in Netlify Deno sandbox on deploy. Inspect for any custom scripts in bundle.

## Install Prerequisites

Install: `npx skills add netlify/context-and-tools --skill netlify-deploy --skill netlify-functions --skill netlify-edge-functions -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[netlify/context-and-tools](https://github.com/netlify/context-and-tools) (official, MIT)

## Comparable Alternatives

Cloudflare Workers / Deno Deploy skills; general edge compute patterns in framework skills (Next.js middleware etc).

> Web-augmented 2026 from repo SKILL.md + README. Evidence only.

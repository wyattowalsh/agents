---
skill: cloudflare
source_type: curated-external
researched_at: '2026-06-16T08:46:20Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

cloudflare is the comprehensive platform skill for Cloudflare (Workers, Pages, KV/D1/R2/Vectorize, Workers AI, Agents SDK, Durable Objects, security WAF/DDoS/Turnstile, networking Tunnel/Spectrum, IaC via Terraform/Pulumi, etc.). It provides decision trees to select the right product and then points to detailed references and official docs. Retrieval-first: always prefer live Cloudflare documentation.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Acts as the entry point that loads or references narrower skills (agents-sdk, wrangler, durable-objects, workers-best-practices, etc.).

## Trust And Risks

install-now-after-trust-gate / curated-trust-gated. Official Cloudflare content. Low direct risk from the skill text; actual risk surface is the Cloudflare account, bindings, secrets, and any deployed Worker/DO code. The skill explicitly tells agents to retrieve fresh limits/pricing/types.

## Install Prerequisites

`npx skills add cloudflare/skills --skill cloudflare ...` (often installed together with the other cloudflare/* skills in one command).

## Upstream Maintainer

Cloudflare (https://github.com/cloudflare/skills). Primary docs: https://developers.cloudflare.com/

## Comparable Alternatives

Per-product official docs or other platform skills (Vercel, AWS, etc.) when the workload is not on Cloudflare.

> Evidence gathered from public GitHub (raw SKILL.md, repo README). Not an endorsement or authority.

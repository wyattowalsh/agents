---
skill: deploy-to-vercel
source_type: curated-external
researched_at: '2026-06-16T20:11:00Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Deploy apps/websites to Vercel (auto-detect 40+ frameworks). "Claimable" deployments for claude.ai/Claude Desktop conversations; returns preview + claim URL (transfer ownership). Handles static + tarball packaging, excludes node_modules/.git. From vercel-labs/agent-skills.

## Harness Coverage

Deploy / Vercel agents. Install targets include antigravity etc.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; risks=Requires auth to Vercel account implicitly via deploy; network upload of project tarball; ownership transfer flow. Review before broad use. policy=Install after trust gate.; evidence=vercel-labs/agent-skills row + config/external-skills.md (grouped with vercel-optimize).

## Install Prerequisites

`npx skills add vercel-labs/agent-skills --skill deploy-to-vercel --skill vercel-optimize ...` status=install-now-after-trust-gate; selector=named.

## Upstream Maintainer

[vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) (official Vercel).

## Comparable Alternatives

Other deploy skills (render, railway, netlify from catalog); general `deploy` patterns.

> Web evidence from vercel-labs/agent-skills README (2026) + config.

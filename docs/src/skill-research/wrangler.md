---
skill: wrangler
source_type: curated-external
researched_at: '2026-06-16T08:46:20Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

wrangler is the dedicated skill for the Cloudflare Workers CLI (deploy, dev, secret management, KV/R2/D1/Vectorize/Hyperdrive/Queues/Workflows/Pipelines/Containers operations, types generation, tail, versions/rollback). It stresses use of wrangler.jsonc, recent compatibility_date, remote bindings for local dev, interactive secret commands, and never echoing secrets.

## Harness Coverage

Target agents from the cloudflare bundle. Complements workers-best-practices and platform skills for all CLI-driven workflows.

## Trust And Risks

install-now-after-trust-gate / curated-trust-gated. Official. Main risks are destructive CLI operations (delete, secret overwrite, deploy) and accidental secret leakage via command history or logs. The skill explicitly warns against common misuses.

## Install Prerequisites

Bundled with cloudflare/skills. The consuming project must have wrangler as devDependency for full type/config schema support.

## Upstream Maintainer

Cloudflare (https://github.com/cloudflare/skills). Wrangler docs: https://developers.cloudflare.com/workers/wrangler/

## Comparable Alternatives

Cloudflare REST API + dashboards for one-off tasks; other IaC (Terraform, Pulumi) skills when managing at scale.

> Evidence gathered from public GitHub (raw SKILL.md). Not an endorsement or authority.

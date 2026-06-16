---
skill: supply-chain-risk-auditor
source_type: curated-external
researched_at: '2026-06-16T20:07:00Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

Generates report on supply-chain threat landscape of direct dependencies (popularity, #maintainers, CVE history, update freq, security contacts). Flags high-risk; suggests alts where known. Uses `gh` CLI queries. Explicitly does NOT scan source for CVEs/creds. Trail of Bits (Spencer Michaels).

## Harness Coverage

Security / audit / supply chain agents.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Depends on gh auth + public data quality; holistic flags not exhaustive CVE scanner; network calls via gh. policy=Inspect.; evidence=trailofbits batch + https://github.com/trailofbits/skills/plugins/supply-chain-risk-auditor .

## Install Prerequisites

Inspect group install cmd. status=inspect-then-install; selector=named.

## Upstream Maintainer

[trailofbits/skills](https://github.com/trailofbits/skills).

## Comparable Alternatives

sast-configuration, secrets-management, general dep tools or wshobson patterns. Supply chain specific.

> Web README evidence.

---
skill: notion-cli
source_type: curated-external
researched_at: '2026-06-16T08:42:27Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

Official makenotion/skills (MIT, 121 stars). notion-cli wraps Notion CLI (ntn) for workers, public API requests, file uploads. Agent skill to use ntn CLI from coding agents. Requires Notion API token handling.

## Harness Coverage

antigravity etc targets.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; official Notion org; API token scope/secret handling is key risk per catalog notes; prefer over third-party notion-api skills.

## Install Prerequisites

npx skills add makenotion/skills --skill notion-cli -y -g -a [agents]; status=inspect-then-install; selector=named. Provide API token.

## Upstream Maintainer

[makenotion/skills](https://github.com/makenotion/skills) (MIT, official).

## Comparable Alternatives

Third-party Notion REST skills; general API client skills.

> Evidence from public GitHub (official + community 2026) + catalog; research evidence, not authority/endorsement.

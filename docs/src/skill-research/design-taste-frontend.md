---
skill: design-taste-frontend
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Install only `design-taste-frontend` from `Leonxlnx/taste-skill` by default. The source-list exposes 12 skills and the repository has strong public adoption, MIT licensing, and no observed hooks in the inspected skill frontmatter, but the bundle substantially overlaps local design/image-generation workflows; keep style variants, image-generation variants, `full-output-enforcement`, and `stitch-design-taste` global-only unless a user explicitly requests them.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Install only `design-taste-frontend` from `Leonxlnx/taste-skill` by default. The source-list exposes 12 skills and the repository has strong public adoption, MIT licensing, and no observed hooks in the inspected skill frontmatter, but the bundle substantially overlaps local design/image-generation workflows; keep style variants, image-generation variants, `full-output-enforcement`, and `stitch-design-taste` global-only unless a user explicitly requests them.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add Leonxlnx/taste-skill --skill design-taste-frontend -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

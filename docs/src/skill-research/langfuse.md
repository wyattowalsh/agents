---
skill: langfuse
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Official Langfuse tracing, prompts, datasets, and CLI/API workflows. Scoped `allowed-tools` target `langfuse.com` and `langfuse-cli`; requires user-owned `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL`. Complements Phoenix/Arize OpenInference skills without duplicating them.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; risks=Official Langfuse tracing, prompts, datasets, and CLI/API workflows. Scoped `allowed-tools` target `langfuse.com` and `langfuse-cli`; requires user-owned `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL`. Complements Phoenix/Arize OpenInference skills without duplicating them.; policy=Install only after trust gate; audit again before repo promotion.; evidence=Curated `npx skills add` command with named `--skill` selectors under `install-now-after-trust-gate` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add langfuse/skills --skill langfuse -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

[langfuse/skills](https://github.com/langfuse/skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

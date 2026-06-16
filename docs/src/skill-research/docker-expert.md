---
skill: docker-expert
source_type: curated-external
researched_at: '2026-06-16T08:37:54Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Expert Docker usage patterns, Dockerfile authoring, multi-stage builds, compose, security scanning, and container debugging for agents. Evidence gathered from upstream SKILL.md, READMEs, and repo structure via web research.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command (web-audited SKILL.md + repo); risks=Requires source inspection for hooks, broad Bash tool scopes (e.g. language CLIs), credential/API usage, and deduplication with local skills before install. Low adoption for some sources; community provenance. Do not endorse without audit. policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Install Prerequisites

Install: `npx skills add sickn33/antigravity-awesome-skills --skill docker-expert -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Web research of upstream repo (SKILL.md/contents); evidence only, not authority. Use external-skill-auditor for live verification before install or promotion. Not an endorsement.

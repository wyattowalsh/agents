---
skill: golang-grpc
source_type: curated-external
researched_at: '2026-06-16T08:37:54Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Go-specific agent skill providing best practices, patterns, and workflows for grpc. Part of a larger curated set of 20+ Go skills from samber. Emphasizes production readiness, statistical rigor for perf, and cross-references other golang skills. Evidence gathered from upstream SKILL.md, READMEs, and repo structure via web research.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command (web-audited SKILL.md + repo); risks=Requires source inspection for hooks, broad Bash tool scopes (e.g. language CLIs), credential/API usage, and deduplication with local skills before install. Low adoption for some sources; community provenance. Do not endorse without audit. policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Install Prerequisites

Install: `npx skills add samber/cc-skills-golang --skill golang-grpc -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[samber/cc-skills-golang](https://github.com/samber/cc-skills-golang)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Web research of upstream repo (SKILL.md/contents); evidence only, not authority. Use external-skill-auditor for live verification before install or promotion. Not an endorsement.

---
skill: semgrep
source_type: curated-external
researched_at: '2026-06-16T20:06:00Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Fast pattern-based (and taint) security scanning with Semgrep using built-in (OWASP, CWE, Trail of Bits), custom YAML rules, taint tracking. Parallel scanner agents per lang category; triager agent (Read/Grep/Glob/Write) for FP classification. SARIF/CI friendly. Part of static-analysis plugin.

## Harness Coverage

Security scan agents.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Rule creation surface (potential for overly broad rules); triage burden on FPs; assumes semgrep available. policy=Inspect.; evidence=trailofbits/skills + config/external-skills.md.

## Install Prerequisites

`npx skills add trailofbits/skills --skill semgrep ...` status=inspect-then-install; selector=named (grouped w/ codeql).

## Upstream Maintainer

[trailofbits/skills](https://github.com/trailofbits/skills).

## Comparable Alternatives

codeql (deeper), insecure-defaults, variant-analysis, sast-configuration.

> Web evidence.

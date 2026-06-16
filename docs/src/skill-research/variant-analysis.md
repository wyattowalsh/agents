---
skill: variant-analysis
source_type: curated-external
researched_at: '2026-06-16T20:08:00Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

5-step systematic variant analysis to find similar vulns/bugs from a seed: 1) understand root cause 2) exact match pattern 3) identify abstractions 4) iteratively generalize 5) analyze/triage. Includes tool guidance (rg/Semgrep/CodeQL), pitfalls, ready CodeQL/Semgrep templates (py,js,java,go,c++). Trail of Bits.

## Harness Coverage

Audit / variant hunt / static analysis agents.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Easy to over-generalize (scope creep, FPs); best after seed vuln found. policy=Inspect.; evidence=config trailofbits + https://github.com/trailofbits/skills (Axel Mierczuk).

## Install Prerequisites

In differential/agentic batch install. status=inspect-then-install.

## Upstream Maintainer

[trailofbits/skills](https://github.com/trailofbits/skills).

## Comparable Alternatives

codeql, semgrep (directly), differential-review. Pattern generalization instruction.

> Web evidence.

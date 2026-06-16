---
skill: differential-review
source_type: curated-external
researched_at: '2026-06-16T20:02:00Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Security-focused differential review of code changes (PRs, commits, diffs) using git history/blame for regressions, blast radius (callers), test coverage gaps, risk-first prioritization (auth/crypto/external/value), adaptive depth (SMALL/MEDIUM/LARGE), and adversarial modeling. Produces structured markdown report. Modular progressive disclosure (core SKILL.md + methodology/adversarial/reporting/patterns.md). Trail of Bits.

## Harness Coverage

Target agents in security/review harnesses. allowed-tools: Read Write Grep Glob Bash. Integrates with audit-context-building and issue-writer.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Time-intensive for large changes; depends on clean git history; must always emit report file (no verbal-only); high blast radius + HIGH risk requires full adversarial. Misuse on greenfield or non-security changes wastes effort. policy=Inspect before install per config.; evidence=trailofbits inspect batch + https://github.com/trailofbits/skills (Omar Inuwa author; detailed plugin docs).

## Install Prerequisites

`npx skills add trailofbits/skills --skill differential-review ...` status=inspect-then-install; selector=named. Part of broader code-auditing plugin set.

## Upstream Maintainer

[trailofbits/skills](https://github.com/trailofbits/skills) — security research org.

## Comparable Alternatives

`honest-review`, other code-review skills (e.g. from PaulRBerg or wshobson); `static-analysis` for non-diff. Scoped to security diff+blast+adversarial.

> Web evidence: plugin README + skills/differential-review/SKILL.md (2026).

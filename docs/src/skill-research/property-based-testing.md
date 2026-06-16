---
skill: property-based-testing
source_type: curated-external
researched_at: '2026-06-16T20:05:00Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Proactively suggests/writes property-based tests for encode/decode, parsers, normalize, validators, collections, pure math/algos, smart contracts. Supports Hypothesis (Python), fast-check (JS/TS), proptest/quickcheck (Rust), rapid/gopter (Go), jqwik (Java), ScalaCheck, Echidna/Medusa (Solidity/Vyper) + more. References library list.

## Harness Coverage

Testing / verification agents.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Only useful on code with suitable pure/roundtrip/invariant patterns; may propose new deps. policy=Inspect group.; evidence=config trailofbits + https://github.com/trailofbits/skills .

## Install Prerequisites

Grouped with codeql/semgrep in inspect install. status=inspect-then-install.

## Upstream Maintainer

[trailofbits/skills](https://github.com/trailofbits/skills).

## Comparable Alternatives

e2e-testing-patterns, python-testing-patterns, javascript-testing-patterns (wshobson). PBT-specific instruction.

> Web evidence repo.

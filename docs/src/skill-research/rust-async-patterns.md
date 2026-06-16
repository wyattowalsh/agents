---
skill: rust-async-patterns
source_type: curated-external
researched_at: '2026-06-16T20:35:00Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

Rust async patterns; risks around Send/Sync, cancellation, deadlock. From wshobson/agents (large multi-harness marketplace, 84 plugins/156 skills; one Markdown source to 5 harnesses).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=inspect-then-install; provenance=verified-install-command; risks=Rust async patterns; risks around Send/Sync, cancellation, deadlock.; policy=Install only after trust gate / inspect source/hooks/credentials/dedupe before promotion.; evidence=wshobson/agents batches (residual + patterns) in config/external-skills.md; upstream https://github.com/wshobson/agents (plugins/*, docs/agent-skills.md, high star count).

## Install Prerequisites

Install: `npx skills add wshobson/agents --skill rust-async-patterns -y -g -a antigravity claude-code ...` status=inspect-then-install; selector=named. Review outputs for safety (esp. generators, k8s, tf, secrets).

## Upstream Maintainer

[wshobson/agents](https://github.com/wshobson/agents) — MIT, broad agentic patterns + quality eval (plugin-eval).

## Comparable Alternatives

Similar patterns in trailofbits, vercel, local skills/* or other curated (e.g. python from modern-python, k8s from hashicorp). General rust async patterns instruction.

> Web evidence from wshobson/agents github (README, docs, example SKILLs 2026) + config notes. Evidence only.

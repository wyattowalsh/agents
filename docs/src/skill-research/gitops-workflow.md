---
skill: gitops-workflow
source_type: curated-external
researched_at: '2026-06-16T20:30:00Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

GitOps workflow patterns (k8s etc). From wshobson/agents multi-harness marketplace (36.8k stars; 84 plugins, 156 skills). One source, five harness adapters.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode (per wshobson rows in config).

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; risks=GitOps workflow patterns (k8s etc).; policy=Install only after trust gate; audit again before repo promotion or use `/review source`.; evidence=Curated wshobson/agents install/inspect batches in config/external-skills.md (multiple residual groups); upstream https://github.com/wshobson/agents (docs/agent-skills.md, plugins/*/skills).

## Install Prerequisites

Install: `npx skills add wshobson/agents --skill gitops-workflow ... -y -g -a ...` status=install-now-after-trust-gate; selector=named. Review generated artifacts (e.g. recipes, charts) before apply.

## Upstream Maintainer

[wshobson/agents](https://github.com/wshobson/agents) — large community agentic plugin/skill marketplace. MIT.

## Comparable Alternatives

Other backend/k8s/devops patterns from catalog (e.g. nodejs-backend, k8s-*, terraform-*) or local equivalents. A general-purpose agent instruction without this exact wshobson gitops-workflow contract.

> Web evidence from wshobson/agents README + plugin docs (2026) + config notes. Evidence only; not endorsement.

---
skill: deployment-pipeline-design
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Curated third-party skill source. Run external-skill-auditor before repo promotion.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add wshobson/agents --skill python-testing-patterns --skill sast-configuration --skill e2e-testing-patterns --skill javascript-testing-patterns --skill rust-async-patterns --skill database-migration --skill terraform-module-library --skill deployment-pipeline-design --skill python-observability --skill incident-runbook-templates --skill secrets-management --skill stride-analysis-patterns --skill slo-implementation -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[wshobson/agents](https://github.com/wshobson/agents)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

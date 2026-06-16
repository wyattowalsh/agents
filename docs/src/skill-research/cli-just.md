---
skill: cli-just
source_type: curated-external
researched_at: '2026-06-16T06:01:40Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Install only `cli-just` from `PaulRBerg/agent-skills` for Justfile and `just` command-runner workflows. The source at audited HEAD `d3f5540ed2fc0fa07f802bd925e06b9387cbe90f` exposes 26 skills, has MIT licensing, and the inspected `cli-just` skill has no observed hooks, `allowed-tools`, or skill-local scripts. Its references are documentation and examples, but include dotenv loading, package-manager, publish, network, and destructive cleanup snippets; review generated Just recipes as executable project code before running them.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; risks=Install only `cli-just` from `PaulRBerg/agent-skills` for Justfile and `just` command-runner workflows. The source at audited HEAD `d3f5540ed2fc0fa07f802bd925e06b9387cbe90f` exposes 26 skills, has MIT licensing, and the inspected `cli-just` skill has no observed hooks, `allowed-tools`, or skill-local scripts. Its references are documentation and examples, but include dotenv loading, package-manager, publish, network, and destructive cleanup snippets; review generated Just recipes as executable project code before running them.; policy=Install only after trust gate; audit again before repo promotion.; evidence=Curated `npx skills add` command with named `--skill` selectors under `install-now-after-trust-gate` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add PaulRBerg/agent-skills@d3f5540ed2fc0fa07f802bd925e06b9387cbe90f --skill cli-just -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

[PaulRBerg/agent-skills](https://github.com/PaulRBerg/agent-skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

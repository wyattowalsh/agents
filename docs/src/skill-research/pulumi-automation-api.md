---
skill: pulumi-automation-api
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Official Pulumi IaC subset: program authoring, components, Automation API, and ESC secrets. Distinct from `terraform-skill` and `hashicorp/agent-skills`; cherry-pick only these four slugs from the 14-skill bundle.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command; risks=Official Pulumi IaC subset: program authoring, components, Automation API, and ESC secrets. Distinct from `terraform-skill` and `hashicorp/agent-skills`; cherry-pick only these four slugs from the 14-skill bundle.; policy=Install only after trust gate; audit again before repo promotion.; evidence=Curated `npx skills add` command with named `--skill` selectors under `install-now-after-trust-gate` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add pulumi/agent-skills --skill pulumi-best-practices --skill pulumi-component --skill pulumi-automation-api --skill pulumi-esc -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

[pulumi/agent-skills](https://github.com/pulumi/agent-skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

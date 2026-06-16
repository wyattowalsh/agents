---
skill: pulumi-esc
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Guidance for working with Pulumi ESC (Environments, Secrets, and Configuration). From Pulumi official agent-skills for infrastructure as code. Part of pulumi/ plugin groups (pulumi skills + migration etc).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command. Web-aug: github.com/pulumi/agent-skills (MIT/Apache mix per files, official Pulumi, ~59 stars, Python, AGENTS.md, supports Claude/Cursor/Copilot/Codex via plugins/marketplaces + npx). IaC surface (stacks, secrets via ESC); audit before full org use.

## Install Prerequisites

Install: `npx skills add pulumi/agent-skills --skill pulumi-best-practices --skill pulumi-component --skill pulumi-automation-api --skill pulumi-esc -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

[pulumi/agent-skills](https://github.com/pulumi/agent-skills) (official Pulumi)

## Comparable Alternatives

Terraform skills (hashicorp, antonbabenko), CDK migration skills, local Pulumi docs.

> Web from pulumi/agent-skills README 2026.

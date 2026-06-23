---
skill: aws-ami-builder
source_type: curated-external
researched_at: '2026-06-16T08:43:06Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Build Amazon Machine Images (AMIs) with Packer using the amazon-ebs builder. Use when creating custom AMIs for EC2 instances. Note: incurs AWS costs.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Web-augmented from upstream SKILL.md + config/external-skills.md (fetched 2026-06-16).

## Install Prerequisites

Install: `npx skills add hashicorp/agent-skills --skill terraform-stacks --skill terraform-search-import --skill aws-ami-builder -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[hashicorp/agent-skills](https://github.com/hashicorp/agent-skills)

## Comparable Alternatives

Other infra skills like `kubernetes-specialist`.

> Web-augmented from public upstream SKILL.md (github raw fetches) and curated config/external-skills.md; use /review source for live evidence and script/hook audit. Not an endorsement. Confidence 0.75 derived from metadata alignment + source inspection depth.

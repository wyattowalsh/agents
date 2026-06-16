---
skill: cli-just
source_type: curated-external
researched_at: '2026-06-16T08:35:46Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Provides Just command runner guidance and Justfile workflows. Part of PRB collection of AI agent skills optimized primarily for Claude Code and Codex (also cross-agent). Helps with defining and using `just` recipes for common dev tasks, replacing or augmenting make/npm scripts. Install name `cli-just`. The source at the curated pinned commit exposes 20 skills total including biome, code review/simplify/polish, commit, tailwind, etc.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

Curated install-now-after-trust-gate / curated-trust-gated. MIT license. Pinned to specific HEAD d3f5540ed2fc0fa07f802bd925e06b9387cbe90f for audit reproducibility. Per config: the inspected cli-just skill has no observed hooks, allowed-tools, or skill-local scripts. References include documentation, examples, dotenv loading, package-manager, publish, network, and destructive cleanup snippets — review any generated Just recipes as executable project code before running. Repo warning: skills optimized for maintainer personal setup/workflow; user must do own due diligence, customize to stack/agents; no warranties. 62 stars on GitHub. Maintainer PaulRBerg.

## Install Prerequisites

`npx skills add PaulRBerg/agent-skills@d3f5540ed2fc0fa07f802bd925e06b9387cbe90f --skill cli-just -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`. status=install-now-after-trust-gate; selector=named. From curated source with pinned commit.

## Upstream Maintainer

PaulRBerg (github.com/PaulRBerg/agent-skills at pinned d3f5540). MIT License. Primary for personal Claude Code / Codex workflows. See also dot-claude and dot-agents from same author. Cross references to vercel-labs/skills.

## Comparable Alternatives

Other CLI runners in same source (e.g. cli-gh, cli-cast); general just/make guidance skills; commit + code-review from same bundle for TS workflow coverage; native just CLI docs or other agent skills like work/end-to-end-task.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.

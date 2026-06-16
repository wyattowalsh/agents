---
skill: obsidian-cli
source_type: curated-external
researched_at: '2026-06-16T08:43:18Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Official agent skill from kepano/obsidian-skills (by Obsidian CEO). Teaches agents to interact with running Obsidian vaults via the official Obsidian CLI: read/create/search/manage notes, tasks, properties; also supports plugin/theme dev with reload, JS eval, screenshots, DOM inspect, console. Follows Agent Skills spec. MIT license. Requires Obsidian app to be open. See raw SKILL.md for command reference (e.g. obsidian create, search, daily:append, plugin:reload).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode (from curated install command).

## Trust And Risks

trust_tier=curated-trust-gated; status=install-now-after-trust-gate; provenance=verified-install-command + official repo by Obsidian founder; MIT license; 35k+ stars context; risks primarily around vault access permissions and requiring running Obsidian instance. Scoped to user own vaults.

## Install Prerequisites

Install: npx skills add kepano/obsidian-skills --skill obsidian-cli --skill obsidian-markdown -y -g -a [agents]. Obsidian must be open for CLI. status=install-now-after-trust-gate; selector=named

## Upstream Maintainer

[kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) (official, MIT).

## Comparable Alternatives

Obsidian-flavored markdown skills from other sources; general file-system or note-taking skills.

> Evidence from public web sources, GitHub (kepano/obsidian-skills official Jun 2026), curated; research evidence, not authority or endorsement.

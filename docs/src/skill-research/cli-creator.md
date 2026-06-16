---
skill: cli-creator
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Guidance and patterns for creating CLIs (often agent-facing). From official openai/skills catalog for Codex (and compatible). Curated or experimental skills in .curated/.experimental.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command. Web-aug: github.com/openai/skills (high stars ~22k, active OpenAI team, Python/JS/Shell, follows agentskills.io standard, documented install via $skill-installer). Inspect for broad scopes in security/CLI creator (write/exec potential). Catalog flags for inspection before promotion.

## Install Prerequisites

Install: `npx skills add openai/skills --skill cli-creator -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` (or via specific .experimental etc) status=inspect-then-install; selector=named. Restart agent after install per docs.

## Upstream Maintainer

[openai/skills](https://github.com/openai/skills) (official OpenAI, high activity)

## Comparable Alternatives

Anthropics skills, local security-auditor / threat-model skills; other platform-specific (e.g. mcp-use).

> Web from repo README 2026 + catalog notes.

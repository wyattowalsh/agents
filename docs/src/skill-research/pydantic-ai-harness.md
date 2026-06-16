---
skill: pydantic-ai-harness
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.77
---

## Purpose

Extend Pydantic AI agents with harness capabilities (e.g. Code Mode sandboxed run). From pydantic/skills: Logfire + Pydantic AI plugins and cross-agent SKILL.md files. Supports Claude Code, Codex, Cursor via plugins + standalone.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command. Web-aug: github.com/pydantic/skills (MIT, active Pydantic team, 80+ stars, plugins/ + skills/ dir, MCP for Logfire, requires LOGFIRE_TOKEN for full use). Official; telemetry surface.

## Install Prerequisites

For plugins: claude/codex/cursor marketplace add pydantic/skills then install specific. Standalone: npx skills add pydantic/skills --skill pydantic-ai-harness status=inspect-then-install.

## Upstream Maintainer

[pydantic/skills](https://github.com/pydantic/skills) (official Pydantic)

## Comparable Alternatives

Other observability (otel, langsmith), agent framework skills (langchain, crewai).

> 2026 web + pydantic README.

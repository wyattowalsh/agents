---
skill: managed-deep-agents
source_type: curated-external
researched_at: '2026-06-16T06:01:41Z'
research_tier: standard
mean_confidence: 0.65
---

## Purpose

Extended LangChain row with Deep Agents core/memory/orchestration, middleware/HITL, dependency pinning, and Managed Deep Agents ops. Confirm source-list slugs before apply.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Extended LangChain row with Deep Agents core/memory/orchestration, middleware/HITL, dependency pinning, and Managed Deep Agents ops. Confirm source-list slugs before apply.; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated `npx skills add` command with named `--skill` selectors under `inspect-then-install` in config/external-skills.md.

## Install Prerequisites

Install: `npx skills add langchain-ai/langchain-skills --skill ecosystem-primer --skill langchain-fundamentals --skill langgraph-fundamentals --skill langgraph-human-in-the-loop --skill langgraph-persistence --skill langchain-rag --skill deep-agents-core --skill deep-agents-memory --skill deep-agents-orchestration --skill langchain-middleware --skill langchain-dependencies --skill managed-deep-agents -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode` status=inspect-then-install; selector=named

## Upstream Maintainer

[langchain-ai/langchain-skills](https://github.com/langchain-ai/langchain-skills)

## Comparable Alternatives

A general-purpose agent instruction without a scoped skill contract

> Sourced from curated config/external-skills.md; use external-skill-auditor for live evidence. Not an endorsement.

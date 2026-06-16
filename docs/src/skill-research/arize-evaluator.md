---
skill: arize-evaluator
source_type: curated-external
researched_at: '2026-06-16T08:38:00Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Arize skill (from Arize-ai/arize-skills or phoenix) for building/running evaluators for LLM apps (RAG relevance, answer relevance, hallucination, groundedness etc). Integrates with Phoenix observability.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; source=Arize AI (phoenix/arize-skills repos); 10k+ stars on phoenix; open source (MIT); pairs tracing + evals; inspect for evaluator model costs and data sent to Arize/Phoenix.

## Install Prerequisites

Install: subset of github/awesome-copilot or direct arize-ai/arize-skills; or npx skills add Arize-ai/phoenix; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[Arize-ai/arize-skills](https://github.com/Arize-ai/arize-skills) and [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) (official Arize)

## Comparable Alternatives

`phoenix-evals`, `agentic-eval`, `eval-driven-dev`; LangSmith evals or other LLM eval harness skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

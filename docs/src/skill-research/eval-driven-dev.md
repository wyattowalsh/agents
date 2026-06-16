---
skill: eval-driven-dev
source_type: curated-external
researched_at: '2026-06-16T08:38:00Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

awesome-copilot skill for eval-driven development: build automated evaluation pipelines that run the AI app end-to-end with real inputs, score outputs with evaluators, produce pass/fail via test frameworks (pixie etc).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; GitHub curated; powerful for regression but involves executing the app under test and scoring (potential cost, flakiness, data needs); inspect eval harness integration and data sources.

## Install Prerequisites

Install: `npx skills add github/awesome-copilot --skill eval-driven-dev`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[github/awesome-copilot](https://github.com/github/awesome-copilot) (GitHub curated)

## Comparable Alternatives

`arize-evaluator`, `phoenix-evals`, `agentic-eval`; general property-based or LLM eval skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.

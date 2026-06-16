---
skill: logging-best-practices
source_type: curated-external
researched_at: '2026-06-16T08:45:57Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

logging-best-practices teaches the wide-event (canonical log line) pattern: emit one structured, context-rich JSON event per request per service at completion, carrying high-cardinality identifiers, business context, environment characteristics, and outcome. Covers middleware usage, single-logger discipline, two-level logging (info/error), anti-patterns (scattered console.log, multiple loggers, unstructured strings), and references to Stripe canonical lines and observability literature.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Provides concrete TypeScript examples and rules files for adoption in services.

## Trust And Risks

install-now-after-trust-gate / curated-trust-gated. MIT-licensed community skill (boristane/agent-skills). Low execution risk — pure guidance. Benefits observability and debugging; ensure consistent schema adoption across services and that high-cardinality fields are handled by downstream stores.

## Install Prerequisites

`npx skills add boristane/agent-skills --skill logging-best-practices -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`

Adoption requires a structured logger (JSON) and middleware or finally-block emission pattern in the application.

## Upstream Maintainer

boristane (https://github.com/boristane/agent-skills). Author blog references included in skill.

## Comparable Alternatives

Framework or platform logging guides (e.g. Pino, Winston best practices, OpenTelemetry logging bridge, vendor-specific canonical logging docs).

> Evidence gathered from public GitHub (raw SKILL.md). Not an endorsement or authority; validate against your observability backend cardinality and retention constraints.

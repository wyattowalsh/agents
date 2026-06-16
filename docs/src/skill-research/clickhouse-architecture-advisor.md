---
skill: clickhouse-architecture-advisor
source_type: curated-external
researched_at: '2026-06-16T08:45:57Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

clickhouse-architecture-advisor complements clickhouse-best-practices with workload-aware decision frameworks (ingestion strategy, partitioning for time-series, join enrichment, late-arriving upserts). It requires explicit provenance labeling (official / derived / field) on every recommendation and reading of workload-specific decision rules. Intended for architecture and modeling choices rather than day-to-day query/schema reviews.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Loads under inspect-then-install because of the inspect gate for the clickhouse/agent-skills bundle.

## Trust And Risks

Status inspect-then-install; trust tier needs-inspection. Official ClickHouse Inc. content (Apache-2.0). The skill mandates provenance classification and prefers official docs. Risks of mis-applying heuristics labeled "field" without sufficient context or workload fit; always cross-check against current ClickHouse documentation and run the referenced decision rules.

## Install Prerequisites

`npx skills add clickhouse/agent-skills --skill clickhouse-architecture-advisor --skill clickhouse-best-practices -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`

Run external-skill-auditor on the source before promotion per curated policy.

## Upstream Maintainer

ClickHouse Inc. (https://github.com/ClickHouse/agent-skills). Official docs linked from skill.

## Comparable Alternatives

Direct use of ClickHouse official best-practices docs + architecture guides; vendor-neutral modeling patterns from other OLAP systems when not ClickHouse-specific.

> Evidence from public GitHub (raw SKILL.md and ClickHouse blog). Summarizes risks; do not endorse installation without inspection. Not authority.

---
skill: clickhouse-best-practices
source_type: curated-external
researched_at: '2026-06-16T08:45:57Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

clickhouse-best-practices encodes 31 prioritized rules (schema PK ordering, data types, JOIN algorithms, insert batching, mutation avoidance, partitioning, skipping indices, agent discovery/safety) that must be checked and cited before giving ClickHouse recommendations. Requires following a strict connect-discover-plan-execute-recover workflow and rule-file consultation order.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Forces rule-driven output format (Rules Checked, Violations, Compliant, Recommendations with citations).

## Trust And Risks

inspect-then-install / needs-inspection per bundle. Official ClickHouse Inc. material. High value when followed; risk of incomplete rule application leading to suboptimal schemas or queries. The skill is advisory only; agents must still validate against live EXPLAIN, cluster topology, and current docs.

## Install Prerequisites

Same install command as the architecture advisor skill. Requires prior audit of the agent-skills source.

## Upstream Maintainer

ClickHouse Inc. (https://github.com/ClickHouse/agent-skills). Complements https://clickhouse.com/docs/best-practices.

## Comparable Alternatives

ClickHouse official documentation, CH community knowledge bases, and direct EXPLAIN-driven tuning without the rule wrapper.

> Evidence from public GitHub (raw SKILL.md and ClickHouse blog). Summarizes risks; do not endorse installation without inspection. Not authority.

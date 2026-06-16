---
skill: otel-instrumentation
source_type: curated-external
researched_at: '2026-06-16T08:46:52Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

otel-instrumentation guides application instrumentation for traces, metrics, and logs using OpenTelemetry SDKs. Covers resource attributes, span hygiene, metric instrument selection, sensitive-data redaction, per-language SDK setup (Node, Go, Python, Java, etc.), and validation checklists. Defers sampling to the Collector.

## Harness Coverage

Paired with otel-collector and semantic-conventions in the dash0 bundle.

## Trust And Risks

inspect-then-install. Risks are incorrect instrumentation (missing context propagation, high cardinality, PII leakage, performance overhead). The skill emphasizes signal density over volume and consistent resource attributes.

## Install Prerequisites

Same dash0hq/agent-skills bundle install.

## Upstream Maintainer

dash0 (https://github.com/dash0hq/agent-skills). Primary: https://opentelemetry.io/docs/

## Comparable Alternatives

Language-specific OTel docs, auto-instrumentation agents, and vendor SDK guides.

> Evidence from public GitHub. Summarizes risks; do not endorse without inspection.

---
skill: otel-collector
source_type: curated-external
researched_at: '2026-06-16T08:46:52Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

otel-collector provides expert configuration for the OpenTelemetry Collector (receivers, exporters, processors, pipelines, deployment modes, sampling, RED metrics, custom distributions). Mandates memory_limiter first, one pipeline per signal, and explicit validation. Includes Dash0 export examples but is vendor-neutral for OTLP.

## Harness Coverage

Target agents from the dash0hq bundle. Used when standing up or tuning a Collector pipeline (k8s, Docker, Helm, Operator, raw manifests).

## Trust And Risks

inspect-then-install / needs-inspection. MIT official-ish vendor skill (dash0). The Collector can drop or mis-route telemetry if pipelines or ordering are wrong; memory exhaustion or data loss are real operational risks. The skill encodes validated patterns but still requires environment-specific validation and secret handling for exporters.

## Install Prerequisites

`npx skills add dash0hq/agent-skills --skill otel-collector --skill otel-instrumentation --skill otel-semantic-conventions -y -g -a ...`

Requires the otelcol binary or contrib image and proper auth for the target backend.

## Upstream Maintainer

dash0 (https://github.com/dash0hq/agent-skills). Complements https://opentelemetry.io/docs/collector/.

## Comparable Alternatives

Direct OpenTelemetry Collector docs + contrib components; vendor-specific distribution guides.

> Evidence from public GitHub raw skills and linked OTel docs. Summarizes risks; do not endorse installation without inspection. Not authority.

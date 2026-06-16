---
skill: otel-semantic-conventions
source_type: curated-external
researched_at: '2026-06-16T08:46:52Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

otel-semantic-conventions is the authority for selecting and placing attributes according to the OTel semconv registry. Requires searching the registry first, preferring stable attributes, correct resource vs span placement, low-cardinality for metrics, and org.namespace.* for customs. Includes versioning/migration and Dash0-derived notes.

## Harness Coverage

Used alongside otel-instrumentation and collector skills for any attribute or metric naming decision.

## Trust And Risks

inspect-then-install. Misuse of custom or high-cardinality attributes can break downstream querying, increase cost, or leak data. The skill is a thin disciplined wrapper over the public registry.

## Install Prerequisites

Same bundle as the other otel skills.

## Upstream Maintainer

dash0 (https://github.com/dash0hq/agent-skills) with direct links to https://opentelemetry.io/docs/specs/semconv/registry/attributes/.

## Comparable Alternatives

Direct use of the OTel semantic conventions specification and registry browser.

> Evidence from public GitHub (raw skill). Summarizes risks; do not endorse without inspection.

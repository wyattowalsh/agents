# Design: Agents Platform Overhaul

## Architecture

The design introduces these layers:

1. Repo inventory and OpenSpec reconciliation.
2. Canonical registry layer.
3. Adapter layer for skills, plugins, MCP, OpenAPI/function-calling, CLI, rules, and OpenSpec.
4. Transaction-safe config engine.
5. Harness projection layer.
6. CI/eval/observability layer.
7. Generated docs and AI instruction truth.

## Decision: skill-first

Agent Skills are the default extension model for reusable, CLI-friendly capabilities. MCP is reserved for live external state, authenticated SaaS, dynamic runtime/browser state, current docs/search, DB/vector/search state, and telemetry streams.

## Decision: support tiers

Support tiers must distinguish validated support from repo-present or planned support.

## Decision: transaction safety

No adapter writes files directly. All writes route through preview/apply/rollback transaction semantics.

## Decision: docs as build artifacts

README, AI instructions, support matrices, skill docs, MCP docs, and harness setup docs are generated or validated from manifests.

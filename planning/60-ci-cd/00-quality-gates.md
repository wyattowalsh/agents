# CI, Eval, And Observability Quality Gates

## Scope

This document defines validation gates before registry, skill, MCP, harness, eval, and telemetry changes can land. It does not modify workflows or tests in this pass.

## Registry And Schema Gates

- JSON manifests validate against `config/schemas/*`.
- Support-tier changes require fixture evidence and owner lane.
- Harness splits must preserve desktop, web/cloud, CLI, editor, and experimental variants.

## Skill And MCP Conformance Gates

- Skills: `wagents validate`, audit script, package dry-run, provenance lock, and no unsafe hooks.
- MCP: registry schema, secret model, transport model, smoke fixture, and rollback/disable path.

## Eval Scenario Schema

Eval scenarios should record:

- Scenario id and owner lane.
- Input fixture.
- Expected output shape.
- Determinism controls.
- Redaction expectations.
- Pass/fail rubric.

## Deterministic Replay Fixtures

Replay fixtures use captured redacted events, not live credentials. They must be runnable offline when possible and clearly mark any live dependency.

## Report Artifacts

Reports should include OpenSpec status, validation commands, fixture coverage, skipped gates, and known blind spots.

## Observability Artifact Contract

Observability artifacts are redacted summaries, not raw traces by default. Each artifact should include:

- Run id, change id, child lane, and harness id when applicable.
- Command or fixture id.
- Result status and duration.
- Redacted failure summary.
- Linked validation output path when a large log exists.
- Run graph references for dependencies between tasks, subagents, validations, and commits.
- Privacy class and retention hint.

Failure-remediation reports should connect each failed gate to owner, suspected cause, next action, and whether the failure is blocking or deferred.

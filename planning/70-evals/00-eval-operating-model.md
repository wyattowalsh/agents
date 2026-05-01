# Eval Operating Model

## Purpose

Define how future evals verify agent asset behavior without relying on live secrets or generated docs side effects.

## Scenario Contract

Each eval scenario includes:

- Name, owner lane, and support-tier gate.
- Input artifacts and fixture data.
- Expected output in JSON, Markdown, or file diff form.
- Deterministic controls for time, network, filesystem, and external services.
- Redaction rules and forbidden outputs.
- Review criteria and failure explanation.

## Replay Contract

Replay uses redacted session event streams and fixture files. Live MCP calls, browser profiles, and user-owned configs are replaced with mocks or skipped with explicit reason.

## Promotion Rule

A support tier cannot be promoted by docs alone. It needs a passing fixture or an explicit exception with owner and expiry.

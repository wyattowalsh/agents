# Agent Run Telemetry

## Objective

Provide visibility into skill invocations, MCP usage, config transactions, cost, errors, and drift.

## Events to capture

- skill installed/updated/removed.
- skill invoked.
- MCP enabled/disabled/smoke-tested.
- config transaction previewed/applied/rolled back.
- docs generated/checked.
- OpenSpec validation result.
- CI conformance result.

## Fields

- timestamp.
- command.
- actor/environment.
- harness.
- capability id.
- version/ref.
- input hash.
- output hash.
- exit code.
- duration.
- cost estimate where applicable.
- error class.
- redaction status.

## Candidate integrations

- OpenTelemetry for traces/metrics/logs.
- Langfuse or Arize Phoenix for LLM/agent traces.
- Sentry for error reporting.
- local JSONL audit logs for offline use.

## Acceptance criteria

- No secrets in telemetry.
- Local-first audit trail works without external SaaS.
- Dashboard can render transaction history and drift state from logs/manifests.

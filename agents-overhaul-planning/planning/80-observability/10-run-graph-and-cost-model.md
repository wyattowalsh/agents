# Run Graph and Cost Model

## Objective

Represent repo automation as auditable run graphs across skills, MCPs, adapters, docs generation, OpenSpec, and CI.

## Source-backed ingredients

- OpenTelemetry GenAI semantic conventions exist for GenAI metrics, spans, events, agent spans, and MCP, but are currently development status.
- Langfuse and Phoenix both support LLM/agent tracing, prompt/eval workflows, and cost/latency visibility.

Sources:

- https://opentelemetry.io/docs/specs/semconv/gen-ai/
- https://langfuse.com/docs/observability/overview
- https://arize.com/docs/phoenix

## Proposed internal event schema

```json
{
  "run_id": "uuid",
  "transaction_id": "uuid|null",
  "phase": "inventory|render|apply|validate|rollback|audit",
  "capability_id": "docs-steward",
  "harness": "claude-code|null",
  "input_refs": [],
  "output_refs": [],
  "duration_ms": 0,
  "tokens": null,
  "cost_usd": null,
  "status": "pass|fail|warn|noop"
}
```

## Acceptance criteria

- CLI commands can emit structured run events.
- CI stores run graph artifacts.
- Dashboard can render drift/audit/transaction history without parsing logs.

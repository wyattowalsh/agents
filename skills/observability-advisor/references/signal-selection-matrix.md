# Signal Selection Matrix

Use this reference when deciding which signal types should answer a specific
operator question.

## Operator Question -> Preferred Signal

| Question | Primary Signal | Supporting Signals | Notes |
|----------|----------------|--------------------|-------|
| Is the user journey healthy right now? | Service-level metrics | Traces, structured logs | Start with latency, success rate, queue depth, or freshness tied to the journey |
| Which dependency is failing or slowing the journey? | Traces | Dependency metrics, error logs | Require stable correlation identifiers across boundaries |
| Why did this specific request or workflow fail? | Structured logs | Trace for the same request, workflow metrics | Use logs for local detail, trace for path reconstruction |
| Is the backlog, retry queue, or async worker unhealthy? | Workflow metrics | Queue logs, traces, saturation metrics | Prefer stalled-age and completion-lag signals over raw throughput alone |
| Is a rare edge case happening on a small subset of traffic? | Structured logs | Exemplars, traces | Logs can carry detail without forcing high-cardinality metric labels |
| Do we need fleet-level capacity or saturation awareness? | Metrics | Profile samples, infra logs | Keep this subordinate to user-impact signals |
| Do we need to understand a multi-hop latency regression? | Traces | Span events, dependency metrics | Sample enough for critical paths before expanding trace depth |

## Selection Rules

1. Start from the operator question, not from the easiest signal to emit.
2. Prefer metrics for fleet-wide detection and trend visibility.
3. Prefer traces for path reconstruction across service or queue boundaries.
4. Prefer structured logs for request-local detail, edge-case diagnosis, and low-frequency failures.
5. Add profiles or infra-level telemetry only when user-impact signals cannot explain the symptom.
6. Avoid adding the same fact to every signal type unless it materially shortens diagnosis time.

## Cost and Risk Checks

| Risk | Guardrail |
|------|-----------|
| High-cardinality dimensions | Keep identifiers in logs or traces unless aggregation by that dimension is essential |
| Sampling hides critical failures | Sample critical paths more aggressively before broadening retention |
| Logs become a data lake | Require a concrete diagnostic use for each field |
| Metrics hide request-local detail | Pair service-level detection with a trace or log path to investigate |
| Traces are too expensive to keep everywhere | Focus first on user-critical journeys and failure-prone boundaries |

# Investigation Workflows

Use this reference for symptom-first diagnosis that stays inside observability
planning rather than incident command.

## Baseline Investigation Flow

1. Confirm the symptom and its time window.
2. Check whether the symptom is user-visible, internal-only, or signal-quality-only.
3. Compare recent deploys, traffic shifts, backlog movement, and dependency health.
4. Correlate service metrics, traces, logs, and queue signals for the same window.
5. Build 2-4 hypotheses and name the next measurement that would disprove each one.
6. Separate telemetry blind spots from real system behavior.
7. If the task now requires live coordination, escalation ownership, or cross-team command, hand off to incident-response-engineer.

## Workflow by Symptom Shape

| Symptom | Start With | Then Check | Common Pitfall |
|---------|------------|------------|----------------|
| Rising 5xx | Service-level error rate metric | Trace failure clusters, structured error logs, dependency health | Jumping to one dependency before checking deployment or traffic shifts |
| High latency | Journey latency metric | Trace critical path, queue lag, downstream saturation | Optimizing internal hotspots before confirming user impact |
| Stalled async work | Queue age or completion-lag metric | Worker logs, retry volume, dependency failures | Watching throughput alone and missing backlog age |
| Missing data or freshness delay | Freshness metric | Upstream ingest health, queue backlog, last-success markers | Using success counts without checking age of data |
| Noisy alert with no customer impact | Alert history and acknowledgement notes | SLO burn, symptom dashboards, duplicate alerts | Treating every threshold breach as page-worthy |

## Investigation Guardrails

1. Do not claim root cause from one signal family alone.
2. Prefer a short hypothesis tree over a long brainstorm list.
3. Name the evidence gap explicitly when the telemetry is insufficient.
4. Escalate to incident-response-engineer when command-and-control is required.

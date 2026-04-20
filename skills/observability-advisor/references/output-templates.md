# Output Templates

Use these templates to keep deliverables consistent across modes.

## Design Template

```text
OBSERVABILITY DESIGN: {system}

Key questions:
- {question 1}
- {question 2}

Critical journeys and failure domains:
- {journey} -> {dependencies} -> {failure domains}

Signal plan:
| Boundary | Metric | Log | Trace/Span | Owner | Notes |
|----------|--------|-----|------------|-------|-------|

Dashboards and alerts:
- Dashboard: {name} -> owner: {team}
- Alert: {symptom} -> escalation: {path}

Constraints:
- Cardinality:
- Sampling:
- Retention:
```

## Review Template

```text
OBSERVABILITY REVIEW: {service}

Coverage gaps:
- {gap}

Alert quality issues:
- {issue}

Operational debt:
- {debt}

Ranked priorities:
1. {highest risk}
2. {next risk}
```

## Instrumentation Template

```text
INSTRUMENTATION PLAN: {workflow}

Boundary map:
- {boundary} -> {decision point}

Emissions:
| Boundary | Metric | Structured Log Fields | Span/Trace Data | Safety Notes |
|----------|--------|-----------------------|-----------------|-------------|

Rollout:
1. {highest-value boundary first}
2. {next boundary}
```

## Alert Template

```text
ALERT PLAN: {service or journey}

Paging alerts:
| Symptom | Threshold | Duration | Owner | Runbook | First Check |
|---------|-----------|----------|-------|---------|-------------|

Non-paging signals:
| Signal | Delivery | Owner | Why not page |
|--------|----------|-------|--------------|
```

## SLO Template

```text
SLO PLAN: {service or journey}

User promise:
- {promise}

SLI definition:
- Numerator:
- Denominator:
- Exclusions:
- Window:

SLO target:
- {target}

Error budget policy:
- {policy}
```

## Investigation Template

```text
INVESTIGATION PLAN: {symptom}

Verified symptom:
- {symptom and time window}

Evidence by signal:
- Metrics:
- Logs:
- Traces:
- Dependencies:

Hypotheses:
1. {hypothesis} -> next measurement: {check}
2. {hypothesis} -> next measurement: {check}

Assessment:
- Signal-quality issue vs system-behavior issue:
- Escalation boundary:
```

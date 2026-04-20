# Timeline and Postmortem Examples

## Timeline Entry Format

Capture only meaningful decisions, signals, and actions.

```text
[timestamp] [owner]
Event: [what happened]
Evidence: [metric, alert, customer report, deploy, log, trace, or verification]
Decision / action: [what changed]
Outcome: [result or next checkpoint]
```

## Example Timeline Snippet

```text
10:03 UTC IC
Event: Elevated checkout 5xx alert fired in eu-west.
Evidence: Alert threshold crossed and support tickets appeared within 3 minutes.
Decision / action: Declared SEV-2 and opened incident channel.
Outcome: Commander assigned and first update due at 10:18 UTC.

10:09 UTC On-call engineer
Event: Error rate correlated with latest payments deploy.
Evidence: 5xx spike began within 2 minutes of rollout; rollback candidate identified.
Decision / action: Began rollback in eu-west only.
Outcome: Error rate started to fall by 10:13 UTC.
```

## Postmortem Structure

1. Summary
2. Customer impact
3. Trigger and timeline
4. Contributing factors
5. Failed defenses
6. What accelerated recovery
7. Corrective actions

## Action Item Pattern

Each action item should name:

- owner
- due date
- expected measurable outcome
- verification method

Example:

```text
Owner: Payments platform team
Due: 2026-05-15
Action: Add deploy guard that blocks region rollout when checkout 5xx rises above baseline by 2x for 5 minutes.
Outcome: Faster automatic rollback on broken payments deploys.
Verification: Staging simulation and production drill evidence.
```

## Review Questions

- Did the timeline distinguish facts from assumptions?
- Did updates match what the timeline shows?
- Did corrective actions fix system weaknesses instead of restating lessons?

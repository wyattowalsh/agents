# Severity Matrix

Use severity to describe impact and response posture, not engineering effort.

## Calibration Heuristics

| Severity | Typical impact | Blast radius | Default response posture |
|----------|----------------|--------------|--------------------------|
| `SEV-1` | Service unavailable, major data loss risk, or clear revenue-critical outage | Broad customer or business-wide impact | Immediate commander, fixed update cadence, customer comms likely required |
| `SEV-2` | Major degradation or partial outage affecting an important journey | Multi-tenant, multi-region, or a high-value customer segment | Commander assigned, aggressive mitigation, stakeholder cadence started |
| `SEV-3` | Degradation with workaround, localized outage, or rising error risk not yet broad | Limited tenant, region, or workflow segment | Triage quickly, decide whether to escalate, prepare containment |
| `SEV-4` | Low-impact issue, single-customer pain, weak signal, or internal degradation with minimal user harm | Narrow or uncertain | Gather evidence, set checkpoint, escalate only if blast radius grows |

## Escalation Questions

Ask these before downgrading or delaying response:

1. Is a revenue, auth, checkout, or data-integrity path affected?
2. Is the issue spreading across tenants, regions, or dependencies?
3. Are customers reporting impact before monitoring explains it?
4. Would waiting 15 minutes materially increase user harm?

If two or more answers are yes, bias toward the higher severity until evidence narrows the blast radius.

## Reassessment Triggers

Re-evaluate severity whenever:

- blast radius expands or contracts
- mitigation fails or causes secondary impact
- a workaround is confirmed
- recovery is partial rather than complete
- customer-facing impact is disproven or newly confirmed

## Output Checklist

Every live severity decision should name:

- current severity
- business impact
- blast radius
- commander
- next checkpoint time
- what evidence could change severity

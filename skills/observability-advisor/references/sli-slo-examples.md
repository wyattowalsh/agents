# SLI and SLO Examples

Use this reference when selecting SLI types, windows, or error-budget policy.

## Example Patterns

### Availability

| Field | Example |
|-------|---------|
| User promise | Customers can complete checkout successfully |
| SLI | Successful checkout requests / total valid checkout requests |
| Window | 30 days |
| SLO | 99.9% success |
| Error budget policy | Freeze risky launches if burn exceeds 25% of monthly budget in one week |

### Latency

| Field | Example |
|-------|---------|
| User promise | Search results return quickly enough for interactive use |
| SLI | Percentage of search requests under 750 ms at p95 |
| Window | 7 days rolling |
| SLO | 99% of requests meet the latency threshold |
| Error budget policy | Require mitigation plan when 2-hour burn rate predicts exhaustion inside 7 days |

### Freshness

| Field | Example |
|-------|---------|
| User promise | Customer webhook deliveries are processed within acceptable delay |
| SLI | Percentage of webhook events delivered within 2 minutes of receipt |
| Window | 28 days |
| SLO | 99.5% within 2 minutes |
| Error budget policy | Pause non-critical queue consumers and prioritize backlog recovery when burn spikes |

### Correctness

| Field | Example |
|-------|---------|
| User promise | Billing totals are computed correctly |
| SLI | Correct invoices / total invoices, measured from reconciliation outcomes |
| Window | 30 days |
| SLO | 99.99% correctness |
| Error budget policy | Escalate immediately because correctness failures can require customer remediation |

## Selection Notes

1. Start from the user promise, then choose the narrowest measurable proxy.
2. Keep numerator, denominator, exclusions, and window explicit.
3. Split availability, latency, freshness, and correctness when one blended metric would hide tradeoffs.
4. Exclusions must be policy-driven and reviewable, not ad hoc.
5. Error budget policy must say what decisions change when burn rises.

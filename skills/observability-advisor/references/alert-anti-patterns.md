# Alert Anti-Patterns

Use this reference when reviewing or designing alerts.

## Common Anti-Patterns

| Anti-Pattern | Why It Fails | Preferred Fix |
|--------------|--------------|---------------|
| Page on every error log spike | Noise rises before operator relevance is proven | Tie paging to user symptoms, burn rate, or stalled workflow evidence |
| Page multiple teams on the same symptom | Creates duplicate wakeups and diffused ownership | Define one owner per symptom and route supporting teams through the runbook |
| Page on CPU or memory alone | Internal stress does not always equal user harm | Use resource signals as supporting evidence unless they predict user-visible failure |
| Alert without runbook or first-check guidance | Operator loses time deciding what to inspect first | Include owner, runbook, and first evidence path for every paging alert |
| Threshold copied from another service | Ignores workload shape, seasonality, and business tolerance | Calibrate by user promise and actual traffic behavior |
| Separate alerts for every layer of one failure | One outage becomes many pages | Group alerts around the user symptom and keep component signals informational |
| Page on tiny sample sizes | High false-positive rate | Require enough volume or time window for the signal to be meaningful |
| Ticket-level issues promoted to paging | Operators burn attention on non-urgent work | Downgrade to review queue, dashboard, or business-hours ticket |

## Alert Quality Checklist

1. What user or operator action does this alert demand?
2. Who owns the first response?
3. What should the operator inspect first?
4. Is this symptom already covered by another alert?
5. Can the alert be tied to SLO burn, stalled work, or a user-facing threshold?
6. Would this page still be useful at 3 a.m. with no extra context?

## Page vs Ticket vs Dashboard

| Delivery | Use When |
|----------|----------|
| Page | Immediate operator action is required to protect users or stop fast budget burn |
| Ticket | Follow-up work is needed, but delayed response is acceptable |
| Dashboard | The signal is useful context or planning input, not an interrupt |

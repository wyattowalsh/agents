# Containment and Recovery Decision Aids

Containment reduces immediate harm. Recovery restores accepted behavior. Keep them separate even when the same action helps both.

## Fast Containment Options

| Option | Best when | Trade-off to call out |
|--------|-----------|-----------------------|
| Rollback | Latest deploy is the strongest suspect and rollback is fast | Loses newest change and may not fix data-side issues |
| Traffic shift | Regional or cluster-local failure exists | May overload healthy capacity if shift is too broad |
| Feature flag disable | Fault is isolated to a feature path | Removes functionality and may create secondary support load |
| Dependency isolation | A downstream is degraded and graceful degradation exists | User experience may remain degraded |
| Failover | Standby path is proven and healthy | Can increase complexity, lag, or operational risk |
| Rate limiting / degraded mode | Stability is at risk from load or backlog | Preserves core service but reduces experience |

## Decision Questions

Before choosing a containment action:

1. Which option reduces customer harm fastest?
2. Which option is reversible if it fails?
3. What evidence would tell us the action worked within one checkpoint?
4. What secondary blast radius could this action create?

## Recovery Confirmation

Do not declare recovered until:

- user-visible symptoms have cleared
- the key metric or health signal is back within accepted bounds
- the chosen mitigation is stable over at least one review window
- customer-facing teams know the current state

## Recovery States

- `contained`: spread stopped, but users may still feel impact
- `partially recovered`: primary path improved, but residual risk or degraded mode remains
- `fully recovered`: service restored and exit criteria met

## Abort Signals

Reverse or change strategy if:

- the chosen mitigation worsens blast radius
- the recovery signal does not improve by the next checkpoint
- a supposedly isolated action triggers a second failure domain

# Rollout Decision Matrix

Use this file when selecting the production exposure pattern in `design`, `cutover`, or `hotfix`.

## Choose the Simplest Safe Pattern

| Pattern | Best When | Avoid When | Operational Tradeoff |
|---------|-----------|------------|----------------------|
| `all-at-once` | Small blast radius, fast rollback, short validation loop, low state coupling | Recovery is slow, customer impact is hard to detect quickly, or state changes are irreversible | Fastest routine lane, highest immediate exposure |
| `canary` | A small slice of traffic can reveal regressions quickly and rollback is still cheap | User segmentation is impossible or partial exposure creates data inconsistency | Best default for medium-risk releases |
| `phased` | Exposure can expand by tenant, region, cohort, or feature flag with clear checkpoints | There is no reliable segmentation or phase ownership is unclear | Slower but easier to observe and pause |
| `blue/green` | Environment swap is cheap, rollback must be near-instant, and state migration is controlled | Stateful changes cannot be made safely reversible or maintaining two environments is too costly | Highest infrastructure cost, fastest environment rollback |

## Selection Questions

Answer these before recommending a rollout shape:

1. What is the maximum acceptable customer impact before rollback?
2. How quickly can operators detect failure from production signals?
3. Can exposure be segmented by tenant, region, or traffic slice?
4. Do state migrations, caches, queues, or background workers make rollback asymmetric?
5. Can the team keep two production-ready environments healthy if needed?

## Default Guidance

- Prefer `all-at-once` for low-blast-radius routine releases with fast detection and clean rollback.
- Prefer `canary` when risk is moderate and a small traffic slice is meaningful.
- Prefer `phased` when exposure needs explicit human checkpoints across cohorts.
- Prefer `blue/green` only when environment-level swap and rollback justify the extra platform complexity.

## Escalation Triggers

Escalate to a safer rollout pattern when any of these are true:

- Rollback requires manual data repair or cache invalidation.
- Recovery depends on multiple teams coordinating under time pressure.
- The release changes authentication, payments, traffic routing, or critical background processing.
- Observability is weak enough that a bad release could hide for more than one decision window.

# Output Templates

Keep responses concise but make the operating decisions explicit.

## Design Template

1. Processing model
2. Sources, sinks, and consumers
3. Stage-by-stage flow
4. Contract at each boundary
5. Checkpoint, replay, and late-data strategy
6. Reliability and observability controls
7. Cost constraints and scaling note
8. Open assumptions or missing inputs

## Review Template

1. Current topology summary
2. Reliability findings
3. Data quality findings
4. Cost and operator burden findings
5. Highest-risk gaps
6. Recommended next changes
7. Missing information that would change the review

## Operate Template

1. Service-level objectives
2. Checkpoint and retry boundaries
3. Quarantine and invalid-record handling
4. Backfill and replay path
5. Alerts and dashboards
6. Immediate operator actions
7. Recovery assumptions that need confirmation

## Migrate Template

1. Current state and migration target
2. Coexistence plan
3. Validation checkpoints
4. Rollback triggers
5. Cutover sequence
6. Post-cutover cleanup
7. Migration risks that need operator review

## Contract Template

1. Dataset owner and consumers
2. Schema and versioning rule
3. Freshness and quality targets
4. Breaking vs non-breaking changes
5. Invalid-record handling
6. Replay and backfill expectations
7. Change-management expectations for consumers

## Output Quality Checklist

- Name the processing model explicitly instead of implying it.
- Keep contracts and ownership visible at every producer-consumer handoff.
- Separate replay, retry, and backfill rather than blending them together.
- Distinguish correctness risk from cost risk and operator burden.
- Call out missing assumptions when a prompt does not provide enough input to be confident.

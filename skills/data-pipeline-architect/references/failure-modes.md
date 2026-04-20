# Data Pipeline Failure Modes

Use this as a review and operate checklist before recommending architecture or
recovery changes.

## How to Use This Checklist

- Scan for symptoms first, then map each symptom to a likely broken boundary.
- Separate source errors, transform errors, and publish errors before proposing retries.
- Check whether the team can prove what data is safe to replay; if not, prioritize state clarity first.

| Failure mode | Typical symptom | Design control |
|--------------|-----------------|----------------|
| Silent data loss | Downstream counts drift with no obvious task failure | Explicit row-count, freshness, and lineage checkpoints at publish boundaries |
| Duplicate publish | Replays or retries produce duplicate outputs | Idempotent sink writes, dedupe keys, and stage-specific retry boundaries |
| Late-data corruption | Metrics change after window close with no audit trail | Watermark rules, reopen policy, and separate late-data path |
| Unbounded backlog | Freshness degrades while jobs still succeed | Capacity thresholds, queue or partition backlog alerts, scalable checkpoint cadence |
| Poison records block progress | One bad record stalls an entire batch or topic | Quarantine lane, invalid-record threshold, and operator-visible triage metadata |
| Hidden contract break | Pipeline runs but downstream semantics change unexpectedly | Versioned contract with explicit breaking-change rules and validation gates |
| Replay harms live path | Backfill competes with production processing | Isolated replay capacity, separate output namespace or staging boundary, cutover validation |
| No trustworthy recovery point | Operators cannot tell what already succeeded | Durable checkpoints with stage ownership and timestamped recovery metadata |
| Cost blowout | Pipeline remains correct but becomes too expensive to operate | Right-sized cadence, bounded retention, selective enrichment, and cost-by-stage visibility |

## Review Questions

- What exact boundary would let an operator restart safely after partial success?
- Which failure mode would cause silent wrong data rather than an obvious task failure?
- Does the pipeline quarantine invalid records, or does one poison record halt useful progress?
- Can the team distinguish live freshness debt from replay or backfill debt?
- Are cost spikes isolated to one stage, or hidden across the whole pipeline?

## Response Priorities

1. Protect correctness before speed.
2. Make recovery state explicit before recommending aggressive retries.
3. Isolate replay and backfill from the live path.
4. Tighten contracts before layering more observability on top.
5. Add cost controls only after recovery and correctness remain intact.

# Worked Examples

Use these examples to anchor recommendations without drifting into vendor-
specific implementation.

## How to Read the Examples

- Each example highlights the topology choice, the contract boundary, and the recovery posture.
- Reuse the shape, not the domain nouns; keep the skill vendor-neutral.
- If a user prompt is partial, adapt the closest example and then call out the missing assumptions.

## Example 1: Nightly SaaS Billing Batch

- **Mode fit:** `design`
- **Topology:** API extract -> raw landing zone -> validation -> invoice normalization -> warehouse publish
- **Why batch:** Source exposes a daily export and correctness matters more than sub-hour freshness
- **Key controls:** contract at export handoff, checkpoint after raw landing, quarantine for malformed invoices, replay from raw landing rather than source API
- **What to watch:** export completeness, delayed invoice corrections, and duplicate publish during recovery

## Example 2: Clickstream to Warehouse and Feature Store

- **Mode fit:** `design` or `contract`
- **Topology:** event ingest -> schema validation -> stream enrichment -> warehouse sink + feature-serving sink
- **Why hybrid:** low-latency features need fast updates, but warehouse truth still benefits from replayable durable ingestion
- **Key controls:** event contract with ordering and retention expectations, watermark for lateness, separate backfill path for warehouse rebuilds
- **What to watch:** late mobile events, schema evolution for downstream consumers, and backlog growth under traffic spikes

## Example 3: Cron Scripts to Managed Orchestration

- **Mode fit:** `migrate`
- **Topology:** existing cron extract/transform scripts -> staged orchestrated tasks -> dual-run validation -> cutover -> contract hardening
- **Why migrate gradually:** preserve source-of-truth semantics and keep rollback simple while hidden dependencies are surfaced
- **Key controls:** stage-by-stage parity checks, explicit coexistence window, separate migration-state tracking, rollback trigger tied to freshness and correctness deltas
- **What to watch:** hidden side effects in scripts, missing lineage, and rollback confusion during dual-run

## Example 4: Pipeline Reliability Review

- **Mode fit:** `review` or `operate`
- **Prompt shape:** “review failed partitions and freshness drift in our nightly orders ETL”
- **Expected output:** reliability findings, data-quality findings, cost or operator burden findings, then checkpoint/replay/quarantine plan
- **What to watch:** whether the review distinguishes data loss from task failure and whether replay shares state with the live path

## Example 5: Contract Hardening for Shared Dataset

- **Mode fit:** `contract`
- **Topology:** producer-owned curated dataset -> multiple downstream consumers with different freshness expectations
- **Why contract mode:** the topology exists, but ownership, versioning, and invalid-record handling are unclear
- **Key controls:** named owner, breaking-change policy, freshness target, validation set, consumer replay expectations
- **What to watch:** consumer assumptions hidden in downstream transforms and undocumented non-breaking changes

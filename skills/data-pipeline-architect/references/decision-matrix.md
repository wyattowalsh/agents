# Data Pipeline Decision Matrix

Use this matrix when the processing model, contract style, or replay posture is
not obvious from the prompt.

## Quick Triage

- Start with user-facing freshness and correctness requirements, not the fanciest runtime.
- Match the topology to source reality first: exports, CDC, APIs, and event streams do not deserve the same design.
- Keep replay posture explicit before optimizing latency, because recovery shape often determines the true architecture.

## Processing Model

| Condition | Prefer | Why |
|-----------|--------|-----|
| Minutes-to-hours latency is acceptable and source data is naturally periodic | Batch | Simpler checkpoints, lower operator overhead, easier cost control |
| Seconds-level latency matters and records can arrive out of order | Streaming | Continuous processing with watermark-based completeness |
| Core flow can run in batch but some consumers need faster freshness | Hybrid | Preserve simple batch truth while exposing faster derived paths |
| Upstream access is rate-limited or only available by export | Batch | Matches source reality and reduces brittle polling loops |
| Replay cost is high but selective reprocessing matters | Hybrid | Keep a stable batch truth path and targeted streaming enrichment |

## Consumer and Sink Shape

| Consumer shape | Bias | Why |
|----------------|------|-----|
| Single warehouse sink | Batch | Simplest lineage, validation, and replay semantics |
| Warehouse plus low-latency online feature path | Hybrid | Separate slow truth from fast serving needs |
| Multiple downstream operational consumers | Streaming or hybrid | Contract, retention, and ordering become first-class concerns |
| Compliance or finance consumers | Batch unless latency clearly dominates | Auditability and replay clarity usually matter more than immediacy |

## Contract Style

| Situation | Contract emphasis |
|-----------|-------------------|
| Internal handoff between tightly aligned teams | Ownership, freshness target, validation rules, rollback expectations |
| Cross-team or cross-domain dataset | Versioning, breaking vs non-breaking changes, lineage, SLA/SLO ownership |
| Event stream with multiple consumers | Ordering guarantees, replay expectations, retention window, schema evolution |
| File drop or API ingestion | Arrival semantics, duplicate handling, invalid-record policy, cutoff window |

## Checkpoint and Recovery Shape

| Topology | Checkpoint bias | Recovery note |
|----------|-----------------|---------------|
| Simple batch | End-of-stage checkpoint | Retry whole stage if outputs are idempotent |
| Multi-stage batch | Stage checkpoint plus publish checkpoint | Keep publish restart separate from upstream extract |
| Streaming | Offset or watermark checkpoint | Reconcile lateness and replay windows explicitly |
| Hybrid | Separate live and backfill checkpoints | Do not share recovery state across the two paths |

## Replay and Recovery Posture

| Failure pattern | Recommended posture |
|-----------------|---------------------|
| Transient infrastructure or network errors | Retry from last checkpoint with bounded backoff |
| Logic bug that corrupted derived outputs | Pause live path, fix transform, replay from last trusted boundary |
| Late-arriving records within tolerated window | Merge through late-data path without reprocessing entire history |
| Historical backfill for newly added consumer | Run isolated backfill path with explicit coexistence and validation |
| Contract-breaking upstream change | Quarantine invalid records, hold publish, renegotiate contract before replay |

## Anti-Patterns

- Choosing streaming only because it feels more modern
- Treating retries as the replay strategy
- Sharing one checkpoint namespace between live, replay, and migration paths
- Defining sink schemas without a producer-consumer contract
- Optimizing cost before understanding correctness and recovery requirements

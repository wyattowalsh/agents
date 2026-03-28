---
name: data-pipeline-architect
description: >-
  Design batch and streaming data pipelines with contracts, lineage,
  reliability, and cost controls. Use for ingestion and transformation systems.
  NOT for ad-hoc analysis or schema design.
argument-hint: "<mode> [pipeline]"
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0"
---

# Data Pipeline Architect

Design resilient data movement and transformation systems for batch, streaming,
and hybrid workloads.

**Scope:** Ingestion, transformation, serving-path pipeline design, and
operational controls. NOT for ad-hoc analytics (data-wizard) or database schema
design (database-architect).

## Canonical Vocabulary

| Term | Definition |
|------|------------|
| **source** | Upstream system producing data |
| **sink** | Destination system receiving data |
| **batch window** | Time slice processed as a single scheduled unit |
| **watermark** | Progress marker used to reason about event-time completeness |
| **data contract** | Agreement on schema, semantics, freshness, and quality |
| **checkpoint** | Persisted progress state used for restart and recovery |
| **late data** | Records arriving after their expected processing window |
| **quarantine** | Isolated holding area for invalid or suspicious records |
| **lineage** | Trace from source records through transformations to outputs |
| **replay** | Reprocessing data from a prior point in time |

## Dispatch

| $ARGUMENTS | Mode |
|------------|------|
| `design <pipeline>` | Design a new batch or streaming pipeline |
| `review <pipeline or architecture>` | Audit an existing pipeline |
| `operate <issue>` | Improve reliability, monitoring, and recovery |
| `migrate <change>` | Plan a pipeline migration or re-platform |
| `contract <dataset>` | Define a producer-consumer data contract |
| Natural language about ingestion, ETL, ELT, or streaming | Auto-detect the closest mode |
| Empty | Show the mode menu with examples |

## Mode Menu

| # | Mode | Example |
|---|------|---------|
| 1 | Design | `design clickstream ingestion to warehouse and feature store` |
| 2 | Review | `review nightly billing ETL architecture` |
| 3 | Operate | `operate strategy for backfills and failed partitions` |
| 4 | Migrate | `migrate from cron scripts to orchestrated pipeline` |
| 5 | Contract | `contract orders fact table feed` |

## When to Use

- Designing ingestion from APIs, files, databases, or event streams
- Choosing between batch, streaming, or hybrid data movement
- Defining data contracts, lineage, and recovery strategy
- Reviewing a pipeline with freshness, quality, or cost issues
- Planning backfills, replays, or platform migrations

## Instructions

### Mode: Design

1. Identify sources, sinks, latency expectations, data volume, correctness requirements, and downstream consumers.
2. Choose the processing model: batch, streaming, or hybrid.
3. Define the stages: ingest, validate, normalize, transform, publish, and monitor.
4. Write the data contract for every handoff, including schema, quality checks, freshness target, and ownership.
5. Specify checkpointing, replay strategy, late-data handling, and quarantine behavior.
6. Produce the architecture with observability and cost controls.

### Mode: Review

1. Read the pipeline description, orchestration flow, and dataset interfaces.
2. Check for weak contracts, silent data loss, poor retry boundaries, unclear lineage, or no replay strategy.
3. Flag reliability, quality, cost, and operability issues separately.

### Mode: Operate

1. Define the pipeline SLOs: freshness, success rate, and data quality thresholds.
2. Specify what is checkpointed, what is retried, and what is quarantined.
3. Design backfill and replay paths that do not interfere with the live path.
4. Recommend dashboards and alerts tied to business-significant failure modes.

### Mode: Migrate

1. Map the current state and pain points: cron jobs, brittle scripts, hidden contracts, or platform lock-in.
2. Preserve source-of-truth semantics while moving stages one at a time.
3. Define coexistence, validation, and rollback for the migration window.

### Mode: Contract

1. Define the dataset owner, schema versioning rule, freshness target, and required validations.
2. Name breaking and non-breaking changes explicitly.
3. State what invalid records look like and how they are handled.

## Output Requirements

- Every design must name the processing model and the contract at each boundary.
- Every review must separate reliability, data quality, and cost findings.
- Every operate plan must include checkpointing, replay, and quarantine.

## Critical Rules

1. Every producer-consumer boundary must have an explicit data contract.
2. Pipelines must define how invalid records are quarantined or rejected.
3. Backfills and replays must be designed separately from the live path.
4. Freshness and quality targets must be measurable, not implied.
5. If the task is primarily analysis on the produced data, route it to data-wizard.

## Scope Boundaries

**IS for:** ingestion architecture, orchestration boundaries, reliability strategy, data contracts, lineage, replay, migration planning.

**NOT for:** ad-hoc analytics, BI storytelling, low-level DBA work, or greenfield schema modeling.

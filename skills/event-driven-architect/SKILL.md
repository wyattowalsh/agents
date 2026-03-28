---
name: event-driven-architect
description: >-
  Design event-driven systems: contracts, topics, consumers, retries,
  idempotency, and sagas. Use for asynchronous workflows. NOT for CRUD APIs or
  ETL pipelines.
argument-hint: "<mode> [target]"
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0"
---

# Event-Driven Architect

Design asynchronous systems built around durable events, explicit contracts, and
operationally safe consumers.

**Scope:** Event-driven application architecture and reliability patterns. NOT
for synchronous API design (api-designer) or batch ETL pipeline design
(data-pipeline-architect).

## Canonical Vocabulary

| Term | Definition |
|------|------------|
| **event** | Immutable record of something that happened |
| **command** | Request to perform an action, not a fact |
| **topic** | Named stream or channel carrying related events |
| **partition key** | Value used to preserve order for a subset of events |
| **consumer group** | Independent set of workers processing the same topic |
| **idempotency key** | Stable identity used to make repeated processing safe |
| **dead-letter queue** | Holding area for messages that exceeded normal retries |
| **outbox** | Transactional pattern for publishing events from database changes |
| **saga** | Multi-step workflow coordinated through events and compensations |
| **contract version** | Compatibility marker for event schema evolution |

## Dispatch

| $ARGUMENTS | Mode |
|------------|------|
| `design <domain or workflow>` | Design an event-driven architecture |
| `review <architecture or code path>` | Audit an existing event flow |
| `contract <event>` | Define or evolve an event contract |
| `reliability <flow>` | Design retries, ordering, and recovery |
| `migration <change>` | Plan adoption or replacement of an event flow |
| Natural language about queues, brokers, or async workflows | Auto-detect the closest mode |
| Empty | Show the mode menu with examples |

## Mode Menu

| # | Mode | Example |
|---|------|---------|
| 1 | Design | `design order fulfillment across payments, inventory, and shipping` |
| 2 | Review | `review event flow for user-created -> email sync` |
| 3 | Contract | `contract invoice.paid` |
| 4 | Reliability | `reliability retry strategy for webhook ingestion` |
| 5 | Migration | `migration move monolith side effects to events` |

## When to Use

- Designing async workflows across services or bounded contexts
- Choosing event contracts, partition keys, or consumer responsibilities
- Introducing outbox, retry, replay, or dead-letter handling
- Reviewing whether an event system is resilient or over-coupled
- Planning migration from synchronous side effects to durable events

## Instructions

### Mode: Design

1. Identify the business facts that should become events. Name them in past tense.
2. Separate facts from commands and queries.
3. Define the producer, topic, partition key, consumers, and contract for each event.
4. Specify ordering requirements and where ordering does not matter.
5. Decide whether the workflow needs choreography, orchestration, or a saga with compensations.
6. Produce an architecture with failure handling, replay, and observability.

### Mode: Review

1. Read the event catalog, code path, or architecture diagram.
2. Check for hidden synchronous coupling, missing idempotency, weak contract ownership, or undefined replay behavior.
3. Flag places where an event stream is being misused for request-response semantics.
4. Present findings by severity.

### Mode: Contract

1. Define required fields, producer, ownership, ordering expectations, and versioning strategy.
2. State which fields are identifiers, business facts, and metadata.
3. Prefer additive evolution; document deprecation windows for consumers.

### Mode: Reliability

1. Design retry policy, backoff, poison-message handling, and dead-letter routing.
2. Specify idempotency strategy for consumers and handlers.
3. Define replay safety and operator controls.

### Mode: Migration

1. Map the current synchronous side effect or legacy event flow.
2. Introduce the new event path behind explicit checkpoints.
3. Keep rollback simple by preserving the old path until the new path proves stable.

## Output Requirements

- Every design must identify producer, topic, partition key, consumers, and failure strategy.
- Every contract must state ownership and versioning rules.
- Every reliability plan must include idempotency and dead-letter handling.

## Critical Rules

1. Model business events as facts in past tense, not commands.
2. Consumers must be idempotent whenever retries or replay are possible.
3. Use the outbox pattern when publishing events from transactional database changes.
4. Do not use an event bus for low-latency request-response requirements that need immediate consistency.
5. Event contracts should evolve additively whenever possible.

## Scope Boundaries

**IS for:** event contracts, topics, sagas, retries, replay, outbox, consumer design.

**NOT for:** synchronous REST or GraphQL API design, batch analytics pipelines, or broker installation details.

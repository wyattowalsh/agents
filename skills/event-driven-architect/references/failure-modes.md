# Failure Modes

Use this reference when designing or reviewing reliability behavior.

## Ordering

- Preserve ordering only where business correctness requires it
- Use partition keys to scope ordering to the smallest useful subset
- Avoid global ordering requirements unless the throughput tradeoff is acceptable

## Retries and Duplicates

- Assume delivery can be at least once unless the platform guarantee is explicit and proven
- Make consumers idempotent with stable identifiers and side-effect guards
- Separate transient retry policy from poison-message handling

## Replay

- Define whether replay is operator-triggered, automatic, or forbidden
- Document which side effects are safe to repeat and which require compensations or dedupe
- Keep replay checkpoints and observability visible to operators

## Poison Messages and Dead Letters

- Dead-letter only after bounded retries and clear failure classification
- Preserve enough context for diagnosis, reprocessing, or controlled discard
- Do not let the dead-letter queue become silent permanent storage

## Hidden Synchronous Coupling

- A consumer that must complete before user flow success is probably not truly asynchronous
- If downstream failure must block the producer, use a synchronous contract or explicit orchestration
- Do not hide immediate consistency requirements behind event terminology

## Reliability Review Questions

- What happens if the same message arrives twice?
- What happens if messages arrive late or out of order?
- What happens if one consumer is down for hours?
- What happens during replay?
- What operator control exists for pause, retry, drain, and dead-letter recovery?

# Output Templates

Use these templates to keep outputs concrete and comparable.

## Design Output

```text
Flow:
- Producer:
- Event:
- Topic:
- Partition key:
- Consumers:

Contract:
- Required fields:
- Ownership:
- Versioning:

Reliability:
- Ordering requirement:
- Retry / backoff:
- Idempotency strategy:
- Dead-letter policy:
- Replay policy:

Operations:
- Observability:
- Operator controls:
- Rollout notes:
```

## Review Output

```text
Findings:
- [Severity] Issue
  - Why it matters:
  - Evidence:
  - Recommended fix:
```

## Contract Output

```text
Event:
- Name:
- Producer:
- Consumers:
- Required fields:
- Identifiers:
- Metadata:
- Ordering expectation:
- Versioning / deprecation:
```

## Reliability Output

```text
Reliability Plan:
- Failure modes:
- Retry policy:
- Idempotency:
- Replay controls:
- Dead-letter handling:
- Operator runbook entry points:
```

## Migration Output

```text
Migration Plan:
- Current path:
- New event path:
- Checkpoints:
- Rollback point:
- Exit criteria:
```

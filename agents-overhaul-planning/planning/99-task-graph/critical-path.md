# Critical Path

The critical path is:

```text
C00-001 -> C00-009 -> C00-010 -> C01-001 -> C01-002 -> C01-003 -> C01-009 -> C02-001 -> C03-005 -> C04-001 -> C05-006 -> C06-001 -> C07-008 -> C08-001 -> C09-001
```

## Bottlenecks

1. Registry schema freeze.
2. Skill-vs-MCP decision tree acceptance.
3. Transaction engine contract.
4. Harness golden fixture stability.
5. Docs truth generation.
6. OpenSpec reconciliation.

## Parallelism unlocked after schema freeze

Once `C01-018` locks registry schema version v1, harness teams, skill packaging, MCP curation, docs generation, and UI/UX flows can proceed with minimal file conflicts.

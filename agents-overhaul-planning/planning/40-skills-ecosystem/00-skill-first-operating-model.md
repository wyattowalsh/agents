# Skill-First Operating Model

## Objective

Make skills the default reusable extension format.

## Principles

1. Package reusable workflows as skills before considering MCP.
2. Keep skill bodies concise and use references/assets/scripts for deeper detail.
3. Prefer deterministic CLI scripts with explicit args and JSON output.
4. Pin or lock external skills before using them in production workflows.
5. Validate every skill package in CI.
6. Treat external skills as supply-chain artifacts.

## Skill lifecycle

```text
discover -> evaluate -> pin -> install -> validate -> project -> document -> monitor -> update/rollback
```

## Required registry fields

- skill id.
- source URL.
- package path.
- version/ref.
- checksum/provenance.
- license.
- maintainers.
- compatibility.
- script inventory.
- allowed tools.
- security posture.
- harness projections.
- test fixtures.

## Acceptance criteria

- Every local skill has a registry entry.
- Every external skill has a trust classification.
- Every script-backed skill has CLI conformance tests.

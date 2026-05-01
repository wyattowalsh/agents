# Adapter Contract

## Objective

Define a common contract for projecting canonical capabilities into harness-specific files, config, plugins, skills, MCP definitions, OpenAPI actions, and instruction/rules files.

## Adapter input

```yaml
registry_version: string
repo_inventory: object
environment_overlay: object
harness: string
capabilities:
  skills: []
  mcps: []
  plugins: []
  instructions: []
policy: object
```

## Adapter output

```yaml
planned_operations:
  - type: write_file | update_json | update_yaml | run_command | noop
    path: string
    before_hash: string | null
    after_hash: string | null
    content_ref: string | null
    safety: safe | review-required | blocked
validation:
  schema_checks: []
  smoke_tests: []
  docs_checks: []
rollback:
  snapshot_paths: []
  restore_strategy: string
```

## Requirements

- Adapters must be deterministic.
- Adapters must not directly mutate files.
- All writes route through the transaction engine.
- Every generated artifact must be traceable to registry source.
- Adapters must emit enough metadata for docs and CI.

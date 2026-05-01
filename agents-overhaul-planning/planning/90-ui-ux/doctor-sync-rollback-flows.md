# Doctor, Sync, and Rollback Flows

## `doctor`

Inputs:

- repo inventory;
- user environment;
- harness registry;
- skill/MCP registries;
- OpenSpec state.

Outputs:

- health table;
- warnings;
- missing prerequisites;
- remediation command suggestions;
- machine-readable report.

## `sync --preview`

Guarantees:

- no writes;
- deterministic output;
- includes all generated file diffs;
- includes transaction risk score.

## `sync --apply`

Guarantees:

- creates backup snapshot;
- applies atomic writes where possible;
- validates after write;
- logs transaction;
- rolls back on blocking validation failure.

## `rollback`

Guarantees:

- restores selected snapshot;
- verifies restored hashes;
- emits audit log;
- explains what changed.

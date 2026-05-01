# CLI Contract for Skill Scripts

## Required for executable skill scripts

Every script under `skills/*/scripts/` should define:

```text
--help
--version or embedded version metadata
--json for machine-readable output when useful
--dry-run for mutations
--input/--output explicit paths where applicable
non-zero exit codes for failures
stderr for logs, stdout for data
```

## Exit code policy

| Code | Meaning |
|---:|---|
| 0 | success |
| 1 | validation/domain failure |
| 2 | missing dependency/env/prerequisite |
| 3 | unsafe operation blocked |
| 4 | network/source unavailable |
| 5 | internal bug |

## Test requirements

- Golden stdout/stderr tests.
- Invalid input tests.
- Dry-run no-write tests.
- Idempotence test for repeated run.
- ShellCheck/Ruff/ty tests depending on language.

# Config Transaction Blueprint

## Objective

Make harness config changes safe, reviewable, atomic, and reversible.

## Transaction phases

1. **Discover**: read current repo and user config paths.
2. **Resolve**: compute desired state from registry and overlays.
3. **Render**: produce candidate config/doc writes.
4. **Diff**: show normalized change set.
5. **Backup**: snapshot files before write.
6. **Apply**: write via atomic temp-file + rename where possible.
7. **Validate**: run schema/golden/smoke checks.
8. **Rollback**: restore backup if validation fails or user requests.
9. **Audit**: persist transaction record.

## Required commands

```bash
wagents doctor
wagents sync --preview
wagents sync --apply
wagents rollback
wagents audit configs
```

## Acceptance criteria

- Preview mode is side-effect free.
- Apply mode creates rollback snapshot.
- Rollback mode verifies restored state.
- Failed validation triggers guided remediation or automatic rollback.

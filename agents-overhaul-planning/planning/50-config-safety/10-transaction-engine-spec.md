# Transaction Engine Spec

## Objective

Ensure all config writes are previewable, atomic, auditable, and reversible.

## Transaction states

```text
planned -> previewed -> backed_up -> applied -> validated -> committed
                                 \-> failed -> rolled_back
```

## Transaction record

```json
{
  "transaction_id": "2026-05-01T...",
  "command": "wagents sync --apply --agent claude-code",
  "inputs": ["harness-registry.yaml", "skill-registry.yaml"],
  "writes": [
    {"path": ".claude/skills/...", "before_hash": "...", "after_hash": "..."}
  ],
  "backups": [".wagents/backups/<id>/..."],
  "validation": {"status": "pass", "gates": []},
  "rollback_command": "wagents rollback <id>"
}
```

## Safety rules

- No write without preview unless `--yes` is explicit and CI-safe.
- Backups are required before overwriting existing files.
- Generated files include source manifest hash.
- User-owned config files are modified only through patch operations or explicit replace confirmation.
- Rollback verifies restored hashes.

# Session ledger

Parent maintains a runtime ledger (gitignored). Suggested path: `.grok-delegate-ledger.jsonl` in the target repo or a user-owned state dir.

## Record shape

```json
{
  "node_id": "w1-api-3",
  "wave": 1,
  "sessionId": "019ef3d7-75a0-7743-8172-afb2f9433c7a",
  "worktree": "w1-api-3",
  "agent": "code-reviewer",
  "cwd": "/absolute/path/to/repo",
  "status": "working",
  "stopReason": null,
  "parent_tune_count": 0,
  "started_at": "2026-06-23T09:37:00Z",
  "completed_at": null
}
```

## Status values

- `working` — subprocess running
- `completed` — gate passed
- `tuned` — completed after one or more tune passes
- `failed` — exhausted retries or unrecoverable error
- `abandoned` — parent cancelled branch

## Accounting rule

N dispatched nodes = N terminal statuses before the next wave gate opens.

## Tune triggers

- `stopReason` indicates wrong or incomplete scope
- Parent gate failure (tests, review)
- User mid-flight redirect
- Stall timer (parent-owned; default 30m per build node)

## Tune command

```bash
grok --no-auto-update -r "<sessionId>" -p "Tune: <delta>" \
  --cwd "<cwd>" --output-format json --max-turns 10
```

Cap `parent_tune_count` at 3 per `node_id` before spawning a fresh worktree node.
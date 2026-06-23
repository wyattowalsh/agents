## Three-tier topology

1. **Parent harness** (Codex fleet, OpenCode Ensemble, Claude teams) owns the macro task graph.
2. **`grok-delegate` skill** owns wave taxonomy, session ledger, gates, and native command templates.
3. **Grok Build CLI** executes micro nodes via `-p`, `-r`, worktrees, leader pool, and optional ACP stdio.

## Session ledger

Parent maintains `grok-delegate-ledger.jsonl` (runtime, gitignored) with `node_id`, `wave`, `sessionId`, `worktree`, `agent`, `cwd`, `status`, `stopReason`, `parent_tune_count`.

Tune via `grok -r <sessionId> -p "<delta>"` when gates fail or scope shifts.

## Leader pool

For dense graphs: `grok agent leader --no-exit-on-disconnect --no-auto-update` once per cwd; clients use `grok agent --leader` or shared `--leader-socket`.

## JSON headless contract (fixture-verified)

```json
{
  "text": "...",
  "stopReason": "EndTurn",
  "sessionId": "uuid",
  "requestId": "uuid",
  "thought": "..."
}
```

## Safety

Never default `--always-approve` for cross-harness delegation. Cap `--max-turns` per wave type. Require explicit `--cwd`.
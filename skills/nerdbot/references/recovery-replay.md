# Recovery And Replay

## Recovery Model

Every mutating workflow should be recoverable from inventory, activity log, review queue, source map, and checkpoints.

Operation IDs and JSONL operation entries are provided by `nerdbot.operations`. Applied workflow commands append `activity/operations.jsonl`. Dry-run replay summaries are provided by `nerdbot.replay` and the `nerdbot replay` CLI command; use them before retrying or resuming interrupted work.

## Replay Requirements

- Re-run inventory after interruption.
- Compare intended layer changes with actual files.
- Rebuild indexes from source and wiki state when possible.
- Preserve append-only logs and avoid trying to erase failed attempts.
- Report quarantine items separately from verified work.

Replay results include `operation_id`, `status`, `changed`, `skipped`, `review_needed`, `failed`, and `resume_token`. Replay must not erase failed attempts or overwrite append-only logs.

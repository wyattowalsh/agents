# Recovery And Replay

## Recovery Model

Every mutating workflow should be recoverable from inventory, activity log, review queue, source map, and checkpoints.

`nerdbot.operations` owns operation IDs, the canonical JSONL journal, and the human activity projection. Every applied workflow holds the project-scoped `activity/.nerdbot-operation.lock` across the complete prepare, mutate, terminal-state, and projection batch. After creating any required coordination directory and lock file, it appends `prepared` before the first workflow data mutation. A successful batch appends `committed`; a normal caught exception appends `failed`; an intentional unresolved stop may append `review-needed`. `committed`, `failed`, and `review-needed` are terminal, so each operation ID has exactly one terminal transition.

An abrupt process stop can leave the last operation in `prepared`. A retry with the same deterministic intent key resumes that operation ID and reconciles byte-identical files and exact append-only rows before committing. A stop after `committed` but before its activity projection does not make the mutation incomplete: `repair_activity_log_projections()` restores only missing committed markers. An immediate same-intent retry recognizes a repaired latest commit and does not create a second operation. `failed` attempts remain durable; a later retry starts a new operation with the same intent prefix and a new unique suffix.

The journal parser is shared by replay and repair. It rejects malformed records, unknown enums, invalid or timezone-free timestamps, non-normalized paths, changed immutable payloads, duplicate `prepared` rows, terminal-first rows, duplicate terminals, and transitions after a terminal. Operation text that could forge a line-oriented projection—control, format, surrogate, newline, Unicode line/paragraph separator, or backtick characters—is rejected. Marker extraction recognizes only ASCII newline-delimited standalone markers, so Unicode separators embedded in legacy prose cannot suppress projection repair. The journal uses strict parsing and project locking rather than a hash chain.

## Replay Requirements

- Re-run inventory after interruption.
- Compare intended layer changes with actual files.
- Rebuild indexes from source and wiki state when possible.
- Preserve append-only logs and avoid trying to erase failed attempts.
- Treat `activity/operations.jsonl` as authoritative; never infer a committed operation solely from the human projection.
- Project only `committed` operations to `activity/log.md`.
- Key each projection with the exact standalone marker `<!-- nerdbot-operation-id: op-........-............ -->`; marker-like prose is not an operation marker.
- Repair a missing human projection by its validated operation ID instead of appending an uncorrelated duplicate.
- Report quarantine items separately from verified work.

Replay results include `operation_id`, `operation_state`, `status`, `changed`, `skipped`, `review_needed`, `failed`, and `resume_token`. `operation_state` is the canonical journal state; `status` is the replay classification. `prepared` and `review-needed` classify as `review-needed`, while `failed` classifies as `failed`. Replay must not erase failed attempts or overwrite append-only logs.

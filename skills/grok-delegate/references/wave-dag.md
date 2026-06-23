# Wave DAG on native Grok bash dispatch

Model parallel teams like OpenCode Ensemble waves, but parent harness dispatches `grok` subprocesses instead of `team_spawn`.

## Supported shape

1. **Wave 0** — parallel scouts (`-w w0-*`, read-biased, no overlapping writes)
2. **Gate G0** — parent synthesizes scout JSON; defines wave-1 slices and file ownership
3. **Wave 1** — parallel builders (distinct worktrees, distinct owners)
4. **Gate G1** — parent inspects diffs; merge policy explicit
5. **Wave 2** — parallel verify/review nodes
6. **Gate G2** — ship or tune

## Dependencies

Encode dependencies as parent gates, not Grok flags. Wave 1 cannot start until G0 completes.

## Tune edges

Any node may loop: `completed` → gate fail → `-r sessionId` tune → re-gate. Ledger tracks `parent_tune_count`.

## Fan-out limits

- Parent harness: scale to independent domains (orchestrator Pattern E).
- Grok per node: internal subagents only; depth 1.
- Worktrees: one writer per `-w` name.
- Leader pool: one leader per `(cwd, leader-socket)` for dense graphs.
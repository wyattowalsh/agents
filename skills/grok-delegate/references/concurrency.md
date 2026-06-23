# Concurrency and isolation

## Worktree naming

`w<wave>-<role>-<n>` — example: `w1-api-2`, `w0-scout-1`, `w2-review-1`.

Never assign two parallel builders the same `-w` value.

## Parent fan-out

Dispatch all independent wave nodes in one parent message (Pattern A). Each node is a separate `grok` subprocess.

## Grok internal fan-out

Grok may spawn internal subagents per node. Platform caps nested depth at **1** — do not delegate nested graphs to Grok; parent parallelizes siblings.

## Leader concurrency

One leader per cwd pool. Serialize leader start; parallelize client `-p` invocations against it.

## Resource hygiene

- `--max-turns` per wave defaults in SKILL.md
- Kill orphaned leaders after graph completion: `grok leader kill`
- Prune stale worktrees via `grok worktree` / git when parent graph completes
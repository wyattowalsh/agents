# Tasks

The cleanup is done. Do not open another wave for it.

## Done

- [x] `wagents` imports. The docs command is `docs`.
- [x] Cursor Task pin is `grok-4.7-xhigh`.
- [x] Docs generation writes `docs/src`, which Astro imports.
- [x] Removed the accidental warning path, the unused 22 MB skill-index module, and `planning/tmp` plus `planning/workspaces`.
- [x] Archived 24 finished OpenSpec changes with `--skip-specs` so older deltas would not delete newer spec scenarios.

## Stop

- [x] Do not collapse skills, hide agents, or rewrite instruction files into pointers as a cleanup.
- [x] Do not run a repo-wide `docs generate` just to prove the cleanup.
- [x] Do not archive `integrate-ideas-backlog` or `replace-supathings-with-things-plus-plus` from this change. The ideas file still has deferred rows. The Things++ manifest path is still inside that change, and the registry schema points at it.
- [x] Leave the other active OpenSpec changes as normal product work. They are not cleanup tasks.

## Later, only when that product work is touched

- [x] Moved `capability-manifest.json` to `config/things-plus-plus/` and pointed the registry schema at it. Removed the live `/mcp/supathings` client entries from `mcp.json`, `opencode.json`, Codex, and Grok config. The change stays open. `/mcp/supathings` remains on the ingress deny list.

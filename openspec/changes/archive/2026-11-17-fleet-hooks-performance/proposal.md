# Proposal

## Why

Every hook-enabled harness (Codex, Claude Code, Cursor, GitHub Copilot, Gemini CLI,
Grok Build, OpenCode) currently spawns one cold `python3` process per registered
policy per event. A single Bash tool call on Cursor fans out to 3+ subprocess
spawns (destructive-shell-guard, protected-file-guard, git-commit-push-guard,
image-input-optimizer-guard, research guards) before the tool ever runs, and the
image optimizer nests a second `uv run` subprocess inside that. `logical_policy`
was added to the registry schema by `fleet-hooks-parity` but was never backfilled
onto any row, so no per-event bundling or dedupe tooling can key off it yet. This
program builds a measured, staged path from per-policy cold-start spawns to
bundled/dedupe-optimized dispatch without weakening any enforce-tier guard.

## What Changes

- Baseline hook-timing instrumentation (`WAGENTS_HOOK_TIMING=1`) and a spawn-count
  inventory script so every later wave has a before/after measurement.
- Backfill `logical_policy` on every `config/hook-registry.json` row; narrow the
  image-input-optimizer-guard matcher off `.*`; add registry schema fields
  (`bundle_group`, `bundle_mode`) for the bundle contract; add dispatcher-side
  caches (module cache, argv fast-path, `lru_cache`, path memoization, audit
  sampling, git-context cache, image fast-exit).
- A new `wagents/hooks/bundle.py` module plus `wagents-hook.py --bundle` /
  `run-wagents-hook --bundle` CLI surface implementing the `enforce-chain`,
  `context-chain`, and `mixed` bundle contract (first-deny-wins semantics,
  budgeted timeouts).
- `wagents/hooks/render.py::collapse_bundle_entries()` plus fleet projection
  updates (Codex, Cursor, Claude, Gemini, Copilot guard entries, Grok, OpenCode
  bridge) so bundled policies emit a single spawn per event where safe.
- In-process image-input optimization, cross-event `logical_policy` dedupe, and
  harness-specific wins (Copilot parallel post-edit, Grok deny dedupe, in-process
  research stop-verifier, Gemini millisecond timeout rendering).
- An optional, default-off `wagents-hook-worker.py` warm-process mode for
  environments that want to opt into the largest available reduction.
- Incremental sync (registry sha256 skip), APM bundle-render parity, and a
  discovery registry parse cache for maintainer-facing sync/apm workflows.
- Hooks hub documentation for the new `WAGENTS_HOOK_PERF_TIER` staged rollout
  flag and promotion of the bundle contract into `openspec/specs/`.

## Impact

- Hook dispatch on Cursor/Codex/Claude/Gemini/Copilot/Grok/OpenCode gets fewer
  process spawns per event once `WAGENTS_HOOK_PERF_TIER` opts a harness into
  `g1`, `bundle`, or `worker` tiers; default tier (`legacy`) is fully
  behavior-neutral so no harness is force-migrated by this change alone.
  `render.py` fleet projection continues to emit the existing one-policy-per-spawn
  entries in the `legacy` tier.
- `config/hook-registry.json` gains `logical_policy` values on every row plus
  optional `bundle_group`/`bundle_mode` fields; schema updated to describe them.
- New module `wagents/hooks/bundle.py`, new script
  `scripts/hooks/hook_perf_inventory.py`, new optional worker
  `hooks/wagents-hook-worker.py` (disabled unless explicitly enabled).

## Scope

W0 through W8 of the Fleet Hooks Performance v2 plan
(`.cursor/plans/fleet_hooks_performance_v2_b354f4b6.plan.md`, read-only
reference — canonical task graph lives in this change's `tasks.md`).

## Out Of Scope

- `sync --apply --targets home` (user-approved only).
- Widening OpenCode/Grok fail-open behavior on dispatcher crash/timeout beyond
  the existing "explicit deny only" contract from `fleet-hooks-guard-expansion`.
- Crush, Antigravity, and Cherry Studio (no hook surface).
- Changing the enforce-tier deny transport contract established by
  `fleet-hooks-guard-expansion` (deny on stdout, exit 0 per harness).

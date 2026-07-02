# Proposal

## Why

`fleet-hooks-performance` delivered bundle collapse, dispatcher caches, and staged
`hook_perf.tier` rollout, but `hook_perf.tier` remains `legacy` in committed
`config/tooling-policy.json`. Cursor/Codex still emit six separate PreToolUse
spawns per Bash event, and GitHub Copilot still runs `./hooks/*.sh` rows that
`_shell_bundle_command()` cannot collapse into `{hook_runner} --bundle` spawns.
This change completes the **single** bundle-tier promotion after mega-bundle registry
work and Copilot dispatcher migration land.

## What Changes

- OpenSpec scaffold (`fleet-hooks-promotion`) with wave coordinator manifests W0–W7.
- Committed baseline JSON artifacts: `hook-perf-baseline-legacy.json` (W1) and
  `hook-perf-baseline-bundle.json` (W5).
- Registry mega-bundle: rename `cursor-shell-file-guards` / `codex-shell-file-guards`
  → `fleet-pre-tool-enforce`; add `git-commit-push-guard` to the same enforce-chain
  group; narrow `image-input-optimizer-guard` matcher off greedy `.*` patterns.
- Copilot dispatcher migration: `destructive_shell_guard.py`, `protected_file_guard.py`,
  `{hook_runner}` registry commands, and `fleet-pre-tool-enforce` bundle for Copilot
  PreToolUse rows.
- Tooling: `hook_perf_inventory.py --tier`, `scripts/hooks/hook_assurance.py`,
  `docs/runbooks/hook-performance.md`.
- **One** W5 promotion: `hook_perf.tier: bundle` + repo sync + APM materialize parity.
- CI `hook-perf` workflow_dispatch enhancement with hyperfine and 10% p95 regression gate
  vs committed baselines; hooks hub documentation update.

## Impact

- Cursor/Codex PreToolUse Bash spawn budget: ≤3 after promotion (mega-bundle + image +
  research bundles).
- GitHub Copilot PreToolUse: ≤2 after Copilot mega-bundle + git guard collapse.
- `legacy` tier tests remain byte-stable; bundle tier is opt-in via tooling policy until W5.

## Scope

Waves W0–W7 of Hooks Bundle Promotion v2 (`.cursor/plans/hooks_bundle_promotion_v2_39873d8c.plan.md`,
read-only reference — canonical task graph lives in this change's `tasks.md`).

## Out Of Scope

- `sync --apply --targets home` without explicit user approval.
- Worker-tier promotion (`hook_perf.tier: worker`).
- Crush, Antigravity, Cherry Studio harnesses.

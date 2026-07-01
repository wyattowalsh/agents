# Proposal

## Why

RTK (Rust Token Killer) can reduce token pressure for shell-heavy agent sessions, but its integration model is uneven across harnesses. Some clients use shell hooks, OpenCode uses a local plugin file, Codex uses instruction files, and app or MCP-only surfaces have no direct shell hook. Treating RTK as a normal repo plugin or skill would create duplicated ownership and stale generated instruction includes.

The repo needs a durable, doctor-verified integration plan that keeps RTK-owned local artifacts local, preserves repo hook and sync ownership, and gives maintainers safe dry-run visibility before any global harness patching.

## What Changes

- Add `config/rtk-integration.json` as the repo policy map for RTK tiers, init commands, verification commands, and non-goals.
- Add a `wagents rtk` CLI group with:
  - `doctor` for binary/version/package checks and per-harness posture.
  - `sync --dry-run` for planned `rtk init` commands.
  - `sync --apply` for explicit local application only.
  - `gain` as a thin savings-report wrapper.
- Add a non-fatal `rtk` row to `wagents self doctor`.
- Keep RTK out of `opencode.json`; RTK owns `~/.config/opencode/plugins/rtk.ts`.
- Keep shared instructions free of `@RTK.md`; platform-specific RTK awareness stays local or minimal.
- Repair the research hook handoff so an explicit implementation prompt after `/research` clears active read-only state for that session without disabling the research guard globally.

## Impact

- Maintainers can see RTK readiness across Claude, Cursor, OpenCode, Codex, Gemini, Copilot, Grok, and non-applicable surfaces.
- Fleet sync remains opt-in and auditable. `--dry-run` is the default.
- Existing repo-managed hooks continue to own safety and quality checks; RTK runs after those projections when applied.
- OpenCode, Codex, and generated instruction surfaces avoid the stale `@RTK.md` failure mode removed in the instruction-corpus cleanup.

## Scope

- RTK policy config, CLI doctor/sync/gain, focused tests, OpenSpec artifacts, and hook handoff fix.
- Planning artifacts with a hyperfine parallel task graph for the full fleet rollout.

## Out Of Scope

- Running `rtk init --apply` or live global installs during this change.
- Vendoring RTK hooks, plugins, or generated `RTK.md` files into the repo.
- Adding RTK to `opencode.json` plugin arrays.
- Custom Grok RTK rewrite hook implementation beyond specification and planning.
- Treating ChatGPT, Cherry Studio, or other MCP-only clients as hookable RTK targets.

## Risks

- RTK upstream changes init semantics: mitigate by doctor output and dry-run evidence instead of hard-coded "installed" assumptions.
- `rtk init -g --agent cursor` also touches Claude RTK assets: mitigate by preserving dry-run default and documenting ordering.
- Prompt-level Codex integration can reintroduce stale `@RTK.md`: mitigate with explicit no-shared-include policy and validation grep.
- Research read-only hooks can block approved implementation after a `/research` plan: mitigate with explicit implementation-handoff state clearing.
